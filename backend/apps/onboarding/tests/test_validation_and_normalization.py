"""
Tests for Import Validation, Normalization, and Error Reporting (Tasks 4.2.1, 4.2.2).
"""

from django.test import TestCase
from django.utils import timezone
from apps.identity.models import User
from apps.onboarding.models import ImportBatch, ImportStagingRow
from apps.onboarding.domain.normalization import normalize_row_dict, clean_header_key
from apps.onboarding.services.import_service import ImportService


class NormalizationAndValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="validator_admin",
            password="Password@123",
            email="validator@edvana.edu"
        )
        self.batch = ImportBatch.objects.create(
            source_file_name="Govt_Data.xlsx",
            source_file_hash="test_hash_val",
            uploaded_by=self.user,
            status="UPLOADED"
        )

    def test_header_cleaning_and_aliasing(self):
        """Task 4.2.2: Verify header cleanup and alias resolution."""
        self.assertEqual(clean_header_key("Candidate Name (Full)"), "candidate_name_full")
        self.assertEqual(clean_header_key("Date of Birth / DOB"), "date_of_birth_dob")
        self.assertEqual(clean_header_key("Aadhaar No."), "aadhaar_no")

        raw_row = {
            "Applicant Name": "Ananya Joshi",
            "Sex": "F",
            "DOB": "15/07/2005",
            "UIDAI No": "1234 5678 9012",
            "Contact No": "+91 9988776655",
            "Quota": "HOME_STATE",
        }
        normalized = normalize_row_dict(raw_row)
        self.assertEqual(normalized["candidate_name"], "Ananya Joshi")
        self.assertEqual(normalized["gender"], "FEMALE")
        self.assertEqual(normalized["date_of_birth"], "2005-07-15")
        self.assertEqual(normalized["aadhaar_number"], "123456789012")
        self.assertEqual(normalized["student_mobile"], "9988776655")
        self.assertEqual(normalized["seat_type"], "HOME_STATE")

    def test_batch_validation_success(self):
        """Task 4.2.1 & 4.2.2: Valid rows get normalized and transition to VALIDATED."""
        staging_row = ImportStagingRow.objects.create(
            import_batch=self.batch,
            row_number=1,
            raw_data={
                "candidate_name": "Vikram Rathore",
                "gender": "Male",
                "date_of_birth": "2005-03-21",
                "application_id": "EN262001",
                "mobile_no": "9123456780",
                "aadhaar": "112233445566"
            },
            processing_status="PENDING"
        )

        ImportService.validate_and_normalize_batch(self.batch)

        self.batch.refresh_from_db()
        staging_row.refresh_from_db()

        self.assertEqual(self.batch.status, "VALIDATED")
        self.assertEqual(self.batch.error_rows, 0)
        self.assertEqual(staging_row.processing_status, "VALIDATED")
        self.assertIsNotNone(staging_row.normalized_data)
        self.assertEqual(staging_row.normalized_data["gender"], "MALE")
        self.assertEqual(staging_row.match_type, "NEW")
        self.assertIsNone(staging_row.validation_errors)

    def test_batch_validation_with_errors(self):
        """Task 4.2.1: Invalid fields trigger validation errors and INVALID status."""
        staging_row = ImportStagingRow.objects.create(
            import_batch=self.batch,
            row_number=1,
            raw_data={
                "candidate_name": "",  # Missing mandatory name
                "gender": "UNKNOWN_GENDER",
                "date_of_birth": "invalid-date",
                "mobile_no": "123",  # Invalid length
                "aadhaar": "999"  # Invalid length
            },
            processing_status="PENDING"
        )

        ImportService.validate_and_normalize_batch(self.batch)

        self.batch.refresh_from_db()
        staging_row.refresh_from_db()

        self.assertEqual(self.batch.status, "VALIDATED")
        self.assertEqual(self.batch.error_rows, 1)
        self.assertEqual(staging_row.processing_status, "INVALID")
        self.assertIsNotNone(staging_row.validation_errors)
        self.assertTrue(len(staging_row.validation_errors) >= 3)
        self.assertIn("Candidate name is required.", staging_row.validation_errors)
