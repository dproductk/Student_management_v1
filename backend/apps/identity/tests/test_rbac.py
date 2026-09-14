from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.identity.models import Role, Permission, RolePermission, UserRole
from apps.identity.services.user_service import UserService
from apps.identity.services.role_service import RoleService
from apps.identity.api.permissions import require_permission, require_role

User = get_user_model()


class MockProtectedAcademicView(APIView):
    """
    Mock protected view for testing permission enforcement.
    Requires 'academic.manage_departments' permission.
    """
    permission_classes = [require_permission('academic.manage_departments')]

    def post(self, request):
        return Response({'status': 'Department created successfully'}, status=status.HTTP_200_OK)


class MockProtectedAdminOnlyView(APIView):
    """
    Mock protected view requiring SYSTEM_ADMIN role.
    """
    permission_classes = [require_role('SYSTEM_ADMIN')]

    def get(self, request):
        return Response({'status': 'Admin dashboard'}, status=status.HTTP_200_OK)


class RolePermissionAssignmentAndEnforcementTests(TestCase):
    """
    Automated tests for Role-Permission mapping, User-Role assignments,
    and server-side authorization enforcement.
    Governed by identity-and-access-prd.md Requirements 10, 11, 12, 13, 14.
    """

    def setUp(self):
        self.client = APIClient()
        self.factory = APIRequestFactory()

        # Create admin user
        self.admin = User.objects.create_superuser(
            username="sec_admin",
            password="AdminPassword123!"
        )

        # Create standard user
        self.staff_user = UserService.create_user(
            username="faculty_01",
            password="FacultyPassword123!",
            email="faculty01@college.edu"
        )

        # Create test roles
        self.hod_role = RoleService.create_role(name="TEST_HOD", scope_type="DEPARTMENT")
        self.clerk_role = RoleService.create_role(name="TEST_CLERK", scope_type="SYSTEM")

        # Create test permissions
        self.dept_perm = RoleService.create_permission(
            codename="academic.manage_departments",
            module="academic",
            description="Manage departments"
        )
        self.student_perm = RoleService.create_permission(
            codename="students.manage_profile",
            module="students",
            description="Manage students"
        )

    def test_assign_and_revoke_permission_to_role(self):
        # Assign permission to role
        rp = RoleService.assign_permission_to_role(str(self.hod_role.id), str(self.dept_perm.id))
        self.assertEqual(rp.role, self.hod_role)
        self.assertEqual(rp.permission, self.dept_perm)

        # Verify role has permission
        perms = RoleService.get_permissions_for_role(str(self.hod_role.id))
        self.assertIn(self.dept_perm, perms)

        # Revoke permission
        RoleService.revoke_permission_from_role(str(self.hod_role.id), str(self.dept_perm.id))
        perms_after = RoleService.get_permissions_for_role(str(self.hod_role.id))
        self.assertNotIn(self.dept_perm, perms_after)

    def test_user_inherits_permissions_through_assigned_role(self):
        # Attach permission to HOD role
        RoleService.assign_permission_to_role(str(self.hod_role.id), str(self.dept_perm.id))

        # Initially user has no permissions
        self.assertFalse(RoleService.user_has_permission(self.staff_user, "academic.manage_departments"))

        # Assign HOD role to user
        RoleService.assign_role_to_user(
            user_id=str(self.staff_user.id),
            role_id=str(self.hod_role.id),
            assigned_by=self.admin
        )

        # User now possesses the permission
        self.assertTrue(RoleService.user_has_permission(self.staff_user, "academic.manage_departments"))
        user_perms = RoleService.get_user_permissions(self.staff_user)
        self.assertIn("academic.manage_departments", user_perms)

    def test_multi_role_permission_aggregation(self):
        # HOD role has dept permission
        RoleService.assign_permission_to_role(str(self.hod_role.id), str(self.dept_perm.id))
        # Clerk role has student permission
        RoleService.assign_permission_to_role(str(self.clerk_role.id), str(self.student_perm.id))

        # Assign both roles to staff user
        RoleService.assign_role_to_user(str(self.staff_user.id), str(self.hod_role.id), assigned_by=self.admin)
        RoleService.assign_role_to_user(str(self.staff_user.id), str(self.clerk_role.id), assigned_by=self.admin)

        # User possesses union of permissions from both roles
        self.assertTrue(RoleService.user_has_permission(self.staff_user, "academic.manage_departments"))
        self.assertTrue(RoleService.user_has_permission(self.staff_user, "students.manage_profile"))

    def test_revoking_role_removes_user_permissions(self):
        RoleService.assign_permission_to_role(str(self.hod_role.id), str(self.dept_perm.id))
        RoleService.assign_role_to_user(str(self.staff_user.id), str(self.hod_role.id), assigned_by=self.admin)
        self.assertTrue(RoleService.user_has_permission(self.staff_user, "academic.manage_departments"))

        # Revoke role from user
        RoleService.revoke_role_from_user(str(self.staff_user.id), str(self.hod_role.id))
        self.assertFalse(RoleService.user_has_permission(self.staff_user, "academic.manage_departments"))

    def test_server_side_enforcement_allowed_for_authorized_user(self):
        # Grant permission to user via role
        RoleService.assign_permission_to_role(str(self.hod_role.id), str(self.dept_perm.id))
        RoleService.assign_role_to_user(str(self.staff_user.id), str(self.hod_role.id), assigned_by=self.admin)

        view = MockProtectedAcademicView.as_view()
        request = self.factory.post('/mock/dept/create/')
        force_authenticate(request, user=self.staff_user)

        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_server_side_enforcement_denied_for_unauthorized_user(self):
        # User lacks 'academic.manage_departments'
        view = MockProtectedAcademicView.as_view()
        request = self.factory.post('/mock/dept/create/')
        force_authenticate(request, user=self.staff_user)

        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['code'], 'PERMISSION_DENIED')

    def test_client_cannot_bypass_authorization_via_headers(self):
        # Spoofed client headers must be completely ignored by backend
        view = MockProtectedAcademicView.as_view()
        request = self.factory.post(
            '/mock/dept/create/',
            HTTP_X_ROLE='SYSTEM_ADMIN',
            HTTP_X_PERMISSIONS='academic.manage_departments'
        )
        force_authenticate(request, user=self.staff_user)  # Actual authenticated user without permission

        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_has_all_permissions_automatically(self):
        view = MockProtectedAcademicView.as_view()
        request = self.factory.post('/mock/dept/create/')
        force_authenticate(request, user=self.admin)

        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RBACAssignmentAPITests(TestCase):
    """
    API integration tests for Role-Permission and User-Role assignment endpoints.
    """

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(username="api_admin", password="AdminPassword123!")
        self.client.force_authenticate(user=self.admin)

        self.user = UserService.create_user(username="target_user", password="UserPassword123!")
        self.role = RoleService.create_role(name="API_ROLE", scope_type="SYSTEM")
        self.perm = RoleService.create_permission(codename="test.api_action", module="test")

    def test_assign_and_revoke_permission_api(self):
        # Assign permission to role
        assign_resp = self.client.post(f'/api/v1/auth/roles/{self.role.id}/permissions/', {
            'permission_id': str(self.perm.id)
        })
        self.assertEqual(assign_resp.status_code, status.HTTP_201_CREATED)

        # List permissions of role
        list_resp = self.client.get(f'/api/v1/auth/roles/{self.role.id}/permissions/')
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_resp.data), 1)

        # Revoke permission
        del_resp = self.client.delete(f'/api/v1/auth/roles/{self.role.id}/permissions/{self.perm.id}/')
        self.assertEqual(del_resp.status_code, status.HTTP_200_OK)

    def test_assign_and_revoke_user_role_api(self):
        # Assign role to user
        assign_resp = self.client.post(f'/api/v1/auth/users/{self.user.id}/roles/', {
            'role_id': str(self.role.id)
        })
        self.assertEqual(assign_resp.status_code, status.HTTP_201_CREATED)

        # List roles of user
        list_resp = self.client.get(f'/api/v1/auth/users/{self.user.id}/roles/')
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_resp.data), 1)

        # Revoke role from user
        del_resp = self.client.delete(f'/api/v1/auth/users/{self.user.id}/roles/{self.role.id}/')
        self.assertEqual(del_resp.status_code, status.HTTP_200_OK)
