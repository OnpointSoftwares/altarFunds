from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import (
    Denomination, Church, Campus, Department, SmallGroup,
    ChurchBankAccount, MpesaAccount
)
from .serializers import (
    DenominationSerializer, ChurchSerializer, ChurchRegistrationSerializer,
    CampusSerializer, DepartmentSerializer, SmallGroupSerializer,
    ChurchBankAccountSerializer, MpesaAccountSerializer,
    ChurchListSerializer, ChurchSummarySerializer,
    ChurchVerificationSerializer, ChurchStatusUpdateSerializer
)
from common.permissions import IsChurchAdmin, IsDenominationAdmin, IsSystemAdmin
from common.services import AuditService
from common.exceptions import AltarFundsException


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
    
    @extend_schema(
        summary="List denominations",
        description="Get list of all denominations"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Create denomination",
        description="Create a new denomination"
    )
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
            return Church.objects.filter(church=user.church)
    
    @extend_schema(
        summary="List churches",
        description="Get list of churches based on user permissions"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Register church",
        description="Register a new church (pending verification)"
    )
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
            return Church.objects.filter(church=user.church)
    
    @extend_schema(
        summary="Get church details",
        description="Get detailed information about a specific church"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Update church",
        description="Update church information"
    )
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
    
    @extend_schema(
        summary="Verify church",
        description="Verify a pending church registration"
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
    
    @extend_schema(
        summary="Update church status",
        description="Update church status (verified, suspended, closed)"
    )
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
