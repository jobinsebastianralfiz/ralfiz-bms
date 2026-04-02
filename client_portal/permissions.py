from rest_framework.permissions import BasePermission


class IsClient(BasePermission):
    """Only allow authenticated users who have a linked client profile"""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'client_profile') and request.user.client_profile is not None


class IsClientOrAdmin(BasePermission):
    """Allow clients or admin/staff users"""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff or request.user.is_superuser:
            return True
        return hasattr(request.user, 'client_profile') and request.user.client_profile is not None
