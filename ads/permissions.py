"""
Custom permissions for the ads app.
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Read permissions are allowed to any request,
        Write permissions are only allowed to the owner of the ad.
        """
        # Read permissions allowed for safe methods
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only allowed to owner
        return obj.seller == request.user


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to access it.
    """
    
    def has_object_permission(self, request, view, obj):
        """Only allow owner to access."""
        return obj.seller == request.user