"""
Tests for Document Types, Metadata, Object-Storage Integration, and Upload
(Tasks 5.1.1, 5.1.2, 5.1.3).
"""

import io
from datetime import date
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage
from apps.identity.models import User
from apps.students.models import Student
from apps.documents.models import StudentDocument
from apps.documents.services.document_service import DocumentService
from apps.documents.services.storage_service import StorageService
from common.exceptions import InvariantViolationError


class DocumentUploadAndStorageTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="doc_officer",
            password="Password@123",
            email="doc_officer@edvana.edu",
            is_staff=True
        )
        self.student = Student.objects.create(
            candidate_name="Rohit Patil",
            gender="MALE",
            date_of_birth=date(2005, 3, 15),
            application_id="APP-DOC-01",
            enrollment_no="ENR-DOC-01"
        )

    def tearDown(self):
        # Clean up any created files in default storage
        docs = StudentDocument.objects.all()
        for d in docs:
            StorageService.delete_document(d.storage_key)

    def test_document_metadata_and_model_foundation(self):
        """Task 5.1.1: Document type and metadata persistence per Deliverable D.6."""
        doc = StudentDocument.objects.create(
            student=self.student,
            document_type="SSC_MARKSHEET",
            storage_key="documents/students/test_ssc.pdf",
            original_filename="ssc_marksheet.pdf",
            file_size_bytes=102400,
            mime_type="application/pdf",
            checksum="sample_sha256_checksum",
            version=1,
            version_status="CURRENT",
            verification_status="PENDING",
            uploaded_by=self.staff_user
        )
        self.assertIsNotNone(doc.id)
        self.assertEqual(doc.document_type, "SSC_MARKSHEET")
        self.assertEqual(doc.version, 1)
        self.assertEqual(doc.version_status, "CURRENT")
        self.assertFalse(doc.is_sensitive)

    def test_invalid_document_type_rejected(self):
        """Task 5.1.1: Unsupported document type raises InvariantViolationError."""
        with self.assertRaises(InvariantViolationError):
            StudentDocument.objects.create(
                student=self.student,
                document_type="RANDOM_INVALID_TYPE",
                storage_key="test.pdf",
                uploaded_by=self.staff_user
            )

    def test_secure_object_storage_upload(self):
        """Task 5.1.2: Document binaries are stored outside DB with SHA-256 and MIME detection."""
        file_content = b"%PDF-1.4 Fake PDF Content for Marksheet Testing"
        uploaded_file = SimpleUploadedFile(
            name="marksheet_tenth.pdf",
            content=file_content,
            content_type="application/pdf"
        )

        doc = DocumentService.upload_student_document(
            student=self.student,
            document_type="SSC_MARKSHEET",
            file_obj=uploaded_file,
            filename="marksheet_tenth.pdf",
            uploaded_by=self.staff_user
        )

        # 1. Metadata matches
        self.assertEqual(doc.original_filename, "marksheet_tenth.pdf")
        self.assertEqual(doc.file_size_bytes, len(file_content))
        self.assertEqual(doc.mime_type, "application/pdf")
        self.assertEqual(doc.version, 1)
        self.assertEqual(doc.version_status, "CURRENT")

        # 2. File exists in external storage
        self.assertTrue(default_storage.exists(doc.storage_key))

        # 3. Stream retrieval returns exact binary content
        with StorageService.get_document_stream(doc.storage_key) as stream:
            read_content = stream.read()
            self.assertEqual(read_content, file_content)

    def test_oversized_file_rejected(self):
        """Task 5.1.2: Files exceeding 10MB limit are rejected."""
        fake_large_content = b"0" * (11 * 1024 * 1024)  # 11 MB
        large_file = SimpleUploadedFile(
            name="huge_file.pdf",
            content=fake_large_content,
            content_type="application/pdf"
        )

        with self.assertRaises(InvariantViolationError) as ctx:
            DocumentService.upload_student_document(
                student=self.student,
                document_type="SSC_MARKSHEET",
                file_obj=large_file,
                filename="huge_file.pdf",
                uploaded_by=self.staff_user
            )
        self.assertIn("exceeds maximum allowable limit", str(ctx.exception))

    def test_unsupported_mime_type_rejected(self):
        """Task 5.1.2: Disallowed file formats (e.g. .exe) are rejected."""
        exe_file = SimpleUploadedFile(
            name="malware.exe",
            content=b"MZ executable content",
            content_type="application/x-msdownload"
        )

        with self.assertRaises(InvariantViolationError) as ctx:
            DocumentService.upload_student_document(
                student=self.student,
                document_type="OTHER",
                file_obj=exe_file,
                filename="malware.exe",
                uploaded_by=self.staff_user
            )
        self.assertIn("is not supported", str(ctx.exception))
