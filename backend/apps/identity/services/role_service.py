"""
Role and Permission application service.
Handles role creation, permission registration, role-permission mappings,
user-role assignments, and permission resolution.
Governed by ARCHITECTURE.md, identity-and-access-prd.md, and DATABASE_ARCHITECTURE.md Deliverables H & N.
"""

from typing import List, Optional, Tuple, Set
from django.db import transaction
from common.exceptions import EntityNotFoundError, InvariantViolationError
from apps.identity.models import User, Role, Permission, RolePermission, UserRole
from apps.audit.services.audit_service import AuditService
from apps.identity.domain.rbac import (
    RoleScopeType,
    CANONICAL_ROLES,
    CANONICAL_PERMISSIONS,
    validate_role_name,
    validate_scope_type,
    validate_permission_codename,
)


class RoleService:
    """
    Application service managing the lifecycle and assignments of Roles and Permissions.
    """

    @classmethod
    @transaction.atomic
    def create_role(cls, name: str, scope_type: str, description: Optional[str] = None) -> Role:
        validate_role_name(name)
        validate_scope_type(scope_type)

        normalized_name = name.strip().upper()
        if Role.objects.filter(name=normalized_name).exists():
            raise InvariantViolationError(f"A role with name '{normalized_name}' already exists.")

        role = Role.objects.create(
            name=normalized_name,
            scope_type=scope_type,
            description=description.strip() if description else None
        )
        return role

    @classmethod
    @transaction.atomic
    def create_permission(cls, codename: str, module: str, description: Optional[str] = None) -> Permission:
        validate_permission_codename(codename)
        if not module or not module.strip():
            raise InvariantViolationError("Module name cannot be empty.")

        normalized_codename = codename.strip().lower()
        if Permission.objects.filter(codename=normalized_codename).exists():
            raise InvariantViolationError(f"A permission with codename '{normalized_codename}' already exists.")

        permission = Permission.objects.create(
            codename=normalized_codename,
            module=module.strip().lower(),
            description=description.strip() if description else None
        )
        return permission

    @classmethod
    def get_role_by_id(cls, role_id: str) -> Role:
        try:
            return Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            raise EntityNotFoundError("Role", str(role_id))

    @classmethod
    def get_role_by_name(cls, name: str) -> Role:
        try:
            return Role.objects.get(name=name.strip().upper())
        except Role.DoesNotExist:
            raise EntityNotFoundError("Role", name)

    @classmethod
    def get_permission_by_id(cls, permission_id: str) -> Permission:
        try:
            return Permission.objects.get(id=permission_id)
        except Permission.DoesNotExist:
            raise EntityNotFoundError("Permission", str(permission_id))

    @classmethod
    def get_permission_by_codename(cls, codename: str) -> Permission:
        try:
            return Permission.objects.get(codename=codename.strip().lower())
        except Permission.DoesNotExist:
            raise EntityNotFoundError("Permission", codename)

    # ── Role-Permission Assignments ───────────────────────────────

    @classmethod
    @transaction.atomic
    def assign_permission_to_role(cls, role_id: str, permission_id: str) -> RolePermission:
        role = cls.get_role_by_id(role_id)
        permission = cls.get_permission_by_id(permission_id)

        rp, created = RolePermission.objects.get_or_create(
            role=role,
            permission=permission
        )

        AuditService.record_audit(
            action="ROLE_PERMISSION_ASSIGNED",
            target_type="ROLE_PERMISSION",
            module="identity",
            target_id=role.id,
            new_value={"role_name": role.name, "permission_codename": permission.codename}
        )
        return rp

    @classmethod
    @transaction.atomic
    def revoke_permission_from_role(cls, role_id: str, permission_id: str) -> None:
        role = cls.get_role_by_id(role_id)
        permission = cls.get_permission_by_id(permission_id)

        deleted_count, _ = RolePermission.objects.filter(
            role=role,
            permission=permission
        ).delete()
        if deleted_count == 0:
            raise EntityNotFoundError("RolePermission", f"Role {role.name} does not have permission {permission.codename}")

        AuditService.record_audit(
            action="ROLE_PERMISSION_REVOKED",
            target_type="ROLE_PERMISSION",
            module="identity",
            target_id=role.id,
            old_value={"role_name": role.name, "permission_codename": permission.codename}
        )

    @classmethod
    def get_permissions_for_role(cls, role_id: str) -> List[Permission]:
        role = cls.get_role_by_id(role_id)
        return list(Permission.objects.filter(permission_roles__role=role))

    # ── User-Role Assignments ─────────────────────────────────────

    @classmethod
    @transaction.atomic
    def assign_role_to_user(
        cls,
        user_id: str,
        role_id: str,
        assigned_by: User,
        scope_department_id: Optional[str] = None,
        scope_batch_id: Optional[str] = None
    ) -> UserRole:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise EntityNotFoundError("User", str(user_id))

        role = cls.get_role_by_id(role_id)

        ur, created = UserRole.objects.get_or_create(
            user=user,
            role=role,
            scope_department_id=scope_department_id,
            scope_batch_id=scope_batch_id,
            defaults={'assigned_by': assigned_by}
        )

        AuditService.record_audit(
            action="ROLE_ASSIGNED",
            target_type="USER_ROLE",
            module="identity",
            actor=assigned_by,
            target_id=user.id,
            new_value={
                "user_id": str(user.id),
                "username": user.username,
                "role_name": role.name,
                "scope_department_id": str(scope_department_id) if scope_department_id else None,
                "scope_batch_id": str(scope_batch_id) if scope_batch_id else None,
            }
        )
        return ur

    @classmethod
    @transaction.atomic
    def revoke_role_from_user(cls, user_id: str, role_id: str) -> None:
        deleted_count, _ = UserRole.objects.filter(
            user_id=user_id,
            role_id=role_id
        ).delete()
        if deleted_count == 0:
            raise EntityNotFoundError("UserRole", f"User {user_id} does not have role {role_id}")

        AuditService.record_audit(
            action="ROLE_REVOKED",
            target_type="USER_ROLE",
            module="identity",
            target_id=user_id,
            old_value={"user_id": str(user_id), "role_id": str(role_id)}
        )

    @classmethod
    def get_user_roles(cls, user_id: str) -> List[Role]:
        return list(Role.objects.filter(role_users__user_id=user_id))

    @classmethod
    def get_user_permissions(cls, user: User) -> Set[str]:
        """
        Resolves all unique permission codenames granted to a user through assigned roles.
        Superuser receives all registered permissions automatically.
        """
        if not user or not user.is_authenticated:
            return set()

        if user.is_superuser:
            return set(Permission.objects.values_list('codename', flat=True))

        user_role_ids = UserRole.objects.filter(user=user).values_list('role_id', flat=True)
        permission_codenames = RolePermission.objects.filter(
            role_id__in=user_role_ids
        ).values_list('permission__codename', flat=True).distinct()

        return set(permission_codenames)

    @classmethod
    def user_has_permission(cls, user: User, permission_codename: str) -> bool:
        """
        Checks whether the user possesses the specified permission codename.
        """
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return permission_codename in cls.get_user_permissions(user)

    @classmethod
    def has_scoped_permission(
        cls,
        user: User,
        permission_codename: str,
        target_department_id: Optional[str] = None,
        target_batch_id: Optional[str] = None,
        target_user_id: Optional[str] = None
    ) -> bool:
        """
        Evaluates whether a user is authorized to perform an action on a target resource
        governed by role scope rules (SYSTEM, DEPARTMENT, BATCH, OWN).
        Governed by DATABASE_ARCHITECTURE.md Deliverable H.
        """
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        # Find all user roles where the role grants the required permission
        matching_user_roles = UserRole.objects.filter(
            user=user,
            role__role_permissions__permission__codename=permission_codename
        ).select_related('role')

        for ur in matching_user_roles:
            scope_type = ur.role.scope_type

            if scope_type == RoleScopeType.SYSTEM.value:
                return True

            if scope_type == RoleScopeType.DEPARTMENT.value:
                if target_department_id and str(ur.scope_department_id) == str(target_department_id):
                    return True

            if scope_type == RoleScopeType.BATCH.value:
                if target_batch_id and str(ur.scope_batch_id) == str(target_batch_id):
                    return True

            if scope_type == RoleScopeType.OWN.value:
                if target_user_id and str(user.id) == str(target_user_id):
                    return True

        return False

    # ── Seed Data ─────────────────────────────────────────────────

    @classmethod
    @transaction.atomic
    def seed_canonical_roles_and_permissions(cls) -> Tuple[int, int]:
        roles_created = 0
        for name, data in CANONICAL_ROLES.items():
            _, created = Role.objects.get_or_create(
                name=name,
                defaults={
                    'scope_type': data['scope_type'],
                    'description': data['description']
                }
            )
            if created:
                roles_created += 1

        permissions_created = 0
        for perm in CANONICAL_PERMISSIONS:
            _, created = Permission.objects.get_or_create(
                codename=perm['codename'],
                defaults={
                    'module': perm['module'],
                    'description': perm['description']
                }
            )
            if created:
                permissions_created += 1

        # Link SYSTEM_ADMIN to all foundational permissions
        try:
            admin_role = Role.objects.get(name="SYSTEM_ADMIN")
            for permission in Permission.objects.all():
                RolePermission.objects.get_or_create(role=admin_role, permission=permission)
        except Role.DoesNotExist:
            pass

        # Link STUDENT role to students.view_own_record
        try:
            student_role = Role.objects.get(name="STUDENT")
            student_perm = Permission.objects.filter(codename="students.view_own_record").first()
            if student_perm:
                RolePermission.objects.get_or_create(role=student_role, permission=student_perm)
        except Role.DoesNotExist:
            pass

        return roles_created, permissions_created
