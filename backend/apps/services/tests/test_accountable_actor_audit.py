from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.students.models import Student
from apps.services.models import ServiceRequestType, ServiceRequest, ServiceRequestAudit
from apps.services.services.request_service import ServiceRequestService

User = get_user_model()


class AccountableActorAuditTestCase(TestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(username="student_audit", email="std@test.com", password="pass")
        self.clerk = User.objects.create_user(username="clerk_audit", email="clerk@test.com", password="pass")
        self.officer = User.objects.create_user(username="officer_audit", email="off@test.com", password="pass")

        self.student = Student.objects.create(
            candidate_name="Ananya Roy",
            gender="FEMALE",
            date_of_birth=date(2005, 6, 15),
            enrollment_no="ENR_AUD_01",
            application_id="APP_AUD_01"
        )
        self.st = ServiceRequestType.objects.create(
            name="Bonafide Certificate",
            code="BONAFIDE",
            is_active=True
        )

    def test_accountable_actor_audit_trail_vertical_slice(self):
        """13.2.2: Full audit trail of accountable actors and state transitions."""
        # 1. Submission audit
        req = ServiceRequestService.submit_request(
            student=self.student,
            service_type=self.st,
            actor=self.student_user
        )
        self.assertEqual(req.audits.count(), 1)
        a1 = req.audits.first()
        self.assertEqual(a1.actor, self.student_user)
        self.assertEqual(a1.action, 'SUBMITTED')
        self.assertIsNone(a1.previous_status)
        self.assertEqual(a1.new_status, 'SUBMITTED')

        # 2. Assignment audit
        ServiceRequestService.assign_request(req, assignee_user=self.clerk, actor=self.officer)
        self.assertEqual(req.audits.count(), 2)
        a2 = req.audits.all()[0] # newest first due to ordering -timestamp
        self.assertEqual(a2.action, 'ASSIGNED')
        self.assertEqual(a2.actor, self.officer)

        # 3. Processing audit
        ServiceRequestService.process_request(req, actor=self.clerk, notes="Reviewing enrollment status")
        self.assertEqual(req.audits.count(), 3)
        a3 = req.audits.all()[0]
        self.assertEqual(a3.action, 'IN_PROGRESS')
        self.assertEqual(a3.actor, self.clerk)
        self.assertEqual(a3.previous_status, 'SUBMITTED')
        self.assertEqual(a3.new_status, 'IN_PROGRESS')

        # 4. Approval audit
        ServiceRequestService.approve_request(req, actor=self.officer, remarks="Verified active enrollment")
        self.assertEqual(req.audits.count(), 4)
        a4 = req.audits.all()[0]
        self.assertEqual(a4.action, 'APPROVED')
        self.assertEqual(a4.actor, self.officer)

        # 5. Completion audit
        ServiceRequestService.complete_request(req, actor=self.clerk, resolution_notes="Certificate printed and delivered")
        self.assertEqual(req.audits.count(), 5)
        a5 = req.audits.all()[0]
        self.assertEqual(a5.action, 'COMPLETED')
        self.assertEqual(a5.actor, self.clerk)
        self.assertEqual(a5.previous_status, 'APPROVED')
        self.assertEqual(a5.new_status, 'COMPLETED')
        self.assertEqual(a5.reason, "Certificate printed and delivered")
