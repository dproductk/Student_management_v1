"""
Tests for Excel Ingestion, Staging Foundation, and Row Preservation (Tasks 4.1.1, 4.1.2, 4.1.3).
"""

import io
import openpyxl
from django.test import TestCase
from django.utils import timezone
from apps.identity.models import User
from apps.academic.models import AcademicYear, Department
from apps.onboarding.models import ImportBatch, ImportStagingRow
from apps.onboarding.services.import_service import ImportService


class ExcelStagingIngestionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="importer_admin",
            password="Password@123",
            email="importer@edvana.edu",
            is_staff=True
        )
        self.academic_year = AcademicYear.objects.create(
            label="2026-2027",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=365),
            is_current=True
        )
        self.dept = Department.objects.create(
            name="Computer Engineering",
            code="COMP",
            is_active=True
        )

    def _create_sample_excel_bytes(self, rows_data):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Allotment_List"
        for r in rows_data:
            ws.append(r)
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf

    def test_import_batch_and_staging_row_creation(self):
        """Task 4.1.1: Database foundation models can be persisted cleanly."""
        batch = ImportBatch.objects.create(
            source_file_name="Govt_CAP_Allotment_Round1.xlsx",
            source_file_hash="dummyhash123",
            academic_year=self.academic_year,
            department=self.dept,
            uploaded_by=self.user,
            status="UPLOADED"
        )
        self.assertIsNotNone(batch.id)
        self.assertEqual(batch.status, "UPLOADED")

        staging_row = ImportStagingRow.objects.create(
            import_batch=batch,
            row_number=1,
            raw_data={"Candidate Name": "Aarav Sharma", "Application ID": "EN261001"},
            processing_status="PENDING"
        )
        self.assertEqual(staging_row.processing_status, "PENDING")
        self.assertEqual(staging_row.raw_data["Candidate Name"], "Aarav Sharma")

    def test_excel_upload_and_staging_preservation(self):
        """Task 4.1.2 & 4.1.3: Ingest Excel, compute SHA-256 hash, and preserve raw rows."""
        excel_data = [
            ["Candidate Name", "Application ID", "Gender", "Date of Birth", "Mobile No"],
            ["Neha Patil", "EN261002", "Female", "2005-04-12", "9876543210"],
            ["Rohan Deshmukh", "EN261003", "Male", "2004-11-23", "9823456789"],
            ["Sanya Verma", "EN261004", "Female", "2005-08-19", "9812345678"],
        ]
        buf = self._create_sample_excel_bytes(excel_data)

        batch = ImportService.upload_and_stage_excel(
            file_obj=buf,
            source_file_name="CAP_Allotment_Round1.xlsx",
            academic_year_id=str(self.academic_year.id),
            department_id=str(self.dept.id),
            uploaded_by=self.user
        )

        self.assertEqual(batch.total_rows, 3)
        self.assertEqual(batch.status, "UPLOADED")
        self.assertTrue(len(batch.source_file_hash) == 64)  # SHA-256 hex length

        staging_rows = ImportStagingRow.objects.filter(import_batch=batch).order_by('row_number')
        self.assertEqual(staging_rows.count(), 3)

        first_row = staging_rows[0]
        self.assertEqual(first_row.row_number, 1)
        self.assertEqual(first_row.raw_data["Candidate Name"], "Neha Patil")
        self.assertEqual(first_row.raw_data["Application ID"], "EN261002")
        self.assertEqual(first_row.processing_status, "PENDING")

    def test_empty_excel_handling(self):
        """Excel with only headers or empty rows is handled gracefully."""
        excel_data = [
            ["Candidate Name", "Application ID"],
            ["", None],
        ]
        buf = self._create_sample_excel_bytes(excel_data)

        batch = ImportService.upload_and_stage_excel(
            file_obj=buf,
            source_file_name="Empty.xlsx",
            uploaded_by=self.user
        )

        self.assertEqual(batch.total_rows, 0)
        self.assertEqual(ImportStagingRow.objects.filter(import_batch=batch).count(), 0)
