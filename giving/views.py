from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
from decimal import Decimal

from .models import GivingCategory, GivingTransaction, RecurringGiving, Pledge, GivingCampaign
from .serializers import (
    GivingCategorySerializer, 
    GivingTransactionSerializer, 
    RecurringGivingSerializer, 
    PledgeSerializer, 
    GivingCampaignSerializer
)
from common.permissions import IsMember, IsChurchAdmin, IsSystemAdmin, IsOwnerOrChurchAdmin
from payments.models import Payment
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def giving_categories(request):
    """Get giving categories for user's church"""
    try:
        user = request.user
        logger.info(f"Fetching categories for user: {user.email}, role: {user.role}, church: {user.church}")
        
        # Check if user has a church
        if not user.church:
            logger.warning(f"User {user.email} has no church assigned")
            return Response({
                'success': False,
                'message': 'User is not associated with any church',
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get categories for user's church
        if user.role == 'system_admin':
            categories = GivingCategory.objects.filter(is_active=True)
            logger.info(f"System admin fetching all active categories: {categories.count()} found")
        else:
            categories = GivingCategory.objects.filter(church=user.church, is_active=True)
            logger.info(f"User {user.email} fetching categories for church {user.church.name}: {categories.count()} found")
        
        serializer = GivingCategorySerializer(categories, many=True)
        
        response_data = {
            'success': True,
            'message': f'Found {len(categories)} categories',
            'data': serializer.data
        }
        logger.info(f"Returning categories response: {response_data}")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching giving categories: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to fetch categories',
            'data': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_giving_transaction(request):
    """Create a giving transaction from mobile app"""
    try:
        user = request.user
        logger.info(f"Creating giving transaction for user: {user.email}")
        
        # Check if user has a church
        if not user.church:
            logger.warning(f"User {user.email} has no church assigned")
            return Response({
                'success': False,
                'message': 'User is not associated with any church',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the member profile for the user
        try:
            member = user.member_profile
        except:
            logger.warning(f"User {user.email} has no member profile")
            return Response({
                'success': False,
                'message': 'User member profile not found',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get request data
        data = request.data
        
        # Validate required fields
        if 'category' not in data or 'amount' not in data:
            return Response({
                'success': False,
                'message': 'Category and amount are required',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get category
        try:
            category = GivingCategory.objects.get(
                id=data['category'], 
                church=user.church, 
                is_active=True
            )
        except GivingCategory.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid category',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create transaction
        transaction = GivingTransaction.objects.create(
            member=member,
            church=user.church,
            category=category,
            amount=data['amount'],
            payment_method=data.get('payment_method', 'mpesa'),
            transaction_type='one_time',
            status='pending',
            transaction_date=timezone.now().date(),
            created_by=user,
            updated_by=user,
            note=data.get('note', ''),
            is_anonymous=data.get('is_anonymous', False)
        )
        
        logger.info(f"Created transaction {transaction.transaction_id} for user {user.email}")
        
        # Serialize and return
        serializer = GivingTransactionSerializer(transaction)
        
        return Response({
            'success': True,
            'message': 'Transaction created successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating giving transaction: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to create transaction',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GivingCategoryViewSet(viewsets.ModelViewSet):
    queryset = GivingCategory.objects.all()
    serializer_class = GivingCategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter active categories for user's church"""
        user = self.request.user
        if user.role == 'system_admin':
            return GivingCategory.objects.filter(is_active=True)
        else:
            return GivingCategory.objects.filter(church=user.church, is_active=True)


class GivingTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = GivingTransactionSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrChurchAdmin]
    queryset = GivingTransaction.objects.all()
    
    def get_queryset(self):
        """Filter giving transactions based on user role"""
        user = self.request.user
        
        # System admins see all transactions
        if user.role == 'system_admin':
            return GivingTransaction.objects.all()
        
        # Church admins see their church's transactions
        if user.role in ['pastor', 'treasurer', 'auditor']:
            return GivingTransaction.objects.filter(church=user.church)
        
        # Members see only their own transactions
        return GivingTransaction.objects.filter(member__user=user)
    
    def perform_create(self, serializer):
        """Create giving transaction and link with payment"""
        serializer.save(member=self.request.user.member_profile)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def history(self, request):
        """Get user's giving history"""
        try:
            user = request.user
            
            # Get query parameters
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            giving_type = request.query_params.get('giving_type')
            church_id = request.query_params.get('church_id')
            
            # Base query
            givings = GivingTransaction.objects.filter(member__user=user)
            
            # Apply filters
            if start_date:
                givings = givings.filter(transaction_date__gte=start_date)
            if end_date:
                givings = givings.filter(transaction_date__lte=end_date)
            if giving_type:
                givings = givings.filter(category__name=giving_type)
            if church_id:
                givings = givings.filter(church_id=church_id)
            
            # Order by date
            givings = givings.order_by('-transaction_date')
            
            # Calculate totals
            total_given = givings.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            # Serialize data
            serializer = self.get_serializer(givings, many=True)
            
            return Response({
                'success': True,
                'data': {
                    'total_given': float(total_given),
                    'transaction_count': givings.count(),
                    'givings': serializer.data
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching giving history: {str(e)}")
            return Response({
                'success': False,
                'message': 'Failed to fetch giving history'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def summary(self, request):
        """Get giving summary statistics"""
        try:
            user = request.user
            
            # Get givings for the current year
            current_year = timezone.now().year
            givings = GivingTransaction.objects.filter(
                member__user=user,
                transaction_date__year=current_year,
                status='completed'
            )
            
            # Calculate totals by category
            by_category = givings.values('category__name').annotate(
                total=Sum('amount'),
                count=Count('id')
            )
            
            # Calculate monthly totals
            monthly_totals = []
            for month in range(1, 13):
                month_givings = givings.filter(transaction_date__month=month)
                total = month_givings.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
                monthly_totals.append({
                    'month': month,
                    'total': float(total),
                    'count': month_givings.count()
                })
            
            # Overall totals
            total_given = givings.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            return Response({
                'success': True,
                'data': {
                    'year': current_year,
                    'total_given': float(total_given),
                    'transaction_count': givings.count(),
                    'by_category': list(by_category),
                    'monthly_totals': monthly_totals
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching giving summary: {str(e)}")
            return Response({
                'success': False,
                'message': 'Failed to fetch giving summary'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RecurringGivingViewSet(viewsets.ModelViewSet):
    serializer_class = RecurringGivingSerializer
    permission_classes = [IsAuthenticated]
    queryset = RecurringGiving.objects.all()
    
    def get_queryset(self):
        """Filter recurring givings by user"""
        user = self.request.user
        
        if user.role == 'system_admin':
            return RecurringGiving.objects.all()
        
        return RecurringGiving.objects.filter(member__user=user)
    
    def perform_create(self, serializer):
        """Create recurring giving"""
        serializer.save(member=self.request.user.member_profile)


class PledgeViewSet(viewsets.ModelViewSet):
    serializer_class = PledgeSerializer
    permission_classes = [IsAuthenticated]
    queryset = Pledge.objects.all()
    
    def get_queryset(self):
        """Filter pledges by user"""
        user = self.request.user
        
        if user.role == 'system_admin':
            return Pledge.objects.all()
        
        if user.role in ['pastor', 'treasurer', 'auditor']:
            return Pledge.objects.filter(church=user.church)
        
        return Pledge.objects.filter(member__user=user)
    
    def perform_create(self, serializer):
        """Create pledge"""
        serializer.save(member=self.request.user.member_profile)


class GivingCampaignViewSet(viewsets.ModelViewSet):
    serializer_class = GivingCampaignSerializer
    permission_classes = [IsAuthenticated]
    queryset = GivingCampaign.objects.all()
    
    def get_queryset(self):
        """Filter campaigns by church"""
        user = self.request.user
        
        if user.role == 'system_admin':
            return GivingCampaign.objects.all()
        
        if user.role in ['pastor', 'treasurer', 'auditor']:
            return GivingCampaign.objects.filter(church=user.church)
        
        # Members see active campaigns from their church
        return GivingCampaign.objects.filter(
            church=user.church,
            is_active=True
        )


@api_view(['GET'])
@permission_classes([IsChurchAdmin])
def church_givings(request, church_id):
    """Get givings for a specific church (Church Admin only)"""
    try:
        user = request.user
        
        # Verify user has access to this church
        if user.role != 'system_admin' and user.church_id != church_id:
            return Response({
                'success': False,
                'message': 'You can only view givings for your own church'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get query parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        giving_type = request.query_params.get('giving_type')
        
        # Base query
        givings = GivingTransaction.objects.filter(
            church_id=church_id,
            status='completed'
        )
        
        # Apply filters
        if start_date:
            givings = givings.filter(transaction_date__gte=start_date)
        if end_date:
            givings = givings.filter(transaction_date__lte=end_date)
        if giving_type:
            givings = givings.filter(category__name=giving_type)
        
        # Calculate totals
        total_received = givings.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Group by category
        by_category = givings.values('category__name').annotate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        # Recent givings
        recent_givings = givings.order_by('-transaction_date')[:10]
        
        giving_data = []
        for giving in recent_givings:
            giving_data.append({
                'id': giving.id,
                'amount': float(giving.amount),
                'member': giving.member.user.get_full_name() if not giving.is_anonymous else 'Anonymous',
                'category': giving.category.name,
                'date': giving.transaction_date,
                'payment_method': giving.payment_method,
                'status': giving.status
            })
        
        return Response({
            'success': True,
            'data': {
                'total_received': float(total_received),
                'transaction_count': givings.count(),
                'by_category': list(by_category),
                'recent_givings': giving_data
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching church givings: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to fetch church givings'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
