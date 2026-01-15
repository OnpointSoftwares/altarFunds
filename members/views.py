from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from accounts.models import User, Member
from rest_framework import serializers


class MemberSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    membership_number = serializers.CharField()
    membership_date = serializers.DateField()
    
    class Meta:
        model = Member
        fields = '__all__'


class MemberListView(generics.ListAPIView):
    """List members with search functionality"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MemberSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Member.objects.filter(user__church=user.church)
        
        # Search functionality
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(membership_number__icontains=search)
            )
            
        return queryset.order_by('-membership_date')
