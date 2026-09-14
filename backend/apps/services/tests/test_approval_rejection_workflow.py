from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.students.models import Student
from apps.services.models import ServiceRequestType, ServiceRequest
from apps.services.services.request_service import ServiceRequestService
from apps.services.domain.invariants import (
    ServiceValidationError,
    InvalidServiceStateTransitionError,
)

User = get_user_model()


class ApprovalRejectionWorkflowTestCase(TestCase):
    def setUp(self):
        self.approver = User.objects.create_user(username="registrar_approver", email="appr@test.com", password="pass")
        self.student = Student.objects.create(
            candidate_name="Kavita Rao",
            gender="FEMALE",
            date_of_birth=date(2005, 5, 20),
            enrollment_no="ENR_APPR_01",
            application_id="APP_APPR_01"
        )
        self.st = ServiceRequestType.objects.create(
            name="Fee Concession Application",
            code="FEE_CONCESSION",
            is_active=True
        )

    def test_approve_and_complete_workflow(self):
        """13.1.4: Workflow from SUBMITTED -> IN_PROGRESS -> APPROVED -> COMPLETED."""
        req = ServiceRequestService.submit_request(student=self.student, service_type=self.st)
        ServiceRequestService.process_request(req, actor=self.approver)

        # Approve
        ServiceRequestService.approve_request(req, actor=self.approver, remarks="Eligible for 25% merit waiver")
        req.refresh_from_db()
        self.assertEqual(req.status, 'APPROVED')
        self.assertEqual(req.resolution_notes, "Eligible for 25% merit waiver")

        # Complete
        ServiceRequestService.complete_request(req, actor=self.approver, resolution_notes="Concession ledger adjustment applied")
        req.refresh_from_db()
        self.assertEqual(req.status, 'COMPLETED')
        self.assertEqual(req.resolution_notes, "Concession ledger adjustment applied")

        # Terminal state: cannot transition COMPLETED request further
        with self.assertRaises(InvalidServiceStateTransitionError):
            ServiceRequestService.approve_request(req, actor=self.approver)

    def test_reject_workflow_requires_reason(self):
        """13.1.4: Rejection requires non-empty mandatory justification and is terminal."""
        req = ServiceRequestService.submit_request(student=self.student, service_type=self.st)
        ServiceRequestService.process_request(req, actor=self.approver)

        # Empty reason must fail
        with self.assertRaises(ServiceValidationError):
            ServiceRequestService.reject_request(req, actor=self.approver, rejection_reason="")

        with self.assertRaises(ServiceValidationError):
            ServiceRequestService.reject_request(req, actor=self.approver, rejection_reason="   ")

        # Valid rejection
        ServiceRequestService.reject_request(req, actor=self.approver, rejection_reason="Income certificate does not meet threshold")
        req.refresh_from_db()
        self.assertEqual(req.status, 'REJECTED')
        self.assertEqual(req.rejection_reason, "Income certificate does not meet threshold")

        # Terminal state: cannot reopen
        with self.assertRaises(InvalidServiceStateTransitionError):
            ServiceRequestService.process_request(req, actor=self.approver)
