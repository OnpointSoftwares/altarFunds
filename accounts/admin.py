from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Member, UserSession, PasswordResetToken
from common.admin import BaseAdmin, FinancialAdmin, colored_status, colored_amount


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom user admin"""
    
    list_display = [
        'email', 'full_name', 'phone_number', 'role', 'church',
        'is_active_colored', 'is_phone_verified', 'is_email_verified',
        'last_login', 'created_at'
    ]
    list_filter = [
        'role', 'is_active', 'is_phone_verified', 'is_email_verified',
        'church', 'is_suspended', 'created_at'
    ]
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        ('Personal Info', {
            'fields': (
                'first_name', 'last_name', 'phone_number', 'date_of_birth',
                'gender', 'profile_picture'
            )
        }),
        ('Church Info', {
            'fields': ('church', 'role')
        }),
        ('Verification', {
            'fields': ('is_phone_verified', 'is_email_verified', 'firebase_uid')
        }),
        ('Address', {
            'fields': (
                'address_line1', 'address_line2', 'city', 'county', 'postal_code'
            ),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'is_suspended',
                'suspension_reason', 'suspended_until'
            )
        }),
        ('Settings', {
            'fields': (
                'email_notifications', 'sms_notifications', 'push_notifications'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('last_login', 'last_login_ip', 'last_login_device', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'first_name', 'last_name', 'phone_number',
                'password1', 'password2', 'role', 'church'
            ),
        }),
    )
    
    readonly_fields = [
        'last_login', 'last_login_ip', 'last_login_device', 'created_at', 'updated_at'
    ]
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Full Name'
    
    def is_active_colored(self, obj):
        """Display status with color"""
        if obj.is_suspended:
            color = 'orange'
            status = 'Suspended'
        elif obj.is_active:
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
    
    def get_queryset(self, request):
        """Filter users based on admin role"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        elif request.user.role == 'denomination_admin':
            return qs.filter(church__denomination=request.user.church.denomination)
        else:
            return qs.filter(church=request.user.church)


@admin.register(Member)
class MemberAdmin(BaseAdmin):
    """Member profile admin"""
    
    list_display = [
        'user', 'membership_number', 'membership_status', 'church',
        'departments_list', 'is_tithe_payer', 'monthly_giving_goal_display',
        'created_at'
    ]
    list_filter = [
        'membership_status', 'is_tithe_payer', 'marital_status',
        'preferred_giving_method', 'created_at'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'membership_number', 'id_number'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'membership_number', 'membership_status', 'membership_date')
        }),
        ('Personal Info', {
            'fields': ('id_number', 'kra_pin', 'occupation', 'employer')
        }),
        ('Family Info', {
            'fields': (
                'marital_status', 'spouse_name', 'emergency_contact_name',
                'emergency_contact_phone'
            )
        }),
        ('Church Involvement', {
            'fields': ('departments', 'small_group', 'is_tithe_payer')
        }),
        ('Giving Info', {
            'fields': (
                'preferred_giving_method', 'monthly_giving_goal'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['membership_number', 'created_at', 'updated_at']
    filter_horizontal = ['departments']
    
    def church(self, obj):
        return obj.user.church.name if obj.user.church else '-'
    church.short_description = 'Church'
    
    def departments_list(self, obj):
        return ', '.join([dept.name for dept in obj.departments.all()]) or '-'
    departments_list.short_description = 'Departments'
    
    def monthly_giving_goal_display(self, obj):
        if obj.monthly_giving_goal:
            return format_html(
                '<span style="color: green; font-weight: bold;">KES {:,.2f}</span>',
                obj.monthly_giving_goal
            )
        return '-'
    monthly_giving_goal_display.short_description = 'Monthly Goal'
    
    def get_queryset(self, request):
        """Filter members based on admin role"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        elif request.user.role == 'denomination_admin':
            return qs.filter(user__church__denomination=request.user.church.denomination)
        else:
            return qs.filter(user__church=request.user.church)


@admin.register(UserSession)
class UserSessionAdmin(BaseAdmin):
    """User session admin"""
    
    list_display = [
        'user', 'ip_address', 'device_info_summary', 'location_summary',
        'is_active_colored', 'created_at', 'last_activity', 'duration'
    ]
    list_filter = ['is_active', 'created_at', 'last_activity']
    search_fields = ['user__email', 'ip_address', 'user_agent']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'session_key', 'ip_address', 'is_active')
        }),
        ('Device Info', {
            'fields': ('user_agent', 'device_info'),
            'classes': ('collapse',)
        }),
        ('Location', {
            'fields': ('location',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_activity', 'expires_at')
        }),
    )
    
    readonly_fields = ['session_key', 'created_at', 'last_activity']
    
    def device_info_summary(self, obj):
        """Summarize device info"""
        device_info = obj.device_info or {}
        platform = device_info.get('platform', 'Unknown')
        browser = device_info.get('browser', 'Unknown')
        return f"{platform} - {browser}"
    device_info_summary.short_description = 'Device'
    
    def location_summary(self, obj):
        """Summarize location info"""
        location = obj.location or {}
        city = location.get('city', 'Unknown')
        country = location.get('country_name', 'Unknown')
        return f"{city}, {country}"
    location_summary.short_description = 'Location'
    
    def is_active_colored(self, obj):
        """Display status with color"""
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
    
    def duration(self, obj):
        """Calculate session duration"""
        from django.utils import timezone
        duration = timezone.now() - obj.created_at
        return str(duration).split('.')[0]
    duration.short_description = 'Duration'
    
    def get_queryset(self, request):
        """Filter sessions based on admin role"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        elif request.user.role == 'denomination_admin':
            return qs.filter(user__church__denomination=request.user.church.denomination)
        else:
            return qs.filter(user__church=request.user.church)


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(BaseAdmin):
    """Password reset token admin"""
    
    list_display = [
        'user', 'token_short', 'is_used_colored', 'ip_address',
        'created_at', 'expires_at', 'used_at'
    ]
    list_filter = ['is_used', 'created_at', 'expires_at']
    search_fields = ['user__email', 'ip_address']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'token', 'is_used')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at', 'used_at')
        }),
        ('Request Info', {
            'fields': ('ip_address',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['token', 'created_at', 'expires_at', 'used_at']
    
    def token_short(self, obj):
        """Display short token"""
        return str(obj.token)[:8] + '...'
    token_short.short_description = 'Token'
    
    def is_used_colored(self, obj):
        """Display usage status with color"""
        if obj.is_used:
            color = 'orange'
            status = 'Used'
        elif obj.expires_at < timezone.now():
            color = 'red'
            status = 'Expired'
        else:
            color = 'green'
            status = 'Valid'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status
        )
    is_used_colored.short_description = 'Status'
    
    def get_queryset(self, request):
        """Filter tokens based on admin role"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        elif request.user.role == 'denomination_admin':
            return qs.filter(user__church__denomination=request.user.church.denomination)
        else:
            return qs.filter(user__church=request.user.church)
