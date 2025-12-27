from rest_framework import generics, status, views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta, date

from .models import (
    PaymentMethod, PaymentRequest, PaymentCallback, 
    PaymentReversal, PaymentBatch
)
from .serializers import (
    PaymentMethodSerializer, PaymentRequestSerializer, PaymentRequestCreateSerializer,
    PaymentCallbackSerializer, PaymentReversalSerializer, PaymentReversalCreateSerializer,
    PaymentBatchSerializer, MpesaCallbackSerializer, PaymentStatusSerializer,
    PaymentStatsSerializer
)
from common.permissions import (
    IsChurchAdmin, IsDenominationAdmin, IsSystemAdmin,
    CanManageChurchFinances, CanViewChurchFinances
)
from common.pagination import StandardResultsSetPagination
from common.services import AuditService
from .services import PaymentService, PaymentSchedulerService


class PaymentMethodListCreateView(generics.ListCreateAPIView):
    """List and create payment methods"""
    
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated, CanManageChurchFinances]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['method_type', 'is_active', 'is_default']
    
    def get_queryset(self):
        """Filter payment methods based on user role"""
        user = self.request.user
        
        if user.is_superuser:
            return PaymentMethod.objects.all()
        elif user.role == 'denomination_admin':
            return PaymentMethod.objects.filter(church__denomination=user.church.denomination)
        else:
            return PaymentMethod.objects.filter(church=user.church)
    
    def perform_create(self, serializer):
        """Create payment method with audit trail"""
        serializer.save(created_by=self.request.user)
        
        AuditService.log_user_action(
            user=self.request.user,
            action='PAYMENT_METHOD_CREATED',
            details={
                'method_name': serializer.validated_data['name'],
                'method_type': serializer.validated_data['method_type'],
                'church': serializer.validated_data['church'].name
            }
        )


class PaymentMethodDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete payment method"""
    
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated, CanManageChurchFinances]
    
    def get_queryset(self):
        """Filter payment methods based on user role"""
        user = self.request.user
        
        if user.is_superuser:
            return PaymentMethod.objects.all()
        elif user.role == 'denomination_admin':
            return PaymentMethod.objects.filter(church__denomination=user.church.denomination)
        else:
            return PaymentMethod.objects.filter(church=user.church)
    
    def perform_update(self, serializer):
        """Update payment method with audit trail"""
        old_instance = self.get_object()
        serializer.save(updated_by=self.request.user)
        
        AuditService.log_user_action(
            user=self.request.user,
            action='PAYMENT_METHOD_UPDATED',
            details={
                'method_name': old_instance.name,
                'changes': serializer.validated_data
            }
        )
    
    def perform_destroy(self, instance):
        """Delete payment method with audit trail"""
        AuditService.log_user_action(
            user=self.request.user,
            action='PAYMENT_METHOD_DELETED',
            details={
                'method_name': instance.name,
                'method_type': instance.method_type
            }
        )
        instance.delete()


class PaymentRequestListCreateView(generics.ListCreateAPIView):
    """List and create payment requests"""
    
    permission_classes = [IsAuthenticated, CanViewChurchFinances]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'request_type', 'payment_method']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on request method"""
        if self.request.method == 'POST':
            return PaymentRequestCreateSerializer
        return PaymentRequestSerializer
    
    def get_queryset(self):
        """Filter payment requests based on user role"""
        user = self.request.user
        
        if user.is_superuser:
            return PaymentRequest.objects.all()
        elif user.role == 'denomination_admin':
            return PaymentRequest.objects.filter(church__denomination=user.church.denomination)
        else:
            return PaymentRequest.objects.filter(church=user.church)
    
    def perform_create(self, serializer):
        """Create payment request with audit trail"""
        payment_request = serializer.save()
        
        AuditService.log_user_action(
            user=self.request.user,
            action='PAYMENT_REQUEST_CREATED',
            details={
                'request_id': str(payment_request.request_id),
                'amount': float(payment_request.amount),
                'payment_method': payment_request.giving_transaction.payment_method
            }
        )


class PaymentRequestDetailView(generics.RetrieveAPIView):
    """Retrieve payment request details"""
    
    serializer_class = PaymentRequestSerializer
    permission_classes = [IsAuthenticated, CanViewChurchFinances]
    
    def get_queryset(self):
        """Filter payment requests based on user role"""
        user = self.request.user
        
        if user.is_superuser:
            return PaymentRequest.objects.all()
        elif user.role == 'denomination_admin':
            return PaymentRequest.objects.filter(church__denomination=user.church.denomination)
        else:
            return PaymentRequest.objects.filter(church=user.church)


class PaymentRequestRetryView(views.APIView):
    """Retry failed payment request"""
    
    permission_classes = [IsAuthenticated, CanManageChurchFinances]
    
    def post(self, request, request_id):
        """Retry payment request"""
        try:
            payment_request = self._get_payment_request(request_id)
            
            if not payment_request.can_retry():
                return Response(
                    {'error': 'Payment request cannot be retried'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Retry payment
            updated_request = PaymentService.retry_payment(payment_request)
            
            return Response({
                'message': 'Payment retry initiated',
                'payment_request': PaymentRequestSerializer(updated_request).data
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _get_payment_request(self, request_id):
        """Get payment request based on user role"""
        user = self.request.user
        
        if user.is_superuser:
            return PaymentRequest.objects.get(request_id=request_id)
        elif user.role == 'denomination_admin':
            return PaymentRequest.objects.get(
                request_id=request_id,
                church__denomination=user.church.denomination
            )
        else:
            return PaymentRequest.objects.get(
                request_id=request_id,
                church=user.church
            )


class PaymentCallbackListView(generics.ListAPIView):
    """List payment callbacks"""
    
    serializer_class = PaymentCallbackSerializer
    permission_classes = [IsAuthenticated, CanViewChurchFinances]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['provider', 'callback_type', 'status', 'is_valid']
    
    def get_queryset(self):
        """Filter callbacks based on user role"""
        user = self.request.user
        
        if user.is_superuser:
            return PaymentCallback.objects.all()
        elif user.role == 'denomination_admin':
            return PaymentCallback.objects.filter(
                payment_request__church__denomination=user.church.denomination
            )
        else:
            return PaymentCallback.objects.filter(
                payment_request__church=user.church
            )


class PaymentReversalListCreateView(generics.ListCreateAPIView):
    """List and create payment reversals"""
    
    permission_classes = [IsAuthenticated, CanManageChurchFinances]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['reversal_type', 'status']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on request method"""
        if self.request.method == 'POST':
            return PaymentReversalCreateSerializer
        return PaymentReversalSerializer
    
    def get_queryset(self):
        """Filter reversals based on user role"""
        user = self.request.user
        
        if user.is_superuser:
            return PaymentReversal.objects.all()
        elif user.role == 'denomination_admin':
            return PaymentReversal.objects.filter(
                original_transaction__church__denomination=user.church.denomination
            )
        else:
            return PaymentReversal.objects.filter(
                original_transaction__church=user.church
            )


class PaymentReversalDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve and update payment reversal"""
    
    serializer_class = PaymentReversalSerializer
    permission_classes = [IsAuthenticated, CanManageChurchFinances]
    
    def get_queryset(self):
        """Filter reversals based on user role"""
        user = self.request.user
        
        if user.is_superuser:
            return PaymentReversal.objects.all()
        elif user.role == 'denomination_admin':
            return PaymentReversal.objects.filter(
                original_transaction__church__denomination=user.church.denomination
            )
        else:
            return PaymentReversal.objects.filter(
                original_transaction__church=user.church
            )
    
    def perform_update(self, serializer):
        """Update reversal with audit trail"""
        serializer.save(updated_by=self.request.user)
        
        AuditService.log_user_action(
            user=self.request.user,
            action='PAYMENT_REVERSAL_UPDATED',
            details={
                'reversal_id': str(self.get_object().reversal_id),
                'changes': serializer.validated_data
            }
        )


class PaymentBatchListCreateView(generics.ListCreateAPIView):
    """List and create payment batches"""
    
    serializer_class = PaymentBatchSerializer
    permission_classes = [IsAuthenticated, CanManageChurchFinances]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['batch_type', 'status']
    
    def get_queryset(self):
        """Filter batches based on user role"""
        user = self.request.user
        
        if user.is_superuser:
            return PaymentBatch.objects.all()
        elif user.role == 'denomination_admin':
            return PaymentBatch.objects.filter(church__denomination=user.church.denomination)
        else:
            return PaymentBatch.objects.filter(church=user.church)
    
    def perform_create(self, serializer):
        """Create batch with audit trail"""
        serializer.save(created_by=self.request.user)
        
        AuditService.log_user_action(
            user=self.request.user,
            action='PAYMENT_BATCH_CREATED',
            details={
                'batch_id': str(serializer.instance.batch_id),
                'batch_type': serializer.validated_data['batch_type'],
                'title': serializer.validated_data['title']
            }
        )


class PaymentBatchDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve and update payment batch"""
    
    serializer_class = PaymentBatchSerializer
    permission_classes = [IsAuthenticated, CanManageChurchFinances]
    
    def get_queryset(self):
        """Filter batches based on user role"""
        user = self.request.user
        
        if user.is_superuser:
            return PaymentBatch.objects.all()
        elif user.role == 'denomination_admin':
            return PaymentBatch.objects.filter(church__denomination=user.church.denomination)
        else:
            return PaymentBatch.objects.filter(church=user.church)


# API Views for External Integrations


@api_view(['POST'])
@permission_classes([])
def mpesa_callback(request):
    """Handle M-Pesa payment callback"""
    try:
        # Process callback
        callback = PaymentService.process_callback(request.data, 'mpesa')
        
        return Response({
            'ResultCode': 0,
            'ResultDesc': 'Callback processed successfully'
        })
        
    except Exception as e:
        logger.error(f"M-Pesa callback processing failed: {e}")
        return Response({
            'ResultCode': 1,
            'ResultDesc': 'Callback processing failed'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageChurchFinances])
def payment_status_check(request, request_id):
    """Check payment request status"""
    try:
        payment_request = PaymentRequest.objects.get(request_id=request_id)
        
        # Check user permissions
        user = request.user
        if not (user.is_superuser or 
                (user.role == 'denomination_admin' and payment_request.church.denomination == user.church.denomination) or
                payment_request.church == user.church):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check transaction status if still processing
        if payment_request.status == 'processing':
            from .services import MpesaPaymentService
            MpesaPaymentService.check_transaction_status(payment_request)
        
        return Response(PaymentStatusSerializer({
            'status': payment_request.status,
            'message': payment_request.response_message,
            'transaction_id': str(payment_request.giving_transaction.transaction_id),
            'amount': payment_request.amount,
            'payment_method': payment_request.giving_transaction.payment_method,
            'created_at': payment_request.created_at,
            'processed_at': payment_request.processing_completed_at,
            'callback_data': payment_request.callback_data
        }).data)
        
    except PaymentRequest.DoesNotExist:
        return Response(
            {'error': 'Payment request not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, CanViewChurchFinances])
def payment_statistics(request):
    """Get payment statistics"""
    try:
        user = request.user
        
        # Filter based on user role
        if user.is_superuser:
            payment_requests = PaymentRequest.objects.all()
        elif user.role == 'denomination_admin':
            payment_requests = PaymentRequest.objects.filter(church__denomination=user.church.denomination)
        else:
            payment_requests = PaymentRequest.objects.filter(church=user.church)
        
        # Calculate statistics
        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        
        # Overall stats
        total_transactions = payment_requests.count()
        total_amount = payment_requests.aggregate(total=Sum('amount'))['total'] or 0
        
        successful_transactions = payment_requests.filter(status='completed').count()
        failed_transactions = payment_requests.filter(status='failed').count()
        pending_transactions = payment_requests.filter(status='pending').count()
        
        success_rate = (successful_transactions / total_transactions * 100) if total_transactions > 0 else 0
        average_amount = total_amount / total_transactions if total_transactions > 0 else 0
        
        # Payment method stats
        payment_method_stats = []
        for method_type, method_name in PaymentRequest.REQUEST_TYPE_CHOICES:
            method_requests = payment_requests.filter(request_type=method_type)
            method_count = method_requests.count()
            method_amount = method_requests.aggregate(total=Sum('amount'))['total'] or 0
            method_success = method_requests.filter(status='completed').count()
            method_success_rate = (method_success / method_count * 100) if method_count > 0 else 0
            
            payment_method_stats.append({
                'method_type': method_type,
                'method_name': method_name,
                'is_active': True,
                'is_default': method_type == 'stk_push',
                'total_transactions': method_count,
                'total_amount': method_amount,
                'success_rate': method_success_rate,
                'average_processing_time': 0  # Would calculate from timestamps
            })
        
        # Daily stats for last 30 days
        daily_stats = []
        for i in range(30):
            day = now - timedelta(days=i)
            day_requests = payment_requests.filter(created_at__date=day.date())
            daily_stats.append({
                'date': day.date().isoformat(),
                'transactions': day_requests.count(),
                'amount': day_requests.aggregate(total=Sum('amount'))['total'] or 0,
                'successful': day_requests.filter(status='completed').count()
            })
        
        # Monthly stats for last 12 months
        monthly_stats = []
        for i in range(12):
            month = now - timedelta(days=30*i)
            month_requests = payment_requests.filter(
                created_at__year=month.year,
                created_at__month=month.month
            )
            monthly_stats.append({
                'month': month.strftime('%Y-%m'),
                'transactions': month_requests.count(),
                'amount': month_requests.aggregate(total=Sum('amount'))['total'] or 0,
                'successful': month_requests.filter(status='completed').count()
            })
        
        return Response(PaymentStatsSerializer({
            'total_transactions': total_transactions,
            'total_amount': total_amount,
            'successful_transactions': successful_transactions,
            'failed_transactions': failed_transactions,
            'pending_transactions': pending_transactions,
            'success_rate': success_rate,
            'average_amount': average_amount,
            'payment_methods': payment_method_stats,
            'daily_stats': daily_stats,
            'monthly_stats': monthly_stats
        }).data)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageChurchFinances])
def trigger_payment_scheduler(request):
    """Manually trigger payment scheduler"""
    try:
        # Process pending payments
        PaymentSchedulerService.process_pending_payments()
        
        # Check transaction status
        PaymentSchedulerService.check_transaction_status()
        
        # Process payment batches
        PaymentSchedulerService.process_payment_batches()
        
        # Log manual trigger
        AuditService.log_user_action(
            user=request.user,
            action='PAYMENT_SCHEDULER_TRIGGERED',
            details={'triggered_by': 'manual'}
        )
        
        return Response({
            'message': 'Payment scheduler triggered successfully',
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
