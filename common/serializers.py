from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import TimeStampedModel, SoftDeleteModel

User = get_user_model()


class BaseSerializer(serializers.ModelSerializer):
    """Base serializer with common fields"""
    
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        abstract = True


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer"""
    
    full_name = serializers.CharField(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'role', 'role_display', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_active']


class SoftDeleteSerializer(serializers.ModelSerializer):
    """Serializer for models with soft delete"""
    
    is_deleted = serializers.BooleanField(read_only=True)
    deleted_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        abstract = True


class ChoiceField(serializers.ChoiceField):
    """Custom choice field that returns value instead of key"""
    
    def to_representation(self, obj):
        if obj == '' and self.allow_blank:
            return obj
        return self._choices.get(obj, obj)


class CurrencyField(serializers.DecimalField):
    """Custom currency field"""
    
    def __init__(self, **kwargs):
        kwargs.setdefault('max_digits', 15)
        kwargs.setdefault('decimal_places', 2)
        kwargs.setdefault('min_value', 0)
        super().__init__(**kwargs)


class PhoneField(serializers.CharField):
    """Custom phone number field with validation"""
    
    def to_internal_value(self, data):
        from .validators import validate_phone_number
        return validate_phone_number(data)


class ErrorResponseSerializer(serializers.Serializer):
    """Standard error response serializer"""
    
    error = serializers.BooleanField(default=True)
    status_code = serializers.IntegerField()
    message = serializers.CharField()
    details = serializers.DictField()
    timestamp = serializers.DateTimeField(required=False)


class SuccessResponseSerializer(serializers.Serializer):
    """Standard success response serializer"""
    
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    data = serializers.DictField(required=False)


class PaginationSerializer(serializers.Serializer):
    """Pagination metadata serializer"""
    
    count = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    current_page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)


class FileUploadSerializer(serializers.Serializer):
    """File upload serializer"""
    
    file = serializers.FileField()
    description = serializers.CharField(required=False, allow_blank=True)
    
    def validate_file(self, value):
        """Validate file upload"""
        max_size = 10 * 1024 * 1024  # 10MB
        
        if value.size > max_size:
            raise serializers.ValidationError("File size cannot exceed 10MB")
        
        # Check file type
        allowed_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'image/jpeg',
            'image/png',
        ]
        
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("File type not allowed")
        
        return value


class DateRangeSerializer(serializers.Serializer):
    """Date range filter serializer"""
    
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    
    def validate(self, attrs):
        """Validate date range"""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date must be before end date")
        
        return attrs


class BulkActionSerializer(serializers.Serializer):
    """Bulk action serializer"""
    
    ids = serializers.ListField(child=serializers.IntegerField())
    action = serializers.ChoiceField(choices=[
        ('activate', 'Activate'),
        ('deactivate', 'Deactivate'),
        ('delete', 'Delete'),
    ])
    
    def validate_ids(self, value):
        """Validate IDs list"""
        if not value:
            raise serializers.ValidationError("At least one ID must be provided")
        
        if len(value) > 100:
            raise serializers.ValidationError("Cannot process more than 100 items at once")
        
        return value
