from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (
    MobileDevice, MobileAppSettings, MobileAppVersion, 
    UserSession, MobileNotification, MobileAppAnalytics, MobileAppFeedback
)
from common.serializers import UserSerializer
from accounts.models import Member
from common.serializers import BaseSerializer


class MobileDeviceSerializer(BaseSerializer):
    """Mobile device serializer"""
    
    device_type_display = serializers.CharField(source='get_device_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = MobileDevice
        fields = [
            'id', 'user', 'device_token', 'device_type', 'device_type_display',
            'device_id', 'app_version', 'os_version', 'status', 'status_display',
            'last_seen', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_device_token(self, value):
        """Validate device token uniqueness"""
        user = self.context['request'].user if 'request' in self.context else None
        
        # Check if token exists for another user
        existing_device = MobileDevice.objects.filter(device_token=value).first()
        if existing_device and existing_device.user != user:
            # Deactivate old device
            existing_device.status = 'inactive'
            existing_device.save()
        
        return value


class MobileAppSettingsSerializer(BaseSerializer):
    """Mobile app settings serializer"""
    
    class Meta:
        model = MobileAppSettings
        fields = ['key', 'value', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class MobileAppVersionSerializer(BaseSerializer):
    """Mobile app version serializer"""
    
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = MobileAppVersion
        fields = [
            'id', 'platform', 'platform_display', 'version', 'build_number',
            'status', 'status_display', 'is_mandatory', 'update_message',
            'download_url', 'min_supported_version', 'release_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSessionSerializer(BaseSerializer):
    """User session serializer"""
    
    user_info = UserSerializer(source='user', read_only=True)
    device_info = MobileDeviceSerializer(source='device', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = UserSession
        fields = [
            'id', 'user', 'user_info', 'device', 'device_info', 'session_token',
            'ip_address', 'user_agent', 'is_active', 'last_activity',
            'expires_at', 'is_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'session_token', 'ip_address', 'user_agent', 'created_at', 'updated_at'
        ]


class MobileNotificationSerializer(BaseSerializer):
    """Mobile notification serializer"""
    
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = MobileNotification
        fields = [
            'id', 'user', 'device', 'notification_type', 'notification_type_display',
            'title', 'message', 'data', 'status', 'status_display', 'sent_at',
            'delivered_at', 'opened_at', 'response_data', 'error_message',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'sent_at', 'delivered_at', 'opened_at', 'response_data',
            'error_message', 'created_at', 'updated_at'
        ]


class MobileAppAnalyticsSerializer(BaseSerializer):
    """Mobile app analytics serializer"""
    
    user_info = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = MobileAppAnalytics
        fields = [
            'id', 'user', 'user_info', 'device', 'event_type', 'event_name',
            'event_data', 'screen_name', 'session_id', 'event_timestamp',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MobileAppFeedbackSerializer(BaseSerializer):
    """Mobile app feedback serializer"""
    
    feedback_type_display = serializers.CharField(source='get_feedback_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    user_info = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = MobileAppFeedback
        fields = [
            'id', 'user', 'user_info', 'device', 'feedback_type', 'feedback_type_display',
            'title', 'description', 'rating', 'status', 'status_display',
            'admin_response', 'responded_by', 'responded_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'admin_response', 'responded_by', 'responded_at', 'created_at', 'updated_at'
        ]


class MemberSerializer(serializers.ModelSerializer):
    member_type = serializers.CharField(source='membership_status')
    join_date = serializers.DateField(source='membership_date', allow_null=True)
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = [
            'id',
            'membership_number',
            'member_type',
            'join_date',
            'is_active',
            'church'
        ]

    def get_is_active(self, obj):
        return obj.membership_status != 'inactive'


# Mobile-specific serializers


class MobileLoginSerializer(serializers.Serializer):
    """Mobile login serializer"""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    device_token = serializers.CharField(required=False)
    device_type = serializers.ChoiceField(
        choices=MobileDevice.DEVICE_TYPE_CHOICES,
        required=False
    )
    device_id = serializers.CharField(required=False)
    app_version = serializers.CharField(required=False)
    os_version = serializers.CharField(required=False)
    
    def validate(self, attrs):
        """Validate login credentials"""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            
            attrs['user'] = user
            return attrs
        
        raise serializers.ValidationError('Email and password are required')


class MobileGoogleLoginSerializer(serializers.Serializer):
    firebase_token = serializers.CharField()
    device_token = serializers.CharField(required=False)
    device_type = serializers.ChoiceField(
        choices=MobileDevice.DEVICE_TYPE_CHOICES,
        required=False
    )
    device_id = serializers.CharField(required=False)
    app_version = serializers.CharField(required=False)
    os_version = serializers.CharField(required=False)


class MobileRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    device_token = serializers.CharField(required=False)
    device_type = serializers.ChoiceField(
        choices=MobileDevice.DEVICE_TYPE_CHOICES,
        required=False
    )
    device_id = serializers.CharField(required=False)
    app_version = serializers.CharField(required=False)
    os_version = serializers.CharField(required=False)

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError('Passwords do not match')
        return attrs


class MobileRegisterDeviceSerializer(serializers.Serializer):
    """Mobile device registration serializer"""
    
    device_token = serializers.CharField()
    device_type = serializers.ChoiceField(choices=MobileDevice.DEVICE_TYPE_CHOICES)
    device_id = serializers.CharField(required=False)
    app_version = serializers.CharField(required=False)
    os_version = serializers.CharField(required=False)


class MobilePushNotificationSerializer(serializers.Serializer):
    """Mobile push notification serializer"""
    
    users = serializers.ListField(child=serializers.UUIDField(), required=False)
    user_groups = serializers.ListField(child=serializers.CharField(), required=False)
    churches = serializers.ListField(child=serializers.UUIDField(), required=False)
    title = serializers.CharField(max_length=200)
    message = serializers.CharField(max_length=1000)
    data = serializers.JSONField(required=False)
    notification_type = serializers.ChoiceField(
        choices=MobileNotification.NOTIFICATION_TYPE_CHOICES,
        default='system'
    )


class MobileAppConfigSerializer(serializers.Serializer):
    """Mobile app configuration serializer"""
    
    app_name = serializers.CharField()
    app_version = serializers.CharField()
    api_base_url = serializers.URLField()
    features = serializers.JSONField()
    settings = serializers.JSONField()
    update_info = MobileAppVersionSerializer(read_only=True)


class MobileUserProfileSerializer(serializers.Serializer):
    """Mobile user profile serializer"""
    
    user = UserSerializer()
    member = MemberSerializer(required=False, allow_null=True)
    devices = MobileDeviceSerializer(many=True, read_only=True)
    church_info = serializers.SerializerMethodField()
    permissions = serializers.ListField(read_only=True)
    
    def get_church_info(self, obj):
        """Get church information"""
        user = obj['user']
        if user.church:
            return {
                'id': user.church.id,
                'name': user.church.name,
                'code': user.church.church_code,
                'logo': user.church.logo.url if user.church.logo else None,
                'is_verified': user.church.is_verified,
                'is_active': user.church.is_active
            }
        return None


class MobileGivingSummarySerializer(serializers.Serializer):
    """Mobile giving summary serializer"""
    
    total_giving = serializers.DecimalField(max_digits=15, decimal_places=2)
    this_month = serializers.DecimalField(max_digits=15, decimal_places=2)
    this_year = serializers.DecimalField(max_digits=15, decimal_places=2)
    last_transaction = serializers.SerializerMethodField()
    giving_categories = serializers.ListField()
    recurring_giving = serializers.ListField()
    
    def get_last_transaction(self, obj):
        """Get last transaction details"""
        last_tx = obj.get('last_transaction')
        if last_tx:
            return {
                'id': str(last_tx.transaction_id),
                'amount': last_tx.amount,
                'category': last_tx.category.name,
                'date': last_tx.transaction_date,
                'status': last_tx.status
            }
        return None


class MobileChurchInfoSerializer(serializers.Serializer):
    """Mobile church information serializer"""
    
    id = serializers.UUIDField()
    name = serializers.CharField()
    code = serializers.CharField()
    description = serializers.CharField()
    logo = serializers.URLField()
    is_verified = serializers.BooleanField()
    is_active = serializers.BooleanField()
    contact_info = serializers.JSONField()
    address = serializers.JSONField()
    campuses = serializers.ListField()
    departments = serializers.ListField()
    giving_categories = serializers.ListField()
    upcoming_events = serializers.ListField()


class MobileQuickActionSerializer(serializers.Serializer):
    """Mobile quick action serializer"""
    
    action_type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    icon = serializers.CharField()
    color = serializers.CharField()
    enabled = serializers.BooleanField()
    required_permissions = serializers.ListField()
