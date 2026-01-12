from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import LoginForm, RegisterForm
from django.utils import timezone
from django.db import transaction

from .models import User, Member, UserSession, PasswordResetToken
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    MemberUpdateSerializer, UserUpdateSerializer, PasswordChangeSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    UserSessionSerializer, UserListSerializer
)
from common.permissions import IsOwnerOrReadOnly, IsChurchAdmin, IsSystemAdmin
from common.services import AuditService
from common.exceptions import AltarFundsException
import uuid
import secrets


class UserRegistrationView(generics.CreateAPIView):
    """User registration endpoint"""
    
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        """Register new user"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Log registration
            AuditService.log_user_action(
                user=user,
                action='USER_REGISTRATION',
                details={'ip_address': self.get_client_ip(request)},
                ip_address=self.get_client_ip(request)
            )
            
            response_data = {
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'message': 'Registration successful'
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserLoginView(generics.GenericAPIView):
    """User login endpoint"""
    
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        """Login user"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Create user session
        session = UserSession.objects.create(
            user=user,
            session_key=secrets.token_hex(20),
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            device_info=self.extract_device_info(request),
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Update last login
        user.last_login = timezone.now()
        user.last_login_ip = self.get_client_ip(request)
        user.last_login_device = request.META.get('HTTP_USER_AGENT', '')
        user.save(update_fields=['last_login', 'last_login_ip', 'last_login_device'])
        
        # Log login
        AuditService.log_user_action(
            user=user,
            action='USER_LOGIN',
            details={'session_id': session.id, 'ip_address': self.get_client_ip(request)},
            ip_address=self.get_client_ip(request)
        )
        
        response_data = {
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'session': UserSessionSerializer(session).data,
            'message': 'Login successful'
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def extract_device_info(self, request):
        """Extract device information from request"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        device_info = {
            'user_agent': user_agent,
            'platform': 'Unknown',
            'browser': 'Unknown',
        }
        
        # Simple device detection (can be enhanced with user-agent parsing library)
        if 'Mobile' in user_agent:
            device_info['platform'] = 'Mobile'
        elif 'Tablet' in user_agent:
            device_info['platform'] = 'Tablet'
        else:
            device_info['platform'] = 'Desktop'
        
        if 'Chrome' in user_agent:
            device_info['browser'] = 'Chrome'
        elif 'Firefox' in user_agent:
            device_info['browser'] = 'Firefox'
        elif 'Safari' in user_agent:
            device_info['browser'] = 'Safari'
        elif 'Edge' in user_agent:
            device_info['browser'] = 'Edge'
        
        return device_info


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """Logout user and invalidate session"""
    try:
        # Deactivate current session
        UserSession.objects.filter(
            user=request.user,
            is_active=True
        ).update(is_active=False)
        
        # Log logout
        AuditService.log_user_action(
            user=request.user,
            action='USER_LOGOUT',
            details={'ip_address': get_client_ip(request)},
            ip_address=get_client_ip(request)
        )
        
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': 'Logout failed', 'details': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile view"""
    
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Get current user"""
        return self.request.user
    
    def get(self, request, *args, **kwargs):
        """Get user profile"""
        return super().get(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        """Update user profile"""
        serializer = UserUpdateSerializer(
            instance=request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Log profile update
        AuditService.log_user_action(
            user=request.user,
            action='PROFILE_UPDATE',
            details={'updated_fields': list(request.data.keys())},
            ip_address=get_client_ip(request)
        )
        
        return Response(UserProfileSerializer(user).data)


class PasswordChangeView(generics.GenericAPIView):
    """Change user password"""
    
    serializer_class = PasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """Change password"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        
        # Log password change
        AuditService.log_user_action(
            user=request.user,
            action='PASSWORD_CHANGE',
            details={'ip_address': get_client_ip(request)},
            ip_address=get_client_ip(request)
        )
        
        return Response({'message': 'Password changed successfully'})


class PasswordResetRequestView(generics.GenericAPIView):
    """Request password reset"""
    
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        """Request password reset"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Create reset token
        token = PasswordResetToken.objects.create(
            user=user,
            token=uuid.uuid4(),
            expires_at=timezone.now() + timezone.timedelta(hours=1),
            ip_address=get_client_ip(request)
        )
        
        # Send reset email
        from common.services import send_email_notification
        reset_link = f"https://altarfunds.co.ke/reset-password/{token.token}/"
        
        send_email_notification.delay(
            subject="Password Reset - AltarFunds",
            message=f"""
            Dear {user.full_name},
            
            You requested a password reset for your AltarFunds account.
            
            Click the link below to reset your password:
            {reset_link}
            
            This link will expire in 1 hour.
            
            If you didn't request this, please ignore this email.
            
            AltarFunds Team
            """,
            recipient_list=[email]
        )
        
        # Log password reset request
        AuditService.log_user_action(
            user=user,
            action='PASSWORD_RESET_REQUEST',
            details={'ip_address': get_client_ip(request)},
            ip_address=get_client_ip(request)
        )
        
        return Response({'message': 'Password reset email sent'})


class PasswordResetConfirmView(generics.GenericAPIView):
    """Confirm password reset"""
    
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        """Confirm password reset"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        
        # Log password reset
        AuditService.log_user_action(
            user=user,
            action='PASSWORD_RESET_CONFIRM',
            details={'ip_address': get_client_ip(request)},
            ip_address=get_client_ip(request)
        )
        
        return Response({'message': 'Password reset successful'})


class UserSessionListView(generics.ListAPIView):
    """List user sessions"""
    
    serializer_class = UserSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get user's active sessions"""
        return UserSession.objects.filter(
            user=self.request.user,
            is_active=True
        ).order_by('-last_activity')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def revoke_session(request, session_id):
    """Revoke a user session"""
    try:
        session = UserSession.objects.get(
            id=session_id,
            user=request.user,
            is_active=True
        )
        session.is_active = False
        session.save()
        
        return Response({'message': 'Session revoked successfully'})
    
    except UserSession.DoesNotExist:
        return Response(
            {'error': 'Session not found'},
            status=status.HTTP_404_NOT_FOUND
        )


class UserListView(generics.ListAPIView):
    """List users (admin only)"""
    
    serializer_class = UserListSerializer
    permission_classes = [IsChurchAdmin]
    filterset_fields = ['role', 'church', 'is_active']
    search_fields = ['first_name', 'last_name', 'email']
    ordering_fields = ['created_at', 'last_login', 'first_name']
    
    def get_queryset(self):
        """Get users based on user role"""
        user = self.request.user
        
        if user.role == 'system_admin':
            return User.objects.all()
        elif user.role == 'denomination_admin':
            # Users from all churches in denomination
            return User.objects.filter(church__denomination=user.church.denomination)
        else:
            # Users from same church
            return User.objects.filter(church=user.church)


class UserDetailView(generics.RetrieveUpdateAPIView):
    """User detail view (admin only)"""
    
    serializer_class = UserProfileSerializer
    permission_classes = [IsChurchAdmin]
    
    def get_queryset(self):
        """Get users based on user role"""
        user = self.request.user
        
        if user.role == 'system_admin':
            return User.objects.all()
        elif user.role == 'denomination_admin':
            return User.objects.filter(church__denomination=user.church.denomination)
        else:
            return User.objects.filter(church=user.church)


@api_view(['POST'])
@permission_classes([IsChurchAdmin])
def suspend_user(request, user_id):
    """Suspend a user"""
    try:
        user = User.objects.get(id=user_id)
        
        # Check permissions
        if not can_manage_user(request.user, user):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        reason = request.data.get('reason', 'No reason provided')
        until = request.data.get('until')
        
        user.suspend(reason, until)
        
        # Log suspension
        AuditService.log_user_action(
            user=request.user,
            action='USER_SUSPENSION',
            details={
                'target_user': user.email,
                'reason': reason,
                'until': until
            },
            ip_address=get_client_ip(request)
        )
        
        return Response({'message': 'User suspended successfully'})
    
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsChurchAdmin])
def unsuspend_user(request, user_id):
    """Unsuspend a user"""
    try:
        user = User.objects.get(id=user_id)
        
        # Check permissions
        if not can_manage_user(request.user, user):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user.unsuspend()
        
        # Log unsuspension
        AuditService.log_user_action(
            user=request.user,
            action='USER_UNSUSPENSION',
            details={'target_user': user.email},
            ip_address=get_client_ip(request)
        )
        
        return Response({'message': 'User unsuspended successfully'})
    
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )


# Helper functions
def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def can_manage_user(admin_user, target_user):
    """Check if admin user can manage target user"""
    if admin_user.role == 'system_admin':
        return True
    elif admin_user.role == 'denomination_admin':
        return (
            target_user.church and
            target_user.church.denomination == admin_user.church.denomination and
            target_user.role not in ['denomination_admin', 'system_admin']
        )
    else:
        return (
            target_user.church == admin_user.church and
            target_user.role not in ['pastor', 'treasurer', 'auditor', 'denomination_admin', 'system_admin']
        )

# Template-based Authentication Views

class RegisterView(View):
    """Handles user registration for the web interface."""
    def get(self, request):
        form = RegisterForm()
        return render(request, 'auth/register.html', {'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('auth:login')
        return render(request, 'auth/register.html', {'form': form})

class LoginView(View):
    """Handles user login for the web interface."""
    def get(self, request):
        form = LoginForm()
        return render(request, 'auth/login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                
                # Check if user is registered to a church
                if not user.church:
                    messages.info(request, 'Please register your church to continue.')
                    return redirect('churches:register')
                
                # Redirect to dashboard or home page after login
                return redirect('dashboard:home')
            else:
                messages.error(request, 'Invalid email or password.')
        return render(request, 'auth/login.html', {'form': form})

class LogoutView(View):
    """Handles user logout for the web interface."""
    def get(self, request):
        logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('auth:login')

