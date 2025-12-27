from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import (
    PaymentMethod, PaymentRequest, PaymentCallback, 
    PaymentReversal, PaymentBatch
)
from common.admin import BaseAdmin, FinancialAdmin, colored_status, colored_amount


@admin.register(PaymentMethod)
class PaymentMethodAdmin(BaseAdmin):
    """Payment method admin"""
    
    list_display = [
        'name', 'church', 'method_type_display', 'is_active_colored',
        'is_default_colored', 'processing_fee_display', 'created_at'
    ]
    list_filter = [
        'method_type', 'is_active', 'is_default', 'requires_verification',
        'auto_confirm', 'church', 'created_at'
    ]
    search_fields = ['name', 'description', 'church__name']
    ordering = ['church', 'method_type', 'name']
    
    fieldsets = (
        (None, {
            'fields': ('church', 'method_type', 'name', 'description')
        }),
        ('Configuration', {
            'fields': (
                'is_active', 'is_default', 'requires_verification', 'auto_confirm'
            )
        }),
        ('Processing Settings', {
            'fields': (
                'processing_fee_percent', 'minimum_amount', 'maximum_amount'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def method_type_display(self, obj):
        return obj.get_method_type_display()
    method_type_display.short_description = 'Type'
    
    def is_active_colored(self, obj):
        if obj.is_active:
            color = 'green'
            status = 'Active'
        else:
            color = 'red'
            status = 'Inactive'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status
        )
    is_active_colored.short_description = 'Status'
    
    def is_default_colored(self, obj):
        if obj.is_default:
            color = 'green'
            status = 'Default'
        else:
            color = 'gray'
            status = 'Secondary'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status
        )
    is_default_colored.short_description = 'Priority'
    
    def processing_fee_display(self, obj):
        if obj.processing_fee_percent > 0:
            return format_html(
                '<span style="color: orange; font-weight: bold;">{}%</span>',
                obj.processing_fee_percent
            )
        return '-'
    processing_fee_display.short_description = 'Processing Fee'
    
    def get_queryset(self, request):
        """Filter payment methods based on admin role"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        elif request.user.role == 'denomination_admin':
            return qs.filter(church__denomination=request.user.church.denomination)
        else:
            return qs.filter(church=request.user.church)


@admin.register(PaymentRequest)
class PaymentRequestAdmin(FinancialAdmin):
    """Payment request admin"""
    
    list_display = [
        'request_id_display', 'giving_transaction', 'church', 'request_type_display',
        'amount_colored', 'phone_number', 'status_colored', 'retry_info',
        'callback_status', 'created_at'
    ]
    list_filter = [
        'status', 'request_type', 'payment_method', 'callback_received',
        'church', 'created_at'
    ]
    search_fields = [
        'request_id', 'giving_transaction__transaction_id',
        'phone_number', 'checkout_request_id'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('request_id', 'giving_transaction', 'church', 'request_type')
        }),
        ('Payment Details', {
            'fields': (
                'amount', 'currency', 'phone_number', 'business_number',
                'account_reference', 'transaction_desc'
            )
        }),
        ('Status', {
            'fields': ('status', 'response_code', 'response_message')
        }),
        ('API Response', {
            'fields': (
                'checkout_request_id', 'merchant_request_id'
            ),
            'classes': ('collapse',)
        }),
        ('Callback Information', {
            'fields': (
                'callback_received', 'callback_data', 'callback_received_at'
            ),
            'classes': ('collapse',)
        }),
        ('Processing Information', {
            'fields': (
                'processing_started_at', 'processing_completed_at',
                'retry_count', 'max_retries', 'next_retry_at'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = [
        'request_id', 'checkout_request_id', 'merchant_request_id',
        'response_code', 'response_message', 'callback_received',
        'callback_data', 'callback_received_at', 'processing_started_at',
        'processing_completed_at', 'retry_count', 'next_retry_at',
        'created_at', 'updated_at'
    ]
    
    def request_id_display(self, obj):
        request_id = str(obj.request_id)[:8]
        return format_html(
            '<span style="color: blue; font-family: monospace;">{}</span>',
            request_id
        )
    request_id_display.short_description = 'Request ID'
    
    def request_type_display(self, obj):
        return obj.get_request_type_display()
    request_type_display.short_description = 'Type'
    
    def amount_colored(self, obj):
        return colored_amount(obj)
    amount_colored.short_description = 'Amount'
    
    def status_colored(self, obj):
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'gray',
            'expired': 'purple'
        }
        color = colors.get(obj.status, 'black')
        return colored_status(obj, color)
    status_colored.short_description = 'Status'
    
    def retry_info(self, obj):
        if obj.retry_count > 0:
            return format_html(
                '<span style="color: orange; font-weight: bold;">{}/{} retries</span>',
                obj.retry_count,
                obj.max_retries
            )
        return '-'
    retry_info.short_description = 'Retries'
    
    def callback_status(self, obj):
        if obj.callback_received:
            color = 'green'
            status = 'Received'
        else:
            color = 'red'
            status = 'Pending'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status
        )
    callback_status.short_description = 'Callback'
    
    def get_queryset(self, request):
        """Filter payment requests based on admin role"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        elif request.user.role == 'denomination_admin':
            return qs.filter(church__denomination=request.user.church.denomination)
        else:
            return qs.filter(church=request.user.church)


@admin.register(PaymentCallback)
class PaymentCallbackAdmin(FinancialAdmin):
    """Payment callback admin"""
    
    list_display = [
        'callback_id_display', 'provider', 'callback_type_display',
        'transaction_id', 'payment_request_link', 'is_valid_colored',
        'status_colored', 'processing_attempts', 'created_at'
    ]
    list_filter = [
        'provider', 'callback_type', 'status', 'is_valid',
        'created_at'
    ]
    search_fields = [
        'callback_id', 'transaction_id', 'payment_request__request_id',
        'giving_transaction__transaction_id'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('callback_id', 'provider', 'callback_type', 'transaction_id')
        }),
        ('Relations', {
            'fields': ('payment_request', 'giving_transaction')
        }),
        ('Data', {
            'fields': ('raw_data', 'processed_data'),
            'classes': ('collapse',)
        }),
        ('Validation', {
            'fields': ('signature', 'is_valid', 'validation_errors')
        }),
        ('Processing', {
            'fields': ('status', 'processed_at', 'processing_attempts')
        }),
        ('Security', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = [
        'callback_id', 'raw_data', 'processed_data', 'signature',
        'is_valid', 'validation_errors', 'status', 'processed_at',
        'processing_attempts', 'ip_address', 'user_agent',
        'created_at', 'updated_at'
    ]
    
    def callback_id_display(self, obj):
        callback_id = str(obj.callback_id)[:8]
        return format_html(
            '<span style="color: blue; font-family: monospace;">{}</span>',
            callback_id
        )
    callback_id_display.short_description = 'Callback ID'
    
    def callback_type_display(self, obj):
        return obj.get_callback_type_display()
    callback_type_display.short_description = 'Type'
    
    def payment_request_link(self, obj):
        if obj.payment_request:
            request_id = str(obj.payment_request.request_id)[:8]
            return format_html(
                '<a href="/admin/payments/paymentrequest/{}/" style="color: blue;">{}</a>',
                obj.payment_request.id,
                request_id
            )
        return '-'
    payment_request_link.short_description = 'Payment Request'
    
    def is_valid_colored(self, obj):
        if obj.is_valid:
            color = 'green'
            status = 'Valid'
        else:
            color = 'red'
            status = 'Invalid'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status
        )
    is_valid_colored.short_description = 'Validation'
    
    def status_colored(self, obj):
        colors = {
            'received': 'blue',
            'processed': 'green',
            'failed': 'red',
            'invalid': 'orange'
        }
        color = colors.get(obj.status, 'black')
        return colored_status(obj, color)
    status_colored.short_description = 'Status'
    
    def get_queryset(self, request):
        """Filter callbacks based on admin role"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        elif request.user.role == 'denomination_admin':
            return qs.filter(
                payment_request__church__denomination=request.user.church.denomination
            )
        else:
            return qs.filter(payment_request__church=request.user.church)


@admin.register(PaymentReversal)
class PaymentReversalAdmin(FinancialAdmin):
    """Payment reversal admin"""
    
    list_display = [
        'reversal_id_display', 'original_transaction_link', 'reversal_type_display',
        'amount_colored', 'requested_by_name', 'approved_by_name',
        'status_colored', 'processed_at', 'created_at'
    ]
    list_filter = [
        'reversal_type', 'status', 'requested_by', 'approved_by', 'created_at'
    ]
    search_fields = [
        'reversal_id', 'original_transaction__transaction_id',
        'reason', 'reversal_transaction_id'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('reversal_id', 'original_transaction', 'payment_request', 'reversal_type')
        }),
        ('Reversal Details', {
            'fields': ('amount', 'reason')
        }),
        ('Status', {
            'fields': ('status', 'reversal_transaction_id', 'processed_at', 'processor_response')
        }),
        ('Approval', {
            'fields': ('requested_by', 'approved_by', 'approved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = [
        'reversal_id', 'reversal_transaction_id', 'processed_at',
        'processor_response', 'approved_by', 'approved_at',
        'created_at', 'updated_at'
    ]
    
    def reversal_id_display(self, obj):
        reversal_id = str(obj.reversal_id)[:8]
        return format_html(
            '<span style="color: blue; font-family: monospace;">{}</span>',
            reversal_id
        )
    reversal_id_display.short_description = 'Reversal ID'
    
    def reversal_type_display(self, obj):
        return obj.get_reversal_type_display()
    reversal_type_display.short_description = 'Type'
    
    def amount_colored(self, obj):
        return colored_amount(obj)
    amount_colored.short_description = 'Amount'
    
    def original_transaction_link(self, obj):
        if obj.original_transaction:
            transaction_id = str(obj.original_transaction.transaction_id)[:8]
            return format_html(
                '<a href="/admin/giving/givingtransaction/{}/" style="color: blue;">{}</a>',
                obj.original_transaction.id,
                transaction_id
            )
        return '-'
    original_transaction_link.short_description = 'Original Transaction'
    
    def requested_by_name(self, obj):
        return obj.requested_by.get_full_name() if obj.requested_by else '-'
    requested_by_name.short_description = 'Requested By'
    
    def approved_by_name(self, obj):
        return obj.approved_by.get_full_name() if obj.approved_by else '-'
    approved_by_name.short_description = 'Approved By'
    
    def status_colored(self, obj):
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return colored_status(obj, color)
    status_colored.short_description = 'Status'
    
    def get_queryset(self, request):
        """Filter reversals based on admin role"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        elif request.user.role == 'denomination_admin':
            return qs.filter(
                original_transaction__church__denomination=request.user.church.denomination
            )
        else:
            return qs.filter(original_transaction__church=request.user.church)


@admin.register(PaymentBatch)
class PaymentBatchAdmin(FinancialAdmin):
    """Payment batch admin"""
    
    list_display = [
        'batch_id_display', 'church', 'batch_type_display', 'title',
        'total_amount_colored', 'transaction_count', 'status_colored',
        'scheduled_for', 'processed_at', 'created_at'
    ]
    list_filter = [
        'batch_type', 'status', 'church', 'scheduled_for', 'created_at'
    ]
    search_fields = [
        'batch_id', 'title', 'description', 'processor_reference'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('batch_id', 'church', 'batch_type', 'title', 'description')
        }),
        ('Financial Information', {
            'fields': (
                'total_amount', 'transaction_count', 'processing_fee', 'net_amount'
            )
        }),
        ('Status', {
            'fields': ('status', 'processed_at', 'processor_reference')
        }),
        ('Processing', {
            'fields': ('processor_response',),
            'classes': ('collapse',)
        }),
        ('Schedule', {
            'fields': ('scheduled_for',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = [
        'batch_id', 'total_amount', 'transaction_count', 'processing_fee',
        'net_amount', 'processed_at', 'processor_reference', 'processor_response',
        'created_at', 'updated_at'
    ]
    
    def batch_id_display(self, obj):
        batch_id = str(obj.batch_id)[:8]
        return format_html(
            '<span style="color: blue; font-family: monospace;">{}</span>',
            batch_id
        )
    batch_id_display.short_description = 'Batch ID'
    
    def batch_type_display(self, obj):
        return obj.get_batch_type_display()
    batch_type_display.short_description = 'Type'
    
    def total_amount_colored(self, obj):
        return colored_amount(obj)
    total_amount_colored.short_description = 'Total Amount'
    
    def status_colored(self, obj):
        colors = {
            'draft': 'gray',
            'pending': 'orange',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'purple'
        }
        color = colors.get(obj.status, 'black')
        return colored_status(obj, color)
    status_colored.short_description = 'Status'
    
    def get_queryset(self, request):
        """Filter batches based on admin role"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        elif request.user.role == 'denomination_admin':
            return qs.filter(church__denomination=request.user.church.denomination)
        else:
            return qs.filter(church=request.user.church)
