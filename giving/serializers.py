from rest_framework import serializers
from .models import GivingCategory, GivingTransaction, RecurringGiving, Pledge, GivingCampaign

class GivingCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GivingCategory
        fields = '__all__'

class GivingTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GivingTransaction
        fields = '__all__'

class RecurringGivingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurringGiving
        fields = '__all__'

class PledgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pledge
        fields = '__all__'

class GivingCampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = GivingCampaign
        fields = '__all__'
