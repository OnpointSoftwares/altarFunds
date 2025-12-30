from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentRequestViewSet, PaymentViewSet, TransactionViewSet

app_name = 'payments'

router = DefaultRouter()
router.register(r'requests', PaymentRequestViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'transactions', TransactionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
