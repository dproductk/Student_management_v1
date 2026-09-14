from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.identity.services.user_service import UserService
from apps.identity.services.auth_service import AuthService

User = get_user_model()


class LogoutAndFailureHandlingTests(TestCase):
    """
    Automated tests for Logout, Token Invalidation/Blacklisting, and Authentication Failure Handling.
    Governed by identity-and-access-prd.md Requirements 6 & 7.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = UserService.create_user(
            username="LOGOUT_TEST_01",
            password="SecurePassword123!",
            email="logout_test_01@college.edu"
        )
        tokens = AuthService.authenticate_and_issue_tokens("LOGOUT_TEST_01", "SecurePassword123!")
        self.access_token = tokens['access']
        self.refresh_token = tokens['refresh']

    def test_logout_success(self):
        """
        Logging out with a valid refresh token must succeed and revoke the refresh token.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post('/api/v1/auth/logout/', {
            'refresh': self.refresh_token
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

        # Attempting to refresh with the blacklisted token must fail with 401
        refresh_resp = self.client.post('/api/v1/auth/token/refresh/', {
            'refresh': self.refresh_token
        })
        self.assertEqual(refresh_resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(refresh_resp.data['code'], 'INVALID_OR_EXPIRED_TOKEN')

    def test_blacklisted_token_cannot_be_logged_out_again(self):
        """
        Attempting to logout with an already revoked/blacklisted token must be rejected.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        # First logout
        self.client.post('/api/v1/auth/logout/', {'refresh': self.refresh_token})

        # Second logout with same refresh token
        second_resp = self.client.post('/api/v1/auth/logout/', {'refresh': self.refresh_token})
        self.assertEqual(second_resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_without_refresh_token(self):
        """
        Missing refresh token field must be rejected with 400.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post('/api/v1/auth/logout/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_unauthenticated(self):
        """
        Calling logout without authentication header must return 401.
        """
        self.client.credentials()  # Clear auth
        response = self.client.post('/api/v1/auth/logout/', {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['code'], 'NOT_AUTHENTICATED')

    def test_malformed_token_header_failure_handling(self):
        """
        Sending a malformed token header must return standardized 401 without exposing internal details.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Bearer this_is_a_garbage_token_12345')
        response = self.client.get('/api/v1/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['code'], 'INVALID_OR_EXPIRED_TOKEN')
        self.assertIn('error', response.data)

    def test_tampered_token_signature_handling(self):
        """
        A tampered token must fail signature verification and return standardized 401.
        """
        tampered_token = self.access_token[:-10] + 'abcdefghij'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tampered_token}')
        response = self.client.get('/api/v1/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['code'], 'INVALID_OR_EXPIRED_TOKEN')
