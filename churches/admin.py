from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Denomination, Church, Campus, Department, SmallGroup,
    ChurchBankAccount, MpesaAccount
)
from common.admin import BaseAdmin, FinancialAdmin, colored_status, colored_amount
import json


@admin.register(Denomination)
class DenominationAdmin(BaseAdmin):
    """Denomination admin"""
    
    list_display = [
        'name', 'church_count', 'total_members', 'leader_name',
        'contact_phone', 'is_active_colored', 'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description', 'leader_name', 'contact_phone']
    ordering = ['name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Contact Info', {
            'fields': (
                'headquarters_address', 'contact_phone', 'contact_email', 'website'
            )
        }),
        ('Leadership', {
            'fields': ('leader_name', 'leader_title', 'leader_phone')
        }),
        ('Registration', {
            'fields': ('registration_number', 'registration_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def church_count(self, obj):
        count = obj.churches.filter(is_active=True).count()
        return format_html('<span style="color: blue; font-weight: bold;">{}</span>', count)
    church_count.short_description = 'Churches'
    
    def total_members(self, obj):
        from accounts.models import Member
        count = Member.objects.filter(
            user__church__denomination=obj,
            user__church__is_active=True
        ).count()
        return format_html('<span style="color: green; font-weight: bold;">{}</span>', count)
    total_members.short_description = 'Total Members'
    
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


@admin.register(Church)
class ChurchAdmin(BaseAdmin):
    """Church admin"""
    
    list_display = [
        'name', 'church_code', 'church_type_display', 'denomination',
        'city', 'county', 'senior_pastor_name', 'status_colored',
        'is_verified_colored', 'member_count', 'created_at'
    ]
    list_filter = [
        'church_type', 'status', 'is_verified', 'is_active',
        'denomination', 'city', 'county', 'created_at'
    ]
    search_fields = [
        'name', 'church_code', 'senior_pastor_name', 'email', 'phone_number'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'church_type', 'church_code', 'denomination')
        }),
        ('Contact Info', {
            'fields': (
                'phone_number', 'email', 'website'
            )
        }),
        ('Address', {
            'fields': (
                'address_line1', 'address_line2', 'city', 'county', 'postal_code',
                'latitude', 'longitude'
            )
        }),
        ('Leadership', {
            'fields': (
                'senior_pastor_name', 'senior_pastor_phone', 'senior_pastor_email'
            )
        }),
        ('Statistics', {
            'fields': (
                'established_date', 'membership_count', 'average_attendance'
            )
        }),
        ('Registration', {
            'fields': ('registration_number', 'registration_date')
        }),
        ('Status', {
            'fields': (
                'status', 'is_verified', 'verification_date', 'verified_by',
                'is_active'
            )
        }),
        ('Settings', {
            'fields': (
                'allow_online_giving', 'require_membership_approval'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['church_code', 'verification_date', 'verified_by', 'created_at', 'updated_at']
    
    def church_type_display(self, obj):
        return obj.get_church_type_display()
    church_type_display.short_description = 'Type'
    
    def status_colored(self, obj):
        colors = {
            'pending': 'orange',
            'verified': 'green',
            'suspended': 'red',
            'closed': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = 'Status'
    
    def is_verified_colored(self, obj):
        if obj.is_verified:
            color = 'green'
            status = 'Verified'
        else:
            color = 'orange'
            status = 'Pending'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status
        )
    is_verified_colored.short_description = 'Verification'
    
    def member_count(self, obj):
        from accounts.models import Member
        count = Member.objects.filter(user__church=obj).count()
        return format_html('<span style="color: blue; font-weight: bold;">{}</span>', count)
    member_count.short_description = 'Members'
    
    def get_queryset(self, request):
        """Filter churches based on admin role"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        elif request.user.role == 'denomination_admin':
            return qs.filter(denomination=request.user.church.denomination)
        else:
            return qs.filter(church=request.user.church)


@admin.register(Campus)
class CampusAdmin(BaseAdmin):
    """Campus admin"""
    
    list_display = [
        'name', 'church', 'city', 'county', 'campus_pastor_name',
        'is_main_campus_colored', 'is_active_colored', 'member_count',
        'created_at'
    ]
    list_filter = ['is_main_campus', 'is_active', 'church', 'city', 'created_at']
    search_fields = ['name', 'campus_pastor_name', 'address_line1']
    ordering = ['church', 'name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'church', 'is_main_campus')
        }),
        ('Contact Info', {
            'fields': ('phone_number', 'email')
        }),
        ('Address', {
            'fields': (
                'address_line1', 'address_line2', 'city', 'county', 'postal_code'
            )
        }),
        ('Leadership', {
            'fields': ('campus_pastor_name', 'campus_pastor_phone')
        }),
        ('Statistics', {
            'fields': ('established_date', 'membership_count', 'average_attendance')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def is_main_campus_colored(self, obj):
        if obj.is_main_campus:
            color = 'green'
            status = 'Main'
        else:
            color = 'gray'
            status = 'Branch'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status
        )
    is_main_campus_colored.short_description = 'Campus Type'
    
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
    
    def member_count(self, obj):
        from accounts.models import Member
        count = Member.objects.filter(user__church=obj.church, campus=obj).count()
        return format_html('<span style="color: blue; font-weight: bold;">{}</span>', count)
    member_count.short_description = 'Members'
    
    def get_queryset(self, request):
        """Filter campuses based on admin role"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        elif request.user.role == 'denomination_admin':
            return qs.filter(church__denomination=request.user.church.denomination)
        else:
            return qs.filter(church=request.user.church)


@admin.register(Department)
class DepartmentAdmin(BaseAdmin):
    """Department admin"""
    
    list_display = [
        'name', 'church', 'department_type_display', 'leader_name',
        'has_budget_colored', 'annual_budget_display', 'is_active_colored',
        'member_count', 'created_at'
    ]
    list_filter = [
        'department_type', 'has_budget', 'is_active', 'requires_approval',
        'church', 'created_at'
    ]
    search_fields = ['name', 'leader_name', 'description']
    ordering = ['church', 'name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'church', 'department_type')
        }),
        ('Leadership', {
            'fields': ('leader_name', 'leader_phone', 'leader_email')
        }),
        ('Details', {
            'fields': ('description', 'has_budget', 'annual_budget', 'requires_approval')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def department_type_display(self, obj):
        return obj.get_department_type_display()
    department_type_display.short_description = 'Type'
    
    def has_budget_colored(self, obj):
        if obj.has_budget:
            color = 'green'
            status = 'Yes'
        else:
            color = 'gray'
            status = 'No'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status
        )
    has_budget_colored.short_description = 'Budget'
    
    def annual_budget_display(self, obj):
        if obj.annual_budget:
            return colored_amount(obj)
        return '-'
    annual_budget_display.short_description = 'Budget'
    
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
    
    def member_count(self, obj):
        count = obj.members.count()
        return format_html('<span style="color: blue; font-weight: bold;">{}</span>', count)
    member_count.short_description = 'Members'


@admin.register(SmallGroup)
class SmallGroupAdmin(BaseAdmin):
    """Small group admin"""
    
    list_display = [
        'name', 'church', 'campus', 'group_type_display', 'leader_name',
        'meeting_day', 'meeting_time', 'is_open_colored', 'is_full_colored',
        'member_count', 'created_at'
    ]
    list_filter = [
        'group_type', 'is_active', 'is_open_to_new_members',
        'church', 'campus', 'meeting_day', 'created_at'
    ]
    search_fields = ['name', 'leader_name', 'meeting_location']
    ordering = ['church', 'name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'church', 'campus', 'group_type')
        }),
        ('Leadership', {
            'fields': ('leader_name', 'leader_phone', 'leader_email')
        }),
        ('Meeting Info', {
            'fields': (
                'meeting_day', 'meeting_time', 'meeting_location'
            )
        }),
        ('Details', {
            'fields': ('description', 'max_members')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_open_to_new_members')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def group_type_display(self, obj):
        return obj.get_group_type_display()
    group_type_display.short_description = 'Type'
    
    def is_open_colored(self, obj):
        if obj.is_open_to_new_members:
            color = 'green'
            status = 'Open'
        else:
            color = 'orange'
            status = 'Closed'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status
        )
    is_open_colored.short_description = 'Open'
    
    def is_full_colored(self, obj):
        if obj.is_full:
            color = 'red'
            status = 'Full'
        else:
            color = 'green'
            status = 'Available'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status
        )
    is_full_colored.short_description = 'Capacity'
    
    def member_count(self, obj):
        count = obj.members.count()
        if obj.max_members:
            percentage = (count / obj.max_members) * 100
            color = 'red' if percentage >= 90 else 'orange' if percentage >= 70 else 'green'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}/{} ({:.0f}%)</span>',
                color,
                count,
                obj.max_members,
                percentage
            )
        return format_template('<span style="color: blue; font-weight: bold;">{}</span>', count)
    member_count.short_description = 'Members'


@admin.register(ChurchBankAccount)
class ChurchBankAccountAdmin(FinancialAdmin):
    """Church bank account admin"""
    
    list_display = [
        'church', 'account_name', 'bank_name', 'account_type_display',
        'masked_account_number', 'is_primary_colored', 'is_active_colored',
        'created_at'
    ]
    list_filter = [
        'account_type', 'is_primary', 'is_active', 'church', 'bank_name'
    ]
    search_fields = ['account_name', 'bank_name', 'bank_branch']
    ordering = ['church', 'bank_name', 'account_name']
    
    fieldsets = (
        (None, {
            'fields': ('church', 'account_name', 'account_number', 'bank_name')
        }),
        ('Account Details', {
            'fields': (
                'bank_branch', 'account_type', 'is_primary', 'is_active'
            )
        }),
        ('Contact Info', {
            'fields': ('bank_phone', 'bank_email')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def account_type_display(self, obj):
        return obj.get_account_type_display()
    account_type_display.short_description = 'Type'
    
    def masked_account_number(self, obj):
        if obj.account_number:
            return f"****{obj.account_number[-4:]}"
        return '-'
    masked_account_number.short_description = 'Account Number'
    
    def is_primary_colored(self, obj):
        if obj.is_primary:
            color = 'green'
            status = 'Primary'
        else:
            color = 'gray'
            status = 'Secondary'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status
        )
    is_primary_colored.short_description = 'Priority'
    
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


@admin.register(MpesaAccount)
class MpesaAccountAdmin(FinancialAdmin):
    """M-Pesa account admin"""
    
    list_display = [
        'church', 'account_name', 'account_type_display',
        'masked_business_number', 'is_test_mode_colored', 'is_active_colored',
        'created_at'
    ]
    list_filter = [
        'account_type', 'is_active', 'is_test_mode', 'church'
    ]
    search_fields = ['account_name', 'business_number']
    ordering = ['church', 'account_type']
    
    fieldsets = (
        (None, {
            'fields': ('church', 'account_name', 'account_type', 'business_number')
        }),
        ('API Credentials', {
            'fields': (
                'consumer_key', 'consumer_secret', 'passkey'
            ),
            'classes': ('collapse',)
        }),
        ('Callback URLs', {
            'fields': (
                'callback_url', 'confirmation_url', 'validation_url'
            ),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_active', 'is_test_mode')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def account_type_display(self, obj):
        return obj.get_account_type_display()
    account_type_display.short_description = 'Type'
    
    def masked_business_number(self, obj):
        if obj.business_number:
            return f"****{obj.business_number[-4:]}"
        return '-'
    masked_business_number.short_description = 'Business Number'
    
    def is_test_mode_colored(self, obj):
        if obj.is_test_mode:
            color = 'orange'
            status = 'Test'
        else:
            color = 'green'
            status = 'Live'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status
        )
    is_test_mode_colored.short_description = 'Mode'
    
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
