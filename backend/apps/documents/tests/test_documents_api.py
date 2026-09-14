"""
API integration tests for student document endpoints.
"""

from datetime import date
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from apps.identity.models import User
from apps.students.models import Student
from apps.documents.models import StudentDocument
from apps.documents.services.document_service import DocumentService
from apps.documents.services.storage_service import StorageService
from apps.audit.models import SensitiveDataAccessLog


class DocumentsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            username="doc_api_admin",
            password="Password@123",
            email="doc_admin@edvana.edu",
            is_staff=True
        )
        self.client.force_authenticate(user=self.staff_user)

        self.student = Student.objects.create(
            candidate_name="Ishaan Deshmukh",
            gender="MALE",
            date_of_birth=date(2004, 12, 5),
            application_id="APP-API-DOC",
            enrollment_no="ENR-API-DOC"
        )

    def tearDown(self):
        for d in StudentDocument.objects.all():
            StorageService.delete_document(d.storage_key)

    def test_api_upload_document(self):
        file_obj = SimpleUploadedFile("tenth.pdf", b"%PDF Tenth Marksheet Content", content_type="application/pdf")
        response = self.client.post(
            "/api/v1/documents/upload/",
            {
                "student_id": str(self.student.id),
                "document_type": "SSC_MARKSHEET",
                "file": file_obj
            },
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["version"], 1)
        self.assertEqual(response.data["version_status"], "CURRENT")
        self.assertFalse(response.data["is_sensitive"])
        self.assertIsNotNone(response.data["download_url"])

    def test_api_download_non_sensitive_document(self):
        file_obj = SimpleUploadedFile("photo.jpg", b"\xFF\xD8\xFFFakeJPEGData", content_type="image/jpeg")
        doc = DocumentService.upload_student_document(
            student=self.student,
            document_type="PHOTO",
            file_obj=file_obj,
            filename="photo.jpg",
            uploaded_by=self.staff_user
        )

        resp = self.client.get(f"/api/v1/documents/{doc.id}/download/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.getvalue(), b"\xFF\xD8\xFFFakeJPEGData")

    def test_api_direct_download_sensitive_document_blocked(self):
        file_obj = SimpleUploadedFile("passbook.pdf", b"Sensitive Bank Info", content_type="application/pdf")
        doc = DocumentService.upload_student_document(
            student=self.student,
            document_type="BANK_PASSBOOK",
            file_obj=file_obj,
            filename="passbook.pdf",
            uploaded_by=self.staff_user
        )

        # Attempt normal download
        resp = self.client.get(f"/api/v1/documents/{doc.id}/download/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Access restricted", resp.data["detail"])

    def test_api_reveal_sensitive_document_success(self):
        file_obj = SimpleUploadedFile("passbook.pdf", b"Sensitive Bank Info", content_type="application/pdf")
        doc = DocumentService.upload_student_document(
            student=self.student,
            document_type="BANK_PASSBOOK",
            file_obj=file_obj,
            filename="passbook.pdf",
            uploaded_by=self.staff_user
        )

        # Perform explicit reveal
        reveal_resp = self.client.post(
            f"/api/v1/documents/{doc.id}/reveal/",
            {"reason": "Auditing bank passbook for scholarship disbursement"},
            format='json'
        )
        self.assertEqual(reveal_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(reveal_resp.getvalue(), b"Sensitive Bank Info")

        # Verify SensitiveDataAccessLog recorded
        self.assertTrue(SensitiveDataAccessLog.objects.filter(
            student_id=self.student.id,
            field_name="BANK_PASSBOOK"
        ).exists())

    def test_api_replace_allotment_letter(self):
        f1 = SimpleUploadedFile("allotment_v1.pdf", b"Round 1", content_type="application/pdf")
        DocumentService.upload_student_document(
            student=self.student,
            document_type="ALLOTMENT_LETTER",
            file_obj=f1,
            filename="allotment_v1.pdf",
            uploaded_by=self.staff_user
        )

        f2 = SimpleUploadedFile("allotment_v2.pdf", b"Round 2 Upgraded", content_type="application/pdf")
        resp = self.client.post(
            f"/api/v1/documents/students/{self.student.id}/allotment-letter/replace/",
            {
                "file": f2,
                "reason": "Seat upgrade in government CAP Round 2"
            },
            format='multipart'
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["version"], 2)
        self.assertEqual(resp.data["version_status"], "CURRENT")
