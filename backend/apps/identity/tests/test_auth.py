import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import UntypedToken
from apps.identity.services.user_service import UserService
from apps.identity.services.auth_service import AuthService
from apps.identity.domain.exceptions import (
    AuthenticationFailedError,
    AccountSuspendedError,
    AccountInactiveError,
)

User = get_user_model()


class AuthenticationServiceTests(TestCase):
    """
    Unit tests for AuthService application service.
    """

    def setUp(self):
        self.user = UserService.create_user(
            username="STU2026_01",
            password="SecurePassword123!",
            email="stu2026_01@college.edu",
            must_change_password=True
        )

    def test_authenticate_success(self):
        result = AuthService.authenticate_and_issue_tokens("STU2026_01", "SecurePassword123!")
        self.assertIn('access', result)
        self.assertIn('refresh', result)
        self.assertEqual(result['user']['username'], "STU2026_01")
        self.assertTrue(result['user']['must_change_password'])
        self.assertIsNotNone(result['user']['last_login'])

        # Decode token payload and verify claims
        decoded = UntypedToken(result['access'])
        self.assertEqual(decoded['user_id'], str(self.user.id))
        self.assertEqual(decoded['username'], "STU2026_01")
        self.assertTrue(decoded['must_change_password'])

    def test_authenticate_invalid_password(self):
        with self.assertRaises(AuthenticationFailedError):
            AuthService.authenticate_and_issue_tokens("STU2026_01", "WrongPassword!")

    def test_authenticate_nonexistent_user(self):
        with self.assertRaises(AuthenticationFailedError):
            AuthService.authenticate_and_issue_tokens("NONEXISTENT_USER", "SomePassword123!")

    def test_authenticate_suspended_user(self):
        UserService.suspend_user(self.user.id, reason="Conduct issue")
        with self.assertRaises(AccountSuspendedError):
            AuthService.authenticate_and_issue_tokens("STU2026_01", "SecurePassword123!")

    def test_authenticate_inactive_user(self):
        UserService.deactivate_user(self.user.id, reason="Withdrawn")
        with self.assertRaises(AccountInactiveError):
            AuthService.authenticate_and_issue_tokens("STU2026_01", "SecurePassword123!")

    def test_token_refresh(self):
        token_data = AuthService.authenticate_and_issue_tokens("STU2026_01", "SecurePassword123!")
        refreshed = AuthService.refresh_access_token(token_data['refresh'])
        self.assertIn('access', refreshed)
        self.assertIsNotNone(refreshed['access'])


class AuthenticationAPITests(TestCase):
    """
    Integration tests for Login, Token Refresh, and Protected Me endpoints.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = UserService.create_user(
            username="STU2026_02",
            password="SecurePassword123!",
            email="stu2026_02@college.edu",
            must_change_password=True
        )

    def test_api_login_success(self):
        response = self.client.post('/api/v1/auth/login/', {
            'username': 'STU2026_02',
            'password': 'SecurePassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['username'], 'STU2026_02')
        self.assertTrue(response.data['user']['must_change_password'])

    def test_api_login_invalid_password(self):
        response = self.client.post('/api/v1/auth/login/', {
            'username': 'STU2026_02',
            'password': 'WrongPassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['code'], 'INVALID_CREDENTIALS')

    def test_api_login_nonexistent_user(self):
        response = self.client.post('/api/v1/auth/login/', {
            'username': 'DOES_NOT_EXIST',
            'password': 'SomePassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['code'], 'INVALID_CREDENTIALS')

    def test_api_login_suspended_user(self):
        UserService.suspend_user(self.user.id, reason="Hold placed")
        response = self.client.post('/api/v1/auth/login/', {
            'username': 'STU2026_02',
            'password': 'SecurePassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['code'], 'ACCOUNT_SUSPENDED')

    def test_api_token_refresh(self):
        login_resp = self.client.post('/api/v1/auth/login/', {
            'username': 'STU2026_02',
            'password': 'SecurePassword123!'
        })
        refresh_token = login_resp.data['refresh']

        refresh_resp = self.client.post('/api/v1/auth/token/refresh/', {
            'refresh': refresh_token
        })
        self.assertEqual(refresh_resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_resp.data)

    def test_api_me_authenticated(self):
        login_resp = self.client.post('/api/v1/auth/login/', {
            'username': 'STU2026_02',
            'password': 'SecurePassword123!'
        })
        access_token = login_resp.data['access']

        # Request /me with Bearer token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        me_resp = self.client.get('/api/v1/auth/me/')
        self.assertEqual(me_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(me_resp.data['username'], 'STU2026_02')
        self.assertEqual(me_resp.data['email'], 'stu2026_02@college.edu')

    def test_api_me_unauthenticated(self):
        # Request /me without token
        self.client.credentials()
        me_resp = self.client.get('/api/v1/auth/me/')
        self.assertEqual(me_resp.status_code, status.HTTP_401_UNAUTHORIZED)
