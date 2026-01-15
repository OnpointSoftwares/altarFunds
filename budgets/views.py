from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from .models import Budget
from accounts.models import User
from rest_framework import serializers


class BudgetSerializer(serializers.ModelSerializer):
    remaining_amount = serializers.ReadOnlyField()
    utilization_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Budget
        fields = '__all__'


class BudgetListCreateView(generics.ListCreateAPIView):
    """List and create budgets"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BudgetSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Budget.objects.filter(user=user)
        
        # Filter by parameters
        year = self.request.query_params.get('year')
        department = self.request.query_params.get('department')
        
        if year:
            queryset = queryset.filter(year=year)
        if department:
            queryset = queryset.filter(department__icontains=department)
            
        return queryset.order_by('-year', '-month')


class BudgetDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete budget"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer
    
    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)
