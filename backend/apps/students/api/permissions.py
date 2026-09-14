"""
Permission classes for Student Management API.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.exceptions import PermissionDenied, NotAuthenticated
from apps.identity.services.role_service import RoleService


class CanViewStudents(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated("Authentication credentials were not provided.")
        if request.user.is_superuser:
            return True
        if RoleService.user_has_permission(request.user, 'students.view_directory') or \
           RoleService.user_has_permission(request.user, 'students.manage_profile'):
            return True
        raise PermissionDenied("You do not possess permission to view the student directory.")


class CanManageStudents(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated("Authentication credentials were not provided.")
        if request.user.is_superuser:
            return True
        if RoleService.user_has_permission(request.user, 'students.manage_profile'):
            return True
        raise PermissionDenied("You do not possess permission to manage student profiles.")
