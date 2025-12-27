from rest_framework import serializers
from .models import (
    PaymentMethod, PaymentRequest, PaymentCallback, 
    PaymentReversal, PaymentBatch
)
from giving.models import GivingTransaction
from common.serializers import BaseSerializer, CurrencyField, PhoneField


class PaymentMethodSerializer(BaseSerializer):
    """Payment method serializer"""
    
    method_type_display = serializers.CharField(source='get_method_type_display', read_only=True)
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'church', 'method_type', 'method_type_display', 'name', 'description',
            'is_active', 'is_default', 'requires_verification', 'auto_confirm',
            'processing_fee_percent', 'minimum_amount', 'maximum_amount',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate payment method data"""
        church = data.get('church')
        is_default = data.get('is_default', False)
        
        # Ensure only one default method per church per type
        if is_default and church:
            existing_default = PaymentMethod.objects.filter(
                church=church,
                method_type=data.get('method_type'),
                is_default=True
            ).exclude(id=self.instance.id if self.instance else None).first()
            
            if existing_default:
                raise serializers.ValidationError({
                    'is_default': f'There is already a default {existing_default.get_method_type_display()} method for this church'
                })
        
        # Validate amount ranges
        minimum_amount = data.get('minimum_amount')
        maximum_amount = data.get('maximum_amount')
        
        if minimum_amount and maximum_amount and minimum_amount > maximum_amount:
            raise serializers.ValidationError({
                'minimum_amount': 'Minimum amount cannot be greater than maximum amount'
            })
        
        return data


class PaymentRequestSerializer(BaseSerializer):
    """Payment request serializer"""
    
    request_type_display = serializers.CharField(source='get_request_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    amount = CurrencyField()
    phone_number = PhoneField()
    time_remaining = serializers.SerializerMethodField()
    can_retry = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PaymentRequest
        fields = [
            'id', 'request_id', 'giving_transaction', 'church', 'request_type',
            'request_type_display', 'amount', 'currency', 'phone_number',
            'business_number', 'account_reference', 'transaction_desc', 'status',
            'status_display', 'checkout_request_id', 'merchant_request_id',
            'response_code', 'response_message', 'callback_received',
            'callback_data', 'callback_received_at', 'processing_started_at',
            'processing_completed_at', 'retry_count', 'max_retries',
            'next_retry_at', 'time_remaining', 'can_retry',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'request_id', 'checkout_request_id', 'merchant_request_id',
            'response_code', 'response_message', 'callback_received',
            'callback_data', 'callback_received_at', 'processing_started_at',
            'processing_completed_at', 'retry_count', 'next_retry_at',
            'time_remaining', 'can_retry', 'created_at', 'updated_at'
        ]
    
    def get_time_remaining(self, obj):
        """Get time remaining for payment completion"""
        if obj.status not in ['pending', 'processing']:
            return None
        
        from django.utils import timezone
        if obj.next_retry_at:
            remaining = obj.next_retry_at - timezone.now()
            return max(0, int(remaining.total_seconds()))
        
        return None
    
    def validate_phone_number(self, value):
        """Validate phone number"""
        from common.validators import validate_phone_number
        validate_phone_number(value)
        return value
    
    def validate_amount(self, value):
        """Validate amount"""
        from common.validators import validate_amount
        validate_amount(value)
        return value


class PaymentRequestCreateSerializer(BaseSerializer):
    """Payment request creation serializer"""
    
    giving_transaction_id = serializers.UUIDField(write_only=True)
    payment_method = serializers.ChoiceField(choices=['mpesa', 'bank_transfer', 'mobile_money'])
    
    class Meta:
        model = PaymentRequest
        fields = ['giving_transaction_id', 'payment_method']
    
    def validate_giving_transaction_id(self, value):
        """Validate giving transaction"""
        try:
            transaction = GivingTransaction.objects.get(transaction_id=value)
            
            if transaction.status != 'pending':
                raise serializers.ValidationError("Transaction is not in pending status")
            
            return transaction
        except GivingTransaction.DoesNotExist:
            raise serializers.ValidationError("Invalid giving transaction")
    
    def create(self, validated_data):
        """Create payment request"""
        giving_transaction = validated_data.pop('giving_transaction_id')
        payment_method = validated_data.pop('payment_method')
        
        from .services import PaymentService
        return PaymentService.initiate_payment(giving_transaction, payment_method)


class PaymentCallbackSerializer(BaseSerializer):
    """Payment callback serializer"""
    
    provider_display = serializers.CharField(source='get_provider_display', read_only=True)
    callback_type_display = serializers.CharField(source='get_callback_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PaymentCallback
        fields = [
            'id', 'callback_id', 'provider', 'provider_display', 'callback_type',
            'callback_type_display', 'transaction_id', 'payment_request',
            'giving_transaction', 'raw_data', 'processed_data', 'signature',
            'is_valid', 'validation_errors', 'status', 'status_display',
            'processed_at', 'processing_attempts', 'ip_address', 'user_agent',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'callback_id', 'raw_data', 'processed_data', 'signature',
            'is_valid', 'validation_errors', 'status', 'processed_at',
            'processing_attempts', 'ip_address', 'user_agent', 'created_at', 'updated_at'
        ]


class PaymentReversalSerializer(BaseSerializer):
    """Payment reversal serializer"""
    
    reversal_type_display = serializers.CharField(source='get_reversal_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    amount = CurrencyField()
    requested_by_name = serializers.CharField(source='requested_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    
    class Meta:
        model = PaymentReversal
        fields = [
            'id', 'reversal_id', 'original_transaction', 'payment_request',
            'reversal_type', 'reversal_type_display', 'amount', 'reason',
            'status', 'status_display', 'reversal_transaction_id',
            'processed_at', 'processor_response', 'requested_by',
            'requested_by_name', 'approved_by', 'approved_by_name',
            'approved_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'reversal_id', 'reversal_transaction_id', 'processed_at',
            'processor_response', 'approved_by', 'approved_by_name',
            'approved_at', 'created_at', 'updated_at'
        ]
    
    def validate_amount(self, value):
        """Validate reversal amount"""
        from common.validators import validate_amount
        validate_amount(value)
        
        # Check if amount doesn't exceed original transaction
        if hasattr(self, 'instance') and self.instance:
            original_amount = self.instance.original_transaction.amount
            if value > original_amount:
                raise serializers.ValidationError(
                    f"Reversal amount cannot exceed original transaction amount of {original_amount}"
                )
        
        return value
    
    def validate_original_transaction(self, value):
        """Validate original transaction"""
        if value.status != 'completed':
            raise serializers.ValidationError("Only completed transactions can be reversed")
        
        # Check for existing reversals
        existing_reversals = PaymentReversal.objects.filter(
            original_transaction=value,
            status='completed'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        if existing_reversals >= value.amount:
            raise serializers.ValidationError("Transaction has already been fully reversed")
        
        return value


class PaymentReversalCreateSerializer(BaseSerializer):
    """Payment reversal creation serializer"""
    
    original_transaction_id = serializers.UUIDField(write_only=True)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    reason = serializers.CharField(max_length=500)
    
    class Meta:
        model = PaymentReversal
        fields = ['original_transaction_id', 'amount', 'reason']
    
    def validate_original_transaction_id(self, value):
        """Validate original transaction"""
        try:
            transaction = GivingTransaction.objects.get(transaction_id=value)
            return transaction
        except GivingTransaction.DoesNotExist:
            raise serializers.ValidationError("Invalid giving transaction")
    
    def create(self, validated_data):
        """Create payment reversal"""
        original_transaction = validated_data.pop('original_transaction_id')
        amount = validated_data['amount']
        reason = validated_data['reason']
        requested_by = self.context['request'].user
        
        from .services import PaymentService
        return PaymentService.reverse_payment(original_transaction, amount, reason, requested_by)


class PaymentBatchSerializer(BaseSerializer):
    """Payment batch serializer"""
    
    batch_type_display = serializers.CharField(source='get_batch_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_amount = CurrencyField()
    processing_fee = CurrencyField()
    net_amount = CurrencyField()
    transaction_count_display = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentBatch
        fields = [
            'id', 'batch_id', 'church', 'batch_type', 'batch_type_display',
            'title', 'description', 'total_amount', 'transaction_count',
            'transaction_count_display', 'processing_fee', 'net_amount',
            'status', 'status_display', 'processed_at', 'processor_reference',
            'processor_response', 'scheduled_for', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'batch_id', 'total_amount', 'transaction_count',
            'processing_fee', 'net_amount', 'processed_at', 'processor_reference',
            'processor_response', 'created_at', 'updated_at'
        ]
    
    def get_transaction_count_display(self, obj):
        """Get formatted transaction count"""
        return f"{obj.transaction_count:,} transactions"
    
    def validate_scheduled_for(self, value):
        """Validate scheduled time"""
        from django.utils import timezone
        if value and value <= timezone.now():
            raise serializers.ValidationError("Scheduled time must be in the future")
        return value


class MpesaCallbackSerializer(serializers.Serializer):
    """M-Pesa callback serializer"""
    
    def to_representation(self, instance):
        """Convert callback data to standard format"""
        if isinstance(instance, dict):
            return instance
        return super().to_representation(instance)


class PaymentStatusSerializer(serializers.Serializer):
    """Payment status response serializer"""
    
    status = serializers.CharField()
    message = serializers.CharField()
    transaction_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    payment_method = serializers.CharField()
    created_at = serializers.DateTimeField()
    processed_at = serializers.DateTimeField(allow_null=True)
    callback_data = serializers.JSONField(allow_null=True)


class PaymentMethodSummarySerializer(serializers.Serializer):
    """Payment method summary serializer"""
    
    method_type = serializers.CharField()
    method_name = serializers.CharField()
    is_active = serializers.BooleanField()
    is_default = serializers.BooleanField()
    total_transactions = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    success_rate = serializers.FloatField()
    average_processing_time = serializers.FloatField()


class PaymentStatsSerializer(serializers.Serializer):
    """Payment statistics serializer"""
    
    total_transactions = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    successful_transactions = serializers.IntegerField()
    failed_transactions = serializers.IntegerField()
    pending_transactions = serializers.IntegerField()
    success_rate = serializers.FloatField()
    average_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    payment_methods = PaymentMethodSummarySerializer(many=True)
    daily_stats = serializers.ListField(child=serializers.DictField())
    monthly_stats = serializers.ListField(child=serializers.DictField())
