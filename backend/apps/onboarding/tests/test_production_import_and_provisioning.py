"""
Tests for Idempotent Production Import, State Transitions, and Account Provisioning
(Tasks 4.3.3, 4.3.4, 4.4.1, 4.4.2).
"""

import io
import openpyxl
from datetime import date
from django.test import TestCase
from django.utils import timezone

from apps.identity.models import User, Role
from apps.academic.models import AcademicYear, Department, Program, Semester, Scheme, Batch
from apps.students.models import Student, StudentAddress, StudentCategory, StudentAdmission, StudentEnrollment
from apps.onboarding.models import ImportBatch, ImportStagingRow
from apps.onboarding.services.import_service import ImportService
from common.security import decrypt_sensitive_value


class ProductionImportAndProvisioningTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="import_officer",
            password="Password@123",
            email="officer@edvana.edu",
            is_staff=True
        )
        self.academic_year = AcademicYear.objects.create(
            label="2026-2027",
            start_date=date(2026, 7, 1),
            end_date=date(2027, 6, 30),
            is_current=True
        )
        self.dept = Department.objects.create(
            name="Mechanical Engineering",
            code="MECH",
            is_active=True
        )
        self.program = Program.objects.create(
            department=self.dept,
            name="B.Tech in Mechanical Engineering",
            code="MECH-UG",
            duration_years=4
        )
        self.semester = Semester.objects.create(
            academic_year=self.academic_year,
            number=1,
            label="Semester 1",
            start_date=date(2026, 7, 1),
            end_date=date(2026, 12, 31)
        )
        self.scheme = Scheme.objects.create(
            program=self.program,
            name="2026 Scheme",
            code="MECH-2026",
            effective_from_year=self.academic_year
        )
        self.batch = Batch.objects.create(
            department=self.dept,
            academic_year=self.academic_year,
            name="2026-2030 Batch"
        )

    def _create_sample_excel(self, rows):
        wb = openpyxl.Workbook()
        ws = wb.active
        for r in rows:
            ws.append(r)
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf

    def test_idempotent_new_student_import_and_account_provisioning(self):
        """Tasks 4.3.3 & 4.4.1: Import creates student, address, category, admission, and provisions account."""
        batch = ImportBatch.objects.create(
            source_file_name="Allotment.xlsx",
            source_file_hash="import_hash_1",
            academic_year=self.academic_year,
            department=self.dept,
            uploaded_by=self.user,
            status="VALIDATED"
        )

        staging_row = ImportStagingRow.objects.create(
            import_batch=batch,
            row_number=1,
            raw_data={"Candidate Name": "Tanvi Joshi"},
            normalized_data={
                "candidate_name": "Tanvi Joshi",
                "gender": "FEMALE",
                "date_of_birth": "2005-08-14",
                "application_id": "APP-TANVI-01",
                "enrollment_no": "ENR-TANVI-01",
                "student_mobile": "9876543210",
                "email": "tanvi.joshi@example.com",
                "aadhaar_number": "112233445566",
                "state": "Maharashtra",
                "district": "Pune",
                "pincode": "411001",
                "category": "OBC",
                "program_code": "MECH-UG"
            },
            match_type="NEW",
            processing_status="VALIDATED"
        )

        ImportService.execute_production_import(
            batch=batch,
            user=self.user,
            default_program_id=str(self.program.id),
            default_semester_id=str(self.semester.id),
            default_scheme_id=str(self.scheme.id),
            default_batch_id=str(self.batch.id)
        )

        batch.refresh_from_db()
        staging_row.refresh_from_db()

        self.assertEqual(batch.status, "COMPLETED")
        self.assertEqual(batch.processed_rows, 1)
        self.assertEqual(staging_row.processing_status, "IMPORTED")

        # Verify Student persisted
        student = Student.objects.get(application_id="APP-TANVI-01")
        self.assertEqual(student.candidate_name, "Tanvi Joshi")
        self.assertEqual(student.enrollment_no, "ENR-TANVI-01")
        self.assertEqual(student.gender, "FEMALE")
        self.assertEqual(student.aadhaar_masked, "XXXX XXXX 5566")
        self.assertEqual(decrypt_sensitive_value(student.aadhaar_encrypted), "112233445566")

        # Verify Related 1:1 models
        self.assertTrue(StudentAddress.objects.filter(student=student, district="Pune").exists())
        self.assertTrue(StudentCategory.objects.filter(student=student, category="OBC").exists())
        self.assertTrue(StudentAdmission.objects.filter(student=student, program=self.program).exists())

        # Verify Academic Enrollment (ADR-005)
        self.assertTrue(StudentEnrollment.objects.filter(
            student=student,
            academic_year=self.academic_year,
            semester=self.semester,
            batch=self.batch
        ).exists())

        # Verify ADR-009 Account Provisioning (Task 4.4.1)
        self.assertIsNotNone(student.user)
        user = student.user
        self.assertEqual(user.username, "ENR-TANVI-01")
        self.assertTrue(user.must_change_password)
        self.assertTrue(user.user_roles.filter(role__name="STUDENT").exists())

    def test_additive_update_to_existing_student(self):
        """Task 4.3.3: Matched existing student receives additive non-destructive updates."""
        existing_student = Student.objects.create(
            candidate_name="Karan Malhotra",
            gender="MALE",
            date_of_birth=date(2004, 5, 10),
            application_id="APP-KARAN-01",
            enrollment_no="ENR-KARAN-01",
            student_mobile=None,  # Empty initially
            email=None
        )

        batch = ImportBatch.objects.create(
            source_file_name="Update.xlsx",
            source_file_hash="karan_hash_1",
            uploaded_by=self.user,
            status="VALIDATED"
        )

        staging_row = ImportStagingRow.objects.create(
            import_batch=batch,
            row_number=1,
            raw_data={},
            normalized_data={
                "candidate_name": "Karan Malhotra",
                "gender": "MALE",
                "date_of_birth": "2004-05-10",
                "application_id": "APP-KARAN-01",
                "student_mobile": "9911223344",
                "email": "karan@edvana.edu"
            },
            matched_student=existing_student,
            match_type="APPLICATION_ID",
            processing_status="VALIDATED"
        )

        ImportService.execute_production_import(batch=batch, user=self.user)

        existing_student.refresh_from_db()
        self.assertEqual(existing_student.student_mobile, "9911223344")
        self.assertEqual(existing_student.email, "karan@edvana.edu")
        self.assertEqual(existing_student.updated_by, self.user)

    def test_import_state_machine_partial_completion(self):
        """Task 4.3.4: Batch with unresolvable/invalid rows results in PARTIALLY_COMPLETED status."""
        batch = ImportBatch.objects.create(
            source_file_name="Mixed.xlsx",
            source_file_hash="mixed_hash",
            uploaded_by=self.user,
            status="VALIDATED"
        )

        # 1 valid row
        ImportStagingRow.objects.create(
            import_batch=batch,
            row_number=1,
            raw_data={},
            normalized_data={
                "candidate_name": "Valid Student",
                "gender": "OTHER",
                "date_of_birth": "2005-01-01",
                "application_id": "APP-VALID-1"
            },
            match_type="NEW",
            processing_status="VALIDATED"
        )

        # 1 invalid row
        ImportStagingRow.objects.create(
            import_batch=batch,
            row_number=2,
            raw_data={},
            processing_status="INVALID",
            validation_errors=["Invalid date"]
        )

        ImportService.execute_production_import(batch=batch, user=self.user)

        batch.refresh_from_db()
        self.assertEqual(batch.status, "PARTIALLY_COMPLETED")
        self.assertEqual(batch.processed_rows, 1)

    def test_end_to_end_flow_upload_to_provisioning(self):
        """Task 4.4.2: Full lifecycle test from raw Excel bytes to provisioned student."""
        excel_data = [
            ["Candidate Name", "Application ID", "Enrollment No", "Gender", "Date of Birth", "Mobile No", "Email"],
            ["Devika Shah", "APP-E2E-01", "ENR-E2E-01", "Female", "2005-09-12", "9876501234", "devika@edvana.edu"],
        ]
        buf = self._create_sample_excel(excel_data)

        # 1. Upload
        batch = ImportService.upload_and_stage_excel(
            file_obj=buf,
            source_file_name="E2E_Import.xlsx",
            academic_year_id=str(self.academic_year.id),
            department_id=str(self.dept.id),
            uploaded_by=self.user
        )
        self.assertEqual(batch.status, "UPLOADED")
        self.assertEqual(batch.total_rows, 1)

        # 2. Validate
        ImportService.validate_and_normalize_batch(batch)
        batch.refresh_from_db()
        self.assertEqual(batch.status, "VALIDATED")

        # 3. Production Import & Provisioning
        ImportService.execute_production_import(
            batch=batch,
            user=self.user,
            default_program_id=str(self.program.id),
            default_semester_id=str(self.semester.id),
            default_scheme_id=str(self.scheme.id),
            default_batch_id=str(self.batch.id)
        )
        batch.refresh_from_db()
        self.assertEqual(batch.status, "COMPLETED")

        # 4. Assert end state
        student = Student.objects.get(application_id="APP-E2E-01")
        self.assertEqual(student.enrollment_no, "ENR-E2E-01")
        self.assertIsNotNone(student.user)
        self.assertEqual(student.user.username, "ENR-E2E-01")
        self.assertTrue(student.user.user_roles.filter(role__name="STUDENT").exists())
        self.assertTrue(StudentEnrollment.objects.filter(student=student, academic_year=self.academic_year).exists())
