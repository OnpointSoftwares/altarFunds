from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django import forms

from .models import (
    Denomination, Church, Campus, Department, SmallGroup,
    ChurchBankAccount, MpesaAccount, ChurchDocument
)
from .serializers import (
    DenominationSerializer, ChurchSerializer, ChurchRegistrationSerializer,
    CampusSerializer, DepartmentSerializer, SmallGroupSerializer,
    ChurchBankAccountSerializer, MpesaAccountSerializer,
    ChurchListSerializer, ChurchSummarySerializer,
    ChurchVerificationSerializer, ChurchStatusUpdateSerializer
)
from common.permissions import (
    IsChurchAdmin, IsDenominationAdmin, IsSystemAdmin, 
    CanApproveChurches, CanManageChurch, IsMember
)
from common.services import AuditService
from common.exceptions import AltarFundsException
import uuid


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def join_church(request):
    """Join a church using church code."""
    church_code = request.data.get('church_code', '').strip()
    church_name = request.data.get('church_name', '').strip()
    user_id = request.data.get('user_id')
    
    if not church_code:
        return Response(
            {'error': 'Church code is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Find church by code
        church = Church.objects.get(code=church_code.upper())
        
        # Get current user
        user = request.user
        
        # Assign church to user
        user.church = church
        user.save()
        
        return Response({
            'message': f'Successfully joined {church.name}',
            'church': {
                'id': church.id,
                'name': church.name,
                'code': church.code
            }
        }, status=status.HTTP_200_OK)
        
    except Church.DoesNotExist:
        return Response(
            {'error': 'Invalid church code. Please check and try again.'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to join church: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class DenominationListCreateView(generics.ListCreateAPIView):
    """Denomination list and create view"""
    
    serializer_class = DenominationSerializer
    permission_classes = [IsDenominationAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        """Get denominations based on user role"""
        user = self.request.user
        
        if user.role == 'system_admin':
            return Denomination.objects.all()
        else:
            return Denomination.objects.filter(is_active=True)
    
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            denomination = serializer.save()
            
            # Log creation
            AuditService.log_user_action(
                user=request.user,
                action='DENOMINATION_CREATION',
                details={'denomination': denomination.name},
                ip_address=get_client_ip(request)
            )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DenominationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Denomination detail view"""
    
    serializer_class = DenominationSerializer
    permission_classes = [IsDenominationAdmin]
    
    def get_queryset(self):
        """Get denominations based on user role"""
        user = self.request.user
        
        if user.role == 'system_admin':
            return Denomination.objects.all()
        else:
            return Denomination.objects.filter(is_active=True)


class ChurchListCreateView(generics.ListCreateAPIView):
    """Church list and create view"""
    
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['church_type', 'status', 'denomination', 'is_active']
    search_fields = ['name', 'church_code', 'city', 'county', 'senior_pastor_name']
    ordering_fields = ['name', 'created_at', 'membership_count']
    
    def get_serializer_class(self):
        """Get appropriate serializer based on request method"""
        if self.request.method == 'POST':
            return ChurchRegistrationSerializer
        return ChurchSerializer
    
    def get_queryset(self):
        """Get churches based on user role"""
        user = self.request.user
        
        if user.role == 'system_admin':
            return Church.objects.all()
        elif user.role == 'denomination_admin':
            return Church.objects.filter(denomination=user.church.denomination)
        else:
            return Church.objects.filter(id=user.church.id)
    
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            church = serializer.save()
            
            # Log registration
            AuditService.log_user_action(
                user=request.user,
                action='CHURCH_REGISTRATION',
                details={'church': church.name, 'church_code': church.church_code},
                ip_address=get_client_ip(request)
            )
            
            # Send notification to admins
            from common.services import NotificationService
            NotificationService.send_church_registration_notification(church)
        
        return Response(ChurchSerializer(church).data, status=status.HTTP_201_CREATED)


class ChurchDetailView(generics.RetrieveUpdateAPIView):
    """Church detail view"""
    
    serializer_class = ChurchSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get churches based on user role"""
        user = self.request.user
        
        if user.role == 'system_admin':
            return Church.objects.all()
        elif user.role == 'denomination_admin':
            return Church.objects.filter(denomination=user.church.denomination)
        else:
            return Church.objects.filter(id=user.church.id)
    
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            instance=self.get_object(),
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            church = serializer.save()
            
            # Log update
            AuditService.log_user_action(
                user=request.user,
                action='CHURCH_UPDATE',
                details={
                    'church': church.name,
                    'updated_fields': list(request.data.keys())
                },
                ip_address=get_client_ip(request)
            )
        
        return Response(serializer.data)


class ChurchVerificationView(generics.UpdateAPIView):
    """Church verification view"""
    
    serializer_class = ChurchVerificationSerializer
    permission_classes = [IsDenominationAdmin]
    
    def get_queryset(self):
        """Get churches pending verification"""
        user = self.request.user
        
        if user.role == 'system_admin':
            return Church.objects.filter(status='pending')
        else:
            return Church.objects.filter(
                denomination=user.church.denomination,
                status='pending'
            )
    
    def patch(self, request, *args, **kwargs):
        church = self.get_object()
        
        with transaction.atomic():
            church.verify(request.user)
            
            # Log verification
            AuditService.log_user_action(
                user=request.user,
                action='CHURCH_VERIFICATION',
                details={'church': church.name},
                ip_address=get_client_ip(request)
            )
            
            # Send verification notification
            from common.services import NotificationService
            NotificationService.send_church_verification_notification(church)
        
        return Response({
            'message': 'Church verified successfully',
            'church': ChurchSerializer(church).data
        })


class ChurchStatusUpdateView(generics.UpdateAPIView):
    """Church status update view"""
    
    serializer_class = ChurchStatusUpdateSerializer
    permission_classes = [IsDenominationAdmin]
    
    def get_queryset(self):
        """Get churches based on user role"""
        user = self.request.user
        
        if user.role == 'system_admin':
            return Church.objects.all()
        else:
            return Church.objects.filter(denomination=user.church.denomination)
    
    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            instance=self.get_object(),
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        church = serializer.save()
        
        return Response({
            'message': 'Church status updated successfully',
            'church': ChurchSerializer(church).data
        })


class CampusListCreateView(generics.ListCreateAPIView):
    """Campus list and create view"""
    
    serializer_class = CampusSerializer
    permission_classes = [IsChurchAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['church', 'is_active', 'is_main_campus']
    search_fields = ['name', 'city', 'campus_pastor_name']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        """Get campuses based on user role"""
        user = self.request.user
        
        if user.role == 'system_admin':
            return Campus.objects.all()
        elif user.role == 'denomination_admin':
            return Campus.objects.filter(church__denomination=user.church.denomination)
        else:
            return Campus.objects.filter(church=user.church)
    
    def perform_create(self, serializer):
        """Create campus with audit trail"""
        campus = serializer.save()
        
        # Log creation
        AuditService.log_user_action(
            user=self.request.user,
            action='CAMPUS_CREATION',
            details={'campus': campus.name, 'church': campus.church.name},
            ip_address=get_client_ip(self.request)
        )


class CampusDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Campus detail view"""
    
    serializer_class = CampusSerializer
    permission_classes = [IsChurchAdmin]
    
    def get_queryset(self):
        """Get campuses based on user role"""
        user = self.request.user
        
        if user.role == 'system_admin':
            return Campus.objects.all()
        elif user.role == 'denomination_admin':
            return Campus.objects.filter(church__denomination=user.church.denomination)
        else:
            return Campus.objects.filter(church=user.church)


class DepartmentListCreateView(generics.ListCreateAPIView):
    """Department list and create view"""
    
    serializer_class = DepartmentSerializer
    permission_classes = [IsChurchAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['church', 'department_type', 'is_active', 'has_budget']
    search_fields = ['name', 'leader_name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        """Get departments based on user role"""
        user = self.request.user
        
        if user.role == 'system_admin':
            return Department.objects.all()
        elif user.role == 'denomination_admin':
            return Department.objects.filter(church__denomination=user.church.denomination)
        else:
            return Department.objects.filter(church=user.church)
    
    def perform_create(self, serializer):
        """Create department with audit trail"""
        department = serializer.save()
        
        # Log creation
        AuditService.log_user_action(
            user=self.request.user,
            action='DEPARTMENT_CREATION',
            details={'department': department.name, 'church': department.church.name},
            ip_address=get_client_ip(self.request)
        )


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Department detail view"""
    
    serializer_class = DepartmentSerializer
    permission_classes = [IsChurchAdmin]
    
    def get_queryset(self):
        """Get departments based on user role"""
        user = self.request.user
        
        if user.role == 'system_admin':
            return Department.objects.all()
        elif user.role == 'denomination_admin':
            return Department.objects.filter(church__denomination=user.church.denomination)
        else:
            return Department.objects.filter(church=user.church)


class SmallGroupListCreateView(generics.ListCreateAPIView):
    """Small group list and create view"""
    
    serializer_class = SmallGroupSerializer
    permission_classes = [IsChurchAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['church', 'campus', 'group_type', 'is_active']
    search_fields = ['name', 'leader_name', 'meeting_location']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        """Get small groups based on user role"""
        user = self.request.user
        
        if user.role == 'system_admin':
            return SmallGroup.objects.all()
        elif user.role == 'denomination_admin':
            return SmallGroup.objects.filter(church__denomination=user.church.denomination)
        else:
            return SmallGroup.objects.filter(church=user.church)
    
    def perform_create(self, serializer):
        """Create small group with audit trail"""
        small_group = serializer.save()
        
        # Log creation
        AuditService.log_user_action(
            user=self.request.user,
            action='SMALL_GROUP_CREATION',
            details={'group': small_group.name, 'church': small_group.church.name},
            ip_address=get_client_ip(self.request)
        )


class SmallGroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Small group detail view"""
    
    serializer_class = SmallGroupSerializer
    permission_classes = [IsChurchAdmin]
    
    def get_queryset(self):
        """Get small groups based on user role"""
        user = self.request.user
        
        if user.role == 'system_admin':
            return SmallGroup.objects.all()
        elif user.role == 'denomination_admin':
            return SmallGroup.objects.filter(church__denomination=user.church.denomination)
        else:
            return SmallGroup.objects.filter(church=user.church)


class ChurchBankAccountListCreateView(generics.ListCreateAPIView):
    """Church bank account list and create view"""
    
    serializer_class = ChurchBankAccountSerializer
    permission_classes = [IsChurchAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['church', 'account_type', 'is_active', 'is_primary']
    search_fields = ['account_name', 'bank_name', 'bank_branch']
    ordering_fields = ['bank_name', 'created_at']
    
    def get_queryset(self):
        """Get bank accounts based on user role"""
        user = self.request.user
        
        if user.role == 'system_admin':
            return ChurchBankAccount.objects.all()
        elif user.role == 'denomination_admin':
            return ChurchBankAccount.objects.filter(church__denomination=user.church.denomination)
        else:
            return ChurchBankAccount.objects.filter(church=user.church)
    
    def perform_create(self, serializer):
        """Create bank account with audit trail"""
        account = serializer.save()
        
        # Log creation
        AuditService.log_user_action(
            user=self.request.user,
            action='BANK_ACCOUNT_CREATION',
            details={
                'account': account.account_name,
                'church': account.church.name,
                'bank': account.bank_name
            },
            ip_address=get_client_ip(self.request)
        )


class ChurchBankAccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Church bank account detail view"""
    
    serializer_class = ChurchBankAccountSerializer
    permission_classes = [IsChurchAdmin]
    
    def get_queryset(self):
        """Get bank accounts based on user role"""
        user = self.request.user
        
        if user.role == 'system_admin':
            return ChurchBankAccount.objects.all()
        elif user.role == 'denomination_admin':
            return ChurchBankAccount.objects.filter(church__denomination=user.church.denomination)
        else:
            return ChurchBankAccount.objects.filter(church=user.church)


class MpesaAccountListCreateView(generics.ListCreateAPIView):
    """M-Pesa account list and create view"""
    
    serializer_class = MpesaAccountSerializer
    permission_classes = [IsChurchAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['church', 'account_type', 'is_active']
    search_fields = ['account_name', 'business_number']
    ordering_fields = ['account_type', 'created_at']
    
    def get_queryset(self):
        """Get M-Pesa accounts based on user role"""
        user = self.request.user
        
        if user.role == 'system_admin':
            return MpesaAccount.objects.all()
        elif user.role == 'denomination_admin':
            return MpesaAccount.objects.filter(church__denomination=user.church.denomination)
        else:
            return MpesaAccount.objects.filter(church=user.church)
    
    def perform_create(self, serializer):
        """Create M-Pesa account with audit trail"""
        account = serializer.save()
        
        # Log creation
        AuditService.log_user_action(
            user=self.request.user,
            action='MPESA_ACCOUNT_CREATION',
            details={
                'account': account.account_name,
                'church': account.church.name,
                'type': account.account_type,
                'business_number': account.business_number
            },
            ip_address=get_client_ip(self.request)
        )


class MpesaAccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    """M-Pesa account detail view"""
    
    serializer_class = MpesaAccountSerializer
    permission_classes = [IsChurchAdmin]
    
    def get_queryset(self):
        """Get M-Pesa accounts based on user role"""
        user = self.request.user
        
        if user.role == 'system_admin':
            return MpesaAccount.objects.all()
        elif user.role == 'denomination_admin':
            return MpesaAccount.objects.filter(church__denomination=user.church.denomination)
        else:
            return MpesaAccount.objects.filter(church=user.church)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def church_summary(request, church_id):
    """Get church summary with statistics"""
    try:
        church = Church.objects.get(id=church_id)
        
        # Check permissions
        if not can_view_church(request.user, church):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ChurchSummarySerializer(church)
        return Response(serializer.data)
    
    except Church.DoesNotExist:
        return Response(
            {'error': 'Church not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def church_options(request):
    """Get church options for dropdowns"""
    """Get church options for dropdowns"""
    user = request.user
    
    if user.role == 'system_admin':
        churches = Church.objects.filter(is_active=True)
    elif user.role == 'denomination_admin':
        churches = Church.objects.filter(
            denomination=user.church.denomination,
            is_active=True
        )
    else:
        churches = Church.objects.filter(id=user.church.id, is_active=True)
    
    serializer = ChurchListSerializer(churches, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def department_options(request):
    """Get department options for dropdowns"""
    user = request.user
    
    if user.role == 'system_admin':
        departments = Department.objects.filter(is_active=True)
    elif user.role == 'denomination_admin':
        departments = Department.objects.filter(
            church__denomination=user.church.denomination,
            is_active=True
        )
    else:
        departments = Department.objects.filter(church=user.church, is_active=True)
    
    serializer = DepartmentListSerializer(departments, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def small_group_options(request):
    """Get small group options for dropdowns"""
    user = request.user
    
    if user.role == 'system_admin':
        groups = SmallGroup.objects.filter(is_active=True)
    elif user.role == 'denomination_admin':
        groups = SmallGroup.objects.filter(
            church__denomination=user.church.denomination,
            is_active=True
        )
    else:
        groups = SmallGroup.objects.filter(church=user.church, is_active=True)
    
    serializer = SmallGroupListSerializer(groups, many=True)
    return Response(serializer.data)


# Helper functions
def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def can_view_church(user, church):
    """Check if user can view church"""
    if user.role == 'system_admin':
        return True
    elif user.role == 'denomination_admin':
        return church.denomination == user.church.denomination
    else:
        return church == user.church


# Template-based Church Registration Views

class ChurchDocumentForm(forms.ModelForm):
    """Form for uploading church documents."""
    
    class Meta:
        model = ChurchDocument
        fields = ['document_type', 'title', 'file', 'description']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-control form-control-lg'}),
            'title': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'file': forms.FileInput(attrs={'class': 'form-control form-control-lg'}),
            'description': forms.Textarea(attrs={'class': 'form-control form-control-lg', 'rows': 2}),
        }


class ChurchRegistrationForm(forms.ModelForm):
    """Form for church registration."""
    
    # Required documents
    registration_certificate = forms.FileField(
        label="Registration Certificate",
        widget=forms.FileInput(attrs={'class': 'form-control form-control-lg', 'required': 'required'}),
        required=True,
        help_text="Upload your church registration certificate"
    )
    
    tax_exemption = forms.FileField(
        label="Tax Exemption Certificate",
        widget=forms.FileInput(attrs={'class': 'form-control form-control-lg'}),
        required=False,
        help_text="Upload tax exemption certificate if available"
    )
    
    constitution = forms.FileField(
        label="Church Constitution",
        widget=forms.FileInput(attrs={'class': 'form-control form-control-lg'}),
        required=False,
        help_text="Upload church constitution or bylaws"
    )
    
    pastor_appointment = forms.FileField(
        label="Pastor Appointment Letter",
        widget=forms.FileInput(attrs={'class': 'form-control form-control-lg'}),
        required=False,
        help_text="Upload letter appointing the senior pastor"
    )
    
    class Meta:
        model = Church
        fields = ['name', 'address_line1', 'address_line2', 'city', 'county', 'postal_code', 
                 'phone_number', 'email', 'website', 'denomination', 'senior_pastor_name', 
                 'senior_pastor_phone', 'senior_pastor_email', 'established_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'city': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'county': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-lg'}),
            'website': forms.URLInput(attrs={'class': 'form-control form-control-lg'}),
            'denomination': forms.Select(attrs={'class': 'form-control form-control-lg'}),
            'senior_pastor_name': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'senior_pastor_phone': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'senior_pastor_email': forms.EmailInput(attrs={'class': 'form-control form-control-lg'}),
            'established_date': forms.DateInput(attrs={'class': 'form-control form-control-lg', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['denomination'].queryset = Denomination.objects.filter(is_active=True)
        self.fields['denomination'].empty_label = "Select a denomination"
        
        # Reorder fields to put documents at the end
        field_order = ['name', 'denomination', 'phone_number', 'email', 'website',
                      'senior_pastor_name', 'senior_pastor_phone', 'senior_pastor_email', 'established_date',
                      'address_line1', 'address_line2', 'city', 'county', 'postal_code',
                      'registration_certificate', 'tax_exemption', 'constitution', 'pastor_appointment']
        self.order_fields(field_order)


class ChurchRegistrationView(View):
    """Handles church registration for the web interface."""
    
    def get(self, request):
        form = ChurchRegistrationForm()
        return render(request, 'churches/register.html', {'form': form})

    def post(self, request):
        form = ChurchRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                # Create the church
                church = form.save()
                
                # Generate church code if not set
                if not church.church_code:
                    church.generate_church_code()
                
                # Handle document uploads
                documents_to_create = []
                
                # Registration Certificate (required)
                if 'registration_certificate' in request.FILES:
                    documents_to_create.append(ChurchDocument(
                        church=church,
                        document_type='registration_certificate',
                        title='Church Registration Certificate',
                        file=request.FILES['registration_certificate'],
                        uploaded_by=request.user,
                        description='Official church registration certificate'
                    ))
                
                # Tax Exemption Certificate (optional)
                if 'tax_exemption' in request.FILES:
                    documents_to_create.append(ChurchDocument(
                        church=church,
                        document_type='tax_exemption',
                        title='Tax Exemption Certificate',
                        file=request.FILES['tax_exemption'],
                        uploaded_by=request.user,
                        description='Tax exemption certificate for the church'
                    ))
                
                # Constitution/Bylaws (optional)
                if 'constitution' in request.FILES:
                    documents_to_create.append(ChurchDocument(
                        church=church,
                        document_type='constitution',
                        title='Church Constitution',
                        file=request.FILES['constitution'],
                        uploaded_by=request.user,
                        description='Church constitution or bylaws document'
                    ))
                
                # Pastor Appointment Letter (optional)
                if 'pastor_appointment' in request.FILES:
                    documents_to_create.append(ChurchDocument(
                        church=church,
                        document_type='pastor_appointment',
                        title='Pastor Appointment Letter',
                        file=request.FILES['pastor_appointment'],
                        uploaded_by=request.user,
                        description='Official letter appointing the senior pastor'
                    ))
                
                # Bulk create all documents
                if documents_to_create:
                    ChurchDocument.objects.bulk_create(documents_to_create)
                
                # Associate the current user with this church
                request.user.church = church
                request.user.save()
                
                messages.success(request, f'Church "{church.name}" registered successfully with {len(documents_to_create)} documents uploaded!')
                return redirect('dashboard:home')
        
        return render(request, 'churches/register.html', {'form': form})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def transfer_church(request):
    """Transfer from one church to another"""
    from_church_id = request.data.get('from_church_id')
    to_church_id = request.data.get('to_church_id')
    reason = request.data.get('reason', '')
    request_letter = request.data.get('request_transfer_letter', False)
    
    if not from_church_id or not to_church_id:
        return Response({
            'success': False,
            'message': 'From church and to church are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if from_church_id == to_church_id:
        return Response({
            'success': False,
            'message': 'Cannot transfer to the same church'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            user = request.user
            from_church = Church.objects.get(id=from_church_id)
            to_church = Church.objects.get(id=to_church_id)
            
            # Verify user belongs to from_church
            if user.church != from_church:
                return Response({
                    'success': False,
                    'message': 'You can only transfer from your current church'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create transfer record (you might need to create a TransferRequest model)
            transfer_data = {
                'user': user,
                'from_church': from_church,
                'to_church': to_church,
                'reason': reason,
                'status': 'pending',
                'reference': f"TF-{uuid.uuid4().hex[:12].upper()}"
            }
            
            # Log the transfer request
            AuditService.log_user_action(
                user=user,
                action='CHURCH_TRANSFER_REQUEST',
                details={
                    'from_church': from_church.name,
                    'to_church': to_church.name,
                    'reason': reason
                },
                ip_address=get_client_ip(request)
            )
            
            return Response({
                'success': True,
                'data': transfer_data,
                'message': 'Transfer request submitted successfully'
            }, status=status.HTTP_200_OK)
            
    except Church.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Church not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Transfer request failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([CanApproveChurches])
def pending_churches(request):
    """Get list of pending church registrations (Super Admin only)"""
    try:
        pending_churches = Church.objects.filter(status='pending').order_by('-created_at')
        
        serializer = ChurchListSerializer(pending_churches, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Failed to fetch pending churches: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([CanApproveChurches])
def approve_church(request, church_id):
    """Approve a church registration (Super Admin only)"""
    try:
        with transaction.atomic():
            church = Church.objects.get(id=church_id)
            
            if church.status != 'pending':
                return Response({
                    'success': False,
                    'message': 'Church is not pending approval'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            church.status = 'verified'
            church.approved_by = request.user
            church.approved_date = timezone.now()
            church.save()
            
            # Log approval
            AuditService.log_user_action(
                user=request.user,
                action='CHURCH_APPROVAL',
                details={'church': church.name},
                ip_address=get_client_ip(request)
            )
            
            # Send notification to church admin
            from common.services import NotificationService
            NotificationService.send_church_approval_notification(church)
            
            return Response({
                'success': True,
                'message': f'Church "{church.name}" approved successfully'
            }, status=status.HTTP_200_OK)
            
    except Church.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Church not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Church approval failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([CanApproveChurches])
def reject_church(request, church_id):
    """Reject a church registration (Super Admin only)"""
    reason = request.data.get('reason', '')
    
    if not reason:
        return Response({
            'success': False,
            'message': 'Rejection reason is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            church = Church.objects.get(id=church_id)
            
            if church.status != 'pending':
                return Response({
                    'success': False,
                    'message': 'Church is not pending approval'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            church.status = 'rejected'
            church.rejection_reason = reason
            church.rejected_by = request.user
            church.rejected_date = timezone.now()
            church.save()
            
            # Log rejection
            AuditService.log_user_action(
                user=request.user,
                action='CHURCH_REJECTION',
                details={
                    'church': church.name,
                    'reason': reason
                },
                ip_address=get_client_ip(request)
            )
            
            # Send notification to church admin
            from common.services import NotificationService
            NotificationService.send_church_rejection_notification(church, reason)
            
            return Response({
                'success': True,
                'message': f'Church "{church.name}" rejected successfully'
            }, status=status.HTTP_200_OK)
            
    except Church.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Church not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Church rejection failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def church_members(request, church_id):
    """Get list of church members (Church Admin only)"""
    try:
        user = request.user
        
        # Check if user is church admin or system admin
        if user.role not in ['pastor', 'treasurer', 'auditor', 'denomination_admin', 'system_admin']:
            return Response({
                'success': False,
                'message': 'Insufficient permissions'
            }, status=status.HTTP_403_FORBIDDEN)
        
        church = Church.objects.get(id=church_id)
        
        # Check if user belongs to this church (except system admin)
        if user.role != 'system_admin' and user.church != church:
            return Response({
                'success': False,
                'message': 'You can only view members of your own church'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get members
        from accounts.models import Member
        members = Member.objects.filter(church=church).select_related('user')
        
        member_data = []
        for member in members:
            member_data.append({
                'id': member.id,
                'user_id': member.user.id,
                'name': member.user.get_full_name(),
                'email': member.user.email,
                'phone': member.user.phone_number,
                'membership_number': member.membership_number,
                'membership_status': member.membership_status,
                'joined_date': member.membership_date,
                'is_tithe_payer': member.is_tithe_payer
            })
        
        return Response({
            'success': True,
            'data': {
                'church': {
                    'id': church.id,
                    'name': church.name
                },
                'members': member_data,
                'total_members': len(member_data)
            }
        }, status=status.HTTP_200_OK)
        
    except Church.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Church not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Failed to fetch church members: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
