from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from common.models import TimeStampedModel, FinancialModel
from common.validators import validate_amount
import uuid


class GivingCategory(TimeStampedModel):
    """Giving category model (Tithe, Offering, Building Fund, etc.)"""
    
    name = models.CharField(_('Category Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    church = models.ForeignKey(
        'churches.Church',
        on_delete=models.CASCADE,
        related_name='giving_categories'
    )
    
    # Category Settings
    is_tax_deductible = models.BooleanField(_('Tax Deductible'), default=True)
    is_active = models.BooleanField(_('Active'), default=True)
    display_order = models.PositiveIntegerField(_('Display Order'), default=0)
    
    # Budget Information
    has_target = models.BooleanField(_('Has Target'), default=False)
    monthly_target = models.DecimalField(
        _('Monthly Target'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    yearly_target = models.DecimalField(
        _('Yearly Target'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    
    class Meta:
        db_table = 'giving_categories'
        verbose_name = _('Giving Category')
        verbose_name_plural = _('Giving Categories')
        ordering = ['church', 'display_order', 'name']
        indexes = [
            models.Index(fields=['church']),
            models.Index(fields=['is_active']),
            models.Index(fields=['display_order']),
        ]
    
    def __str__(self):
        return f"{self.church.name} - {self.name}"
    
    @property
    def current_month_total(self):
        """Get total giving for current month"""
        from django.utils import timezone
        now = timezone.now()
        
        return self.giving_transactions.filter(
            transaction_date__year=now.year,
            transaction_date__month=now.month,
            status='completed'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    @property
    def current_year_total(self):
        """Get total giving for current year"""
        from django.utils import timezone
        now = timezone.now()
        
        return self.giving_transactions.filter(
            transaction_date__year=now.year,
            status='completed'
        ).aggregate(total=models.Sum('amount'))['total'] or 0


class GivingTransaction(FinancialModel):
    """Giving transaction model"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('one_time', _('One-Time')),
        ('recurring', _('Recurring')),
        ('pledge_payment', _('Pledge Payment')),
        ('special_offering', _('Special Offering')),
        ('mission_trip', _('Mission Trip')),
        ('building_fund', _('Building Fund')),
        ('other', _('Other')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
        ('cancelled', _('Cancelled')),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', _('M-Pesa')),
        ('bank_transfer', _('Bank Transfer')),
        ('cash', _('Cash')),
        ('check', _('Check')),
        ('mobile_money', _('Mobile Money')),
        ('card', _('Card')),
        ('other', _('Other')),
    ]
    
    # Basic Information
    transaction_id = models.UUIDField(
        _('Transaction ID'),
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    member = models.ForeignKey(
        'accounts.Member',
        on_delete=models.PROTECT,
        related_name='giving_transactions'
    )
    church = models.ForeignKey(
        'churches.Church',
        on_delete=models.PROTECT,
        related_name='giving_transactions'
    )
    category = models.ForeignKey(
        GivingCategory,
        on_delete=models.PROTECT,
        related_name='giving_transactions'
    )
    
    # Transaction Details
    transaction_type = models.CharField(
        _('Transaction Type'),
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        default='one_time'
    )
    amount = models.DecimalField(
        _('Amount'),
        max_digits=15,
        decimal_places=2,
        validators=[validate_amount]
    )
    currency = models.CharField(_('Currency'), max_length=3, default='KES')
    
    # Payment Information
    payment_method = models.CharField(
        _('Payment Method'),
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='mpesa'
    )
    payment_reference = models.CharField(
        _('Payment Reference'),
        max_length=100,
        blank=True,
        help_text=_('M-Pesa transaction ID, bank reference, etc.')
    )
    
    # Transaction Status
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    transaction_date = models.DateTimeField(_('Transaction Date'))
    completed_date = models.DateTimeField(_('Completed Date'), null=True, blank=True)
    
    # Additional Information
    notes = models.TextField(_('Notes'), blank=True)
    is_anonymous = models.BooleanField(_('Anonymous'), default=False)
    dedication = models.CharField(_('Dedication'), max_length=500, blank=True)
    
    # Recurring Information
    recurring_giving = models.ForeignKey(
        'RecurringGiving',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    
    # Pledge Information
    pledge = models.ForeignKey(
        'Pledge',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )
    
    # Refund Information
    refund_amount = models.DecimalField(
        _('Refund Amount'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    refund_reason = models.TextField(_('Refund Reason'), blank=True)
    refund_date = models.DateTimeField(_('Refund Date'), null=True, blank=True)
    
    class Meta:
        db_table = 'giving_transactions'
        verbose_name = _('Giving Transaction')
        verbose_name_plural = _('Giving Transactions')
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['member']),
            models.Index(fields=['church']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['transaction_date']),
            models.Index(fields=['payment_reference']),
        ]
    
    def __str__(self):
        return f"{self.member.user.full_name} - KES {self.amount} - {self.get_status_display()}"
    
    def mark_completed(self, payment_reference=None):
        """Mark transaction as completed"""
        from django.utils import timezone
        
        self.status = 'completed'
        self.completed_date = timezone.now()
        if payment_reference:
            self.payment_reference = payment_reference
        self.save()
        
        # Send confirmation notification
        from common.services import NotificationService
        NotificationService.send_giving_confirmation(
            self.member,
            self.amount,
            str(self.transaction_id)
        )
        
        # Update pledge if applicable
        if self.pledge:
            self.pledge.update_paid_amount()
        
        # Log completion
        from common.services import AuditService
        AuditService.log_financial_transaction(
            user=self.created_by,
            action='GIVING_COMPLETED',
            amount=self.amount,
            details={
                'transaction_id': str(self.transaction_id),
                'member': self.member.user.email,
                'category': self.category.name,
                'payment_method': self.payment_method
            }
        )
    
    def mark_failed(self, reason):
        """Mark transaction as failed"""
        self.status = 'failed'
        self.notes = f"Failed: {reason}"
        self.save()
        
        # Send failure notification
        from common.services import NotificationService
        NotificationService.send_payment_failure_notification(
            self.member,
            self.amount,
            reason
        )
    
    def refund(self, amount, reason):
        """Process refund"""
        from django.utils import timezone
        
        self.status = 'refunded'
        self.refund_amount = amount
        self.refund_reason = reason
        self.refund_date = timezone.now()
        self.save()
        
        # Log refund
        from common.services import AuditService
        AuditService.log_financial_transaction(
            user=self.updated_by,
            action='GIVING_REFUND',
            amount=amount,
            details={
                'original_transaction': str(self.transaction_id),
                'reason': reason
            }
        )


class RecurringGiving(FinancialModel):
    """Recurring giving model"""
    
    FREQUENCY_CHOICES = [
        ('weekly', _('Weekly')),
        ('bi_weekly', _('Bi-Weekly')),
        ('monthly', _('Monthly')),
        ('quarterly', _('Quarterly')),
        ('yearly', _('Yearly')),
    ]
    
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('paused', _('Paused')),
        ('cancelled', _('Cancelled')),
        ('completed', _('Completed')),
    ]
    
    # Basic Information
    member = models.ForeignKey(
        'accounts.Member',
        on_delete=models.CASCADE,
        related_name='recurring_giving'
    )
    church = models.ForeignKey(
        'churches.Church',
        on_delete=models.CASCADE,
        related_name='recurring_giving'
    )
    category = models.ForeignKey(
        GivingCategory,
        on_delete=models.PROTECT,
        related_name='recurring_giving'
    )
    
    # Recurring Details
    frequency = models.CharField(
        _('Frequency'),
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='monthly'
    )
    amount = models.DecimalField(
        _('Amount'),
        max_digits=15,
        decimal_places=2,
        validators=[validate_amount]
    )
    
    # Schedule Information
    start_date = models.DateField(_('Start Date'))
    end_date = models.DateField(_('End Date'), null=True, blank=True)
    next_payment_date = models.DateField(_('Next Payment Date'))
    
    # Status
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    # Payment Method
    payment_method = models.CharField(
        _('Payment Method'),
        max_length=20,
        choices=GivingTransaction.PAYMENT_METHOD_CHOICES,
        default='mpesa'
    )
    
    # Additional Information
    notes = models.TextField(_('Notes'), blank=True)
    
    # Statistics
    total_amount_given = models.DecimalField(
        _('Total Amount Given'),
        max_digits=15,
        decimal_places=2,
        default=0
    )
    total_transactions = models.PositiveIntegerField(_('Total Transactions'), default=0)
    
    class Meta:
        db_table = 'giving_recurring'
        verbose_name = _('Recurring Giving')
        verbose_name_plural = _('Recurring Giving')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['member']),
            models.Index(fields=['church']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['frequency']),
            models.Index(fields=['next_payment_date']),
        ]
    
    def __str__(self):
        return f"{self.member.user.full_name} - KES {self.amount} ({self.get_frequency_display()})"
    
    def pause(self):
        """Pause recurring giving"""
        self.status = 'paused'
        self.save()
    
    def resume(self):
        """Resume recurring giving"""
        self.status = 'active'
        self.save()
    
    def cancel(self):
        """Cancel recurring giving"""
        self.status = 'cancelled'
        self.save()
    
    def update_next_payment_date(self):
        """Update next payment date based on frequency"""
        from datetime import timedelta, date
        
        current_date = self.next_payment_date
        
        if self.frequency == 'weekly':
            self.next_payment_date = current_date + timedelta(weeks=1)
        elif self.frequency == 'bi_weekly':
            self.next_payment_date = current_date + timedelta(weeks=2)
        elif self.frequency == 'monthly':
            # Add one month
            if current_date.month == 12:
                self.next_payment_date = date(current_date.year + 1, 1, current_date.day)
            else:
                self.next_payment_date = date(current_date.year, current_date.month + 1, current_date.day)
        elif self.frequency == 'quarterly':
            self.next_payment_date = current_date + timedelta(weeks=13)
        elif self.frequency == 'yearly':
            self.next_payment_date = date(current_date.year + 1, current_date.month, current_date.day)
        
        self.save()
    
    def process_payment(self):
        """Process recurring payment"""
        from django.utils import timezone
        
        if self.status != 'active':
            return None
        
        # Create transaction
        transaction = GivingTransaction.objects.create(
            member=self.member,
            church=self.church,
            category=self.category,
            transaction_type='recurring',
            amount=self.amount,
            payment_method=self.payment_method,
            transaction_date=timezone.now().date(),
            recurring_giving=self,
            created_by=self.member.user
        )
        
        # Update statistics
        self.total_amount_given += self.amount
        self.total_transactions += 1
        
        # Update next payment date
        self.update_next_payment_date()
        
        # Check if end date reached
        if self.end_date and self.next_payment_date > self.end_date:
            self.status = 'completed'
        
        self.save()
        
        return transaction


class Pledge(TimeStampedModel):
    """Pledge model for fundraising campaigns"""
    
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('partially_paid', _('Partially Paid')),
        ('fully_paid', _('Fully Paid')),
        ('overdue', _('Overdue')),
        ('cancelled', _('Cancelled')),
    ]
    
    # Basic Information
    member = models.ForeignKey(
        'accounts.Member',
        on_delete=models.CASCADE,
        related_name='pledges'
    )
    church = models.ForeignKey(
        'churches.Church',
        on_delete=models.CASCADE,
        related_name='pledges'
    )
    category = models.ForeignKey(
        GivingCategory,
        on_delete=models.PROTECT,
        related_name='pledges'
    )
    
    # Pledge Details
    pledge_amount = models.DecimalField(
        _('Pledge Amount'),
        max_digits=15,
        decimal_places=2,
        validators=[validate_amount]
    )
    paid_amount = models.DecimalField(
        _('Paid Amount'),
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    # Schedule Information
    pledge_date = models.DateField(_('Pledge Date'))
    start_date = models.DateField(_('Start Date'))
    end_date = models.DateField(_('End Date'))
    
    # Status
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    # Additional Information
    title = models.CharField(_('Pledge Title'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    notes = models.TextField(_('Notes'), blank=True)
    
    # Payment Schedule
    payment_frequency = models.CharField(
        _('Payment Frequency'),
        max_length=20,
        choices=RecurringGiving.FREQUENCY_CHOICES,
        default='monthly'
    )
    installment_amount = models.DecimalField(
        _('Installment Amount'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'giving_pledges'
        verbose_name = _('Pledge')
        verbose_name_plural = _('Pledges')
        ordering = ['-pledge_date']
        indexes = [
            models.Index(fields=['member']),
            models.Index(fields=['church']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['pledge_date']),
            models.Index(fields=['end_date']),
        ]
    
    def __str__(self):
        return f"{self.member.user.full_name} - KES {self.pledge_amount} ({self.title})"
    
    @property
    def balance_amount(self):
        """Get remaining balance"""
        return self.pledge_amount - self.paid_amount
    
    @property
    def completion_percentage(self):
        """Get completion percentage"""
        if self.pledge_amount == 0:
            return 0
        return (self.paid_amount / self.pledge_amount) * 100
    
    @property
    def is_overdue(self):
        """Check if pledge is overdue"""
        from django.utils import timezone
        return (
            self.end_date < timezone.now().date() and
            self.paid_amount < self.pledge_amount
        )
    
    def update_paid_amount(self):
        """Update paid amount from transactions"""
        total_paid = self.payments.filter(
            status='completed'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        self.paid_amount = total_paid
        
        # Update status
        if total_paid >= self.pledge_amount:
            self.status = 'fully_paid'
        elif total_paid > 0:
            self.status = 'partially_paid'
        elif self.is_overdue:
            self.status = 'overdue'
        
        self.save()
    
    def calculate_installment_amount(self):
        """Calculate installment amount"""
        if self.installment_amount:
            return self.installment_amount
        
        # Calculate based on frequency and duration
        from datetime import date
        duration_days = (self.end_date - self.start_date).days
        
        if self.payment_frequency == 'weekly':
            installments = duration_days // 7
        elif self.payment_frequency == 'bi_weekly':
            installments = duration_days // 14
        elif self.payment_frequency == 'monthly':
            installments = duration_days // 30
        elif self.payment_frequency == 'quarterly':
            installments = duration_days // 90
        elif self.payment_frequency == 'yearly':
            installments = duration_days // 365
        else:
            installments = 1
        
        if installments > 0:
            return self.pledge_amount / installments
        
        return self.pledge_amount


class GivingCampaign(TimeStampedModel):
    """Giving campaign model for special fundraising initiatives"""
    
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('active', _('Active')),
        ('paused', _('Paused')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]
    
    # Basic Information
    title = models.CharField(_('Campaign Title'), max_length=200)
    description = models.TextField(_('Description'))
    church = models.ForeignKey(
        'churches.Church',
        on_delete=models.CASCADE,
        related_name='giving_campaigns'
    )
    category = models.ForeignKey(
        GivingCategory,
        on_delete=models.PROTECT,
        related_name='campaigns'
    )
    
    # Campaign Goals
    target_amount = models.DecimalField(
        _('Target Amount'),
        max_digits=15,
        decimal_places=2,
        validators=[validate_amount]
    )
    current_amount = models.DecimalField(
        _('Current Amount'),
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    # Schedule
    start_date = models.DateTimeField(_('Start Date'))
    end_date = models.DateTimeField(_('End Date'))
    
    # Status
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    # Additional Information
    featured_image = models.CharField(
        _('Featured Image URL'),
        max_length=500,
        null=True,
        blank=True
    )
    video_url = models.URLField(_('Video URL'), blank=True)
    terms_and_conditions = models.TextField(_('Terms and Conditions'), blank=True)
    
    # Settings
    allow_anonymous = models.BooleanField(_('Allow Anonymous Giving'), default=True)
    show_publicly = models.BooleanField(_('Show Publicly'), default=True)
    enable_updates = models.BooleanField(_('Enable Updates'), default=True)
    
    class Meta:
        db_table = 'giving_campaigns'
        verbose_name = _('Giving Campaign')
        verbose_name_plural = _('Giving Campaigns')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['church']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
        ]
    
    def __str__(self):
        return f"{self.church.name} - {self.title}"
    
    @property
    def progress_percentage(self):
        """Get campaign progress percentage"""
        if self.target_amount == 0:
            return 0
        return (self.current_amount / self.target_amount) * 100
    
    @property
    def days_remaining(self):
        """Get days remaining in campaign"""
        from django.utils import timezone
        if self.end_date <= timezone.now():
            return 0
        return (self.end_date - timezone.now()).days
    
    @property
    def is_active(self):
        """Check if campaign is currently active"""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.status == 'active' and
            self.start_date <= now <= self.end_date
        )
    
    def update_current_amount(self):
        """Update current amount from transactions"""
        total = self.transactions.filter(
            status='completed'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        self.current_amount = total
        self.save()
    
    def add_transaction(self, transaction):
        """Add transaction to campaign"""
        self.transactions.add(transaction)
        self.update_current_amount()


class GivingTransactionCampaign(models.Model):
    """Through model for transaction-campaign relationship"""
    
    transaction = models.ForeignKey(
        GivingTransaction,
        on_delete=models.CASCADE,
        related_name='campaigns'
    )
    campaign = models.ForeignKey(
        GivingCampaign,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    allocated_amount = models.DecimalField(
        _('Allocated Amount'),
        max_digits=15,
        decimal_places=2
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    class Meta:
        db_table = 'giving_transaction_campaigns'
        verbose_name = _('Transaction Campaign')
        verbose_name_plural = _('Transaction Campaigns')
        unique_together = ['transaction', 'campaign']
        indexes = [
            models.Index(fields=['transaction']),
            models.Index(fields=['campaign']),
        ]
