from rest_framework import permissions
from django.contrib.auth.models import AnonymousUser


class IsUserOwnerOrAdmin(permissions.BasePermission):
    """Allow access if user is owner or admin"""
    
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, AnonymousUser):
            return False
        
        # Admin users can access any user
        if request.user.role in ['denomination_admin', 'system_admin']:
            return True
        
        # Users can only access their own profile
        return obj == request.user


class CanManageUsers(permissions.BasePermission):
    """Allow access to users who can manage other users"""
    
    def has_permission(self, request, view):
        if not request.user or isinstance(request.user, AnonymousUser):
            return False
        
        return request.user.role in ['pastor', 'treasurer', 'auditor', 'denomination_admin', 'system_admin']


class CanSuspendUsers(permissions.BasePermission):
    """Allow access to users who can suspend other users"""
    
    def has_permission(self, request, view):
        if not request.user or isinstance(request.user, AnonymousUser):
            return False
        
        return request.user.role in ['denomination_admin', 'system_admin']


class CanViewUserList(permissions.BasePermission):
    """Allow access to users who can view user lists"""
    
    def has_permission(self, request, view):
        if not request.user or isinstance(request.user, AnonymousUser):
            return False
        
        return request.user.role in ['pastor', 'treasurer', 'auditor', 'denomination_admin', 'system_admin']
