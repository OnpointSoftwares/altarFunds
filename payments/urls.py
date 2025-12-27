from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment Methods
    path('methods/', views.PaymentMethodListCreateView.as_view(), name='payment-method-list-create'),
    path('methods/<int:pk>/', views.PaymentMethodDetailView.as_view(), name='payment-method-detail'),
    
    # Payment Requests
    path('requests/', views.PaymentRequestListCreateView.as_view(), name='payment-request-list-create'),
    path('requests/<uuid:request_id>/', views.PaymentRequestDetailView.as_view(), name='payment-request-detail'),
    path('requests/<uuid:request_id>/retry/', views.PaymentRequestRetryView.as_view(), name='payment-request-retry'),
    path('requests/<uuid:request_id>/status/', views.payment_status_check, name='payment-status-check'),
    
    # Payment Callbacks
    path('callbacks/', views.PaymentCallbackListView.as_view(), name='payment-callback-list'),
    path('callbacks/mpesa/', views.mpesa_callback, name='mpesa-callback'),
    
    # Payment Reversals
    path('reversals/', views.PaymentReversalListCreateView.as_view(), name='payment-reversal-list-create'),
    path('reversals/<int:pk>/', views.PaymentReversalDetailView.as_view(), name='payment-reversal-detail'),
    
    # Payment Batches
    path('batches/', views.PaymentBatchListCreateView.as_view(), name='payment-batch-list-create'),
    path('batches/<int:pk>/', views.PaymentBatchDetailView.as_view(), name='payment-batch-detail'),
    
    # Payment Statistics
    path('statistics/', views.payment_statistics, name='payment-statistics'),
    
    # Payment Scheduler
    path('scheduler/trigger/', views.trigger_payment_scheduler, name='payment-scheduler-trigger'),
]
