from django.contrib import admin
from .models import User, Member, UserSession, PasswordResetToken

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'church', 'is_active', 'is_suspended', 'date_joined')
    list_filter = ('is_active', 'is_suspended', 'role', 'church')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'church', 'membership_number', 'membership_date', 'membership_status')
    list_filter = ('membership_status', 'church')
    search_fields = ('membership_number', 'user__email', 'church__name')
    ordering = ('-membership_date',)

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'is_active', 'last_activity', 'created_at')
    list_filter = ('is_active', 'created_at', 'last_activity')
    search_fields = ('user__email', 'ip_address')
    ordering = ('-last_activity',)
    readonly_fields = ('user', 'session_key', 'ip_address', 'user_agent', 'device_info', 'created_at', 'expires_at', 'last_activity')

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_used', 'used_at', 'created_at', 'expires_at', 'ip_address')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'token')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'token', 'created_at', 'expires_at', 'is_used', 'used_at', 'ip_address')
