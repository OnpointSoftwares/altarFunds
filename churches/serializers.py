from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Denomination, Church, Campus, Department, SmallGroup,
    ChurchBankAccount, MpesaAccount
)
from common.serializers import BaseSerializer, UserSerializer
from common.validators import (
    validate_phone_number, validate_paybill_number, validate_till_number,
    validate_bank_account_number, validate_church_name
)

User = get_user_model()


class DenominationSerializer(BaseSerializer):
    """Denomination serializer"""
    
    church_count = serializers.ReadOnlyField()
    total_members = serializers.ReadOnlyField()
    
    class Meta:
        model = Denomination
        fields = [
            'id', 'name', 'description', 'headquarters_address',
            'contact_phone', 'contact_email', 'website', 'leader_name',
            'leader_title', 'leader_phone', 'registration_number',
            'registration_date', 'is_active', 'church_count', 'total_members',
            'created_at', 'updated_at'
        ]
    
    def validate_contact_phone(self, value):
        """Validate contact phone number"""
        if value:
            return validate_phone_number(value)
        return value
    
    def validate_leader_phone(self, value):
        """Validate leader phone number"""
        if value:
            return validate_phone_number(value)
        return value


class ChurchSerializer(BaseSerializer):
    """Church serializer"""
    
    denomination_name = serializers.CharField(source='denomination.name', read_only=True)
    member_count = serializers.ReadOnlyField()
    active_member_count = serializers.ReadOnlyField()
    total_giving_this_month = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    church_type_display = serializers.CharField(source='get_church_type_display', read_only=True)
    
    class Meta:
        model = Church
        fields = [
            'id', 'name', 'church_type', 'church_type_display', 'denomination',
            'denomination_name', 'church_code', 'phone_number', 'email', 'website',
            'address_line1', 'address_line2', 'city', 'county', 'postal_code',
            'latitude', 'longitude', 'senior_pastor_name', 'senior_pastor_phone',
            'senior_pastor_email', 'established_date', 'membership_count',
            'average_attendance', 'registration_number', 'registration_date',
            'status', 'status_display', 'is_verified', 'verification_date',
            'verified_by', 'is_active', 'allow_online_giving',
            'require_membership_approval', 'member_count', 'active_member_count',
            'total_giving_this_month', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'church_code', 'is_verified', 'verification_date', 'verified_by'
        ]
    
    def validate_phone_number(self, value):
        """Validate phone number"""
        return validate_phone_number(value)
    
    def validate_senior_pastor_phone(self, value):
        """Validate senior pastor phone"""
        if value:
            return validate_phone_number(value)
        return value
    
    def validate_name(self, value):
        """Validate church name"""
        return validate_church_name(value)
    
    def create(self, validated_data):
        """Create church with auto-generated code"""
        church = super().create(validated_data)
        church.generate_church_code()
        return church


class ChurchRegistrationSerializer(serializers.ModelSerializer):
    """Church registration serializer for new churches"""
    
    class Meta:
        model = Church
        fields = [
            'name', 'church_type', 'phone_number', 'email', 'website',
            'address_line1', 'address_line2', 'city', 'county', 'postal_code',
            'senior_pastor_name', 'senior_pastor_phone', 'senior_pastor_email',
            'established_date', 'membership_count', 'average_attendance',
            'registration_number', 'registration_date'
        ]
    
    def validate_phone_number(self, value):
        """Validate phone number"""
        return validate_phone_number(value)
    
    def validate_senior_pastor_phone(self, value):
        """Validate senior pastor phone"""
        if value:
            return validate_phone_number(value)
        return value
    
    def validate_name(self, value):
        """Validate church name"""
        return validate_church_name(value)
    
    def create(self, validated_data):
        """Create church with pending status"""
        church = Church.objects.create(
            status='pending',
            is_verified=False,
            **validated_data
        )
        church.generate_church_code()
        return church


class CampusSerializer(BaseSerializer):
    """Campus serializer"""
    
    church_name = serializers.CharField(source='church.name', read_only=True)
    member_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Campus
        fields = [
            'id', 'name', 'church', 'church_name', 'phone_number', 'email',
            'address_line1', 'address_line2', 'city', 'county', 'postal_code',
            'campus_pastor_name', 'campus_pastor_phone', 'established_date',
            'membership_count', 'average_attendance', 'is_active',
            'is_main_campus', 'member_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['member_count']
    
    def validate_phone_number(self, value):
        """Validate phone number"""
        if value:
            return validate_phone_number(value)
        return value
    
    def validate_campus_pastor_phone(self, value):
        """Validate campus pastor phone"""
        if value:
            return validate_phone_number(value)
        return value


class DepartmentSerializer(BaseSerializer):
    """Department serializer"""
    
    church_name = serializers.CharField(source='church.name', read_only=True)
    department_type_display = serializers.CharField(source='get_department_type_display', read_only=True)
    member_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'church', 'church_name', 'department_type',
            'department_type_display', 'leader_name', 'leader_phone',
            'leader_email', 'description', 'has_budget', 'annual_budget',
            'is_active', 'requires_approval', 'member_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['member_count']
    
    def validate_leader_phone(self, value):
        """Validate leader phone"""
        if value:
            return validate_phone_number(value)
        return value


class SmallGroupSerializer(BaseSerializer):
    """Small group serializer"""
    
    church_name = serializers.CharField(source='church.name', read_only=True)
    campus_name = serializers.CharField(source='campus.name', read_only=True)
    group_type_display = serializers.CharField(source='get_group_type_display', read_only=True)
    member_count = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()
    
    class Meta:
        model = SmallGroup
        fields = [
            'id', 'name', 'church', 'church_name', 'campus', 'campus_name',
            'group_type', 'group_type_display', 'leader_name', 'leader_phone',
            'leader_email', 'meeting_day', 'meeting_time', 'meeting_location',
            'description', 'max_members', 'is_active', 'is_open_to_new_members',
            'member_count', 'is_full', 'created_at', 'updated_at'
        ]
        read_only_fields = ['member_count', 'is_full']
    
    def validate_leader_phone(self, value):
        """Validate leader phone"""
        if value:
            return validate_phone_number(value)
        return value


class ChurchBankAccountSerializer(BaseSerializer):
    """Church bank account serializer"""
    
    church_name = serializers.CharField(source='church.name', read_only=True)
    account_type_display = serializers.CharField(source='get_account_type_display', read_only=True)
    masked_account_number = serializers.SerializerMethodField()
    
    class Meta:
        model = ChurchBankAccount
        fields = [
            'id', 'church', 'church_name', 'account_name', 'account_number',
            'masked_account_number', 'bank_name', 'bank_branch', 'account_type',
            'account_type_display', 'bank_phone', 'bank_email', 'is_active',
            'is_primary', 'created_at', 'updated_at'
        ]
    
    def get_masked_account_number(self, obj):
        """Return masked account number"""
        if not obj.account_number:
            return ''
        # Show last 4 digits only
        return f"****{obj.account_number[-4:]}"
    
    def validate_account_number(self, value):
        """Validate account number"""
        return validate_bank_account_number(value)
    
    def validate_bank_phone(self, value):
        """Validate bank phone"""
        if value:
            return validate_phone_number(value)
        return value


class MpesaAccountSerializer(BaseSerializer):
    """M-Pesa account serializer"""
    
    church_name = serializers.CharField(source='church.name', read_only=True)
    account_type_display = serializers.CharField(source='get_account_type_display', read_only=True)
    masked_business_number = serializers.SerializerMethodField()
    
    class Meta:
        model = MpesaAccount
        fields = [
            'id', 'church', 'church_name', 'account_type', 'account_type_display',
            'business_number', 'masked_business_number', 'account_name',
            'consumer_key', 'consumer_secret', 'passkey', 'callback_url',
            'confirmation_url', 'validation_url', 'is_active', 'is_test_mode',
            'created_at', 'updated_at'
        ]
    
    def get_masked_business_number(self, obj):
        """Return masked business number"""
        if not obj.business_number:
            return ''
        # Show last 4 digits only
        return f"****{obj.business_number[-4:]}"
    
    def validate(self, attrs):
        """Validate business number based on account type"""
        account_type = attrs.get('account_type')
        business_number = attrs.get('business_number')
        
        if account_type == 'paybill':
            validate_paybill_number(business_number)
        elif account_type == 'till':
            validate_till_number(business_number)
        
        return attrs


class ChurchListSerializer(serializers.ModelSerializer):
    """Church list serializer for dropdowns"""
    
    church_type_display = serializers.CharField(source='get_church_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Church
        fields = [
            'id', 'name', 'church_code', 'church_type_display',
            'status_display', 'city', 'county', 'is_active'
        ]


class DepartmentListSerializer(serializers.ModelSerializer):
    """Department list serializer"""
    
    department_type_display = serializers.CharField(source='get_department_type_display', read_only=True)
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'department_type_display', 'is_active'
        ]


class SmallGroupListSerializer(serializers.ModelSerializer):
    """Small group list serializer"""
    
    group_type_display = serializers.CharField(source='get_group_type_display', read_only=True)
    
    class Meta:
        model = SmallGroup
        fields = [
            'id', 'name', 'group_type_display', 'meeting_day',
            'meeting_time', 'is_active', 'is_open_to_new_members'
        ]


class ChurchSummarySerializer(serializers.ModelSerializer):
    """Church summary serializer with statistics"""
    
    denomination_name = serializers.CharField(source='denomination.name', read_only=True)
    member_count = serializers.ReadOnlyField()
    active_member_count = serializers.ReadOnlyField()
    campus_count = serializers.SerializerMethodField()
    department_count = serializers.SerializerMethodField()
    small_group_count = serializers.SerializerMethodField()
    total_giving_this_month = serializers.ReadOnlyField()
    
    class Meta:
        model = Church
        fields = [
            'id', 'name', 'church_code', 'denomination_name', 'city', 'county',
            'senior_pastor_name', 'member_count', 'active_member_count',
            'campus_count', 'department_count', 'small_group_count',
            'total_giving_this_month', 'is_active', 'status'
        ]
    
    def get_campus_count(self, obj):
        """Get campus count"""
        return obj.campuses.filter(is_active=True).count()
    
    def get_department_count(self, obj):
        """Get department count"""
        return obj.departments.filter(is_active=True).count()
    
    def get_small_group_count(self, obj):
        """Get small group count"""
        return obj.small_groups.filter(is_active=True).count()


class ChurchVerificationSerializer(serializers.ModelSerializer):
    """Church verification serializer"""
    
    class Meta:
        model = Church
        fields = ['id', 'name', 'church_code', 'status', 'is_verified']
        read_only_fields = ['id', 'name', 'church_code', 'status', 'is_verified']


class ChurchStatusUpdateSerializer(serializers.ModelSerializer):
    """Church status update serializer"""
    
    reason = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Church
        fields = ['status', 'reason']
    
    def update(self, instance, validated_data):
        """Update church status with audit trail"""
        reason = validated_data.pop('reason', 'Status updated')
        old_status = instance.status
        new_status = validated_data['status']
        
        instance.status = new_status
        
        # Handle verification
        if new_status == 'verified' and not instance.is_verified:
            instance.is_verified = True
            instance.verification_date = timezone.now()
            instance.verified_by = self.context['request'].user
        elif new_status == 'suspended':
            instance.is_active = False
        
        instance.save()
        
        # Log status change
        from common.services import AuditService
        AuditService.log_user_action(
            user=self.context['request'].user,
            action='CHURCH_STATUS_CHANGE',
            details={
                'church': instance.name,
                'old_status': old_status,
                'new_status': new_status,
                'reason': reason
            }
        )
        
        return instance
