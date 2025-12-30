from rest_framework import viewsets
from .models import GivingCategory, GivingTransaction, RecurringGiving, Pledge, GivingCampaign
from .serializers import (
    GivingCategorySerializer, 
    GivingTransactionSerializer, 
    RecurringGivingSerializer, 
    PledgeSerializer, 
    GivingCampaignSerializer
)

class GivingCategoryViewSet(viewsets.ModelViewSet):
    queryset = GivingCategory.objects.all()
    serializer_class = GivingCategorySerializer

class GivingTransactionViewSet(viewsets.ModelViewSet):
    queryset = GivingTransaction.objects.all()
    serializer_class = GivingTransactionSerializer

class RecurringGivingViewSet(viewsets.ModelViewSet):
    queryset = RecurringGiving.objects.all()
    serializer_class = RecurringGivingSerializer

class PledgeViewSet(viewsets.ModelViewSet):
    queryset = Pledge.objects.all()
    serializer_class = PledgeSerializer

class GivingCampaignViewSet(viewsets.ModelViewSet):
    queryset = GivingCampaign.objects.all()
    serializer_class = GivingCampaignSerializer
