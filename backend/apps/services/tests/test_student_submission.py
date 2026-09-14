from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.students.models import Student
from apps.services.models import ServiceRequestType, ServiceRequest
from apps.services.services.request_service import ServiceRequestService
from apps.services.domain.invariants import ServiceValidationError

User = get_user_model()


class StudentSubmissionTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="student1", email="s1@test.com", password="pass")
        self.user2 = User.objects.create_user(username="student2", email="s2@test.com", password="pass")

        self.student1 = Student.objects.create(
            candidate_name="Student One",
            gender="MALE",
            date_of_birth=date(2005, 1, 1),
            enrollment_no="ENR_SUB_01",
            application_id="APP_SUB_01"
        )
        self.student2 = Student.objects.create(
            candidate_name="Student Two",
            gender="FEMALE",
            date_of_birth=date(2005, 2, 2),
            enrollment_no="ENR_SUB_02",
            application_id="APP_SUB_02"
        )

        self.st_active = ServiceRequestType.objects.create(
            name="Official Transcript",
            code="TRANSCRIPT",
            is_active=True
        )
        self.st_inactive = ServiceRequestType.objects.create(
            name="Archived Service",
            code="ARCHIVED_SVC",
            is_active=False
        )

    def test_student_submission_and_status_vertical_slice(self):
        """13.1.2: Student submits service request and checks status."""
        req = ServiceRequestService.submit_request(
            student=self.student1,
            service_type=self.st_active,
            request_data={'destination': 'Foreign University', 'sealed_envelope': True},
            actor=self.user1
        )

        self.assertEqual(req.status, 'SUBMITTED')
        self.assertEqual(req.student, self.student1)
        self.assertTrue(req.request_number.startswith("SR-"))

        # Inactive service type rejection
        with self.assertRaises(ServiceValidationError):
            ServiceRequestService.submit_request(
                student=self.student1,
                service_type=self.st_inactive,
                actor=self.user1
            )

    def test_student_request_isolation(self):
        """13.1.2: Scoping ensures students can only see their own requests."""
        req1 = ServiceRequestService.submit_request(
            student=self.student1, service_type=self.st_active, actor=self.user1
        )
        req2 = ServiceRequestService.submit_request(
            student=self.student2, service_type=self.st_active, actor=self.user2
        )

        # Query filtered by student
        s1_requests = ServiceRequest.objects.filter(student=self.student1)
        self.assertIn(req1, s1_requests)
        self.assertNotIn(req2, s1_requests)

        s2_requests = ServiceRequest.objects.filter(student=self.student2)
        self.assertIn(req2, s2_requests)
        self.assertNotIn(req1, s2_requests)
