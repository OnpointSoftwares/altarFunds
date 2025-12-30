from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GivingCategoryViewSet, 
    GivingTransactionViewSet, 
    RecurringGivingViewSet, 
    PledgeViewSet, 
    GivingCampaignViewSet
)

app_name = 'giving'

router = DefaultRouter()
router.register(r'categories', GivingCategoryViewSet)
router.register(r'transactions', GivingTransactionViewSet)
router.register(r'recurring', RecurringGivingViewSet)
router.register(r'pledges', PledgeViewSet)
router.register(r'campaigns', GivingCampaignViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
