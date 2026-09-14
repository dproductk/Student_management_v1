from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.students.models import Student
from apps.services.models import ServiceRequestType, ServiceRequest
from apps.services.services.request_service import ServiceRequestService

User = get_user_model()


class ServiceFrameworkTestCase(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="registrar_staff", email="staff@clg.edu", password="pass")
        self.student = Student.objects.create(
            candidate_name="Meera Kapoor",
            gender="FEMALE",
            date_of_birth=date(2005, 7, 12),
            enrollment_no="ENR2024777",
            application_id="APP2024777",
            email="meera@student.edu"
        )

    def test_service_type_and_reusable_foundation_vertical_slice(self):
        """13.1.1: Service type catalog and reusable request model foundation."""
        # 1. Create a service type
        st = ServiceRequestType.objects.create(
            name="Bonafide Certificate",
            code="BONAFIDE",
            description="Official certificate confirming student current enrollment",
            requires_document=False,
            is_active=True
        )
        self.assertEqual(st.code, "BONAFIDE")
        self.assertTrue(st.is_active)

        # 2. Reusable service request submission
        req = ServiceRequestService.submit_request(
            student=self.student,
            service_type=st,
            request_data={'purpose': 'Passport Application', 'copies': 2},
            priority='HIGH',
            actor=self.staff
        )

        self.assertIsNotNone(req.id)
        self.assertTrue(req.request_number.startswith("SR-"))
        self.assertEqual(req.student, self.student)
        self.assertEqual(req.service_type, st)
        self.assertEqual(req.status, 'SUBMITTED')
        self.assertEqual(req.priority, 'HIGH')
        self.assertEqual(req.request_data['purpose'], 'Passport Application')
        self.assertEqual(req.request_data['copies'], 2)
