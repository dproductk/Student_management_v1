"""
Unit tests for Reporting Analytics Aggregator Service (Tasks 14.2.1 through 14.2.6).
"""
from datetime import date
from django.test import TestCase
from apps.students.models import Student
from apps.verification.models import VerificationRequest
from apps.audit.models import AuditLog
from apps.identity.models import User
from apps.reporting.services.analytics_service import ReportingAnalyticsService


class AnalyticsServicesTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="analytics_officer", email="ao@test.com", password="pass")
        self.student = Student.objects.create(
            candidate_name="Analytics Student",
            gender="FEMALE",
            date_of_birth=date(2005, 1, 1),
            enrollment_no="ENR_AN_01",
            application_id="APP_AN_01",
            status="ACTIVE"
        )

        VerificationRequest.objects.create(
            student=self.student,
            entity_type='PERSONAL_INFO',
            submitted_by=self.user,
            status='APPROVED'
        )

        AuditLog.objects.create(
            actor=self.user,
            action='LOGIN_SUCCESS',
            target_type='USER',
            target_id=self.user.id,
            module='identity'
        )

    def test_executive_kpis(self):
        """Validates executive KPI aggregation."""
        kpis = ReportingAnalyticsService.get_executive_kpis()
        self.assertIn('total_students', kpis)
        self.assertIn('collection_percentage', kpis)
        self.assertIn('academic_pass_percentage', kpis)
        self.assertIn('verification_approval_rate', kpis)
        self.assertEqual(kpis['total_students'], 1)
        self.assertEqual(kpis['verification_approval_rate'], 100.0)

    def test_verification_analytics(self):
        """14.2.3: Verification analytics."""
        res = ReportingAnalyticsService.get_verification_analytics()
        self.assertEqual(res['total_requests'], 1)
        self.assertEqual(res['approved_count'], 1)
        self.assertEqual(res['approval_rate'], 100.0)

    def test_user_activity_analytics(self):
        """14.2.6: Administrative/user activity analytics."""
        act = ReportingAnalyticsService.get_user_activity_analytics()
        self.assertEqual(act['total_audit_events'], 1)
        self.assertEqual(act['events_by_module'][0]['module'], 'identity')
        self.assertEqual(act['events_by_action'][0]['action'], 'LOGIN_SUCCESS')
