from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from common.models import TimeStampedModel, SoftDeleteModel
from common.validators import validate_phone_number, validate_id_number
import uuid


class User(AbstractUser, TimeStampedModel):
    """Custom user model with Firebase integration"""
    
    ROLE_CHOICES = [
        ('member', _('Member')),
        ('pastor', _('Pastor')),
        ('treasurer', _('Treasurer')),
        ('auditor', _('Auditor')),
        ('denomination_admin', _('Denomination Admin')),
        ('system_admin', _('System Admin')),
    ]
    
    # Override username to make it optional (we use email as unique identifier)
    username = None
    email = models.EmailField(_('Email Address'), unique=True)
    
    # Personal Information
    first_name = models.CharField(_('First Name'), max_length=50)
    last_name = models.CharField(_('Last Name'), max_length=50)
    phone_number = models.CharField(
        _('Phone Number'),
        max_length=20,
        unique=True,
        validators=[validate_phone_number],
        help_text=_('Kenyan phone number in international format (+254...)')
    )
    
    # Role and Permissions
    role = models.CharField(
        _('Role'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='member',
        help_text=_('User role in the church system')
    )
    
    # Firebase Integration
    firebase_uid = models.CharField(
        _('Firebase UID'),
        max_length=128,
        unique=True,
        null=True,
        blank=True,
        help_text=_('Firebase authentication unique identifier')
    )
    
    # Verification Status
    is_phone_verified = models.BooleanField(_('Phone Verified'), default=False)
    is_email_verified = models.BooleanField(_('Email Verified'), default=False)
    
    # Church Membership
    church = models.ForeignKey(
        'churches.Church',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='members',
        help_text=_('Church the user belongs to')
    )
    
    # Profile Information
    profile_picture = models.ImageField(
        _('Profile Picture'),
        upload_to='profile_pictures/',
        null=True,
        blank=True
    )
    date_of_birth = models.DateField(_('Date of Birth'), null=True, blank=True)
    gender = models.CharField(
        _('Gender'),
        max_length=10,
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        null=True,
        blank=True
    )
    
    # Address Information
    address_line1 = models.CharField(_('Address Line 1'), max_length=255, blank=True)
    address_line2 = models.CharField(_('Address Line 2'), max_length=255, blank=True)
    city = models.CharField(_('City'), max_length=100, blank=True)
    county = models.CharField(_('County'), max_length=100, blank=True)
    postal_code = models.CharField(_('Postal Code'), max_length=20, blank=True)
    
    # Last Login Tracking
    last_login_ip = models.GenericIPAddressField(_('Last Login IP'), null=True, blank=True)
    last_login_device = models.CharField(_('Last Login Device'), max_length=255, blank=True)
    
    # Account Status
    is_suspended = models.BooleanField(_('Suspended'), default=False)
    suspension_reason = models.TextField(_('Suspension Reason'), blank=True)
    suspended_until = models.DateTimeField(_('Suspended Until'), null=True, blank=True)
    
    # Settings
    email_notifications = models.BooleanField(_('Email Notifications'), default=True)
    sms_notifications = models.BooleanField(_('SMS Notifications'), default=True)
    push_notifications = models.BooleanField(_('Push Notifications'), default=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']
    
    class Meta:
        db_table = 'accounts_users'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['firebase_uid']),
            models.Index(fields=['church', 'role']),
        ]
    
    @property
    def full_name(self):
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_church_admin(self):
        """Check if user has church administration privileges"""
        return self.role in ['pastor', 'treasurer', 'auditor']
    
    @property
    def is_denomination_admin(self):
        """Check if user has denomination administration privileges"""
        return self.role in ['denomination_admin', 'system_admin']
    
    @property
    def is_financial_admin(self):
        """Check if user can manage financial operations"""
        return self.role in ['treasurer', 'denomination_admin', 'system_admin']
    
    @property
    def can_approve_expenses(self):
        """Check if user can approve expenses"""
        return self.role in ['pastor', 'denomination_admin', 'system_admin']
    
    def get_church_permissions(self):
        """Get user's permissions within their church"""
        if not self.church:
            return []
        
        permissions = []
        
        if self.role == 'member':
            permissions = ['view_own_giving', 'view_personal_reports']
        elif self.role == 'pastor':
            permissions = [
                'view_church_giving', 'view_church_reports', 'approve_expenses',
                'manage_members', 'view_financial_summary'
            ]
        elif self.role == 'treasurer':
            permissions = [
                'manage_finances', 'view_all_transactions', 'reconcile_payments',
                'manage_expenses', 'view_church_reports', 'generate_reports'
            ]
        elif self.role == 'auditor':
            permissions = [
                'view_all_transactions', 'audit_records', 'view_church_reports',
                'export_data', 'view_audit_logs'
            ]
        elif self.role == 'denomination_admin':
            permissions = ['all_permissions']
        elif self.role == 'system_admin':
            permissions = ['all_permissions', 'system_management']
        
        return permissions
    
    def suspend(self, reason, until=None):
        """Suspend user account"""
        self.is_suspended = True
        self.suspension_reason = reason
        self.suspended_until = until
        self.is_active = False
        self.save()
    
    def unsuspend(self):
        """Unsuspend user account"""
        self.is_suspended = False
        self.suspension_reason = ''
        self.suspended_until = None
        self.is_active = True
        self.save()


class Member(TimeStampedModel):
    """Extended member profile for church membership"""
    
    MEMBERSHIP_STATUS_CHOICES = [
        ('visitor', _('Visitor')),
        ('regular_attender', _('Regular Attender')),
        ('member', _('Member')),
        ('leadership', _('Leadership')),
        ('staff', _('Staff')),
        ('former_member', _('Former Member')),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='member_profile'
    )
    
    # Membership Information
    membership_number = models.CharField(
        _('Membership Number'),
        max_length=20,
        unique=True,
        blank=True,
        null=True
    )
    membership_status = models.CharField(
        _('Membership Status'),
        max_length=20,
        choices=MEMBERSHIP_STATUS_CHOICES,
        default='visitor'
    )
    membership_date = models.DateField(_('Membership Date'), null=True, blank=True)
    
    # Personal Information
    id_number = models.CharField(
        _('ID Number'),
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        validators=[validate_id_number]
    )
    kra_pin = models.CharField(_('KRA PIN'), max_length=20, blank=True)
    occupation = models.CharField(_('Occupation'), max_length=100, blank=True)
    employer = models.CharField(_('Employer'), max_length=200, blank=True)
    
    # Family Information
    marital_status = models.CharField(
        _('Marital Status'),
        max_length=20,
        choices=[
            ('single', 'Single'),
            ('married', 'Married'),
            ('divorced', 'Divorced'),
            ('widowed', 'Widowed'),
        ],
        blank=True
    )
    spouse_name = models.CharField(_('Spouse Name'), max_length=200, blank=True)
    emergency_contact_name = models.CharField(_('Emergency Contact Name'), max_length=200, blank=True)
    emergency_contact_phone = models.CharField(
        _('Emergency Contact Phone'),
        max_length=20,
        blank=True,
        validators=[validate_phone_number]
    )
    
    # Church Involvement
    departments = models.ManyToManyField(
        'churches.Department',
        blank=True,
        related_name='members'
    )
    small_group = models.ForeignKey(
        'churches.SmallGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members'
    )
    is_tithe_payer = models.BooleanField(_('Tithe Payer'), default=True)
    
    # Giving Information
    preferred_giving_method = models.CharField(
        _('Preferred Giving Method'),
        max_length=20,
        choices=[
            ('mpesa', 'M-Pesa'),
            ('bank', 'Bank Transfer'),
            ('cash', 'Cash'),
            ('check', 'Check'),
        ],
        default='mpesa'
    )
    monthly_giving_goal = models.DecimalField(
        _('Monthly Giving Goal'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Monthly giving goal in KES')
    )
    
    class Meta:
        db_table = 'accounts_members'
        verbose_name = _('Member')
        verbose_name_plural = _('Members')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['membership_number']),
            models.Index(fields=['membership_status']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.membership_number or 'No Number'}"
    
    def generate_membership_number(self):
        """Generate unique membership number"""
        if self.membership_number:
            return self.membership_number
        
        # Generate format: CHURCH_ID + YEAR + SEQUENCE
        church_id = self.user.church.id if self.user.church else '999'
        year = str(self.created_at.year)[-2:]
        
        # Get sequence number
        last_member = Member.objects.filter(
            membership_number__startswith=f"{church_id}{year}"
        ).order_by('-membership_number').first()
        
        if last_member and last_member.membership_number:
            sequence = int(last_member.membership_number[-4:]) + 1
        else:
            sequence = 1
        
        self.membership_number = f"{church_id}{year}{sequence:04d}"
        self.save()
        return self.membership_number


class UserSession(models.Model):
    """Track user sessions for security and audit"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    session_key = models.CharField(_('Session Key'), max_length=40)
    ip_address = models.GenericIPAddressField(_('IP Address'))
    user_agent = models.TextField(_('User Agent'))
    device_info = models.JSONField(_('Device Info'), default=dict, blank=True)
    location = models.JSONField(_('Location'), default=dict, blank=True)
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    last_activity = models.DateTimeField(_('Last Activity'), auto_now=True)
    expires_at = models.DateTimeField(_('Expires At'))
    
    class Meta:
        db_table = 'accounts_user_sessions'
        verbose_name = _('User Session')
        verbose_name_plural = _('User Sessions')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.ip_address}"


class PasswordResetToken(models.Model):
    """Password reset tokens for users"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens'
    )
    token = models.UUIDField(_('Token'), default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    expires_at = models.DateTimeField(_('Expires At'))
    is_used = models.BooleanField(_('Used'), default=False)
    used_at = models.DateTimeField(_('Used At'), null=True, blank=True)
    ip_address = models.GenericIPAddressField(_('IP Address'), null=True, blank=True)
    
    class Meta:
        db_table = 'accounts_password_reset_tokens'
        verbose_name = _('Password Reset Token')
        verbose_name_plural = _('Password Reset Tokens')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['token']),
            models.Index(fields=['is_used']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.token}"
    
    def is_valid(self):
        """Check if token is still valid"""
        from django.utils import timezone
        return not self.is_used and self.expires_at > timezone.now()
