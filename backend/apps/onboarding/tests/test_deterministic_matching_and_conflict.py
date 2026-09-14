"""
Tests for Deterministic Identity Matching and Conflict Resolution (Tasks 4.3.1, 4.3.2).
"""

from datetime import date
from django.test import TestCase
from apps.identity.models import User
from apps.students.models import Student
from apps.onboarding.models import ImportBatch, ImportStagingRow
from apps.onboarding.services.import_service import ImportService
from apps.onboarding.domain.matching import match_staging_student


class DeterministicMatchingAndConflictTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="matcher_admin",
            password="Password@123",
            email="matcher@edvana.edu"
        )
        self.batch = ImportBatch.objects.create(
            source_file_name="Matching_Test.xlsx",
            source_file_hash="match_hash_1",
            uploaded_by=self.user,
            status="UPLOADED"
        )

        # Existing student in DB
        self.student_1 = Student.objects.create(
            candidate_name="Pooja Kulkarni",
            gender="FEMALE",
            date_of_birth=date(2005, 6, 15),
            application_id="APP-MATCH-01",
            enrollment_no="ENR-MATCH-01",
            board_enrollment_no="BRD-MATCH-01"
        )

        self.student_2 = Student.objects.create(
            candidate_name="Sameer Shaikh",
            gender="MALE",
            date_of_birth=date(2004, 9, 20),
            application_id="APP-MATCH-02",
            enrollment_no="ENR-MATCH-02",
            board_enrollment_no="BRD-MATCH-02"
        )

    def test_matching_precedence_application_id(self):
        """Task 4.3.1: Precedence 1 matches by Application ID."""
        normalized = {
            "candidate_name": "Pooja Kulkarni",
            "application_id": "APP-MATCH-01",
            "enrollment_no": "ENR-DIFF-99",  # Non-existing enrollment
        }
        match_type, matched, conflict = match_staging_student(normalized)
        self.assertEqual(match_type, "APPLICATION_ID")
        self.assertEqual(matched, self.student_1)
        self.assertIsNone(conflict)

    def test_matching_precedence_enrollment_no(self):
        """Task 4.3.1: Precedence 2 matches by Enrollment Number when Application ID absent."""
        normalized = {
            "candidate_name": "Sameer Shaikh",
            "enrollment_no": "ENR-MATCH-02",
            "board_enrollment_no": "BRD-DIFF-99",
        }
        match_type, matched, conflict = match_staging_student(normalized)
        self.assertEqual(match_type, "ENROLLMENT_NO")
        self.assertEqual(matched, self.student_2)

    def test_matching_precedence_board_enrollment_no(self):
        """Task 4.3.1: Precedence 3 matches by Board Enrollment Number."""
        normalized = {
            "candidate_name": "Sameer Shaikh",
            "board_enrollment_no": "BRD-MATCH-02",
        }
        match_type, matched, conflict = match_staging_student(normalized)
        self.assertEqual(match_type, "BOARD_ENROLLMENT_NO")
        self.assertEqual(matched, self.student_2)

    def test_matching_precedence_new_student(self):
        """Task 4.3.1: Identifiers that do not match existing students resolve to NEW."""
        normalized = {
            "candidate_name": "Brand New Student",
            "application_id": "APP-NEW-99",
            "enrollment_no": "ENR-NEW-99",
        }
        match_type, matched, conflict = match_staging_student(normalized)
        self.assertEqual(match_type, "NEW")
        self.assertIsNone(matched)

    def test_conflict_detection_when_identifiers_diverge(self):
        """Task 4.3.2: When application_id maps to student_1 and enrollment_no maps to student_2, CONFLICT is flagged."""
        staging_row = ImportStagingRow.objects.create(
            import_batch=self.batch,
            row_number=1,
            raw_data={
                "candidate_name": "Conflicting Identity",
                "gender": "Female",
                "date_of_birth": "2005-06-15",
                "application_id": "APP-MATCH-01",  # belongs to student_1
                "enrollment_no": "ENR-MATCH-02",    # belongs to student_2
            },
            processing_status="PENDING"
        )

        ImportService.validate_and_normalize_batch(self.batch)

        staging_row.refresh_from_db()
        self.assertEqual(staging_row.processing_status, "CONFLICT")
        self.assertEqual(staging_row.match_type, "CONFLICT")
        self.assertIsNotNone(staging_row.conflict_details)
        self.assertIn("point to different existing student records", staging_row.conflict_details["message"])

    def test_manual_conflict_resolution_link_to_student(self):
        """Task 4.3.2: Manual resolution via LINK_TO_STUDENT sets chosen student and VALIDATED status."""
        staging_row = ImportStagingRow.objects.create(
            import_batch=self.batch,
            row_number=1,
            raw_data={"candidate_name": "Conflicting Row"},
            processing_status="CONFLICT",
            match_type="CONFLICT"
        )

        resolved = ImportService.resolve_staging_conflict(
            staging_row=staging_row,
            resolution_action="LINK_TO_STUDENT",
            chosen_student_id=str(self.student_1.id),
            resolved_by=self.user
        )

        self.assertEqual(resolved.processing_status, "VALIDATED")
        self.assertEqual(resolved.matched_student, self.student_1)

    def test_manual_conflict_resolution_force_as_new_and_skip(self):
        """Task 4.3.2: Manual resolution can force row as NEW or mark as SKIPPED."""
        row_new = ImportStagingRow.objects.create(
            import_batch=self.batch,
            row_number=2,
            raw_data={"candidate_name": "Forced Row"},
            processing_status="CONFLICT",
            match_type="CONFLICT"
        )
        resolved_new = ImportService.resolve_staging_conflict(
            staging_row=row_new,
            resolution_action="FORCE_AS_NEW"
        )
        self.assertEqual(resolved_new.processing_status, "VALIDATED")
        self.assertEqual(resolved_new.match_type, "NEW")
        self.assertIsNone(resolved_new.matched_student)

        row_skip = ImportStagingRow.objects.create(
            import_batch=self.batch,
            row_number=3,
            raw_data={"candidate_name": "Skipped Row"},
            processing_status="CONFLICT",
            match_type="CONFLICT"
        )
        resolved_skip = ImportService.resolve_staging_conflict(
            staging_row=row_skip,
            resolution_action="SKIP"
        )
        self.assertEqual(resolved_skip.processing_status, "SKIPPED")
