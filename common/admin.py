from django.contrib import admin
from django.utils.html import format_html


class BaseAdmin(admin.ModelAdmin):
    """Base admin with common functionality"""
    
    def get_queryset(self, request):
        """Filter out soft-deleted records"""
        qs = super().get_queryset(request)
        if hasattr(self.model, 'is_deleted'):
            return qs.filter(is_deleted=False)
        return qs
    
    def delete_model(self, request, obj):
        """Override delete to use soft delete if available"""
        if hasattr(obj, 'delete'):
            obj.delete()  # This will call soft delete
        else:
            super().delete_model(request, obj)


class TimestampedAdmin(BaseAdmin):
    """Admin for timestamped models"""
    
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ()
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class FinancialAdmin(BaseAdmin):
    """Admin for financial models with enhanced security"""
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of financial records"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Restrict changes to authorized users"""
        if request.user.is_superuser:
            return True
        
        # Only allow treasurers and above to modify financial records
        if hasattr(request.user, 'role'):
            return request.user.role in ['treasurer', 'denomination_admin', 'system_admin']
        
        return False
    
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    def save_model(self, request, obj, form, change):
        """Set created_by/updated_by fields"""
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


def colored_status(self, obj):
    """Display status with color coding"""
    if hasattr(obj, 'is_active'):
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
    return '-'
colored_status.short_description = 'Status'


def colored_amount(self, obj):
    """Display currency amounts with proper formatting"""
    if hasattr(obj, 'amount'):
        amount = getattr(obj, 'amount', 0)
        if amount >= 0:
            color = 'green'
            sign = ''
        else:
            color = 'red'
            sign = '-'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">KES {}{:,}</span>',
            color,
            sign,
            abs(amount)
        )
    return '-'
colored_amount.short_description = 'Amount'
