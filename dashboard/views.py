from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

from giving.models import GivingTransaction, GivingCategory
from expenses.models import Expense
from accounts.models import User

@login_required
def dashboard_view(request):
    """Renders the main dashboard page."""
    return render(request, 'dashboard/index.html')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def financial_summary(request):
    """Get financial summary for dashboard."""
    user = request.user
    
    # Check if user has a church assigned
    if not user.church:
        return Response({
            'totalIncome': 0,
            'monthlyIncome': 0,
            'totalExpenses': 0,
            'monthlyExpenses': 0,
            'netBalance': 0,
            'church': None,
            'message': 'No church assigned. Please join a church to view financial data.'
        })
    
    church = user.church
    
    # Calculate income (donations)
    total_income = GivingTransaction.objects.filter(
        church=church
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    monthly_income = GivingTransaction.objects.filter(
        church=church,
        created_at__gte=timezone.now() - timedelta(days=30)
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Calculate expenses
    total_expenses = Expense.objects.filter(
        church=church
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    monthly_expenses = Expense.objects.filter(
        church=church,
        created_at__gte=timezone.now() - timedelta(days=30)
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    return Response({
        'totalIncome': total_income,
        'monthlyIncome': monthly_income,
        'totalExpenses': total_expenses,
        'monthlyExpenses': monthly_expenses,
        'netBalance': total_income - total_expenses,
        'church': {
            'id': church.id,
            'name': church.name,
            'code': church.code,
            'is_verified': church.is_verified,
            'is_active': church.is_active
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monthly_trend(request):
    """Get monthly income/expense trend."""
    user = request.user
    
    # Check if user has a church assigned
    if not user.church:
        return Response({
            'trend': [],
            'church': None,
            'message': 'No church assigned. Please join a church to view financial data.'
        }, status=200)
    
    church = user.church
    months = 12
    
    trend_data = []
    for i in range(months):
        month_start = timezone.now() - timedelta(days=30 * (months - i - 1))
        month_end = timezone.now() - timedelta(days=30 * (months - i - 2))
        
        income = GivingTransaction.objects.filter(
            church=church,
            created_at__range=[month_start, month_end]
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        expenses = Expense.objects.filter(
            church=church,
            created_at__range=[month_start, month_end]
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        trend_data.append({
            'month': month_start.strftime('%Y-%m'),
            'income': income,
            'expenses': expenses,
            'net': income - expenses
        })
    
    return Response({
        'trend': trend_data,
        'church': {
            'id': church.id,
            'name': church.name,
            'code': church.code,
            'is_verified': church.is_verified,
            'is_active': church.is_active
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def income_breakdown(request):
    """Get income breakdown by category."""
    user = request.user
    
    # Check if user has a church assigned
    if not user.church:
        return Response({
            'breakdown': [],
            'church': None,
            'message': 'No church assigned. Please join a church to view financial data.'
        }, status=200)
    
    church = user.church
    categories = GivingCategory.objects.filter(church=church)
    breakdown = []
    
    for category in categories:
        total = GivingTransaction.objects.filter(
            church=church,
            category=category
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        breakdown.append({
            'category': category.name,
            'amount': total,
            'percentage': (total / max(1, GivingTransaction.objects.filter(
                church=church
            ).aggregate(total=Sum('amount'))['total'] or 1)) * 100
        })
    
    return Response({
        'breakdown': breakdown,
        'church': {
            'id': church.id,
            'name': church.name,
            'code': church.code,
            'is_verified': church.is_verified,
            'is_active': church.is_active
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def expense_breakdown(request):
    """Get expense breakdown by category."""
    user = request.user
    
    # Check if user has a church assigned
    if not user.church:
        return Response({
            'breakdown': [],
            'church': None,
            'message': 'No church assigned. Please join a church to view financial data.'
        }, status=200)
    
    church = user.church
    
    # Group expenses by category
    expenses = Expense.objects.filter(church=church).values('category').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    total_expenses = Expense.objects.filter(church=church).aggregate(
        total=Sum('amount')
    )['total'] or 1
    
    breakdown = []
    for expense in expenses:
        breakdown.append({
            'category': expense['category'],
            'amount': expense['total'],
            'count': expense['count'],
            'percentage': (expense['total'] / total_expenses) * 100
        })
    
    return Response({
        'breakdown': breakdown,
        'church': {
            'id': church.id,
            'name': church.name,
            'code': church.code,
            'is_verified': church.is_verified,
            'is_active': church.is_active
        }
    })
