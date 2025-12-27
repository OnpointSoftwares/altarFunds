from django.db import models
from django.utils.translation import gettext_lazy as _
from common.models import TimeStampedModel, SoftDeleteModel, FinancialModel
from common.validators import validate_phone_number, validate_paybill_number, validate_till_number, validate_bank_account_number
import uuid


class Denomination(TimeStampedModel):
    """Denomination model for church groupings"""
    
    name = models.CharField(_('Denomination Name'), max_length=200, unique=True)
    description = models.TextField(_('Description'), blank=True)
    headquarters_address = models.TextField(_('Headquarters Address'), blank=True)
    contact_phone = models.CharField(
        _('Contact Phone'),
        max_length=20,
        validators=[validate_phone_number],
        blank=True
    )
    contact_email = models.EmailField(_('Contact Email'), blank=True)
    website = models.URLField(_('Website'), blank=True)
    
    # Leadership
    leader_name = models.CharField(_('Leader Name'), max_length=200, blank=True)
    leader_title = models.CharField(_('Leader Title'), max_length=100, blank=True)
    leader_phone = models.CharField(
        _('Leader Phone'),
        max_length=20,
        validators=[validate_phone_number],
        blank=True
    )
    
    # Registration Details
    registration_number = models.CharField(_('Registration Number'), max_length=50, blank=True)
    registration_date = models.DateField(_('Registration Date'), null=True, blank=True)
    
    # Settings
    is_active = models.BooleanField(_('Active'), default=True)
    
    class Meta:
        db_table = 'churches_denominations'
        verbose_name = _('Denomination')
        verbose_name_plural = _('Denominations')
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def church_count(self):
        """Get number of churches in denomination"""
        return self.churches.filter(is_active=True).count()
    
    @property
    def total_members(self):
        """Get total members across all churches"""
        from accounts.models import Member
        return Member.objects.filter(
            user__church__denomination=self,
            user__church__is_active=True
        ).count()


class Church(TimeStampedModel, SoftDeleteModel):
    """Church model with comprehensive information"""
    
    CHURCH_TYPE_CHOICES = [
        ('main', _('Main Church')),
        ('branch', _('Branch Church')),
        ('plant', _('Church Plant')),
        ('chaplaincy', _('Chaplaincy')),
        ('mission', _('Mission Station')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending Verification')),
        ('verified', _('Verified')),
        ('suspended', _('Suspended')),
        ('closed', _('Closed')),
    ]
    
    # Basic Information
    name = models.CharField(_('Church Name'), max_length=200)
    church_type = models.CharField(
        _('Church Type'),
        max_length=20,
        choices=CHURCH_TYPE_CHOICES,
        default='main'
    )
    denomination = models.ForeignKey(
        Denomination,
        on_delete=models.PROTECT,
        related_name='churches',
        null=True,
        blank=True,
        help_text=_('Denomination affiliation (optional)')
    )
    
    # Church Code (Unique identifier)
    church_code = models.CharField(
        _('Church Code'),
        max_length=10,
        unique=True,
        help_text=_('Unique church identifier (e.g., NBI001)')
    )
    
    # Contact Information
    phone_number = models.CharField(
        _('Phone Number'),
        max_length=20,
        validators=[validate_phone_number]
    )
    email = models.EmailField(_('Email Address'))
    website = models.URLField(_('Website'), blank=True)
    
    # Address Information
    address_line1 = models.CharField(_('Address Line 1'), max_length=255)
    address_line2 = models.CharField(_('Address Line 2'), max_length=255, blank=True)
    city = models.CharField(_('City'), max_length=100)
    county = models.CharField(_('County'), max_length=100)
    postal_code = models.CharField(_('Postal Code'), max_length=20, blank=True)
    latitude = models.DecimalField(
        _('Latitude'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        _('Longitude'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    
    # Leadership Information
    senior_pastor_name = models.CharField(_('Senior Pastor Name'), max_length=200)
    senior_pastor_phone = models.CharField(
        _('Senior Pastor Phone'),
        max_length=20,
        validators=[validate_phone_number],
        blank=True
    )
    senior_pastor_email = models.EmailField(_('Senior Pastor Email'), blank=True)
    
    # Church Statistics
    established_date = models.DateField(_('Established Date'), null=True, blank=True)
    membership_count = models.PositiveIntegerField(_('Membership Count'), default=0)
    average_attendance = models.PositiveIntegerField(_('Average Attendance'), default=0)
    
    # Registration Details
    registration_number = models.CharField(_('Registration Number'), max_length=50, blank=True)
    registration_date = models.DateField(_('Registration Date'), null=True, blank=True)
    
    # Status and Verification
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    is_verified = models.BooleanField(_('Verified'), default=False)
    verification_date = models.DateTimeField(_('Verification Date'), null=True, blank=True)
    verified_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )
    
    # Settings
    is_active = models.BooleanField(_('Active'), default=True)
    allow_online_giving = models.BooleanField(_('Allow Online Giving'), default=True)
    require_membership_approval = models.BooleanField(_('Require Membership Approval'), default=False)
    
    class Meta:
        db_table = 'churches'
        verbose_name = _('Church')
        verbose_name_plural = _('Churches')
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['church_code']),
            models.Index(fields=['denomination']),
            models.Index(fields=['status']),
            models.Index(fields=['is_active']),
            models.Index(fields=['city', 'county']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.church_code})"
    
    def generate_church_code(self):
        """Generate unique church code"""
        if self.church_code:
            return self.church_code
        
        # Use city abbreviation + sequence
        city_abbr = self.city[:3].upper() if self.city else 'UNK'
        
        # Get last sequence for this city
        last_church = Church.objects.filter(
            church_code__startswith=city_abbr
        ).order_by('-church_code').first()
        
        if last_church and last_church.church_code:
            sequence = int(last_church.church_code[3:]) + 1
        else:
            sequence = 1
        
        self.church_code = f"{city_abbr}{sequence:03d}"
        self.save()
        return self.church_code
    
    @property
    def member_count(self):
        """Get actual member count from member profiles"""
        from accounts.models import Member
        return Member.objects.filter(user__church=self).count()
    
    @property
    def active_member_count(self):
        """Get active member count"""
        from accounts.models import Member
        return Member.objects.filter(
            user__church=self,
            user__is_active=True,
            membership_status='member'
        ).count()
    
    @property
    def total_giving_this_month(self):
        """Get total giving for current month"""
        from giving.models import GivingTransaction
        from django.utils import timezone
        
        now = timezone.now()
        return GivingTransaction.objects.filter(
            member__user__church=self,
            transaction_date__year=now.year,
            transaction_date__month=now.month,
            status='completed'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    def verify(self, verified_by):
        """Verify church"""
        self.is_verified = True
        self.verification_date = timezone.now()
        self.verified_by = verified_by
        self.status = 'verified'
        self.save()
    
    def suspend(self, reason):
        """Suspend church"""
        self.status = 'suspended'
        self.is_active = False
        self.save()


class Campus(TimeStampedModel, SoftDeleteModel):
    """Church campus model for multi-campus churches"""
    
    name = models.CharField(_('Campus Name'), max_length=200)
    church = models.ForeignKey(
        Church,
        on_delete=models.CASCADE,
        related_name='campuses'
    )
    
    # Contact Information
    phone_number = models.CharField(
        _('Phone Number'),
        max_length=20,
        validators=[validate_phone_number],
        blank=True
    )
    email = models.EmailField(_('Email Address'), blank=True)
    
    # Address Information
    address_line1 = models.CharField(_('Address Line 1'), max_length=255)
    address_line2 = models.CharField(_('Address Line 2'), max_length=255, blank=True)
    city = models.CharField(_('City'), max_length=100)
    county = models.CharField(_('County'), max_length=100)
    postal_code = models.CharField(_('Postal Code'), max_length=20, blank=True)
    
    # Leadership
    campus_pastor_name = models.CharField(_('Campus Pastor Name'), max_length=200, blank=True)
    campus_pastor_phone = models.CharField(
        _('Campus Pastor Phone'),
        max_length=20,
        validators=[validate_phone_number],
        blank=True
    )
    
    # Campus Information
    established_date = models.DateField(_('Established Date'), null=True, blank=True)
    membership_count = models.PositiveIntegerField(_('Membership Count'), default=0)
    average_attendance = models.PositiveIntegerField(_('Average Attendance'), default=0)
    
    # Settings
    is_active = models.BooleanField(_('Active'), default=True)
    is_main_campus = models.BooleanField(_('Main Campus'), default=False)
    
    class Meta:
        db_table = 'churches_campuses'
        verbose_name = _('Campus')
        verbose_name_plural = _('Campuses')
        ordering = ['church', 'name']
        indexes = [
            models.Index(fields=['church']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_main_campus']),
        ]
    
    def __str__(self):
        return f"{self.church.name} - {self.name}"
    
    @property
    def member_count(self):
        """Get member count for this campus"""
        from accounts.models import Member
        return Member.objects.filter(user__church=self.church, campus=self).count()


class Department(TimeStampedModel, SoftDeleteModel):
    """Church department model"""
    
    DEPARTMENT_TYPE_CHOICES = [
        ('ministry', _('Ministry')),
        ('admin', _('Administration')),
        ('support', _('Support')),
        ('outreach', _('Outreach')),
        ('education', _('Education')),
        ('worship', _('Worship')),
        ('youth', _('Youth')),
        ('children', _('Children')),
        ('men', _('Men')),
        ('women', _('Women')),
        ('other', _('Other')),
    ]
    
    name = models.CharField(_('Department Name'), max_length=200)
    church = models.ForeignKey(
        Church,
        on_delete=models.CASCADE,
        related_name='departments'
    )
    department_type = models.CharField(
        _('Department Type'),
        max_length=20,
        choices=DEPARTMENT_TYPE_CHOICES,
        default='ministry'
    )
    
    # Leadership
    leader_name = models.CharField(_('Department Leader Name'), max_length=200, blank=True)
    leader_phone = models.CharField(
        _('Department Leader Phone'),
        max_length=20,
        validators=[validate_phone_number],
        blank=True
    )
    leader_email = models.EmailField(_('Department Leader Email'), blank=True)
    
    # Description
    description = models.TextField(_('Description'), blank=True)
    
    # Budget and Finance
    has_budget = models.BooleanField(_('Has Budget'), default=False)
    annual_budget = models.DecimalField(
        _('Annual Budget'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Settings
    is_active = models.BooleanField(_('Active'), default=True)
    requires_approval = models.BooleanField(_('Requires Approval'), default=False)
    
    class Meta:
        db_table = 'churches_departments'
        verbose_name = _('Department')
        verbose_name_plural = _('Departments')
        ordering = ['church', 'name']
        indexes = [
            models.Index(fields=['church']),
            models.Index(fields=['name']),
            models.Index(fields=['department_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.church.name} - {self.name}"
    
    @property
    def member_count(self):
        """Get member count in department"""
        from accounts.models import Member
        return self.members.count()


class SmallGroup(TimeStampedModel, SoftDeleteModel):
    """Small group / cell group model"""
    
    GROUP_TYPE_CHOICES = [
        ('bible_study', _('Bible Study')),
        ('prayer', _('Prayer Group')),
        ('fellowship', _('Fellowship')),
        ('discipleship', _('Discipleship')),
        ('outreach', _('Outreach')),
        ('youth', _('Youth Group')),
        ('children', _('Children Group')),
        ('other', _('Other')),
    ]
    
    name = models.CharField(_('Group Name'), max_length=200)
    church = models.ForeignKey(
        Church,
        on_delete=models.CASCADE,
        related_name='small_groups'
    )
    campus = models.ForeignKey(
        Campus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='small_groups'
    )
    group_type = models.CharField(
        _('Group Type'),
        max_length=20,
        choices=GROUP_TYPE_CHOICES,
        default='bible_study'
    )
    
    # Leadership
    leader_name = models.CharField(_('Group Leader Name'), max_length=200)
    leader_phone = models.CharField(
        _('Group Leader Phone'),
        max_length=20,
        validators=[validate_phone_number],
        blank=True
    )
    leader_email = models.EmailField(_('Group Leader Email'), blank=True)
    
    # Meeting Information
    meeting_day = models.CharField(_('Meeting Day'), max_length=20, blank=True)
    meeting_time = models.TimeField(_('Meeting Time'), null=True, blank=True)
    meeting_location = models.CharField(_('Meeting Location'), max_length=255, blank=True)
    
    # Group Details
    description = models.TextField(_('Description'), blank=True)
    max_members = models.PositiveIntegerField(_('Maximum Members'), null=True, blank=True)
    
    # Settings
    is_active = models.BooleanField(_('Active'), default=True)
    is_open_to_new_members = models.BooleanField(_('Open to New Members'), default=True)
    
    class Meta:
        db_table = 'churches_small_groups'
        verbose_name = _('Small Group')
        verbose_name_plural = _('Small Groups')
        ordering = ['church', 'name']
        indexes = [
            models.Index(fields=['church']),
            models.Index(fields=['campus']),
            models.Index(fields=['name']),
            models.Index(fields=['group_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.church.name} - {self.name}"
    
    @property
    def member_count(self):
        """Get member count in small group"""
        from accounts.models import Member
        return self.members.count()
    
    @property
    def is_full(self):
        """Check if group is at maximum capacity"""
        if not self.max_members:
            return False
        return self.member_count >= self.max_members


class ChurchBankAccount(FinancialModel):
    """Church bank account information"""
    
    ACCOUNT_TYPE_CHOICES = [
        ('current', _('Current Account')),
        ('savings', _('Savings Account')),
        ('fixed_deposit', _('Fixed Deposit')),
        ('call_account', _('Call Account')),
    ]
    
    church = models.ForeignKey(
        Church,
        on_delete=models.CASCADE,
        related_name='bank_accounts'
    )
    account_name = models.CharField(_('Account Name'), max_length=200)
    account_number = models.CharField(
        _('Account Number'),
        max_length=30,
        validators=[validate_bank_account_number]
    )
    bank_name = models.CharField(_('Bank Name'), max_length=200)
    bank_branch = models.CharField(_('Bank Branch'), max_length=200, blank=True)
    account_type = models.CharField(
        _('Account Type'),
        max_length=20,
        choices=ACCOUNT_TYPE_CHOICES,
        default='current'
    )
    
    # Contact Information
    bank_phone = models.CharField(
        _('Bank Phone'),
        max_length=20,
        validators=[validate_phone_number],
        blank=True
    )
    bank_email = models.EmailField(_('Bank Email'), blank=True)
    
    # Status
    is_active = models.BooleanField(_('Active'), default=True)
    is_primary = models.BooleanField(_('Primary Account'), default=False)
    
    class Meta:
        db_table = 'churches_bank_accounts'
        verbose_name = _('Church Bank Account')
        verbose_name_plural = _('Church Bank Accounts')
        ordering = ['church', 'bank_name', 'account_name']
        indexes = [
            models.Index(fields=['church']),
            models.Index(fields=['bank_name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_primary']),
        ]
    
    def __str__(self):
        return f"{self.church.name} - {self.bank_name} ({self.account_number[-4:]})"


class MpesaAccount(FinancialModel):
    """M-Pesa account information for churches"""
    
    ACCOUNT_TYPE_CHOICES = [
        ('paybill', _('Paybill')),
        ('till', _('Till Number')),
    ]
    
    church = models.ForeignKey(
        Church,
        on_delete=models.CASCADE,
        related_name='mpesa_accounts'
    )
    account_type = models.CharField(
        _('Account Type'),
        max_length=10,
        choices=ACCOUNT_TYPE_CHOICES
    )
    business_number = models.CharField(
        _('Business Number'),
        max_length=10
    )
    account_name = models.CharField(_('Account Name'), max_length=200)
    
    # M-Pesa API Credentials
    consumer_key = models.CharField(_('Consumer Key'), max_length=200, blank=True)
    consumer_secret = models.CharField(_('Consumer Secret'), max_length=200, blank=True)
    passkey = models.CharField(_('Passkey'), max_length=200, blank=True)
    
    # Callback Configuration
    callback_url = models.URLField(_('Callback URL'), blank=True)
    confirmation_url = models.URLField(_('Confirmation URL'), blank=True)
    validation_url = models.URLField(_('Validation URL'), blank=True)
    
    # Status
    is_active = models.BooleanField(_('Active'), default=True)
    is_test_mode = models.BooleanField(_('Test Mode'), default=False)
    
    class Meta:
        db_table = 'churches_mpesa_accounts'
        verbose_name = _('M-Pesa Account')
        verbose_name_plural = _('M-Pesa Accounts')
        ordering = ['church', 'account_type']
        indexes = [
            models.Index(fields=['church']),
            models.Index(fields=['account_type']),
            models.Index(fields=['business_number']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.church.name} - {self.get_account_type_display()} ({self.business_number})"
    
    def clean(self):
        """Validate business number based on account type"""
        if self.account_type == 'paybill':
            validate_paybill_number(self.business_number)
        elif self.account_type == 'till':
            validate_till_number(self.business_number)
