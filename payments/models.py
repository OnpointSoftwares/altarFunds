from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from common.models import TimeStampedModel, FinancialModel
from common.validators import validate_amount, validate_phone_number, validate_paybill_number, validate_till_number
import uuid
import hashlib


class PaymentMethod(TimeStampedModel):
    """Payment method configuration for churches"""
    
    METHOD_TYPE_CHOICES = [
        ('mpesa', _('M-Pesa')),
        ('bank_transfer', _('Bank Transfer')),
        ('mobile_money', _('Mobile Money')),
        ('card', _('Card')),
        ('cash', _('Cash')),
        ('check', _('Check')),
        ('other', _('Other')),
    ]
    
    church = models.ForeignKey(
        'churches.Church',
        on_delete=models.CASCADE,
        related_name='payment_methods'
    )
    method_type = models.CharField(
        _('Method Type'),
        max_length=20,
        choices=METHOD_TYPE_CHOICES
    )
    name = models.CharField(_('Method Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    
    # Configuration
    is_active = models.BooleanField(_('Active'), default=True)
    is_default = models.BooleanField(_('Default'), default=False)
    requires_verification = models.BooleanField(_('Requires Verification'), default=True)
    
    # Processing Settings
    auto_confirm = models.BooleanField(_('Auto Confirm'), default=False)
    processing_fee_percent = models.DecimalField(
        _('Processing Fee %'),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    minimum_amount = models.DecimalField(
        _('Minimum Amount'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    maximum_amount = models.DecimalField(
        _('Maximum Amount'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    
    class Meta:
        db_table = 'payment_methods'
        verbose_name = _('Payment Method')
        verbose_name_plural = _('Payment Methods')
        ordering = ['church', 'method_type', 'name']
        indexes = [
            models.Index(fields=['church']),
            models.Index(fields=['method_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_default']),
        ]
    
    def __str__(self):
        return f"{self.church.name} - {self.name}"


class PaymentRequest(FinancialModel):
    """Payment request for processing payments"""
    
    REQUEST_TYPE_CHOICES = [
        ('stk_push', _('STK Push')),
        ('c2b', _('C2B')),
        ('b2c', _('B2C')),
        ('b2b', _('B2B')),
        ('transaction_status', _('Transaction Status')),
        ('account_balance', _('Account Balance')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
        ('expired', _('Expired')),
    ]
    
    # Basic Information
    request_id = models.UUIDField(
        _('Request ID'),
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    giving_transaction = models.ForeignKey(
        'giving.GivingTransaction',
        on_delete=models.PROTECT,
        related_name='payment_requests'
    )
    church = models.ForeignKey(
        'churches.Church',
        on_delete=models.PROTECT,
        related_name='payment_requests'
    )
    
    # Request Details
    request_type = models.CharField(
        _('Request Type'),
        max_length=20,
        choices=REQUEST_TYPE_CHOICES,
        default='stk_push'
    )
    amount = models.DecimalField(
        _('Amount'),
        max_digits=15,
        decimal_places=2,
        validators=[validate_amount]
    )
    currency = models.CharField(_('Currency'), max_length=3, default='KES')
    
    # M-Pesa Specific
    phone_number = models.CharField(
        _('Phone Number'),
        max_length=20,
        validators=[validate_phone_number]
    )
    business_number = models.CharField(
        _('Business Number'),
        max_length=10
    )
    account_reference = models.CharField(
        _('Account Reference'),
        max_length=100,
        blank=True
    )
    transaction_desc = models.CharField(
        _('Transaction Description'),
        max_length=100,
        blank=True
    )
    
    # Request Status
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # API Response
    checkout_request_id = models.CharField(
        _('Checkout Request ID'),
        max_length=200,
        blank=True
    )
    merchant_request_id = models.CharField(
        _('Merchant Request ID'),
        max_length=200,
        blank=True
    )
    response_code = models.CharField(
        _('Response Code'),
        max_length=10,
        blank=True
    )
    response_message = models.TextField(
        _('Response Message'),
        blank=True
    )
    
    # Callback Information
    callback_received = models.BooleanField(_('Callback Received'), default=False)
    callback_data = models.JSONField(_('Callback Data'), null=True, blank=True)
    callback_received_at = models.DateTimeField(
        _('Callback Received At'),
        null=True,
        blank=True
    )
    
    # Processing Information
    processing_started_at = models.DateTimeField(
        _('Processing Started At'),
        null=True,
        blank=True
    )
    processing_completed_at = models.DateTimeField(
        _('Processing Completed At'),
        null=True,
        blank=True
    )
    
    # Retry Information
    retry_count = models.PositiveIntegerField(_('Retry Count'), default=0)
    max_retries = models.PositiveIntegerField(_('Max Retries'), default=3)
    next_retry_at = models.DateTimeField(
        _('Next Retry At'),
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'payment_requests'
        verbose_name = _('Payment Request')
        verbose_name_plural = _('Payment Requests')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['request_id']),
            models.Index(fields=['giving_transaction']),
            models.Index(fields=['church']),
            models.Index(fields=['status']),
            models.Index(fields=['request_type']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['checkout_request_id']),
            models.Index(fields=['callback_received']),
            models.Index(fields=['next_retry_at']),
        ]
    
    def __str__(self):
        return f"Payment Request {self.request_id} - KES {self.amount}"
    
    def generate_checkout_request_id(self):
        """Generate unique checkout request ID"""
        timestamp = str(int(self.created_at.timestamp()))
        unique_string = f"{self.phone_number}{self.amount}{timestamp}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:32]
    
    def mark_processing(self):
        """Mark request as processing"""
        from django.utils import timezone
        
        self.status = 'processing'
        self.processing_started_at = timezone.now()
        self.save()
    
    def mark_completed(self, response_data):
        """Mark request as completed"""
        from django.utils import timezone
        
        self.status = 'completed'
        self.processing_completed_at = timezone.now()
        self.checkout_request_id = response_data.get('CheckoutRequestID', '')
        self.merchant_request_id = response_data.get('MerchantRequestID', '')
        self.response_code = response_data.get('ResponseCode', '')
        self.response_message = response_data.get('ResponseMessage', '')
        self.save()
    
    def mark_failed(self, response_data):
        """Mark request as failed"""
        from django.utils import timezone
        
        self.status = 'failed'
        self.processing_completed_at = timezone.now()
        self.response_code = response_data.get('ResponseCode', '')
        self.response_message = response_data.get('ResponseMessage', '')
        self.save()
    
    def record_callback(self, callback_data):
        """Record callback data"""
        from django.utils import timezone
        
        self.callback_received = True
        self.callback_data = callback_data
        self.callback_received_at = timezone.now()
        self.save()
    
    def can_retry(self):
        """Check if request can be retried"""
        return (
            self.status in ['failed', 'expired'] and
            self.retry_count < self.max_retries
        )
    
    def schedule_retry(self):
        """Schedule retry attempt"""
        from datetime import timedelta
        from django.utils import timezone
        
        self.retry_count += 1
        
        # Exponential backoff: 1min, 5min, 15min
        retry_delays = [1, 5, 15]
        delay_minutes = retry_delays[min(self.retry_count - 1, len(retry_delays) - 1)]
        
        self.next_retry_at = timezone.now() + timedelta(minutes=delay_minutes)
        self.status = 'pending'
        self.save()


class PaymentCallback(FinancialModel):
    """Payment callback from payment providers"""
    
    PROVIDER_CHOICES = [
        ('mpesa', _('M-Pesa')),
        ('bank', _('Bank')),
        ('mobile_money', _('Mobile Money')),
        ('card_processor', _('Card Processor')),
        ('other', _('Other')),
    ]
    
    CALLBACK_TYPE_CHOICES = [
        ('payment_confirmation', _('Payment Confirmation')),
        ('payment_failed', _('Payment Failed')),
        ('transaction_status', _('Transaction Status')),
        ('account_balance', _('Account Balance')),
        ('reversal', _('Reversal')),
    ]
    
    STATUS_CHOICES = [
        ('received', _('Received')),
        ('processed', _('Processed')),
        ('failed', _('Failed')),
        ('invalid', _('Invalid')),
    ]
    
    # Basic Information
    callback_id = models.UUIDField(
        _('Callback ID'),
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    provider = models.CharField(
        _('Provider'),
        max_length=20,
        choices=PROVIDER_CHOICES
    )
    callback_type = models.CharField(
        _('Callback Type'),
        max_length=30,
        choices=CALLBACK_TYPE_CHOICES
    )
    
    # Transaction Information
    transaction_id = models.CharField(
        _('Transaction ID'),
        max_length=200,
        db_index=True
    )
    payment_request = models.ForeignKey(
        PaymentRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='callbacks'
    )
    giving_transaction = models.ForeignKey(
        'giving.GivingTransaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='callbacks'
    )
    
    # Callback Data
    raw_data = models.JSONField(_('Raw Callback Data'))
    processed_data = models.JSONField(_('Processed Data'), null=True, blank=True)
    
    # Validation
    signature = models.CharField(_('Signature'), max_length=500, blank=True)
    is_valid = models.BooleanField(_('Is Valid'), default=False)
    validation_errors = models.TextField(_('Validation Errors'), blank=True)
    
    # Processing
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='received'
    )
    processed_at = models.DateTimeField(
        _('Processed At'),
        null=True,
        blank=True
    )
    processing_attempts = models.PositiveIntegerField(
        _('Processing Attempts'),
        default=0
    )
    
    # Security
    ip_address = models.GenericIPAddressField(_('IP Address'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    
    class Meta:
        db_table = 'payment_callbacks'
        verbose_name = _('Payment Callback')
        verbose_name_plural = _('Payment Callbacks')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['callback_id']),
            models.Index(fields=['provider']),
            models.Index(fields=['callback_type']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['payment_request']),
            models.Index(fields=['giving_transaction']),
            models.Index(fields=['status']),
            models.Index(fields=['is_valid']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Callback {self.callback_id} - {self.provider} - {self.transaction_id}"
    
    def validate_signature(self, secret_key):
        """Validate callback signature"""
        import hmac
        import hashlib
        
        try:
            # Generate expected signature
            payload = str(self.raw_data).encode('utf-8')
            expected_signature = hmac.new(
                secret_key.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            self.is_valid = hmac.compare_digest(
                expected_signature,
                self.signature
            )
            
            if not self.is_valid:
                self.validation_errors = "Signature mismatch"
            
            return self.is_valid
            
        except Exception as e:
            self.is_valid = False
            self.validation_errors = f"Validation error: {str(e)}"
            return False
    
    def mark_processed(self, processed_data):
        """Mark callback as processed"""
        from django.utils import timezone
        
        self.status = 'processed'
        self.processed_data = processed_data
        self.processed_at = timezone.now()
        self.save()


class PaymentReversal(FinancialModel):
    """Payment reversal/refund records"""
    
    REVERSAL_TYPE_CHOICES = [
        ('refund', _('Refund')),
        ('reversal', _('Reversal')),
        ('chargeback', _('Chargeback')),
        ('correction', _('Correction')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
    ]
    
    # Basic Information
    reversal_id = models.UUIDField(
        _('Reversal ID'),
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    original_transaction = models.ForeignKey(
        'giving.GivingTransaction',
        on_delete=models.PROTECT,
        related_name='reversals'
    )
    payment_request = models.ForeignKey(
        PaymentRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reversals'
    )
    
    # Reversal Details
    reversal_type = models.CharField(
        _('Reversal Type'),
        max_length=20,
        choices=REVERSAL_TYPE_CHOICES
    )
    amount = models.DecimalField(
        _('Amount'),
        max_digits=15,
        decimal_places=2,
        validators=[validate_amount]
    )
    reason = models.TextField(_('Reason'))
    
    # Status
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Processing Information
    reversal_transaction_id = models.CharField(
        _('Reversal Transaction ID'),
        max_length=200,
        blank=True
    )
    processed_at = models.DateTimeField(
        _('Processed At'),
        null=True,
        blank=True
    )
    processor_response = models.TextField(
        _('Processor Response'),
        blank=True
    )
    
    # Request Information
    requested_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='reversal_requests'
    )
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='approved_reversals'
    )
    approved_at = models.DateTimeField(
        _('Approved At'),
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'payment_reversals'
        verbose_name = _('Payment Reversal')
        verbose_name_plural = _('Payment Reversals')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reversal_id']),
            models.Index(fields=['original_transaction']),
            models.Index(fields=['payment_request']),
            models.Index(fields=['reversal_type']),
            models.Index(fields=['status']),
            models.Index(fields=['requested_by']),
            models.Index(fields=['approved_by']),
        ]
    
    def __str__(self):
        return f"Reversal {self.reversal_id} - KES {self.amount}"
    
    def approve(self, approved_by):
        """Approve reversal"""
        from django.utils import timezone
        
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.status = 'processing'
        self.save()
    
    def mark_completed(self, reversal_transaction_id):
        """Mark reversal as completed"""
        from django.utils import timezone
        
        self.status = 'completed'
        self.reversal_transaction_id = reversal_transaction_id
        self.processed_at = timezone.now()
        self.save()
    
    def mark_failed(self, processor_response):
        """Mark reversal as failed"""
        from django.utils import timezone
        
        self.status = 'failed'
        self.processor_response = processor_response
        self.processed_at = timezone.now()
        self.save()


class PaymentBatch(FinancialModel):
    """Batch processing for payments"""
    
    BATCH_TYPE_CHOICES = [
        ('settlement', _('Settlement')),
        ('payout', _('Payout')),
        ('refund', _('Refund')),
        ('reconciliation', _('Reconciliation')),
    ]
    
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
    ]
    
    # Basic Information
    batch_id = models.UUIDField(
        _('Batch ID'),
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    church = models.ForeignKey(
        'churches.Church',
        on_delete=models.CASCADE,
        related_name='payment_batches'
    )
    batch_type = models.CharField(
        _('Batch Type'),
        max_length=20,
        choices=BATCH_TYPE_CHOICES
    )
    title = models.CharField(_('Batch Title'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    
    # Financial Information
    total_amount = models.DecimalField(
        _('Total Amount'),
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[validate_amount]
    )
    transaction_count = models.PositiveIntegerField(
        _('Transaction Count'),
        default=0
    )
    processing_fee = models.DecimalField(
        _('Processing Fee'),
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[validate_amount]
    )
    net_amount = models.DecimalField(
        _('Net Amount'),
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[validate_amount]
    )
    
    # Status
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    # Processing Information
    processed_at = models.DateTimeField(
        _('Processed At'),
        null=True,
        blank=True
    )
    processor_reference = models.CharField(
        _('Processor Reference'),
        max_length=200,
        blank=True
    )
    processor_response = models.JSONField(
        _('Processor Response'),
        null=True,
        blank=True
    )
    
    # Schedule
    scheduled_for = models.DateTimeField(
        _('Scheduled For'),
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'payment_batches'
        verbose_name = _('Payment Batch')
        verbose_name_plural = _('Payment Batches')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['batch_id']),
            models.Index(fields=['church']),
            models.Index(fields=['batch_type']),
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_for']),
        ]
    
    def __str__(self):
        return f"Batch {self.batch_id} - {self.title}"
    
    def calculate_totals(self):
        """Calculate batch totals from transactions"""
        # This would be implemented based on batch type
        pass
    
    def mark_processed(self, processor_reference, processor_response):
        """Mark batch as processed"""
        from django.utils import timezone
        
        self.status = 'completed'
        self.processed_at = timezone.now()
        self.processor_reference = processor_reference
        self.processor_response = processor_response
        self.save()
