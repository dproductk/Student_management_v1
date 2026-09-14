from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from common.exceptions import InvariantViolationError, EntityNotFoundError
from apps.identity.models import Role, Permission
from apps.identity.services.role_service import RoleService
from apps.identity.domain.rbac import RoleScopeType, CANONICAL_ROLES

User = get_user_model()


class RolesAndPermissionsDomainTests(TestCase):
    """
    Unit tests for Role and Permission models, invariants, and application services.
    Governed by DATABASE_ARCHITECTURE.md Deliverable H and identity-and-access-prd.md.
    """

    def test_create_role_success(self):
        role = RoleService.create_role(
            name="DEAN_ACADEMICS",
            scope_type="SYSTEM",
            description="Dean of Academic Affairs"
        )
        self.assertIsNotNone(role.id)
        self.assertEqual(role.name, "DEAN_ACADEMICS")
        self.assertEqual(role.scope_type, "SYSTEM")

    def test_duplicate_role_name_rejected(self):
        RoleService.create_role(name="LIBRARIAN", scope_type="SYSTEM")
        with self.assertRaises(InvariantViolationError):
            RoleService.create_role(name="LIBRARIAN", scope_type="SYSTEM")

    def test_invalid_role_scope_rejected(self):
        with self.assertRaises(InvariantViolationError):
            RoleService.create_role(name="INVALID_ROLE", scope_type="INVALID_SCOPE")

    def test_empty_role_name_rejected(self):
        with self.assertRaises(InvariantViolationError):
            RoleService.create_role(name="   ", scope_type="SYSTEM")

    def test_create_permission_success(self):
        perm = RoleService.create_permission(
            codename="academic.publish_syllabus",
            module="academic",
            description="Publish syllabus for a scheme"
        )
        self.assertIsNotNone(perm.id)
        self.assertEqual(perm.codename, "academic.publish_syllabus")
        self.assertEqual(perm.module, "academic")

    def test_duplicate_permission_codename_rejected(self):
        RoleService.create_permission(codename="identity.audit_view", module="identity")
        with self.assertRaises(InvariantViolationError):
            RoleService.create_permission(codename="identity.audit_view", module="identity")

    def test_invalid_permission_format_rejected(self):
        with self.assertRaises(InvariantViolationError):
            RoleService.create_permission(codename="invalid_without_dot", module="academic")

    def test_seed_canonical_roles_and_permissions_idempotent(self):
        # First seed
        roles_created, perms_created = RoleService.seed_canonical_roles_and_permissions()
        self.assertEqual(roles_created, len(CANONICAL_ROLES))
        self.assertGreater(perms_created, 0)

        # Verify all 8 canonical roles exist
        for role_name in CANONICAL_ROLES.keys():
            self.assertTrue(Role.objects.filter(name=role_name).exists())

        # Second seed run must create 0 duplicates (idempotent)
        roles_second, perms_second = RoleService.seed_canonical_roles_and_permissions()
        self.assertEqual(roles_second, 0)
        self.assertEqual(perms_second, 0)


class RolesAndPermissionsAPITests(TestCase):
    """
    Integration tests for Role and Permission REST endpoints.
    """

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username="rbac_admin",
            password="AdminPassword123!"
        )
        self.regular_user = User.objects.create_user(
            username="regular_staff",
            password="StaffPassword123!"
        )

    def test_admin_create_role_endpoint(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/v1/auth/roles/', {
            'name': 'LAB_INCHARGE',
            'scope_type': 'DEPARTMENT',
            'description': 'Manages computer labs'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'LAB_INCHARGE')
        self.assertEqual(response.data['scope_type'], 'DEPARTMENT')

    def test_regular_user_cannot_create_role(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post('/api/v1/auth/roles/', {
            'name': 'UNAUTHORIZED_ROLE',
            'scope_type': 'SYSTEM'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_seed_rbac_endpoint(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/v1/auth/rbac/seed/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('roles_created', response.data)
        self.assertGreaterEqual(response.data['total_roles'], 8)

    def test_admin_create_permission_endpoint(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/v1/auth/permissions/', {
            'codename': 'finance.export_receipts',
            'module': 'finance',
            'description': 'Export student fee receipts'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['codename'], 'finance.export_receipts')
