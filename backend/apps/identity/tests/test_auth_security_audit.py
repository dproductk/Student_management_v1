"""
Cross-Cutting Authentication and Authorization Security Audit Test Suite.
Governed by TASKS.md 15.1.1, production-hardening-prd.md R-001, and ADR-002/006.
"""

from rest_framework.test import APITestCase
from rest_framework import status
from apps.identity.models import User, Role, UserRole
from rest_framework_simplejwt.tokens import RefreshToken


class CrossCuttingAuthSecurityAuditTests(APITestCase):
    """
    Audits all protected application endpoints across bounded contexts
    to ensure strict authentication and role-based access control.
    """

    def setUp(self):
        # Create a basic student user with only the Student role
        self.student_role, _ = Role.objects.get_or_create(
            name='Student',
            defaults={'description': 'Standard student role'}
        )
        self.student_user = User.objects.create_user(
            username='STU_AUDIT_001',
            email='student_audit@example.com',
            password='TestPassword123!',
            is_active=True
        )
        UserRole.objects.get_or_create(
            user=self.student_user,
            role=self.student_role,
            defaults={'assigned_by': self.student_user}
        )

        # Generate JWT tokens for student
        self.refresh = RefreshToken.for_user(self.student_user)
        self.access_token = str(self.refresh.access_token)

    def test_unauthenticated_requests_strictly_denied_401(self):
        """Verify unauthenticated requests across all major endpoints are rejected with HTTP 401."""
        endpoints = [
            ('/api/v1/students/', 'get'),
            ('/api/v1/academic/departments/', 'get'),
            ('/api/v1/finance/accounts/', 'get'),
            ('/api/v1/finance/charges/', 'get'),
            ('/api/v1/finance/record-payment/', 'post'),
            ('/api/v1/results/batches/', 'get'),
            ('/api/v1/results/records/', 'get'),
            ('/api/v1/verification/requests/', 'get'),
            ('/api/v1/reporting/analytics/kpis/', 'get'),
            ('/api/v1/reporting/export/', 'post'),
            ('/api/v1/services/requests/', 'get'),
            ('/api/v1/auth/audit/', 'get'),
            ('/api/v1/faculty/', 'get'),
            ('/api/v1/documents/', 'get'),
            ('/api/v1/onboarding/batches/', 'get'),
            ('/api/v1/register/students/', 'get'),
        ]

        # Ensure no credentials
        self.client.credentials()

        for url, method in endpoints:
            with self.subTest(endpoint=url, method=method):
                if method == 'get':
                    response = self.client.get(url)
                else:
                    response = self.client.post(url, {})

                self.assertEqual(
                    response.status_code,
                    status.HTTP_401_UNAUTHORIZED,
                    f"Expected 401 for unauthenticated access to {url}, got {response.status_code}"
                )
                self.assertIn('error', response.data)

    def test_student_role_forbidden_from_administrative_endpoints_403(self):
        """Verify student role without administrative permissions receives 403 Forbidden."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        admin_restricted_endpoints = [
            ('/api/v1/auth/users/', 'get', None),
            ('/api/v1/auth/users/create/', 'post', {}),
            ('/api/v1/auth/roles/', 'post', {'name': 'UnauthorizedRole', 'scope_type': 'SYSTEM'}),
            ('/api/v1/auth/permissions/', 'post', {'codename': 'unauthorized.perm', 'module': 'identity'}),
            ('/api/v1/auth/audit/', 'get', None),
            ('/api/v1/auth/users/provision-student/', 'post', {}),
        ]

        for item in admin_restricted_endpoints:
            url = item[0]
            method = item[1]
            payload = item[2]
            with self.subTest(endpoint=url, method=method):
                if method == 'get':
                    response = self.client.get(url)
                else:
                    response = self.client.post(url, payload)

                self.assertEqual(
                    response.status_code,
                    status.HTTP_403_FORBIDDEN,
                    f"Expected 403 Forbidden for student on {url}, got {response.status_code}"
                )

    def test_blacklisted_token_strictly_rejected(self):
        """Verify that blacklisting a refresh token prevents token renewal."""
        refresh_token_str = str(self.refresh)
        
        # Blacklist the refresh token
        self.refresh.blacklist()

        # Attempt to refresh access token using blacklisted refresh token
        refresh_response = self.client.post('/api/v1/auth/token/refresh/', {
            'refresh': refresh_token_str
        })

        self.assertEqual(
            refresh_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Blacklisted refresh token must not be permitted to obtain new access tokens"
        )

    def test_malformed_token_header_rejected(self):
        """Verify invalid or malformed Authorization headers return 401."""
        malformed_headers = [
            'Bearer invalid_token_string_here',
            'Token invalid_prefix_format',
            'Bearer',
            'Basic dXNlcm5hbWU6cGFzc3dvcmQ=',
        ]

        for auth_hdr in malformed_headers:
            self.client.credentials(HTTP_AUTHORIZATION=auth_hdr)
            response = self.client.get('/api/v1/students/')
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                f"Header '{auth_hdr}' should have been rejected with 401"
            )
