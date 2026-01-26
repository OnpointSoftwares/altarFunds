from django.contrib import admin
from giving.models import GivingTransaction, GivingCategory
from expenses.models import Expense, ExpenseCategory
from budgets.models import Budget


@admin.register(GivingTransaction)
class GivingTransactionAdmin(admin.ModelAdmin):
    """Giving transaction admin"""
    
    list_display = [
        'transaction_id', 'member', 'church', 'category', 'amount',
        'transaction_type', 'status', 'payment_method', 'transaction_date'
    ]
    list_filter = [
        'status', 'transaction_type', 'payment_method', 'church',
        'transaction_date', 'category'
    ]
    search_fields = [
        'member__user__email', 'member__user__first_name', 
        'member__user__last_name', 'payment_reference', 'transaction_id'
    ]
    readonly_fields = ['transaction_id', 'created_at', 'updated_at']
    ordering = ['-transaction_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('member', 'church', 'category', 'transaction_type')
        }),
        ('Financial Details', {
            'fields': ('amount', 'currency', 'payment_method', 'payment_reference')
        }),
        ('Status', {
            'fields': ('status', 'transaction_date')
        }),
        ('System Information', {
            'fields': ('transaction_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(GivingCategory)
class GivingCategoryAdmin(admin.ModelAdmin):
    """Giving category admin"""
    
    list_display = ['name', 'church', 'is_active', 'is_tax_deductible', 'display_order']
    list_filter = ['is_active', 'is_tax_deductible', 'church']
    search_fields = ['name', 'church__name']
    ordering = ['church', 'display_order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'church')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_tax_deductible', 'display_order')
        }),
        ('Budget Target', {
            'fields': ('has_target', 'monthly_target'),
            'classes': ('collapse',)
        })
    )


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    """Expense admin"""
    
    list_display = [
        'title', 'user', 'category', 'amount', 'status', 'date'
    ]
    list_filter = ['status', 'category', 'date']
    search_fields = [
        'title', 'description', 'user__email', 'user__first_name', 'user__last_name'
    ]
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'user', 'category')
        }),
        ('Financial Details', {
            'fields': ('amount', 'receipt')
        }),
        ('Status', {
            'fields': ('status', 'date')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    """Expense category admin"""
    
    list_display = ['name', 'description']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    """Budget admin"""
    
    list_display = [
        'name', 'user', 'department', 'allocated_amount', 
        'spent_amount', 'remaining_amount', 'period', 'year'
    ]
    list_filter = ['period', 'year', 'department']
    search_fields = [
        'name', 'department', 'user__email', 'user__first_name', 'user__last_name'
    ]
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-year', '-month', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'user', 'department')
        }),
        ('Financial Details', {
            'fields': ('allocated_amount', 'spent_amount')
        }),
        ('Period', {
            'fields': ('period', 'year', 'month')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def remaining_amount(self, obj):
        return obj.remaining_amount
    remaining_amount.short_description = 'Remaining Amount'