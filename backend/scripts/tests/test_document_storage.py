"""
Automated Tests for Document Object Storage Integrity & Auditing.
Governed by TASKS.md 15.4.3, production-hardening-prd.md R-016, and ADR-031.
"""

import hashlib
import io
import shutil
import tempfile
from datetime import date
from pathlib import Path
from django.test import TestCase, override_settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from apps.identity.models import User
from apps.students.models import Student
from apps.documents.models import StudentDocument
from scripts.verify_document_storage import verify_storage_integrity


class DocumentStorageAuditTests(TestCase):
    def setUp(self):
        self.temp_media = tempfile.mkdtemp()
        self.settings_override = override_settings(MEDIA_ROOT=self.temp_media)
        self.settings_override.enable()

        self.user = User.objects.create(
            username="doc_uploader_test",
            email="uploader@test.com"
        )
        self.student = Student.objects.create(
            candidate_name="Test Student Storage",
            enrollment_no="ENR-STORAGE-001",
            gender="MALE",
            date_of_birth=date(2000, 1, 1),
            status="ACTIVE"
        )

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.temp_media, ignore_errors=True)

    def test_verify_storage_integrity_passes_on_valid_documents(self):
        """Documents properly saved in storage with matching checksum are verified as valid."""
        file_content = b"PDF_HEADER_VALID_CONTENT"
        sha256 = hashlib.sha256(file_content).hexdigest()
        storage_key = f"documents/students/{self.student.id}/test_cert.pdf"
        default_storage.save(storage_key, ContentFile(file_content))

        StudentDocument.objects.create(
            student=self.student,
            document_type="SSC_MARKSHEET",
            storage_key=storage_key,
            original_filename="test_cert.pdf",
            checksum=sha256,
            file_size_bytes=len(file_content),
            mime_type="application/pdf",
            uploaded_by=self.user
        )

        report = verify_storage_integrity()
        self.assertEqual(report['total_documents_checked'], 1)
        self.assertEqual(report['valid_documents'], 1)
        self.assertEqual(report['missing_storage_files'], 0)
        self.assertEqual(report['checksum_mismatches'], 0)
        self.assertEqual(len(report['errors']), 0)

    def test_verify_storage_integrity_detects_missing_storage_file(self):
        """Flags missing physical files when database record exists but file is missing in storage."""
        StudentDocument.objects.create(
            student=self.student,
            document_type="HSC_MARKSHEET",
            storage_key="documents/students/missing_file.pdf",
            original_filename="missing_file.pdf",
            checksum="dummychecksum",
            file_size_bytes=100,
            uploaded_by=self.user
        )

        report = verify_storage_integrity()
        self.assertGreaterEqual(report['total_documents_checked'], 1)
        self.assertEqual(report['missing_storage_files'], 1)
        self.assertEqual(report['errors'][0]['issue'], 'FILE_MISSING_ON_STORAGE')

    def test_verify_storage_integrity_detects_tampered_storage_file(self):
        """Flags checksum mismatch when binary content on disk was modified."""
        original_content = b"ORIGINAL_CERTIFICATE"
        expected_sha = hashlib.sha256(original_content).hexdigest()
        storage_key = f"documents/students/{self.student.id}/tampered_cert.pdf"
        
        # Save tampered content to storage
        tampered_content = b"TAMPERED_CERTIFICATE_CONTENT"
        default_storage.save(storage_key, ContentFile(tampered_content))

        StudentDocument.objects.create(
            student=self.student,
            document_type="OTHER",
            storage_key=storage_key,
            original_filename="tampered_cert.pdf",
            checksum=expected_sha,  # expects original hash
            file_size_bytes=len(original_content),
            uploaded_by=self.user
        )

        report = verify_storage_integrity()
        self.assertEqual(report['checksum_mismatches'], 1)
        self.assertEqual(report['errors'][0]['issue'], 'CHECKSUM_INTEGRITY_MISMATCH')
