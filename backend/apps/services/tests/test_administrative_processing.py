from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.students.models import Student
from apps.services.models import ServiceRequestType, ServiceRequest
from apps.services.services.request_service import ServiceRequestService
from apps.services.domain.invariants import InvalidServiceStateTransitionError

User = get_user_model()


class AdministrativeProcessingTestCase(TestCase):
    def setUp(self):
        self.staff1 = User.objects.create_user(username="clerk_exam", email="clerk@test.com", password="pass")
        self.staff2 = User.objects.create_user(username="officer_exam", email="officer@test.com", password="pass")

        self.student = Student.objects.create(
            candidate_name="Deepak Sharma",
            gender="MALE",
            date_of_birth=date(2005, 3, 15),
            enrollment_no="ENR_ADMIN_01",
            application_id="APP_ADMIN_01"
        )
        self.st = ServiceRequestType.objects.create(
            name="ID Card Replacement",
            code="ID_CARD",
            is_active=True
        )

    def test_administrative_processing_vertical_slice(self):
        """13.1.3: Staff views queue, assigns handler, and starts processing."""
        # 1. Student submits request
        req = ServiceRequestService.submit_request(
            student=self.student,
            service_type=self.st,
            request_data={'reason': 'Lost in transit'}
        )
        self.assertEqual(req.status, 'SUBMITTED')

        # 2. Assign to handler staff2
        ServiceRequestService.assign_request(req, assignee_user=self.staff2, actor=self.staff1)
        req.refresh_from_db()
        self.assertEqual(req.assigned_to, self.staff2)

        # 3. Staff initiates processing -> IN_PROGRESS
        ServiceRequestService.process_request(req, actor=self.staff2, notes="Checking previous card records")
        req.refresh_from_db()
        self.assertEqual(req.status, 'IN_PROGRESS')
        self.assertEqual(req.processed_by, self.staff2)
        self.assertIsNotNone(req.processed_at)
        self.assertEqual(req.resolution_notes, "Checking previous card records")

    def test_invalid_lifecycle_transition_prevention(self):
        """13.1.3: Prevent illegal state transitions (e.g. SUBMITTED directly to COMPLETED)."""
        req = ServiceRequestService.submit_request(student=self.student, service_type=self.st)
        with self.assertRaises(InvalidServiceStateTransitionError):
            ServiceRequestService.complete_request(req, actor=self.staff1, resolution_notes="Illegal bypass")
