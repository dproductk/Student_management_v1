"""
Tests for Sensitive Document Masking, Restricted Access, and Explicit Reveal
(Tasks 5.3.1, 5.3.2 - Flagged for Human Review).
"""

from datetime import date
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.identity.models import User
from apps.students.models import Student
from apps.documents.models import StudentDocument
from apps.documents.services.document_service import DocumentService
from apps.documents.services.storage_service import StorageService
from apps.documents.api.serializers import StudentDocumentSerializer
from apps.audit.models import SensitiveDataAccessLog
from common.exceptions import InvariantViolationError


class SensitiveDocumentsAndRevealTests(TestCase):
    def setUp(self):
        self.staff_admin = User.objects.create_user(
            username="verifier_officer",
            password="Password@123",
            email="verifier@edvana.edu",
            is_staff=True
        )
        self.student_user = User.objects.create_user(
            username="ENR-SENS-01",
            password="Password@123",
            email="student@edvana.edu"
        )
        self.student = Student.objects.create(
            user=self.student_user,
            candidate_name="Sneha Kulkarni",
            gender="FEMALE",
            date_of_birth=date(2005, 1, 10),
            application_id="APP-SENS-01",
            enrollment_no="ENR-SENS-01"
        )

        # Upload Aadhaar (Sensitive)
        aadhaar_file = SimpleUploadedFile("aadhaar.pdf", b"Sensitive Aadhaar Card Binary", content_type="application/pdf")
        self.aadhaar_doc = DocumentService.upload_student_document(
            student=self.student,
            document_type="AADHAAR_CARD",
            file_obj=aadhaar_file,
            filename="aadhaar.pdf",
            uploaded_by=self.staff_admin
        )

        # Upload Bank Passbook (Sensitive)
        bank_file = SimpleUploadedFile("bank_passbook.pdf", b"Sensitive Bank Passbook Binary", content_type="application/pdf")
        self.bank_doc = DocumentService.upload_student_document(
            student=self.student,
            document_type="BANK_PASSBOOK",
            file_obj=bank_file,
            filename="bank_passbook.pdf",
            uploaded_by=self.staff_admin
        )

    def tearDown(self):
        docs = StudentDocument.objects.all()
        for d in docs:
            StorageService.delete_document(d.storage_key)

    def test_sensitive_document_masking_in_serializer(self):
        """Task 5.3.1: Sensitive documents are masked by default (download_url is null)."""
        self.assertTrue(self.aadhaar_doc.is_sensitive)
        self.assertTrue(self.bank_doc.is_sensitive)

        data = StudentDocumentSerializer(self.aadhaar_doc).data
        self.assertTrue(data["is_sensitive"])
        self.assertIsNone(data["download_url"], "Direct download_url MUST be null for sensitive documents by default.")

    def test_explicit_sensitive_reveal_creates_audit_log(self):
        """Task 5.3.2: Explicit reveal checks permission and logs to SensitiveDataAccessLog."""
        reason_text = "Verifying Aadhaar number against government scholarship portal"
        
        doc = DocumentService.reveal_sensitive_document(
            document=self.aadhaar_doc,
            user=self.staff_admin,
            reason=reason_text,
            ip_address="192.168.1.50"
        )
        self.assertEqual(doc.id, self.aadhaar_doc.id)

        # Verify SensitiveDataAccessLog entry created
        log_entry = SensitiveDataAccessLog.objects.filter(
            student_id=self.student.id,
            field_name="AADHAAR_CARD"
        ).first()
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.accessor, self.staff_admin)
        self.assertEqual(log_entry.reason, reason_text)
        self.assertEqual(log_entry.ip_address, "192.168.1.50")

    def test_administrative_reveal_requires_valid_reason(self):
        """Task 5.3.2: Staff reveal without justification is rejected."""
        with self.assertRaises(InvariantViolationError) as ctx:
            DocumentService.reveal_sensitive_document(
                document=self.bank_doc,
                user=self.staff_admin,
                reason=" "  # Empty reason
            )
        self.assertIn("valid business reason", str(ctx.exception))

    def test_unauthorized_third_party_cannot_reveal(self):
        """Task 5.3.2: Unauthorized user cannot reveal student's sensitive documents."""
        unauthorized_user = User.objects.create_user(
            username="random_student_user",
            password="Password@123",
            email="random@edvana.edu"
        )

        with self.assertRaises(InvariantViolationError) as ctx:
            DocumentService.reveal_sensitive_document(
                document=self.aadhaar_doc,
                user=unauthorized_user,
                reason="Curiosity"
            )
        self.assertIn("do not have permission", str(ctx.exception))

    def test_student_can_reveal_own_document(self):
        """Task 5.3.2: Student can access their own document."""
        doc = DocumentService.reveal_sensitive_document(
            document=self.aadhaar_doc,
            user=self.student_user,
            reason=""
        )
        self.assertEqual(doc.id, self.aadhaar_doc.id)
        # Check audit log recorded for self access as well
        self.assertTrue(SensitiveDataAccessLog.objects.filter(
            accessor=self.student_user,
            student_id=self.student.id
        ).exists())
