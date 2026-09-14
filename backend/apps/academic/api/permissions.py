"""
Permissions for Academic Foundation module.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.exceptions import PermissionDenied, NotAuthenticated
from apps.identity.services.role_service import RoleService


class CanManageAcademicStructure(BasePermission):
    """
    Enforces 'academic.manage_structure' for create/update/delete operations,
    and 'academic.view_structure' (or authenticated user) for read operations.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated("Authentication credentials were not provided.")
        
        if request.user.is_superuser:
            return True

        if request.method in SAFE_METHODS:
            return True
        
        if RoleService.user_has_permission(request.user, 'academic.manage_structure'):
            return True
        raise PermissionDenied("You do not have permission to modify academic structure.")


class CanManageCurriculum(BasePermission):
    """
    Enforces 'academic.manage_curriculum' for mutating schemes, subjects, and scheme-subjects,
    and allows authenticated users for read operations.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated("Authentication credentials were not provided.")
        
        if request.user.is_superuser:
            return True

        if request.method in SAFE_METHODS:
            return True
        
        if RoleService.user_has_permission(request.user, 'academic.manage_curriculum'):
            return True
        raise PermissionDenied("You do not have permission to modify curriculum data.")
