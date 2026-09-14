"""
API integration tests for Verification endpoints.
"""

from datetime import date
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.identity.models import User
from apps.students.models import Student
from apps.verification.models import VerificationRequest, VerificationDecision


class VerificationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="verif_api_admin",
            password="Password@123",
            email="verif_admin@edvana.edu",
            is_staff=True
        )
        self.client.force_authenticate(user=self.admin)

        self.student = Student.objects.create(
            candidate_name="Deepak Joshi",
            gender="MALE",
            date_of_birth=date(2005, 4, 18),
            application_id="APP-API-VERIF",
            enrollment_no="ENR-API-VERIF",
            student_mobile="9800000000"
        )

    def test_api_submit_verification_request(self):
        resp = self.client.post(
            "/api/v1/verification/requests/submit/",
            {
                "student_id": str(self.student.id),
                "entity_type": "PERSONAL_INFO",
                "field_name": "student_mobile",
                "submitted_value": "9811111111"
            },
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["status"], "PENDING")
        self.assertEqual(resp.data["current_version"], 1)
        self.assertEqual(resp.data["submitted_value"], "9811111111")

    def test_api_decide_and_resubmit_verification_request(self):
        # 1. Submit
        sub_resp = self.client.post(
            "/api/v1/verification/requests/submit/",
            {
                "student_id": str(self.student.id),
                "entity_type": "PERSONAL_INFO",
                "field_name": "student_mobile",
                "submitted_value": "9811111111"
            },
            format='json'
        )
        req_id = sub_resp.data["id"]

        # 2. Reject / Request correction
        dec_resp = self.client.post(
            f"/api/v1/verification/requests/{req_id}/decide/",
            {
                "decision": "NEEDS_CORRECTION",
                "rejection_reason": "Number does not match admission form"
            },
            format='json'
        )
        self.assertEqual(dec_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(dec_resp.data["status"], "NEEDS_CORRECTION")
        self.assertEqual(len(dec_resp.data["decisions"]), 1)

        # 3. Resubmit
        resub_resp = self.client.post(
            f"/api/v1/verification/requests/{req_id}/resubmit/",
            {"new_submitted_value": "9822222222"},
            format='json'
        )
        self.assertEqual(resub_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resub_resp.data["status"], "PENDING")
        self.assertEqual(resub_resp.data["current_version"], 2)
        self.assertEqual(resub_resp.data["submitted_value"], "9822222222")

        # 4. Approve
        appr_resp = self.client.post(
            f"/api/v1/verification/requests/{req_id}/decide/",
            {
                "decision": "APPROVED",
                "notes": "Verified against affidavit"
            },
            format='json'
        )
        self.assertEqual(appr_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(appr_resp.data["status"], "APPROVED")

        # Student record updated
        self.student.refresh_from_db()
        self.assertEqual(self.student.student_mobile, "9822222222")
