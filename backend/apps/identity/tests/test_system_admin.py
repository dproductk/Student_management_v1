"""
Automated tests for System Admin User and Role-Management vertical slice.
Governed by identity-and-access-prd.md Requirements 15, 16, 17, 18,
ARCHITECTURE.md, and DECISIONS.md.
"""

from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework import status
from django.urls import reverse

from apps.identity.models import User, Role, UserRole, Permission
from apps.identity.domain.state_machines import UserStatus
from apps.identity.domain.rbac import RoleScopeType
from apps.identity.services.role_service import RoleService
from apps.identity.services.user_service import UserService
from apps.identity.api.views import (
    UserViewSet,
    CreateUserView,
    SuspendUserView,
    ReactivateUserView,
    DeactivateUserView,
    RoleViewSet,
    PermissionViewSet,
    RolePermissionView,
    RolePermissionDetailView,
    UserRoleView,
    UserRoleDetailView,
    SeedRBACView,
)


class SystemAdminIdentityManagementTests(APITestCase):
    """
    Tests administrative user lifecycle and role-permission management
    driven by canonical RBAC authority (SYSTEM_ADMIN) rather than legacy flags.
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        RoleService.seed_canonical_roles_and_permissions()

        # Create System Admin user WITHOUT Django staff flag (is_staff=False, is_superuser=False)
        # to prove that authority is purely governed by canonical RBAC in the database
        self.system_admin_user = User.objects.create_user(
            username="sysadmin_operator",
            password="AdminPassword123!",
            email="sysadmin@college.edu",
            must_change_password=False,
            status=UserStatus.ACTIVE.value,
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )
        admin_role = Role.objects.get(name="SYSTEM_ADMIN")
        UserRole.objects.create(
            user=self.system_admin_user,
            role=admin_role,
            assigned_by=self.system_admin_user
        )

        # Create regular student user
        self.student_user = User.objects.create_user(
            username="student_regular",
            password="StudentPassword123!",
            email="student@college.edu",
            must_change_password=False,
            status=UserStatus.ACTIVE.value,
            is_active=True,
        )
        student_role = Role.objects.get(name="STUDENT")
        UserRole.objects.create(
            user=self.student_user,
            role=student_role,
            assigned_by=self.system_admin_user
        )

        # Create superuser
        self.superuser = User.objects.create_superuser(
            username="super_operator",
            password="SuperPassword123!",
            email="super@college.edu",
        )

    def test_system_admin_user_lifecycle_management(self):
        """
        System Admin can create, list, filter, suspend, reactivate, and deactivate users.
        """
        # 1. Create User
        req = self.factory.post(reverse('user-create'), {
            'username': 'NEW_FACULTY_01',
            'password': 'InitialPassword123!',
            'email': 'faculty01@college.edu',
            'must_change_password': True
        }, format='json')
        force_authenticate(req, user=self.system_admin_user)
        resp = CreateUserView.as_view()(req)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        new_user_id = resp.data['id']

        # 2. List & Filter Users
        req_list = self.factory.get(reverse('user-list'), {'status': 'ACTIVE', 'search': 'FACULTY'})
        force_authenticate(req_list, user=self.system_admin_user)
        resp_list = UserViewSet.as_view({'get': 'list'})(req_list)
        self.assertEqual(resp_list.status_code, status.HTTP_200_OK)
        usernames = [u['username'] for u in resp_list.data['results'] if 'results' in resp_list.data] or [u['username'] for u in resp_list.data]
        self.assertIn('NEW_FACULTY_01', usernames)

        # 3. Suspend User
        req_sus = self.factory.post(reverse('user-suspend', kwargs={'user_id': new_user_id}), {
            'reason': 'Administrative review pending'
        }, format='json')
        force_authenticate(req_sus, user=self.system_admin_user)
        resp_sus = SuspendUserView.as_view()(req_sus, user_id=new_user_id)
        self.assertEqual(resp_sus.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_sus.data['status'], UserStatus.SUSPENDED.value)

        # 4. Reactivate User
        req_act = self.factory.post(reverse('user-reactivate', kwargs={'user_id': new_user_id}))
        force_authenticate(req_act, user=self.system_admin_user)
        resp_act = ReactivateUserView.as_view()(req_act, user_id=new_user_id)
        self.assertEqual(resp_act.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_act.data['status'], UserStatus.ACTIVE.value)

        # 5. Deactivate User
        req_deact = self.factory.post(reverse('user-deactivate', kwargs={'user_id': new_user_id}), {
            'reason': 'Employment concluded'
        }, format='json')
        force_authenticate(req_deact, user=self.system_admin_user)
        resp_deact = DeactivateUserView.as_view()(req_deact, user_id=new_user_id)
        self.assertEqual(resp_deact.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_deact.data['status'], UserStatus.INACTIVE.value)

    def test_system_admin_role_and_permission_management(self):
        """
        System Admin can create roles, permissions, map role permissions, and assign user roles.
        """
        # 1. Create Role
        req_role = self.factory.post(reverse('role-list-create'), {
            'name': 'LAB_ASSISTANT',
            'scope_type': 'DEPARTMENT',
            'description': 'Laboratory assistant role'
        }, format='json')
        force_authenticate(req_role, user=self.system_admin_user)
        resp_role = RoleViewSet.as_view({'post': 'create'})(req_role)
        self.assertEqual(resp_role.status_code, status.HTTP_201_CREATED)
        role_id = resp_role.data['id']

        # 2. Create Permission
        req_perm = self.factory.post(reverse('permission-list-create'), {
            'codename': 'academic.access_lab',
            'module': 'academic',
            'description': 'Access lab resources'
        }, format='json')
        force_authenticate(req_perm, user=self.system_admin_user)
        resp_perm = PermissionViewSet.as_view({'post': 'create'})(req_perm)
        self.assertEqual(resp_perm.status_code, status.HTTP_201_CREATED)
        perm_id = resp_perm.data['id']

        # 3. Attach Permission to Role
        req_attach = self.factory.post(reverse('role-permissions', kwargs={'role_id': role_id}), {
            'permission_id': perm_id
        }, format='json')
        force_authenticate(req_attach, user=self.system_admin_user)
        resp_attach = RolePermissionView.as_view()(req_attach, role_id=role_id)
        self.assertEqual(resp_attach.status_code, status.HTTP_201_CREATED)

        # 4. Assign Role to User
        req_assign = self.factory.post(reverse('user-roles', kwargs={'user_id': self.student_user.id}), {
            'role_id': role_id
        }, format='json')
        force_authenticate(req_assign, user=self.system_admin_user)
        resp_assign = UserRoleView.as_view()(req_assign, user_id=self.student_user.id)
        self.assertEqual(resp_assign.status_code, status.HTTP_201_CREATED)

        # 5. Revoke Role from User
        req_revoke = self.factory.delete(reverse('user-role-detail', kwargs={'user_id': self.student_user.id, 'role_id': role_id}))
        force_authenticate(req_revoke, user=self.system_admin_user)
        resp_revoke = UserRoleDetailView.as_view()(req_revoke, user_id=self.student_user.id, role_id=role_id)
        self.assertEqual(resp_revoke.status_code, status.HTTP_200_OK)

        # 6. Seed RBAC
        req_seed = self.factory.post(reverse('rbac-seed'))
        force_authenticate(req_seed, user=self.system_admin_user)
        resp_seed = SeedRBACView.as_view()(req_seed)
        self.assertEqual(resp_seed.status_code, status.HTTP_200_OK)

    def test_non_admin_forbidden_from_admin_operations(self):
        """
        Regular users (e.g. students) attempting user or role management receive 403 Forbidden.
        """
        # Attempt to create user
        req = self.factory.post(reverse('user-create'), {'username': 'HACK_USER'}, format='json')
        force_authenticate(req, user=self.student_user)
        resp = CreateUserView.as_view()(req)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # Attempt to list users
        req_list = self.factory.get(reverse('user-list'))
        force_authenticate(req_list, user=self.student_user)
        resp_list = UserViewSet.as_view({'get': 'list'})(req_list)
        self.assertEqual(resp_list.status_code, status.HTTP_403_FORBIDDEN)

        # Attempt to create role
        req_role = self.factory.post(reverse('role-list-create'), {'name': 'ILLEGAL_ROLE', 'scope_type': 'SYSTEM'}, format='json')
        force_authenticate(req_role, user=self.student_user)
        resp_role = RoleViewSet.as_view({'post': 'create'})(req_role)
        self.assertEqual(resp_role.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_rejected(self):
        """
        Anonymous requests receive 401 Unauthorized.
        """
        req = self.factory.get(reverse('user-list'))
        resp = UserViewSet.as_view({'get': 'list'})(req)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_superuser_full_bypass(self):
        """
        Superuser has universal administrative bypass.
        """
        req = self.factory.get(reverse('user-list'))
        force_authenticate(req, user=self.superuser)
        resp = UserViewSet.as_view({'get': 'list'})(req)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
