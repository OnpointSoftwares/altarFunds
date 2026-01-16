from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from giving.models import GivingTransaction, GivingCategory
from expenses.models import Expense


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def comprehensive_dashboard(request):
    """Get comprehensive dashboard data with church information."""
    user = request.user
    
    # Check if user has a church assigned
    if not user.church:
        return Response({
            'church': None,
            'message': 'No church assigned. Please join a church to view financial data.',
            'financial_summary': {
                'totalIncome': 0,
                'monthlyIncome': 0,
                'totalExpenses': 0,
                'monthlyExpenses': 0,
                'netBalance': 0
            },
            'monthly_trend': []
        }, status=200)
    
    church = user.church
    
    # Financial Summary
    total_income = GivingTransaction.objects.filter(
        church=church
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    monthly_income = GivingTransaction.objects.filter(
        church=church,
        created_at__gte=timezone.now() - timedelta(days=30)
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_expenses = Expense.objects.filter(
        church=church
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    monthly_expenses = Expense.objects.filter(
        church=church,
        created_at__gte=timezone.now() - timedelta(days=30)
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Monthly Trend (simplified for performance)
    months = 6  # Reduced for better performance
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
        'church': {
            'id': church.id,
            'name': church.name,
            'code': church.code,
            'is_verified': church.is_verified,
            'is_active': church.is_active
        },
        'financial_summary': {
            'totalIncome': total_income,
            'monthlyIncome': monthly_income,
            'totalExpenses': total_expenses,
            'monthlyExpenses': monthly_expenses,
            'netBalance': total_income - total_expenses
        },
        'monthly_trend': trend_data
    })
