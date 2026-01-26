from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GivingCategoryViewSet, 
    GivingTransactionViewSet, 
    RecurringGivingViewSet, 
    PledgeViewSet, 
    GivingCampaignViewSet,
    church_givings,
    giving_categories
)

app_name = 'giving'

router = DefaultRouter()
# Register with different prefixes to avoid conflicts
router.register(r'categories-list', GivingCategoryViewSet)
router.register(r'transactions', GivingTransactionViewSet)
router.register(r'recurring', RecurringGivingViewSet)
router.register(r'pledges', PledgeViewSet)
router.register(r'campaigns', GivingCampaignViewSet)

urlpatterns = [
    path('categories/', giving_categories, name='giving_categories'),
    path('', include(router.urls)),
    path('church/<int:church_id>/', church_givings, name='church_givings'),
]
