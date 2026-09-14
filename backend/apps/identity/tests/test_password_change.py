"""
Automated tests for Mandatory First-Login Password Change vertical slice.
Governed by ADR-009, ARCHITECTURE.md, and identity-and-access-prd.md.
"""

from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.urls import reverse

from common.exceptions import InvariantViolationError
from apps.identity.models import User
from apps.identity.domain.state_machines import UserStatus
from apps.identity.domain.exceptions import AuthenticationFailedError
from apps.identity.services.auth_service import AuthService
from apps.identity.services.role_service import RoleService
from apps.identity.services.provisioning import StudentAccountProvisioningService
from apps.identity.api.views import ChangePasswordView
from apps.identity.api.permissions import RequirePasswordChanged


class DummyProtectedOperationView(APIView):
    """
    Test endpoint protected by RequirePasswordChanged.
    """
    permission_classes = [IsAuthenticated, RequirePasswordChanged]

    def get(self, request):
        return Response({"status": "access_granted"})


class MandatoryPasswordChangeTests(APITestCase):
    """
    Unit and integration tests for mandatory first-login password change.
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        RoleService.seed_canonical_roles_and_permissions()

        # Provision a student account per ADR-009
        self.enrollment_number = "EN2026CS999"
        self.student_user, _ = StudentAccountProvisioningService.provision_student_account(
            enrollment_number=self.enrollment_number,
            email="student999@college.edu"
        )
        self.assertTrue(self.student_user.must_change_password)

    def test_first_login_password_change_success(self):
        """
        Tests successful first-login password change:
        - Updates password hash
        - Clears must_change_password flag
        - Returns fresh tokens with must_change_password=False
        - Old password no longer works
        """
        url = reverse('auth-change-password')
        data = {
            "current_password": self.enrollment_number,
            "new_password": "NewSecurePassword123!",
            "confirm_password": "NewSecurePassword123!"
        }

        request = self.factory.post(url, data, format='json')
        force_authenticate(request, user=self.student_user)
        response = ChangePasswordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['user']['must_change_password'])
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])

        # Reload student user from database
        self.student_user.refresh_from_db()
        self.assertFalse(self.student_user.must_change_password)
        self.assertTrue(self.student_user.check_password("NewSecurePassword123!"))
        self.assertFalse(self.student_user.check_password(self.enrollment_number))

    def test_change_password_invalid_current_password(self):
        """
        Rejects password change if current password does not match.
        """
        url = reverse('auth-change-password')
        data = {
            "current_password": "WrongCurrentPassword123!",
            "new_password": "NewSecurePassword123!",
            "confirm_password": "NewSecurePassword123!"
        }

        request = self.factory.post(url, data, format='json')
        force_authenticate(request, user=self.student_user)
        response = ChangePasswordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.student_user.refresh_from_db()
        self.assertTrue(self.student_user.must_change_password)
        self.assertTrue(self.student_user.check_password(self.enrollment_number))

    def test_change_password_retaining_current_password_rejected(self):
        """
        Per ADR-009, rejects attempting to reuse the same initial credential.
        """
        url = reverse('auth-change-password')
        data = {
            "current_password": self.enrollment_number,
            "new_password": self.enrollment_number,
            "confirm_password": self.enrollment_number
        }

        request = self.factory.post(url, data, format='json')
        force_authenticate(request, user=self.student_user)
        response = ChangePasswordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.student_user.refresh_from_db()
        self.assertTrue(self.student_user.must_change_password)

    def test_change_password_new_equals_username_rejected(self):
        """
        Rejects setting new password to username / enrollment number.
        """
        with self.assertRaises(InvariantViolationError):
            AuthService.change_password(
                user=self.student_user,
                current_password=self.enrollment_number,
                new_password=self.enrollment_number,
                confirm_password=self.enrollment_number
            )

    def test_change_password_confirmation_mismatch_rejected(self):
        """
        Rejects request when new password does not match confirmation.
        """
        url = reverse('auth-change-password')
        data = {
            "current_password": self.enrollment_number,
            "new_password": "Password123!",
            "confirm_password": "DifferentPassword123!"
        }

        request = self.factory.post(url, data, format='json')
        force_authenticate(request, user=self.student_user)
        response = ChangePasswordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_weak_password_rejected(self):
        """
        Rejects new password that is shorter than 8 characters.
        """
        url = reverse('auth-change-password')
        data = {
            "current_password": self.enrollment_number,
            "new_password": "short",
            "confirm_password": "short"
        }

        request = self.factory.post(url, data, format='json')
        force_authenticate(request, user=self.student_user)
        response = ChangePasswordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_require_password_changed_permission_enforcement(self):
        """
        Validates that RequirePasswordChanged blocks protected operations
        when must_change_password=True, and allows access once changed.
        """
        view = DummyProtectedOperationView.as_view()

        # Attempt to access protected operation before password change
        request = self.factory.get('/dummy-protected/')
        force_authenticate(request, user=self.student_user)
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Now change password
        AuthService.change_password(
            user=self.student_user,
            current_password=self.enrollment_number,
            new_password="BrandNewPassword123!",
            confirm_password="BrandNewPassword123!"
        )
        self.student_user.refresh_from_db()
        self.assertFalse(self.student_user.must_change_password)

        # Re-attempt access after password change
        request2 = self.factory.get('/dummy-protected/')
        force_authenticate(request2, user=self.student_user)
        response2 = view(request2)

        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data["status"], "access_granted")

    def test_unauthenticated_request_rejected(self):
        """
        Rejects unauthenticated requests to change-password endpoint.
        """
        url = reverse('auth-change-password')
        data = {
            "current_password": "AnyPassword",
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!"
        }

        request = self.factory.post(url, data, format='json')
        response = ChangePasswordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
