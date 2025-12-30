from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, Member, UserSession, PasswordResetToken
from common.serializers import BaseSerializer, UserSerializer
from common.validators import validate_phone_number, validate_id_number
from common.exceptions import AltarFundsException
import firebase_admin
from firebase_admin import auth


class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer"""
    
    password = serializers.CharField(
        write_only=True,
        min_length=12,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True)
    firebase_token = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone_number',
            'password', 'password_confirm', 'role', 'church',
            'firebase_token'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'church': {'required': False}
        }
    
    def validate_email(self, value):
        """Validate email is not already registered"""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("Email already registered")
        return value.lower()
    
    def validate_phone_number(self, value):
        """Validate and format phone number"""
        return validate_phone_number(value)
    
    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Validate Firebase token if provided
        firebase_token = attrs.get('firebase_token')
        if firebase_token:
            try:
                decoded_token = auth.verify_id_token(firebase_token)
                attrs['firebase_uid'] = decoded_token['uid']
            except Exception:
                raise serializers.ValidationError("Invalid Firebase token")
        
        return attrs
    
    def create(self, validated_data):
        """Create user with encrypted password"""
        validated_data.pop('password_confirm')
        validated_data.pop('firebase_token', None)
        church = validated_data.pop('church', None)

        password = validated_data.pop('password')
        validated_data['username'] = validated_data['email']

        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        # Create member profile
        Member.objects.create(user=user, church=church)

        return user


class UserLoginSerializer(serializers.Serializer):
    """User login serializer"""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    firebase_token = serializers.CharField(write_only=True, required=False)
    
    def validate(self, attrs):
        """Validate login credentials"""
        email = attrs.get('email').lower()
        password = attrs.get('password')
        
        user = authenticate(username=email, password=password)
        
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        
        if not user.is_active:
            raise serializers.ValidationError("Account is suspended")
        
        # Validate Firebase token if provided
        firebase_token = attrs.get('firebase_token')
        if firebase_token:
            try:
                decoded_token = auth.verify_id_token(firebase_token)
                if not user.firebase_uid:
                    user.firebase_uid = decoded_token['uid']
                    user.save()
            except Exception:
                pass  # Allow login without valid Firebase token
        
        attrs['user'] = user
        return attrs


class UserProfileSerializer(UserSerializer):
    """Extended user profile serializer"""
    
    member_profile = serializers.SerializerMethodField()
    church_name = serializers.CharField(source='church.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    permissions = serializers.SerializerMethodField()
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            'date_of_birth', 'gender', 'address_line1', 'address_line2',
            'city', 'county', 'postal_code', 'profile_picture',
            'church_name', 'member_profile', 'permissions',
            'email_notifications', 'sms_notifications', 'push_notifications',
            'is_phone_verified', 'is_email_verified'
        ]
    
    def get_member_profile(self, obj):
        """Get member profile information"""
        try:
            member = obj.member_profile
            return MemberProfileSerializer(member).data
        except Member.DoesNotExist:
            return None
    
    def get_permissions(self, obj):
        """Get user's permissions"""
        return obj.get_church_permissions()


class MemberProfileSerializer(serializers.ModelSerializer):
    """Member profile serializer"""
    
    user = UserSerializer(read_only=True)
    departments = serializers.StringRelatedField(many=True, read_only=True)
    small_group = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Member
        fields = [
            'user', 'membership_number', 'membership_status', 'membership_date',
            'id_number', 'kra_pin', 'occupation', 'employer', 'marital_status',
            'spouse_name', 'emergency_contact_name', 'emergency_contact_phone',
            'departments', 'small_group', 'is_tithe_payer',
            'preferred_giving_method', 'monthly_giving_goal'
        ]
        read_only_fields = ['membership_number', 'user']


class MemberUpdateSerializer(serializers.ModelSerializer):
    """Member profile update serializer"""
    
    class Meta:
        model = Member
        fields = [
            'occupation', 'employer', 'marital_status', 'spouse_name',
            'emergency_contact_name', 'emergency_contact_phone',
            'is_tithe_payer', 'preferred_giving_method', 'monthly_giving_goal'
        ]
    
    def validate_emergency_contact_phone(self, value):
        """Validate emergency contact phone"""
        if value:
            return validate_phone_number(value)
        return value


class UserUpdateSerializer(serializers.ModelSerializer):
    """User profile update serializer"""
    
    member_profile = MemberUpdateSerializer(required=False)
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number', 'date_of_birth',
            'gender', 'address_line1', 'address_line2', 'city', 'county',
            'postal_code', 'profile_picture', 'email_notifications',
            'sms_notifications', 'push_notifications', 'member_profile'
        ]
    
    def validate_phone_number(self, value):
        """Validate phone number"""
        return validate_phone_number(value)
    
    def update(self, instance, validated_data):
        """Update user and member profile"""
        member_data = validated_data.pop('member_profile', None)
        
        # Update user
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update member profile
        if member_data and hasattr(instance, 'member_profile'):
            member = instance.member_profile
            for attr, value in member_data.items():
                setattr(member, attr, value)
            member.save()
        
        return instance


class PasswordChangeSerializer(serializers.Serializer):
    """Password change serializer"""
    
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True,
        min_length=12,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate_current_password(self, value):
        """Validate current password"""
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect")
        return value
    
    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs
    
    def save(self):
        """Change user password"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """Password reset request serializer"""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Validate email exists"""
        if not User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("Email not found")
        return value.lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Password reset confirmation serializer"""
    
    token = serializers.UUIDField()
    new_password = serializers.CharField(
        write_only=True,
        min_length=12,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Validate token and password confirmation"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Validate token
        try:
            token_obj = PasswordResetToken.objects.get(
                token=attrs['token'],
                is_used=False
            )
            if not token_obj.is_valid():
                raise serializers.ValidationError("Token has expired")
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid token")
        
        attrs['token_obj'] = token_obj
        return attrs
    
    def save(self):
        """Reset password"""
        token_obj = self.validated_data['token_obj']
        user = token_obj.user
        
        user.set_password(self.validated_data['new_password'])
        user.save()
        
        # Mark token as used
        token_obj.is_used = True
        token_obj.used_at = timezone.now()
        token_obj.save()
        
        return user


class UserSessionSerializer(serializers.ModelSerializer):
    """User session serializer"""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSession
        fields = [
            'id', 'user_email', 'ip_address', 'user_agent', 'device_info',
            'location', 'is_active', 'created_at', 'last_activity', 'duration'
        ]
    
    def get_duration(self, obj):
        """Get session duration"""
        from django.utils import timezone
        duration = timezone.now() - obj.created_at
        return str(duration).split('.')[0]


class UserListSerializer(serializers.ModelSerializer):
    """User list serializer for admin views"""
    
    full_name = serializers.CharField(read_only=True)
    church_name = serializers.CharField(source='church.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    is_active_colored = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'phone_number', 'role', 'role_display',
            'church_name', 'is_active', 'is_phone_verified', 'is_email_verified',
            'is_active_colored', 'created_at', 'last_login'
        ]
    
    def get_is_active_colored(self, obj):
        """Get colored status"""
        if obj.is_active and not obj.is_suspended:
            return {'status': 'active', 'color': 'green'}
        elif obj.is_suspended:
            return {'status': 'suspended', 'color': 'orange'}
        else:
            return {'status': 'inactive', 'color': 'red'}
