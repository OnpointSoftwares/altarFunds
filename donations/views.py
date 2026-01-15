from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from giving.models import GivingTransaction, GivingCategory
from accounts.models import User
from rest_framework import serializers


class DonationSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = GivingTransaction
        fields = '__all__'


class DonationListCreateView(generics.ListCreateAPIView):
    """List and create donations"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DonationSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = GivingTransaction.objects.filter(member__user=user)
        
        # Filter by parameters
        category = self.request.query_params.get('type')
        date_from = self.request.query_params.get('dateFrom')
        date_to = self.request.query_params.get('dateTo')
        
        if category:
            queryset = queryset.filter(category__name__icontains=category)
        if date_from:
            queryset = queryset.filter(transaction_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(transaction_date__lte=date_to)
            
        return queryset.order_by('-transaction_date')
    
    def perform_create(self, serializer):
        # Assign to user's member profile
        user = self.request.user
        if hasattr(user, 'member_profile'):
            serializer.save(member=user.member_profile)
        else:
            # Create member profile if it doesn't exist
            from accounts.models import Member
            member = Member.objects.create(user=user)
            serializer.save(member=member)
