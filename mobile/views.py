from rest_framework import generics, status, views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta, date
import uuid
import requests

from .models import (
    MobileDevice, MobileAppSettings, MobileAppVersion, 
    UserSession, MobileNotification, MobileAppAnalytics, MobileAppFeedback
)
from .serializers import (
    MobileDeviceSerializer, MobileAppSettingsSerializer, MobileAppVersionSerializer,
    UserSessionSerializer, MobileNotificationSerializer, MobileAppAnalyticsSerializer,
    MobileAppFeedbackSerializer, MobileLoginSerializer, MobileRegisterDeviceSerializer,
    MobilePushNotificationSerializer, MobileAppConfigSerializer, MobileUserProfileSerializer,
    MobileGivingSummarySerializer, MobileChurchInfoSerializer, MobileQuickActionSerializer,
    MobileGoogleLoginSerializer, MobileRegisterSerializer, MemberSerializer
)
from common.serializers import UserSerializer
from django.contrib.auth import get_user_model
from accounts.models import Member
from common.permissions import IsOwnerOrReadOnly, CanManageChurchFinances
from common.pagination import StandardResultsSetPagination
from common.services import NotificationService, AuditService
from .services import MobileAuthService, MobileNotificationService, MobileAnalyticsService

User = get_user_model()


class MobileLoginView(views.APIView):
    """Mobile login endpoint"""
    
    permission_classes = []
    
    def post(self, request):
        """Handle mobile login"""
        serializer = MobileLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Create or update device
            device_data = {
                'user': user,
                'device_token': serializer.validated_data.get('device_token'),
                'device_type': serializer.validated_data.get('device_type', 'android'),
                'device_id': serializer.validated_data.get('device_id'),
                'app_version': serializer.validated_data.get('app_version'),
                'os_version': serializer.validated_data.get('os_version')
            }
            
            device = MobileAuthService.register_device(device_data)
            
            # Create session
            session = MobileAuthService.create_session(user, device, request)
            
            # Generate tokens
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            
            # Log login
            AuditService.log_user_action(
                user=user,
                action='MOBILE_LOGIN',
                details={
                    'device_type': device.device_type,
                    'app_version': device.app_version,
                    'ip_address': request.META.get('REMOTE_ADDR')
                }
            )
            
            return Response({
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'session_id': session.session_token,
                'user': UserSerializer(user).data,
                'member': MemberSerializer(user.member_profile).data if hasattr(user, 'member_profile') else None,
                'device': MobileDeviceSerializer(device).data
            })
        
        return Response({
            'error': True,
            'message': 'Login failed. Please check your email and password.',
            'details': serializer.errors,
            'error_code': 'INVALID_CREDENTIALS'
        }, status=status.HTTP_400_BAD_REQUEST)


class MobileGoogleLoginView(views.APIView):
    """Google Sign-In login endpoint (ID token)"""

    permission_classes = []

    def post(self, request):
        serializer = MobileGoogleLoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        id_token = serializer.validated_data['firebase_token'] if 'firebase_token' in serializer.validated_data else serializer.validated_data.get('id_token')
        if not id_token:
            return Response({'error': 'id_token is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify token with Google tokeninfo (keeps Android side free of Firebase requirements)
        try:
            token_info_resp = requests.get(
                'https://oauth2.googleapis.com/tokeninfo',
                params={'id_token': id_token},
                timeout=10
            )
            if token_info_resp.status_code != 200:
                return Response({'error': 'Invalid Google token'}, status=status.HTTP_400_BAD_REQUEST)

            token_info = token_info_resp.json()
        except Exception:
            return Response({'error': 'Token verification failed'}, status=status.HTTP_400_BAD_REQUEST)

        email = (token_info.get('email') or '').lower()
        sub = token_info.get('sub')

        if not email or not sub:
            return Response({'error': 'Invalid token payload'}, status=status.HTTP_400_BAD_REQUEST)

        # Find or create user
        user = User.objects.filter(firebase_uid=sub).first() or User.objects.filter(email=email).first()
        if not user:
            user = User.objects.create_user(email=email)
            user.set_unusable_password()
            user.firebase_uid = sub
            user.is_email_verified = token_info.get('email_verified') == 'true'
            user.save()
            Member.objects.get_or_create(user=user)
        else:
            if not user.firebase_uid:
                user.firebase_uid = sub
                user.save(update_fields=['firebase_uid'])
            Member.objects.get_or_create(user=user)

        # Register/update device
        device_token = serializer.validated_data.get('device_token') or f"anon-{uuid.uuid4()}"
        device_data = {
            'user': user,
            'device_token': device_token,
            'device_type': serializer.validated_data.get('device_type', 'android'),
            'device_id': serializer.validated_data.get('device_id'),
            'app_version': serializer.validated_data.get('app_version'),
            'os_version': serializer.validated_data.get('os_version')
        }
        device = MobileAuthService.register_device(device_data)

        session = MobileAuthService.create_session(user, device, request)

        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)

        return Response({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'session_id': session.session_token,
            'user': UserSerializer(user).data,
            'member': MemberSerializer(user.member_profile).data if hasattr(user, 'member_profile') else None,
            'device': MobileDeviceSerializer(device).data
        })


class MobileRegisterView(views.APIView):
    """Mobile email/password registration endpoint"""

    permission_classes = []

    def post(self, request):
        serializer = MobileRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'error': True,
                'message': 'Registration failed. Please check your information and try again.',
                'details': serializer.errors,
                'error_code': 'VALIDATION_ERROR'
            }, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email'].lower()
        password = serializer.validated_data['password']

        if User.objects.filter(email=email).exists():
            return Response({
                'error': True,
                'message': 'This email is already registered. Please use a different email or try logging in.',
                'error_code': 'EMAIL_EXISTS'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(email=email, password=password)
        user.save()
        Member.objects.get_or_create(user=user)

        device_token = serializer.validated_data.get('device_token') or f"anon-{uuid.uuid4()}"
        device_data = {
            'user': user,
            'device_token': device_token,
            'device_type': serializer.validated_data.get('device_type', 'android'),
            'device_id': serializer.validated_data.get('device_id'),
            'app_version': serializer.validated_data.get('app_version'),
            'os_version': serializer.validated_data.get('os_version')
        }
        device = MobileAuthService.register_device(device_data)
        session = MobileAuthService.create_session(user, device, request)

        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)

        return Response({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'session_id': session.session_token,
            'user': UserSerializer(user).data,
            'member': MemberSerializer(user.member_profile).data if hasattr(user, 'member_profile') else None,
            'device': MobileDeviceSerializer(device).data
        }, status=status.HTTP_201_CREATED)


class MobileRegisterDeviceView(views.APIView):
    """Register mobile device"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Register device for push notifications"""
        serializer = MobileRegisterDeviceSerializer(data=request.data)
        
        if serializer.is_valid():
            device_data = serializer.validated_data
            device_data['user'] = request.user
            
            device = MobileAuthService.register_device(device_data)
            
            return Response({
                'message': 'Device registered successfully',
                'device': MobileDeviceSerializer(device).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MobileDeviceListView(generics.ListAPIView):
    """List user's mobile devices"""
    
    serializer_class = MobileDeviceSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        return MobileDevice.objects.filter(user=self.request.user, status='active')


class MobileDeviceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Mobile device details"""
    
    serializer_class = MobileDeviceSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        return MobileDevice.objects.filter(user=self.request.user)
    
    def perform_destroy(self, instance):
        """Deactivate device instead of deleting"""
        instance.status = 'disabled'
        instance.save()
        
        AuditService.log_user_action(
            user=self.request.user,
            action='MOBILE_DEVICE_DISABLED',
            details={
                'device_token': instance.device_token,
                'device_type': instance.device_type
            }
        )


class MobileAppConfigView(views.APIView):
    """Get mobile app configuration"""
    
    permission_classes = []
    
    def get(self, request):
        """Get app configuration"""
        from django.conf import settings
        
        # Get latest app version
        platform = request.GET.get('platform', 'android')
        current_version = request.GET.get('version', '1.0.0')
        
        latest_version = MobileAppVersion.objects.filter(
            platform=platform,
            status='production'
        ).first()
        
        # Check if update is available
        update_available = False
        is_mandatory = False
        
        if latest_version:
            update_available = MobileAuthService.compare_versions(
                current_version, latest_version.version
            ) < 0
            is_mandatory = latest_version.is_mandatory
        
        # Get app settings
        app_settings = MobileAppSettings.objects.filter(is_active=True)
        settings_dict = {setting.key: setting.value for setting in app_settings}
        
        config = {
            'app_name': 'AltarFunds',
            'app_version': latest_version.version if latest_version else current_version,
            'api_base_url': settings.API_BASE_URL,
            'features': {
                'giving': True,
                'recurring_giving': True,
                'pledges': True,
                'campaigns': True,
                'church_info': True,
                'notifications': True,
                'reports': True
            },
            'settings': settings_dict,
            'update_info': {
                'available': update_available,
                'mandatory': is_mandatory,
                'latest_version': latest_version.version if latest_version else None,
                'download_url': latest_version.download_url if latest_version else None,
                'update_message': latest_version.update_message if latest_version else None
            }
        }
        
        return Response(MobileAppConfigSerializer(config).data)


class MobileUserProfileView(views.APIView):
    """Get mobile user profile"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user profile with mobile-specific data"""
        user = request.user
        
        # Get user devices
        devices = MobileDevice.objects.filter(user=user, status='active')
        
        # Get user permissions
        permissions = []
        if user.role:
            permissions = [user.role]
            if user.is_superuser:
                permissions.append('admin')
        
        profile_data = {
            'user': user,
            'member': user.member_profile if hasattr(user, 'member_profile') else None,
            'devices': devices,
            'permissions': permissions
        }
        
        return Response(MobileUserProfileSerializer(profile_data).data)


class MobileEnhancedDashboardView(views.APIView):
    """Enhanced mobile dashboard with comprehensive data"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get comprehensive dashboard data for mobile app"""
        user = request.user
        
        if not hasattr(user, 'member_profile') or not user.member_profile:
            return Response({'error': 'Member profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
        member = user.member_profile
        
        # Import dashboard functions for enhanced data
        from dashboard.views import financial_summary, monthly_trend, income_breakdown, expense_breakdown
        
        # Get all dashboard data
        financial_data = financial_summary(request).data
        trend_data = monthly_trend(request).data
        income_data = income_breakdown(request).data
        expense_data = expense_breakdown(request).data
        
        # Personal giving statistics
        from giving.models import GivingTransaction, RecurringGiving
        from expenses.models import Expense
        from members.models import Member
        
        now = timezone.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Personal metrics
        personal_giving = GivingTransaction.objects.filter(
            member=member,
            status='completed'
        ).aggregate(
            total=Sum('amount'),
            this_month=Sum('amount', filter=Q(transaction_date__gte=current_month_start)),
            count=Count('id')
        )
        
        # Church metrics
        total_members = Member.objects.filter(church=user.church).count()
        active_members = Member.objects.filter(
            church=user.church, 
            user__is_active=True
        ).count()
        
        # Recent activity
        recent_transactions = GivingTransaction.objects.filter(
            church=user.church
        ).order_by('-transaction_date')[:5]
        
        recent_expenses = Expense.objects.filter(
            church=user.church
        ).order_by('-created_at')[:5]
        
        # Dashboard summary
        dashboard_data = {
            'financial_overview': {
                'total_income': financial_data.get('totalIncome', 0),
                'monthly_income': financial_data.get('monthlyIncome', 0),
                'total_expenses': financial_data.get('totalExpenses', 0),
                'monthly_expenses': financial_data.get('monthlyExpenses', 0),
                'net_balance': financial_data.get('totalIncome', 0) - financial_data.get('totalExpenses', 0),
                'monthly_net': financial_data.get('monthlyIncome', 0) - financial_data.get('monthlyExpenses', 0)
            },
            
            'personal_giving': {
                'total_giving': personal_giving.get('total', 0),
                'this_month': personal_giving.get('this_month', 0),
                'transaction_count': personal_giving.get('count', 0),
                'percentage_of_church': (personal_giving.get('this_month', 0) / financial_data.get('monthlyIncome', 1)) * 100 if financial_data.get('monthlyIncome', 0) > 0 else 0
            },
            
            'church_metrics': {
                'total_members': total_members,
                'active_members': active_members,
                'member_growth_rate': self._calculate_growth_rate(user.church)
            },
            
            'trends': trend_data,
            'income_breakdown': income_data,
            'expense_breakdown': expense_data,
            
            'recent_activity': {
                'recent_transactions': [
                    {
                        'id': t.id,
                        'amount': t.amount,
                        'member': t.member.user.get_full_name() or t.member.user.email,
                        'category': t.category.name,
                        'date': t.transaction_date
                    } for t in recent_transactions
                ],
                'recent_expenses': [
                    {
                        'id': e.id,
                        'amount': e.amount,
                        'description': e.description,
                        'category': e.category.name if e.category else 'General',
                        'date': e.created_at
                    } for e in recent_expenses
                ]
            },
            
            'quick_stats': {
                'avg_monthly_giving': self._calculate_avg_monthly_giving(member),
                'giving_goal_progress': self._calculate_giving_goal_progress(member),
                'days_until_next_recurring': self._days_until_next_recurring(member)
            }
        }
        
        return Response(dashboard_data)
    
    def _calculate_growth_rate(self, church):
        """Calculate member growth rate"""
        from members.models import Member
        from datetime import timedelta
        
        now = timezone.now()
        last_month = now - timedelta(days=30)
        
        current_members = Member.objects.filter(church=church).count()
        previous_members = Member.objects.filter(
            church=church,
            created_at__lt=last_month
        ).count()
        
        if previous_members == 0:
            return 100
        
        growth = ((current_members - previous_members) / previous_members) * 100
        return round(growth, 2)
    
    def _calculate_avg_monthly_giving(self, member):
        """Calculate average monthly giving"""
        from giving.models import GivingTransaction
        
        total = GivingTransaction.objects.filter(
            member=member,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Get months since first donation
        first_donation = GivingTransaction.objects.filter(
            member=member,
            status='completed'
        ).order_by('transaction_date').first()
        
        if not first_donation:
            return 0
        
        months = (timezone.now().date() - first_donation.transaction_date.date()).days / 30
        if months < 1:
            months = 1
        
        return round(total / months, 2)
    
    def _calculate_giving_goal_progress(self, member):
        """Calculate progress towards giving goal (assuming $1000/month goal)"""
        from giving.models import GivingTransaction
        
        monthly_goal = 1000  # This could be configurable
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        current_giving = GivingTransaction.objects.filter(
            member=member,
            status='completed',
            transaction_date__gte=current_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return {
            'goal': monthly_goal,
            'current': current_giving,
            'progress': (current_giving / monthly_goal) * 100,
            'remaining': max(0, monthly_goal - current_giving)
        }
    
    def _days_until_next_recurring(self, member):
        """Calculate days until next recurring payment"""
        from giving.models import RecurringGiving
        
        next_payment = RecurringGiving.objects.filter(
            member=member,
            status='active'
        ).order_by('next_payment_date').first()
        
        if not next_payment or not next_payment.next_payment_date:
            return None
        
        days = (next_payment.next_payment_date.date() - timezone.now().date()).days
        return max(0, days)


class MobileGivingSummaryView(views.APIView):
    """Get enhanced mobile giving summary using dashboard data"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get enhanced giving summary for mobile dashboard"""
        user = request.user
        
        if not hasattr(user, 'member_profile') or not user.member_profile:
            return Response({'error': 'Member profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
        member = user.member_profile
        
        # Import dashboard functions for enhanced data
        from dashboard.views import financial_summary, monthly_trend, income_breakdown, expense_breakdown
        
        # Get enhanced financial data
        financial_data = financial_summary(request).data
        
        # Get monthly trends
        trend_data = monthly_trend(request).data
        
        # Get income breakdown
        income_data = income_breakdown(request).data
        
        # Get expense breakdown  
        expense_data = expense_breakdown(request).data
        
        # Personal giving statistics (member-specific)
        from giving.models import GivingTransaction, RecurringGiving
        
        now = timezone.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Personal giving totals
        personal_total_giving = GivingTransaction.objects.filter(
            member=member,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        personal_this_month = GivingTransaction.objects.filter(
            member=member,
            status='completed',
            transaction_date__gte=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        personal_this_year = GivingTransaction.objects.filter(
            member=member,
            status='completed',
            transaction_date__gte=current_year_start
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Last transaction
        last_transaction = GivingTransaction.objects.filter(
            member=member,
            status='completed'
        ).order_by('-transaction_date').first()
        
        # Giving categories
        categories = GivingTransaction.objects.filter(
            member=member,
            status='completed'
        ).values('category__name', 'category__id').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        # Recurring giving
        recurring = RecurringGiving.objects.filter(
            member=member,
            status='active'
        ).values('category__name', 'frequency', 'amount', 'next_payment_date')
        
        # Enhanced summary data combining church-wide and personal data
        summary_data = {
            # Church-wide financial data (from enhanced dashboard)
            'church_financial': financial_data,
            'monthly_trends': trend_data,
            'income_breakdown': income_data,
            'expense_breakdown': expense_data,
            
            # Personal giving data
            'personal_giving': {
                'total_giving': personal_total_giving,
                'this_month': personal_this_month,
                'this_year': personal_this_year,
                'last_transaction': last_transaction,
                'giving_categories': list(categories),
                'recurring_giving': list(recurring)
            },
            
            # Summary metrics
            'summary': {
                'personal_percentage': (personal_this_month / financial_data.get('monthlyIncome', 1)) * 100 if financial_data.get('monthlyIncome', 0) > 0 else 0,
                'giving_streak': self._calculate_giving_streak(member),
                'next_recurring_payment': self._get_next_recurring_payment(recurring)
            }
        }
        
        return Response(MobileGivingSummarySerializer(summary_data).data)
    
    def _calculate_giving_streak(self, member):
        """Calculate consecutive months of giving"""
        from giving.models import GivingTransaction
        from django.db.models import Max
        
        # Get months with giving transactions
        giving_months = GivingTransaction.objects.filter(
            member=member,
            status='completed'
        ).extra({
            'month': "strftime('%Y-%m', transaction_date)"
        }).values('month').distinct().order_by('-month')
        
        # Calculate streak (simplified)
        return len(giving_months) if giving_months else 0
    
    def _get_next_recurring_payment(self, recurring):
        """Get next recurring payment date"""
        if not recurring:
            return None
        
        next_payment = min((r['next_payment_date'] for r in recurring if r['next_payment_date']), default=None)
        return next_payment


class MobileChurchInfoView(views.APIView):
    """Get mobile church information"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get church information for mobile app"""
        user = request.user
        
        if not user.church:
            return Response({'error': 'Church not found'}, status=status.HTTP_404_NOT_FOUND)
        
        church = user.church
        
        # Get church details
        church_data = {
            'id': church.id,
            'name': church.name,
            'code': church.church_code,
            'description': church.description,
            'logo': church.logo.url if church.logo else None,
            'is_verified': church.is_verified,
            'is_active': church.is_active,
            'contact_info': {
                'phone': church.phone_number,
                'email': church.email,
                'website': church.website
            },
            'address': {
                'street': church.address,
                'city': church.city,
                'county': church.county,
                'country': church.country
            }
        }
        
        # Get campuses
        campuses = church.campuses.filter(is_active=True).values(
            'id', 'name', 'address', 'phone_number', 'is_main_campus'
        )
        
        # Get departments
        departments = church.departments.filter(is_active=True).values(
            'id', 'name', 'description', 'head_name'
        )
        
        # Get giving categories
        giving_categories = church.giving_categories.filter(is_active=True).values(
            'id', 'name', 'description', 'is_tax_deductible'
        )
        
        # Get upcoming events (placeholder)
        upcoming_events = []
        
        church_data['campuses'] = list(campuses)
        church_data['departments'] = list(departments)
        church_data['giving_categories'] = list(giving_categories)
        church_data['upcoming_events'] = upcoming_events
        
        return Response(MobileChurchInfoSerializer(church_data).data)


class MobileQuickActionsView(views.APIView):
    """Get mobile quick actions"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get quick actions based on user permissions"""
        user = request.user
        
        # Define available actions
        all_actions = [
            {
                'action_type': 'give',
                'title': 'Give Now',
                'description': 'Make a one-time donation',
                'icon': 'donate',
                'color': '#4CAF50',
                'enabled': True,
                'required_permissions': []
            },
            {
                'action_type': 'recurring',
                'title': 'Recurring Giving',
                'description': 'Set up recurring donations',
                'icon': 'repeat',
                'color': '#2196F3',
                'enabled': True,
                'required_permissions': []
            },
            {
                'action_type': 'pledge',
                'title': 'Make Pledge',
                'description': 'Commit to a giving pledge',
                'icon': 'handshake',
                'color': '#FF9800',
                'enabled': True,
                'required_permissions': []
            },
            {
                'action_type': 'history',
                'title': 'Giving History',
                'description': 'View your giving history',
                'icon': 'history',
                'color': '#9C27B0',
                'enabled': True,
                'required_permissions': []
            },
            {
                'action_type': 'reports',
                'title': 'Reports',
                'description': 'View financial reports',
                'icon': 'chart-bar',
                'color': '#F44336',
                'enabled': user.role in ['treasurer', 'church_admin', 'denomination_admin', 'system_admin'],
                'required_permissions': ['treasurer', 'church_admin', 'denomination_admin', 'system_admin']
            },
            {
                'action_type': 'members',
                'title': 'Members',
                'description': 'Manage church members',
                'icon': 'people',
                'color': '#607D8B',
                'enabled': user.role in ['church_admin', 'denomination_admin', 'system_admin'],
                'required_permissions': ['church_admin', 'denomination_admin', 'system_admin']
            }
        ]
        
        # Filter actions based on user permissions
        enabled_actions = [
            action for action in all_actions
            if action['enabled'] and (
                not action['required_permissions'] or
                user.role in action['required_permissions']
            )
        ]
        
        return Response([MobileQuickActionSerializer(action).data for action in enabled_actions])


class MobileNotificationListView(generics.ListAPIView):
    """List mobile notifications"""
    
    serializer_class = MobileNotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['notification_type', 'status']
    
    def get_queryset(self):
        return MobileNotification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


class MobileNotificationDetailView(generics.RetrieveUpdateAPIView):
    """Mobile notification details"""
    
    serializer_class = MobileNotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return MobileNotification.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        """Mark notification as opened"""
        if serializer.validated_data.get('status') == 'opened':
            serializer.save(opened_at=timezone.now())


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageChurchFinances])
def mobile_send_push_notification(request):
    """Send push notification to mobile devices"""
    serializer = MobilePushNotificationSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            # Send notification
            result = MobileNotificationService.send_push_notification(
                users=serializer.validated_data.get('users'),
                user_groups=serializer.validated_data.get('user_groups'),
                churches=serializer.validated_data.get('churches'),
                title=serializer.validated_data['title'],
                message=serializer.validated_data['message'],
                data=serializer.validated_data.get('data'),
                notification_type=serializer.validated_data['notification_type']
            )
            
            return Response({
                'message': 'Push notification sent successfully',
                'result': result
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mobile_track_analytics(request):
    """Track mobile app analytics"""
    try:
        user = request.user
        device = MobileDevice.objects.filter(
            user=user,
            device_token=request.data.get('device_token')
        ).first()
        
        if not device:
            return Response(
                {'error': 'Device not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create analytics record
        MobileAnalyticsService.track_event(
            user=user,
            device=device,
            event_type=request.data.get('event_type'),
            event_name=request.data.get('event_name'),
            event_data=request.data.get('event_data'),
            screen_name=request.data.get('screen_name'),
            session_id=request.data.get('session_id')
        )
        
        return Response({'message': 'Analytics recorded successfully'})
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mobile_submit_feedback(request):
    """Submit mobile app feedback"""
    serializer = MobileAppFeedbackSerializer(data=request.data)
    
    if serializer.is_valid():
        serializer.save(user=request.user)
        
        # Log feedback submission
        AuditService.log_user_action(
            user=request.user,
            action='MOBILE_FEEDBACK_SUBMITTED',
            details={
                'feedback_type': serializer.validated_data['feedback_type'],
                'title': serializer.validated_data['title']
            }
        )
        
        return Response({
            'message': 'Feedback submitted successfully',
            'feedback_id': serializer.instance.id
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
