"""
Automated tests for Student Account Provisioning Policy vertical slice.
Governed by ADR-009, ARCHITECTURE.md, and identity-and-access-prd.md.
"""

from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework import status
from django.urls import reverse

from common.exceptions import InvariantViolationError
from apps.identity.models import User, Role, UserRole, Permission, RolePermission
from apps.identity.domain.state_machines import UserStatus
from apps.identity.domain.rbac import RoleScopeType
from apps.identity.services.auth_service import AuthService
from apps.identity.services.role_service import RoleService
from apps.identity.services.provisioning import (
    StudentAccountProvisioningService,
    EnrollmentNumberProvisioningPolicy,
    StudentProvisioningPolicy,
)
from apps.identity.api.views import ProvisionStudentView, BulkProvisionStudentView


class StudentAccountProvisioningPolicyTests(APITestCase):
    """
    Unit and integration tests for ADR-009 initial student account provisioning.
    """

    def setUp(self):
        self.factory = APIRequestFactory()

        # Seed canonical roles and permissions
        RoleService.seed_canonical_roles_and_permissions()

        # Create admin user with identity.manage_users permission
        self.admin_user = User.objects.create_user(
            username="admin_provisioner",
            password="StrongAdminPassword123!",
            email="admin@college.edu",
            must_change_password=False,
            status=UserStatus.ACTIVE.value,
            is_active=True
        )
        admin_role = Role.objects.get(name="SYSTEM_ADMIN")
        UserRole.objects.create(user=self.admin_user, role=admin_role, assigned_by=self.admin_user)

        # Create standard non-admin user
        self.regular_user = User.objects.create_user(
            username="regular_staff",
            password="StaffPassword123!",
            email="staff@college.edu",
            must_change_password=False,
            status=UserStatus.ACTIVE.value,
            is_active=True
        )

    def test_student_provisioning_adr009_credentials(self):
        """
        Per ADR-009:
        - Username = Enrollment Number
        - Initial Password = Enrollment Number
        - must_change_password = True
        - Status = ACTIVE
        """
        enrollment_num = "EN2026CSE001"
        user, created = StudentAccountProvisioningService.provision_student_account(
            enrollment_number=enrollment_num,
            email="en2026cse001@college.edu"
        )

        self.assertTrue(created)
        self.assertEqual(user.username, enrollment_num)
        self.assertEqual(user.email, "en2026cse001@college.edu")
        self.assertTrue(user.must_change_password)
        self.assertEqual(user.status, UserStatus.ACTIVE.value)
        self.assertTrue(user.is_active)

        # Verify password matches the enrollment number per ADR-009
        self.assertTrue(user.check_password(enrollment_num))

    def test_provisioned_student_receives_student_role(self):
        """
        Verifies that a newly provisioned student automatically receives
        the canonical STUDENT role with scope OWN.
        """
        enrollment_num = "EN2026ME042"
        user, _ = StudentAccountProvisioningService.provision_student_account(
            enrollment_number=enrollment_num
        )

        student_role = Role.objects.get(name="STUDENT")
        self.assertEqual(student_role.scope_type, RoleScopeType.OWN.value)

        user_role = UserRole.objects.filter(user=user, role=student_role).first()
        self.assertIsNotNone(user_role)
        self.assertEqual(user_role.role.name, "STUDENT")

        # Verify student possesses own record permission
        perms = RoleService.get_user_permissions(user)
        self.assertIn("students.view_own_record", perms)

    def test_student_provisioning_idempotency(self):
        """
        Ensures repeated provisioning of the same enrollment number
        is safe, idempotent, and returns (user, created=False) without duplicating records.
        """
        enrollment_num = "EN2026ECE099"
        user1, created1 = StudentAccountProvisioningService.provision_student_account(
            enrollment_number=enrollment_num
        )
        self.assertTrue(created1)

        user2, created2 = StudentAccountProvisioningService.provision_student_account(
            enrollment_number=enrollment_num
        )
        self.assertFalse(created2)
        self.assertEqual(user1.id, user2.id)
        self.assertEqual(User.objects.filter(username=enrollment_num).count(), 1)

    def test_provisioned_student_authentication_and_jwt_claims(self):
        """
        Verifies that the provisioned student can immediately authenticate
        using their enrollment number as both username and password,
        and the issued JWT includes must_change_password=True.
        """
        enrollment_num = "EN2026EE105"
        StudentAccountProvisioningService.provision_student_account(
            enrollment_number=enrollment_num
        )

        tokens = AuthService.authenticate_and_issue_tokens(
            username=enrollment_num,
            password=enrollment_num
        )

        self.assertIn('access', tokens)
        self.assertIn('refresh', tokens)
        self.assertTrue(tokens['user']['must_change_password'])
        self.assertEqual(tokens['user']['username'], enrollment_num)

    def test_provisioning_policy_validation(self):
        """
        Validates that empty or blank enrollment numbers are rejected.
        """
        with self.assertRaises(InvariantViolationError):
            StudentAccountProvisioningService.provision_student_account(
                enrollment_number=""
            )

        with self.assertRaises(InvariantViolationError):
            StudentAccountProvisioningService.provision_student_account(
                enrollment_number="   "
            )

    def test_custom_provisioning_policy_pluggability(self):
        """
        Verifies that future activation policies (e.g. OTP activation)
        can be injected without modifying the core service.
        """
        class MockOTPPolicy(StudentProvisioningPolicy):
            def generate_credentials(self, enrollment_number):
                return f"student_{enrollment_number.lower()}", "TemporarySecurePass#99", True

        custom_policy = MockOTPPolicy()
        user, created = StudentAccountProvisioningService.provision_student_account(
            enrollment_number="EN2026CIVIL01",
            policy=custom_policy
        )

        self.assertTrue(created)
        self.assertEqual(user.username, "student_en2026civil01")
        self.assertTrue(user.check_password("TemporarySecurePass#99"))

    def test_bulk_provisioning_service(self):
        """
        Verifies bulk student provisioning with mixed new, existing, and invalid records.
        """
        records = [
            {"enrollment_number": "EN_BULK_01", "email": "bulk1@college.edu"},
            {"enrollment_number": "EN_BULK_02", "email": "bulk2@college.edu"},
            {"enrollment_number": "", "email": "invalid@college.edu"},  # Invalid
        ]

        result = StudentAccountProvisioningService.bulk_provision_student_accounts(records)

        self.assertEqual(result["total"], 3)
        self.assertEqual(result["created_count"], 2)
        self.assertEqual(result["existing_count"], 0)
        self.assertEqual(result["failed_count"], 1)

        # Run again to test existing detection
        second_result = StudentAccountProvisioningService.bulk_provision_student_accounts(records[:2])
        self.assertEqual(second_result["created_count"], 0)
        self.assertEqual(second_result["existing_count"], 2)

    def test_api_provision_student_authorized(self):
        """
        POST /api/v1/auth/users/provision-student/
        Succeeds with 201 Created for actor with identity.manage_users permission.
        """
        url = reverse('user-provision-student')
        data = {
            "enrollment_number": "EN_API_2026_01",
            "email": "api_student1@college.edu"
        }

        request = self.factory.post(url, data, format='json')
        force_authenticate(request, user=self.admin_user)
        response = ProvisionStudentView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "EN_API_2026_01")
        self.assertTrue(response.data["must_change_password"])
        self.assertTrue(response.data["created"])

        # Repeat call returns 200 OK with created=False
        request2 = self.factory.post(url, data, format='json')
        force_authenticate(request2, user=self.admin_user)
        response2 = ProvisionStudentView.as_view()(request2)

        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertFalse(response2.data["created"])

    def test_api_provision_student_forbidden_for_unauthorized_user(self):
        """
        Non-admin user without identity.manage_users receives 403 Forbidden.
        """
        url = reverse('user-provision-student')
        data = {"enrollment_number": "EN_FORBIDDEN_01"}

        request = self.factory.post(url, data, format='json')
        force_authenticate(request, user=self.regular_user)
        response = ProvisionStudentView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_bulk_provision_student(self):
        """
        POST /api/v1/auth/users/provision-student/bulk/
        Bulk provisions student accounts via API.
        """
        url = reverse('user-provision-student-bulk')
        data = {
            "students": [
                {"enrollment_number": "EN_API_BULK_A"},
                {"enrollment_number": "EN_API_BULK_B"}
            ]
        }

        request = self.factory.post(url, data, format='json')
        force_authenticate(request, user=self.admin_user)
        response = BulkProvisionStudentView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 2)
        self.assertEqual(response.data["created_count"], 2)
        self.assertEqual(response.data["failed_count"], 0)
