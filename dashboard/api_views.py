from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

from giving.models import GivingTransaction, GivingCategory
from expenses.models import Expense, ExpenseCategory
from budgets.models import Budget
from accounts.models import User, Member

import calendar


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def financial_summary(request):
    """Get financial summary for dashboard"""
    user = request.user
    
    # Get current date info
    now = timezone.now()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current_year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Total income (this month)
    total_income = GivingTransaction.objects.filter(
        transaction_date__gte=current_month_start,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Total expenses (this month)
    total_expenses = Expense.objects.filter(
        date__gte=current_month_start,
        status='approved'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Balance
    balance = total_income - total_expenses
    
    # This year's data
    yearly_income = GivingTransaction.objects.filter(
        transaction_date__gte=current_year_start,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    yearly_expenses = Expense.objects.filter(
        date__gte=current_year_start,
        status='approved'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    return Response({
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': balance,
        'yearly_income': yearly_income,
        'yearly_expenses': yearly_expenses,
        'yearly_balance': yearly_income - yearly_expenses,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def monthly_trend(request):
    """Get monthly income/expense trends"""
    user = request.user
    now = timezone.now()
    
    # Get last 12 months data
    monthly_data = []
    for i in range(12):
        month_date = now - timedelta(days=i*30)
        month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get month end
        _, last_day = calendar.monthrange(month_date.year, month_date.month)
        month_end = month_date.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
        
        income = GivingTransaction.objects.filter(
            transaction_date__gte=month_start,
            transaction_date__lte=month_end,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        expenses = Expense.objects.filter(
            date__gte=month_start,
            date__lte=month_end,
            status='approved'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_data.append({
            'month': month_date.strftime('%Y-%m'),
            'income': income,
            'expenses': expenses,
            'balance': income - expenses
        })
    
    return Response(list(reversed(monthly_data)))


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def income_breakdown(request):
    """Get income breakdown by category"""
    user = request.user
    now = timezone.now()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    income_by_category = GivingTransaction.objects.filter(
        transaction_date__gte=current_month_start,
        status='completed'
    ).values('category__name').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    return Response(list(income_by_category))


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def expense_breakdown(request):
    """Get expense breakdown by category"""
    user = request.user
    now = timezone.now()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    expenses_by_category = Expense.objects.filter(
        date__gte=current_month_start,
        status='approved'
    ).values('category__name').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    return Response(list(expenses_by_category))
