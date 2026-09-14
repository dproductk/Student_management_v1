"""
DRF Custom Permission classes for server-side authorization enforcement.
Governed by identity-and-access-prd.md Requirements 10, 11, 12, 13, 14.
"""

from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied, NotAuthenticated
from apps.identity.models import User
from apps.identity.services.role_service import RoleService


class RequirePermission(BasePermission):
    """
    Factory-like permission class enforcing that the authenticated actor
    possesses the specified permission codename.
    Usage:
        class SomeView(APIView):
            permission_classes = [RequirePermission('academic.manage_departments')]
    """
    permission_codename: str = ""

    def __init__(self, permission_codename: str = None):
        if permission_codename:
            self.permission_codename = permission_codename

    def __call__(self):
        return self

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated("Authentication credentials were not provided.")

        required_codename = getattr(view, 'required_permission', None) or self.permission_codename
        if not required_codename:
            return True

        if RoleService.user_has_permission(request.user, required_codename):
            return True

        raise PermissionDenied(
            f"You do not possess the required permission '{required_codename}' to perform this action."
        )


class RequireRole(BasePermission):
    """
    Permission class enforcing that the user has a specific role name assigned.
    """
    role_name: str = ""

    def __init__(self, role_name: str = None):
        if role_name:
            self.role_name = role_name

    def __call__(self):
        return self

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated("Authentication credentials were not provided.")

        if request.user.is_superuser:
            return True

        target_role = getattr(view, 'required_role', None) or self.role_name
        if not target_role:
            return True

        user_role_names = [r.name for r in RoleService.get_user_roles(str(request.user.id))]
        if target_role.strip().upper() in user_role_names:
            return True

        raise PermissionDenied(
            f"You do not possess the required role '{target_role}' to access this resource."
        )


def require_permission(codename: str):
    """
    Helper function returning a concrete DRF Permission class configured with the codename.
    Usage:
        permission_classes = [require_permission('identity.manage_roles')]
    """
    class ConfiguredRequirePermission(RequirePermission):
        def __init__(self):
            super().__init__(permission_codename=codename)

    return ConfiguredRequirePermission


def require_role(role_name: str):
    """
    Helper function returning a concrete DRF Permission class configured with the role name.
    Usage:
        permission_classes = [require_role('SYSTEM_ADMIN')]
    """
    class ConfiguredRequireRole(RequireRole):
        def __init__(self):
            super().__init__(role_name=role_name)

    return ConfiguredRequireRole


class RequireScopedPermission(BasePermission):
    """
    Object-level permission enforcing that the user has the required permission AND
    satisfies the scope (SYSTEM, DEPARTMENT, BATCH, OWN) for the target object.
    Governed by DATABASE_ARCHITECTURE.md Deliverable H.
    """
    permission_codename: str = ""

    def __init__(self, permission_codename: str = None):
        if permission_codename:
            self.permission_codename = permission_codename

    def __call__(self):
        return self

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated("Authentication credentials were not provided.")

        required_codename = getattr(view, 'required_permission', None) or self.permission_codename
        if not required_codename:
            return True

        if RoleService.user_has_permission(request.user, required_codename):
            return True

        raise PermissionDenied(
            f"You do not possess the required permission '{required_codename}' to perform this action."
        )

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated("Authentication credentials were not provided.")

        if request.user.is_superuser:
            return True

        required_codename = getattr(view, 'required_permission', None) or self.permission_codename

        dept_id = (
            getattr(obj, 'department_id', None) or
            getattr(getattr(obj, 'department', None), 'id', None) or
            getattr(obj, 'scope_department_id', None)
        )
        batch_id = (
            getattr(obj, 'batch_id', None) or
            getattr(getattr(obj, 'batch', None), 'id', None) or
            getattr(obj, 'scope_batch_id', None)
        )
        user_id = (
            getattr(obj, 'user_id', None) or
            getattr(getattr(obj, 'user', None), 'id', None) or
            (getattr(obj, 'id', None) if isinstance(obj, User) else None)
        )

        has_scope = RoleService.has_scoped_permission(
            user=request.user,
            permission_codename=required_codename,
            target_department_id=str(dept_id) if dept_id else None,
            target_batch_id=str(batch_id) if batch_id else None,
            target_user_id=str(user_id) if user_id else None
        )

        if has_scope:
            return True

        raise PermissionDenied(
            "You do not have scoped authorization to access or modify this specific resource."
        )


def require_scoped_permission(codename: str):
    """
    Helper function returning a concrete DRF Permission class configured with scoped check.
    Usage:
        permission_classes = [require_scoped_permission('students.view_record')]
    """
    class ConfiguredRequireScopedPermission(RequireScopedPermission):
        def __init__(self):
            super().__init__(permission_codename=codename)

    return ConfiguredRequireScopedPermission


class RequirePasswordChanged(BasePermission):
    """
    Enforces that authenticated actors have completed any mandatory
    first-login password change (must_change_password=False) before accessing
    protected application resources.
    """
    message = "A mandatory password change is required before accessing this resource. Please change your password at /api/v1/auth/change-password/."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return True

        if getattr(request.user, 'must_change_password', False):
            raise PermissionDenied(
                self.message,
                code="PASSWORD_CHANGE_REQUIRED"
            )

        return True

