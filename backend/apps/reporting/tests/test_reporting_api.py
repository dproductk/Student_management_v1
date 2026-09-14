"""
Integration tests for Reporting & Analytics API endpoints.
"""
from datetime import date
from django.test import TestCase
from rest_framework.test import APIClient
from apps.identity.models import User
from apps.students.models import Student


class ReportingAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="reporting_user", email="rep@test.com", password="pass")
        self.client.force_authenticate(user=self.user)

        self.student = Student.objects.create(
            candidate_name="API Rep Student",
            gender="FEMALE",
            date_of_birth=date(2005, 3, 3),
            enrollment_no="ENR_API_REP_01",
            application_id="APP_API_REP_01",
            status="ACTIVE"
        )

    def test_unauthenticated_access_rejected(self):
        """Validates that anonymous requests are rejected."""
        unauth_client = APIClient()
        response = unauth_client.get('/api/v1/reporting/analytics/kpis/')
        self.assertEqual(response.status_code, 401)

    def test_executive_kpi_endpoint(self):
        """GET /api/v1/reporting/analytics/kpis/"""
        response = self.client.get('/api/v1/reporting/analytics/kpis/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_students', response.data)
        self.assertEqual(response.data['total_students'], 1)

    def test_population_analytics_endpoint(self):
        """GET /api/v1/reporting/analytics/population/"""
        response = self.client.get('/api/v1/reporting/analytics/population/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_students', response.data)

    def test_demographics_endpoint(self):
        """GET /api/v1/reporting/analytics/demographics/"""
        response = self.client.get('/api/v1/reporting/analytics/demographics/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('by_gender', response.data)

    def test_fees_endpoint(self):
        """GET /api/v1/reporting/analytics/fees/"""
        response = self.client.get('/api/v1/reporting/analytics/fees/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('summary', response.data)

    def test_academic_endpoint(self):
        """GET /api/v1/reporting/analytics/academic/"""
        response = self.client.get('/api/v1/reporting/analytics/academic/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('performance', response.data)

    def test_verification_endpoint(self):
        """GET /api/v1/reporting/analytics/verification/"""
        response = self.client.get('/api/v1/reporting/analytics/verification/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_requests', response.data)

    def test_activity_endpoint(self):
        """GET /api/v1/reporting/analytics/activity/"""
        response = self.client.get('/api/v1/reporting/analytics/activity/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_audit_events', response.data)

    def test_export_endpoint(self):
        """GET /api/v1/reporting/export/?type=students&limit=5"""
        response = self.client.get('/api/v1/reporting/export/?type=students&limit=5')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('API Rep Student', response.content.decode('utf-8'))
