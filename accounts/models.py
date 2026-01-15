from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """Custom user manager where email is the unique identifier"""
    
    def create_user(self, email, password, **extra_fields):
        """Create and save a user with the given email and password."""
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user
    
    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('member', _('Member')),
        ('pastor', _('Pastor')),
        ('treasurer', _('Treasurer')),
        ('auditor', _('Auditor')),
        ('denomination_admin', _('Denomination Admin')),
        ('system_admin', _('System Admin')),
    ]
    GENDER_CHOICES = [
        ('male', _('Male')),
        ('female', _('Female')),
        ('other', _('Other')),
    ]

    # Use email as the username field for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    # Use custom manager
    objects = CustomUserManager()

    # Override the email field to make it unique
    email = models.EmailField(_('email address'), unique=True)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    church = models.ForeignKey('churches.Church', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    firebase_uid = models.CharField(max_length=128, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    county = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    profile_picture = models.CharField(max_length=500, null=True, blank=True)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_device = models.TextField(blank=True)
    is_suspended = models.BooleanField(default=False)

    def get_church_permissions(self):
        # Placeholder for church-specific permissions
        if self.is_superuser or self.role == 'system_admin':
            return ['all']
        
        permissions = []
        if self.role in ['pastor', 'treasurer', 'auditor', 'denomination_admin']:
            permissions.append('can_manage_church')
        if self.role in ['treasurer']:
            permissions.append('can_manage_finances')
            
        return permissions

    class Meta:
        db_table = 'users'

class Member(models.Model):
    MEMBERSHIP_STATUS_CHOICES = [
        ('visitor', _('Visitor')),
        ('new_member', _('New Member')),
        ('member', _('Member')),
        ('inactive', _('Inactive')),
    ]
    MARITAL_STATUS_CHOICES = [
        ('single', _('Single')),
        ('married', _('Married')),
        ('divorced', _('Divorced')),
        ('widowed', _('Widowed')),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member_profile')
    church = models.ForeignKey('churches.Church', on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    membership_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    membership_status = models.CharField(max_length=20, choices=MEMBERSHIP_STATUS_CHOICES, default='new_member')
    membership_date = models.DateField(null=True, blank=True)
    id_number = models.CharField(max_length=20, blank=True)
    kra_pin = models.CharField(max_length=20, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    employer = models.CharField(max_length=100, blank=True)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True)
    spouse_name = models.CharField(max_length=100, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    departments = models.ManyToManyField('churches.Department', related_name='members', blank=True)
    small_group = models.ForeignKey('churches.SmallGroup', on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    is_tithe_payer = models.BooleanField(default=False)
    preferred_giving_method = models.CharField(max_length=20, blank=True)
    monthly_giving_goal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.church.name}"

class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    device_info = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
