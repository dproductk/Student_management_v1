"""
API Security, Input-Validation, Rate-Limiting, and Safe Error Handling Audit.
Governed by TASKS.md 15.1.3, production-hardening-prd.md R-003, R-004, and R-005.
"""

from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.exceptions import Throttled
from common.exception_handler import custom_exception_handler
from apps.identity.models import User


class APISecurityAuditTests(APITestCase):
    """
    Audits API security boundaries: rate limiting, security headers,
    input validation, and safe error exposure without traceback leakage.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="security_audit_user",
            email="security_audit@example.com",
            password="TestPassword123!",
            is_active=True
        )

    def test_security_headers_present_in_responses(self):
        """Verify standard security headers are enforced across HTTP responses."""
        response = self.client.get('/api/v1/auth/token/')
        # Even on 405 or 400, security middleware should inject headers
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('X-Frame-Options'), 'DENY')

    def test_throttling_exception_returns_standardized_json_429(self):
        """Verify throttled requests return 429 with REQUEST_THROTTLED code."""
        throttled_exc = Throttled(wait=42)
        response = custom_exception_handler(throttled_exc, {})

        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(response.data.get('code'), 'REQUEST_THROTTLED')
        self.assertIn('Expected available in 42 seconds', response.data.get('error'))
        self.assertEqual(response.data.get('available_in_seconds'), 42)

    def test_unhandled_server_error_masks_traceback_when_debug_false(self):
        """Verify unhandled 500 exceptions mask internal stack traces when DEBUG is False."""
        with override_settings(DEBUG=False):
            generic_server_exc = Exception("FATAL: Database connection leaked or unhandled syntax error!")
            response = custom_exception_handler(generic_server_exc, {})

            self.assertIsNotNone(response)
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(response.data.get('code'), 'INTERNAL_SERVER_ERROR')
            self.assertNotIn("FATAL", response.data.get('error'))
            self.assertNotIn("traceback", str(response.data).lower())

    def test_malformed_json_returns_clean_400_bad_request(self):
        """Verify sending malformed JSON payload returns clean 400 without crashing."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/v1/auth/change-password/',
            data='{"old_password": "broken JSON payload...',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_anonymous_rate_limiting_triggers_429(self):
        """Verify anonymous requests exceeding rate limits receive 429."""
        from django.core.cache import cache
        from rest_framework.throttling import AnonRateThrottle

        cache.clear()
        self.client.force_authenticate(user=None)
        self.client.credentials()  # Unauthenticated

        original_rate = getattr(AnonRateThrottle, 'rate', None)
        try:
            AnonRateThrottle.rate = '2/min'
            # Request 1 & 2 hit endpoint without being throttled
            self.client.post('/api/v1/auth/login/', {})
            self.client.post('/api/v1/auth/login/', {})

            # Request 3 should be throttled (429)
            res3 = self.client.post('/api/v1/auth/login/', {})
            self.assertEqual(res3.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
            self.assertEqual(res3.data.get('code'), 'REQUEST_THROTTLED')
        finally:
            AnonRateThrottle.rate = original_rate
