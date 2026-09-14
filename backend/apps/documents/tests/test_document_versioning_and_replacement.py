"""
Tests for Document Versioning, Supersession, and Allotment-Letter Replacement
(Tasks 5.2.1, 5.2.2).
"""

from datetime import date
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.identity.models import User
from apps.students.models import Student
from apps.documents.models import StudentDocument
from apps.documents.services.document_service import DocumentService
from apps.documents.services.storage_service import StorageService
from apps.audit.models import AuditLog
from common.exceptions import InvariantViolationError


class DocumentVersioningAndReplacementTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="registrar_user",
            password="Password@123",
            email="registrar@edvana.edu",
            is_staff=True
        )
        self.student = Student.objects.create(
            candidate_name="Meera Rao",
            gender="FEMALE",
            date_of_birth=date(2005, 7, 20),
            application_id="APP-MEERA-01",
            enrollment_no="ENR-MEERA-01"
        )

    def tearDown(self):
        docs = StudentDocument.objects.all()
        for d in docs:
            StorageService.delete_document(d.storage_key)

    def test_document_versioning_and_supersession(self):
        """Task 5.2.1: Re-uploading document type creates v2 CURRENT and supersedes v1."""
        # 1. Upload v1
        v1_file = SimpleUploadedFile("hsc_v1.pdf", b"Content HSC Version 1", content_type="application/pdf")
        doc_v1 = DocumentService.upload_student_document(
            student=self.student,
            document_type="HSC_MARKSHEET",
            file_obj=v1_file,
            filename="hsc_v1.pdf",
            uploaded_by=self.staff_user
        )
        self.assertEqual(doc_v1.version, 1)
        self.assertEqual(doc_v1.version_status, "CURRENT")
        self.assertIsNone(doc_v1.superseded_by)

        # 2. Upload v2 (e.g. re-evaluated marksheet)
        v2_file = SimpleUploadedFile("hsc_v2.pdf", b"Content HSC Version 2 Re-evaluated", content_type="application/pdf")
        doc_v2 = DocumentService.upload_student_document(
            student=self.student,
            document_type="HSC_MARKSHEET",
            file_obj=v2_file,
            filename="hsc_v2.pdf",
            uploaded_by=self.staff_user
        )

        doc_v1.refresh_from_db()

        # Check v2 is CURRENT
        self.assertEqual(doc_v2.version, 2)
        self.assertEqual(doc_v2.version_status, "CURRENT")
        self.assertIsNone(doc_v2.superseded_by)

        # Check v1 is SUPERSEDED and points to v2
        self.assertEqual(doc_v1.version_status, "SUPERSEDED")
        self.assertEqual(doc_v1.superseded_by, doc_v2)

        # 3. Upload v3
        v3_file = SimpleUploadedFile("hsc_v3.pdf", b"Content HSC Version 3 Final", content_type="application/pdf")
        doc_v3 = DocumentService.upload_student_document(
            student=self.student,
            document_type="HSC_MARKSHEET",
            file_obj=v3_file,
            filename="hsc_v3.pdf",
            uploaded_by=self.staff_user
        )

        doc_v2.refresh_from_db()
        self.assertEqual(doc_v3.version, 3)
        self.assertEqual(doc_v3.version_status, "CURRENT")
        self.assertEqual(doc_v2.version_status, "SUPERSEDED")
        self.assertEqual(doc_v2.superseded_by, doc_v3)

    def test_controlled_allotment_letter_replacement(self):
        """Task 5.2.2: Controlled allotment-letter replacement enforces supersession and logs audit event."""
        # 1. Initial allotment letter
        initial_file = SimpleUploadedFile("cap_round1.pdf", b"CAP Round 1 Allotment", content_type="application/pdf")
        doc_v1 = DocumentService.upload_student_document(
            student=self.student,
            document_type="ALLOTMENT_LETTER",
            file_obj=initial_file,
            filename="cap_round1.pdf",
            uploaded_by=self.staff_user
        )

        # 2. Controlled replacement with reason
        round2_file = SimpleUploadedFile("cap_round2.pdf", b"CAP Round 2 Upgraded Allotment", content_type="application/pdf")
        doc_v2 = DocumentService.replace_allotment_letter(
            student=self.student,
            file_obj=round2_file,
            filename="cap_round2.pdf",
            uploaded_by=self.staff_user,
            reason="Upgraded from Mechanical to Computer Engineering in CAP Round 2"
        )

        doc_v1.refresh_from_db()
        self.assertEqual(doc_v2.version, 2)
        self.assertEqual(doc_v2.version_status, "CURRENT")
        self.assertEqual(doc_v1.version_status, "SUPERSEDED")
        self.assertEqual(doc_v1.superseded_by, doc_v2)

        # Check audit log entry exists
        audit_entry = AuditLog.objects.filter(
            target_id=doc_v2.id,
            action="DOCUMENT_REPLACED_ALLOTMENT_LETTER"
        ).first()
        self.assertIsNotNone(audit_entry)
        self.assertEqual(audit_entry.actor, self.staff_user)
        self.assertIn("Upgraded from Mechanical", audit_entry.reason)

    def test_allotment_letter_replacement_requires_reason(self):
        """Task 5.2.2: Blank or missing reason triggers validation error."""
        file_obj = SimpleUploadedFile("letter.pdf", b"Content", content_type="application/pdf")
        with self.assertRaises(InvariantViolationError) as ctx:
            DocumentService.replace_allotment_letter(
                student=self.student,
                file_obj=file_obj,
                filename="letter.pdf",
                uploaded_by=self.staff_user,
                reason="  "
            )
        self.assertIn("mandatory replacement reason", str(ctx.exception))
