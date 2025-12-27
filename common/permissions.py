from rest_framework import permissions
from django.contrib.auth.models import AnonymousUser


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Allow read-only access to anyone, but write access only to owner"""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if object has an owner field
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'member'):
            return obj.member.user == request.user
        
        return False


class IsChurchAdmin(permissions.BasePermission):
    """Allow access only to church administrators"""
    
    def has_permission(self, request, view):
        if not request.user or isinstance(request.user, AnonymousUser):
            return False
        
        return request.user.role in ['pastor', 'treasurer', 'auditor', 'denomination_admin', 'system_admin']


class IsDenominationAdmin(permissions.BasePermission):
    """Allow access only to denomination administrators"""
    
    def has_permission(self, request, view):
        if not request.user or isinstance(request.user, AnonymousUser):
            return False
        
        return request.user.role in ['denomination_admin', 'system_admin']


class IsSystemAdmin(permissions.BasePermission):
    """Allow access only to system administrators"""
    
    def has_permission(self, request, view):
        if not request.user or isinstance(request.user, AnonymousUser):
            return False
        
        return request.user.role == 'system_admin'


class IsMemberOfChurch(permissions.BasePermission):
    """Allow access only to members of the same church"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user or isinstance(request.user, AnonymousUser):
            return False
        
        # Get user's church
        user_church = getattr(request.user, 'church', None)
        if not user_church:
            return False
        
        # Check if object belongs to the same church
        if hasattr(obj, 'church'):
            return obj.church == user_church
        elif hasattr(obj, 'member') and hasattr(obj.member, 'church'):
            return obj.member.church == user_church
        elif hasattr(obj, 'campus') and hasattr(obj.campus, 'church'):
            return obj.campus.church == user_church
        
        return False


class CanViewChurchFinances(permissions.BasePermission):
    """Allow access to users who can view church finances"""
    
    def has_permission(self, request, view):
        if not request.user or isinstance(request.user, AnonymousUser):
            return False
        
        return request.user.role in ['pastor', 'treasurer', 'auditor', 'denomination_admin', 'system_admin']


class CanManageChurchFinances(permissions.BasePermission):
    """Allow access to users who can manage church finances"""
    
    def has_permission(self, request, view):
        if not request.user or isinstance(request.user, AnonymousUser):
            return False
        
        return request.user.role in ['treasurer', 'denomination_admin', 'system_admin']


class CanApproveExpenses(permissions.BasePermission):
    """Allow access to users who can approve expenses"""
    
    def has_permission(self, request, view):
        if not request.user or isinstance(request.user, AnonymousUser):
            return False
        
        return request.user.role in ['pastor', 'denomination_admin', 'system_admin']
