from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from giving.models import GivingTransaction
from expenses.models import Expense
from budgets.models import Budget
from churches.models import Church
from accounts.models import Member
from common.permissions import IsChurchAdmin, IsSystemAdmin
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def financial_summary(request):
    """Get financial summary for dashboard"""
    try:
        user = request.user
        
        # Get query parameters
        church_id = request.query_params.get('church_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Determine church filter based on role
        if user.role == 'system_admin':
            # System admin can view any church or all churches
            church_filter = Q(church_id=church_id) if church_id else Q()
        elif user.role in ['pastor', 'treasurer', 'auditor']:
            # Church admin can only view their church
            church_filter = Q(church=user.church)
        else:
            # Members view their own data
            church_filter = Q(church=user.church)
        
        # Date filter
        date_filter = Q()
        if start_date:
            date_filter &= Q(transaction_date__gte=start_date)
        if end_date:
            date_filter &= Q(transaction_date__lte=end_date)
        else:
            # Default to current month
            start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            date_filter &= Q(transaction_date__gte=start_of_month)
        
        # Calculate income (givings)
        givings = GivingTransaction.objects.filter(
            church_filter,
            date_filter,
            status='completed'
        )
        total_income = givings.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Calculate expenses
        expenses = Expense.objects.filter(
            date_filter,
            status='approved'
        )
        
        # Apply church filter for expenses through user's church
        if user.role != 'system_admin':
            expenses = expenses.filter(user__church=user.church)
        total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Calculate net income
        net_income = total_income - total_expenses
        
        # Calculate budget utilization
        budgets = Budget.objects.all()
        
        # Apply church filter for budgets through user's church
        if user.role != 'system_admin':
            budgets = budgets.filter(user__church=user.church)
        total_budget = budgets.aggregate(total=Sum('allocated_amount'))['total'] or Decimal('0.00')
        budget_spent = budgets.aggregate(total=Sum('spent_amount'))['total'] or Decimal('0.00')
        budget_utilization = (float(budget_spent) / float(total_budget) * 100) if total_budget > 0 else 0
        
        # Income by category
        income_by_category = givings.values('category__name').annotate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        # Expenses by category
        expenses_by_category = expenses.values('category__name').annotate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        return Response({
            'success': True,
            'data': {
                'total_income': float(total_income),
                'total_expenses': float(total_expenses),
                'net_income': float(net_income),
                'total_budget': float(total_budget),
                'budget_spent': float(budget_spent),
                'budget_utilization': round(budget_utilization, 2),
                'income_by_category': list(income_by_category),
                'expenses_by_category': list(expenses_by_category),
                'period': {
                    'start_date': start_date or start_of_month.isoformat(),
                    'end_date': end_date or timezone.now().isoformat()
                }
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching financial summary: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to fetch financial summary'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def giving_trends(request):
    """Get giving trends analysis"""
    try:
        user = request.user
        
        # Get query parameters
        church_id = request.query_params.get('church_id')
        period = request.query_params.get('period', 'monthly')  # monthly, quarterly, yearly
        
        # Determine church filter
        if user.role == 'system_admin':
            church_filter = Q(church_id=church_id) if church_id else Q()
        elif user.role in ['pastor', 'treasurer', 'auditor']:
            church_filter = Q(church=user.church)
        else:
            church_filter = Q(member__user=user)
        
        # Get current year data
        current_year = timezone.now().year
        givings = GivingTransaction.objects.filter(
            church_filter,
            transaction_date__year=current_year,
            status='completed'
        )
        
        # Calculate trends based on period
        trends = []
        if period == 'monthly':
            for month in range(1, 13):
                month_givings = givings.filter(transaction_date__month=month)
                total = month_givings.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
                trends.append({
                    'period': f"{current_year}-{month:02d}",
                    'total': float(total),
                    'count': month_givings.count()
                })
        elif period == 'quarterly':
            for quarter in range(1, 5):
                start_month = (quarter - 1) * 3 + 1
                end_month = quarter * 3
                quarter_givings = givings.filter(
                    transaction_date__month__gte=start_month,
                    transaction_date__month__lte=end_month
                )
                total = quarter_givings.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
                trends.append({
                    'period': f"{current_year}-Q{quarter}",
                    'total': float(total),
                    'count': quarter_givings.count()
                })
        
        # Giving by type
        by_type = givings.values('category__name').annotate(
            total=Sum('amount'),
            count=Count('id'),
            avg=Avg('amount')
        )
        
        # Top givers (for church admins only)
        top_givers = []
        if user.role in ['pastor', 'treasurer', 'auditor', 'system_admin']:
            top_givers_data = givings.values('member__user__first_name', 'member__user__last_name').annotate(
                total=Sum('amount'),
                count=Count('id')
            ).order_by('-total')[:10]
            
            for giver in top_givers_data:
                top_givers.append({
                    'name': f"{giver['member__user__first_name']} {giver['member__user__last_name']}",
                    'total': float(giver['total']),
                    'count': giver['count']
                })
        
        return Response({
            'success': True,
            'data': {
                'trends': trends,
                'by_type': list(by_type),
                'top_givers': top_givers,
                'period': period,
                'year': current_year
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching giving trends: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to fetch giving trends'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsChurchAdmin])
def member_statistics(request):
    """Get member statistics (Church Admin only)"""
    try:
        user = request.user
        
        # Get query parameters
        church_id = request.query_params.get('church_id')
        
        # Determine church filter
        if user.role == 'system_admin':
            if church_id:
                church = Church.objects.get(id=church_id)
            else:
                # System-wide statistics
                total_members = Member.objects.count()
                active_members = Member.objects.filter(membership_status='member').count()
                new_members_this_month = Member.objects.filter(
                    membership_date__month=timezone.now().month,
                    membership_date__year=timezone.now().year
                ).count()
                tithe_payers = Member.objects.filter(is_tithe_payer=True).count()
                
                return Response({
                    'success': True,
                    'data': {
                        'total_members': total_members,
                        'active_members': active_members,
                        'new_members_this_month': new_members_this_month,
                        'tithe_payers': tithe_payers,
                        'tithe_payer_percentage': round((tithe_payers / total_members * 100) if total_members > 0 else 0, 2)
                    }
                }, status=status.HTTP_200_OK)
        else:
            church = user.church
        
        # Get church members
        members = Member.objects.filter(church=church)
        total_members = members.count()
        
        # Active members
        active_members = members.filter(membership_status='member').count()
        
        # New members this month
        new_members_this_month = members.filter(
            membership_date__month=timezone.now().month,
            membership_date__year=timezone.now().year
        ).count()
        
        # Tithe payers
        tithe_payers = members.filter(is_tithe_payer=True).count()
        
        # Members by status
        by_status = members.values('membership_status').annotate(count=Count('id'))
        
        # Growth trend (last 12 months)
        growth_trend = []
        for i in range(11, -1, -1):
            date = timezone.now() - timedelta(days=i*30)
            count = members.filter(membership_date__lte=date).count()
            growth_trend.append({
                'month': date.strftime('%Y-%m'),
                'total_members': count
            })
        
        return Response({
            'success': True,
            'data': {
                'church': {
                    'id': church.id,
                    'name': church.name
                },
                'total_members': total_members,
                'active_members': active_members,
                'new_members_this_month': new_members_this_month,
                'tithe_payers': tithe_payers,
                'tithe_payer_percentage': round((tithe_payers / total_members * 100) if total_members > 0 else 0, 2),
                'by_status': list(by_status),
                'growth_trend': growth_trend
            }
        }, status=status.HTTP_200_OK)
        
    except Church.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Church not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching member statistics: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to fetch member statistics'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsChurchAdmin])
def church_performance(request):
    """Get church performance metrics (Church Admin only)"""
    try:
        user = request.user
        
        # Get query parameters
        church_id = request.query_params.get('church_id')
        
        # Determine church
        if user.role == 'system_admin' and church_id:
            church = Church.objects.get(id=church_id)
        else:
            church = user.church
        
        # Get current month and year
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        # This month's givings
        this_month_givings = GivingTransaction.objects.filter(
            church=church,
            transaction_date__month=current_month,
            transaction_date__year=current_year,
            status='completed'
        )
        this_month_total = this_month_givings.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Last month's givings
        last_month = current_month - 1 if current_month > 1 else 12
        last_month_year = current_year if current_month > 1 else current_year - 1
        last_month_givings = GivingTransaction.objects.filter(
            church=church,
            transaction_date__month=last_month,
            transaction_date__year=last_month_year,
            status='completed'
        )
        last_month_total = last_month_givings.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Calculate growth
        growth_percentage = 0
        if last_month_total > 0:
            growth_percentage = ((this_month_total - last_month_total) / last_month_total * 100)
        
        # Average giving per member
        total_members = Member.objects.filter(church=church).count()
        avg_giving_per_member = (this_month_total / total_members) if total_members > 0 else Decimal('0.00')
        
        # Budget performance
        budgets = Budget.objects.filter(church=church, isActive=True)
        total_budget = budgets.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        budget_spent = budgets.aggregate(total=Sum('spent'))['total'] or Decimal('0.00')
        budget_remaining = total_budget - budget_spent
        
        # Expenses this month
        this_month_expenses = Expense.objects.filter(
            church=church,
            expense_date__month=current_month,
            expense_date__year=current_year,
            status='approved'
        )
        expenses_total = this_month_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        return Response({
            'success': True,
            'data': {
                'church': {
                    'id': church.id,
                    'name': church.name
                },
                'givings': {
                    'this_month': float(this_month_total),
                    'last_month': float(last_month_total),
                    'growth_percentage': round(float(growth_percentage), 2),
                    'avg_per_member': float(avg_giving_per_member)
                },
                'budget': {
                    'total': float(total_budget),
                    'spent': float(budget_spent),
                    'remaining': float(budget_remaining),
                    'utilization_percentage': round((float(budget_spent) / float(total_budget) * 100) if total_budget > 0 else 0, 2)
                },
                'expenses': {
                    'this_month': float(expenses_total)
                },
                'members': {
                    'total': total_members
                }
            }
        }, status=status.HTTP_200_OK)
        
    except Church.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Church not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching church performance: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to fetch church performance metrics'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsSystemAdmin])
def system_overview(request):
    """Get system-wide overview (Super Admin only)"""
    try:
        # Total churches
        total_churches = Church.objects.count()
        active_churches = Church.objects.filter(status='verified', is_active=True).count()
        pending_churches = Church.objects.filter(status='pending').count()
        
        # Total members
        total_members = Member.objects.count()
        
        # Total givings (this month)
        current_month = timezone.now().month
        current_year = timezone.now().year
        this_month_givings = GivingTransaction.objects.filter(
            transaction_date__month=current_month,
            transaction_date__year=current_year,
            status='completed'
        )
        total_givings = this_month_givings.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Total expenses (this month)
        this_month_expenses = Expense.objects.filter(
            expense_date__month=current_month,
            expense_date__year=current_year,
            status='approved'
        )
        total_expenses = this_month_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Top performing churches
        top_churches = GivingTransaction.objects.filter(
            transaction_date__month=current_month,
            transaction_date__year=current_year,
            status='completed'
        ).values('church__name').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')[:10]
        
        # Recent activities
        recent_givings = GivingTransaction.objects.filter(
            status='completed'
        ).order_by('-transaction_date')[:5]
        
        recent_activities = []
        for giving in recent_givings:
            recent_activities.append({
                'type': 'giving',
                'church': giving.church.name,
                'amount': float(giving.amount),
                'date': giving.transaction_date
            })
        
        return Response({
            'success': True,
            'data': {
                'churches': {
                    'total': total_churches,
                    'active': active_churches,
                    'pending': pending_churches
                },
                'members': {
                    'total': total_members
                },
                'financials': {
                    'total_givings_this_month': float(total_givings),
                    'total_expenses_this_month': float(total_expenses),
                    'net_income': float(total_givings - total_expenses)
                },
                'top_churches': list(top_churches),
                'recent_activities': recent_activities
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching system overview: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to fetch system overview'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
