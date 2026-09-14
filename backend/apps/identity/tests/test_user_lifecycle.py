import uuid
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from common.exceptions import InvariantViolationError, StateTransitionError, EntityNotFoundError
from apps.identity.domain.state_machines import UserStatus, UserLifecycleStateMachine
from apps.identity.services.user_service import UserService

User = get_user_model()


class UserModelAndDomainTests(TestCase):
    """
    Tests for User model constraints, password hashing, and domain lifecycle rules.
    """

    def test_create_user_success(self):
        user = UserService.create_user(
            username="ENR2026001",
            password="InitialPassword123!",
            email="student@college.edu"
        )
        self.assertIsNotNone(user.id)
        self.assertEqual(user.username, "ENR2026001")
        self.assertEqual(user.email, "student@college.edu")
        self.assertTrue(user.is_active)
        self.assertTrue(user.must_change_password)
        self.assertEqual(user.status, UserStatus.ACTIVE.value)
        # Password must be hashed, not plaintext
        self.assertNotEqual(user.password, "InitialPassword123!")
        self.assertTrue(user.check_password("InitialPassword123!"))

    def test_duplicate_username_rejected(self):
        UserService.create_user(username="ENR2026002", password="Password123!")
        with self.assertRaises(InvariantViolationError):
            UserService.create_user(username="ENR2026002", password="AnotherPassword123!")

    def test_short_password_rejected(self):
        with self.assertRaises(InvariantViolationError):
            UserService.create_user(username="ENR2026003", password="short")

    def test_empty_username_rejected(self):
        with self.assertRaises(InvariantViolationError):
            UserService.create_user(username="   ", password="Password123!")

    def test_user_suspension_lifecycle(self):
        user = UserService.create_user(username="ENR2026004", password="Password123!")
        suspended_user = UserService.suspend_user(user.id, reason="Administrative review")
        self.assertEqual(suspended_user.status, UserStatus.SUSPENDED.value)
        self.assertFalse(suspended_user.is_active)

        # Reactivate
        reactivated_user = UserService.reactivate_user(user.id)
        self.assertEqual(reactivated_user.status, UserStatus.ACTIVE.value)
        self.assertTrue(reactivated_user.is_active)

    def test_user_deactivation_is_terminal(self):
        user = UserService.create_user(username="ENR2026005", password="Password123!")
        deactivated_user = UserService.deactivate_user(user.id, reason="Graduated and archived")
        self.assertEqual(deactivated_user.status, UserStatus.INACTIVE.value)
        self.assertFalse(deactivated_user.is_active)

        # Attempting to reactivate from INACTIVE must fail
        with self.assertRaises(StateTransitionError):
            UserService.reactivate_user(user.id)

    def test_password_change_clears_must_change_flag(self):
        user = UserService.create_user(username="ENR2026006", password="InitialPassword123!", must_change_password=True)
        self.assertTrue(user.must_change_password)

        updated_user = UserService.set_user_password(user.id, "NewSecurePassword456!")
        self.assertFalse(updated_user.must_change_password)
        self.assertTrue(updated_user.check_password("NewSecurePassword456!"))


class UserLifecycleAPITests(TestCase):
    """
    Tests for User lifecycle REST endpoints.
    """

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username="admin_user",
            password="AdminPassword123!",
            email="admin@college.edu"
        )
        self.client.force_authenticate(user=self.admin)

    def test_create_user_endpoint(self):
        response = self.client.post('/api/v1/auth/users/create/', {
            'username': 'STU99001',
            'password': 'StrongPassword123!',
            'email': 'stu99001@college.edu'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'STU99001')
        self.assertTrue(response.data['must_change_password'])
        self.assertNotIn('password', response.data)
        self.assertNotIn('password_hash', response.data)

    def test_suspend_and_reactivate_endpoints(self):
        user = UserService.create_user(username="STU99002", password="Password123!")

        # Suspend
        suspend_resp = self.client.post(f'/api/v1/auth/users/{user.id}/suspend/', {'reason': 'Fees overdue'})
        self.assertEqual(suspend_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(suspend_resp.data['status'], 'SUSPENDED')
        self.assertFalse(suspend_resp.data['is_active'])

        # Reactivate
        reactivate_resp = self.client.post(f'/api/v1/auth/users/{user.id}/reactivate/')
        self.assertEqual(reactivate_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(reactivate_resp.data['status'], 'ACTIVE')
        self.assertTrue(reactivate_resp.data['is_active'])

    def test_deactivate_endpoint(self):
        user = UserService.create_user(username="STU99003", password="Password123!")
        deactivate_resp = self.client.post(f'/api/v1/auth/users/{user.id}/deactivate/', {'reason': 'Left college'})
        self.assertEqual(deactivate_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(deactivate_resp.data['status'], 'INACTIVE')
