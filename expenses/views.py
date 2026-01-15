from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from .models import Expense, ExpenseCategory
from accounts.models import User


class ExpenseListCreateView(generics.ListCreateAPIView):
    """List and create expenses"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Expense.objects.filter(user=user)
        
        # Filter by parameters
        category = self.request.query_params.get('category')
        status = self.request.query_params.get('status')
        date_from = self.request.query_params.get('dateFrom')
        date_to = self.request.query_params.get('dateTo')
        
        if category:
            queryset = queryset.filter(category__name__icontains=category)
        if status:
            queryset = queryset.filter(status=status)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
            
        return queryset.order_by('-date')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ExpenseCreateSerializer
        return ExpenseSerializer


class ExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete expense"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = Expense.objects.all()
    
    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def approve_expense(request, pk):
    """Approve expense"""
    try:
        expense = Expense.objects.get(pk=pk, user=request.user)
        expense.status = 'approved'
        expense.save()
        return Response({'message': 'Expense approved successfully'})
    except Expense.DoesNotExist:
        return Response({'error': 'Expense not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reject_expense(request, pk):
    """Reject expense"""
    try:
        expense = Expense.objects.get(pk=pk, user=request.user)
        expense.status = 'rejected'
        expense.save()
        return Response({'message': 'Expense rejected successfully'})
    except Expense.DoesNotExist:
        return Response({'error': 'Expense not found'}, status=status.HTTP_404_NOT_FOUND)


# Simple serializers for now
from rest_framework import serializers

class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = '__all__'


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Expense
        fields = '__all__'


class ExpenseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ['title', 'description', 'amount', 'category', 'date', 'receipt']
