"""
API Integration tests for student onboarding endpoints.
"""

import io
import openpyxl
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.identity.models import User
from apps.onboarding.models import ImportBatch, ImportStagingRow


class OnboardingAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="api_admin",
            password="Password@123",
            email="api_admin@edvana.edu",
            is_staff=True
        )
        self.client.force_authenticate(user=self.admin)

    def _create_sample_excel_file(self):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Candidate Name", "Gender", "Date of Birth", "Application ID"])
        ws.append(["Kavita Sharma", "Female", "2005-04-10", "APP-API-01"])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return SimpleUploadedFile("students.xlsx", buf.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    def test_api_upload_excel_batch(self):
        excel_file = self._create_sample_excel_file()
        response = self.client.post(
            "/api/v1/onboarding/batches/upload/",
            {"file": excel_file},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["total_rows"], 1)
        self.assertEqual(response.data["status"], "UPLOADED")

    def test_api_validate_and_execute_batch(self):
        excel_file = self._create_sample_excel_file()
        upload_resp = self.client.post(
            "/api/v1/onboarding/batches/upload/",
            {"file": excel_file},
            format='multipart'
        )
        batch_id = upload_resp.data["id"]

        # 1. Validate
        val_resp = self.client.post(f"/api/v1/onboarding/batches/{batch_id}/validate/")
        self.assertEqual(val_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(val_resp.data["status"], "VALIDATED")

        # 2. Inspect staging rows
        rows_resp = self.client.get(f"/api/v1/onboarding/batches/{batch_id}/staging-rows/")
        self.assertEqual(rows_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(rows_resp.data), 1)
        self.assertEqual(rows_resp.data[0]["processing_status"], "VALIDATED")

        # 3. Execute production import
        exec_resp = self.client.post(f"/api/v1/onboarding/batches/{batch_id}/execute/", {})
        self.assertEqual(exec_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(exec_resp.data["status"], "COMPLETED")
        self.assertEqual(exec_resp.data["processed_rows"], 1)

    def test_api_conflict_resolution(self):
        batch = ImportBatch.objects.create(
            source_file_name="Conflict.xlsx",
            source_file_hash="conflict_hash",
            uploaded_by=self.admin,
            status="VALIDATED"
        )
        row = ImportStagingRow.objects.create(
            import_batch=batch,
            row_number=1,
            raw_data={"candidate_name": "Conflict Person"},
            processing_status="CONFLICT",
            match_type="CONFLICT"
        )

        resp = self.client.post(
            f"/api/v1/onboarding/staging-rows/{row.id}/resolve/",
            {"action": "FORCE_AS_NEW"}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["processing_status"], "VALIDATED")
        self.assertEqual(resp.data["match_type"], "NEW")
