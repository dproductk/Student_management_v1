from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.academic.models import Department, Program, AcademicYear, Semester, Scheme, Subject, SchemeSubject, Batch
from apps.students.models import Student, StudentEnrollment
from apps.results.models import ResultImportBatch, StudentResult, StudentResultDetail
from apps.results.services.result_service import ResultService
from apps.results.domain.invariants import (
    ResultImmutabilityViolation,
    InvalidLifecycleTransitionError,
    validate_result_immutability,
)

User = get_user_model()


class ResultLifecycleTestCase(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="staff1", email="staff@test.com", password="pass")
        self.approver = User.objects.create_user(username="dean_academic", email="dean@test.com", password="pass")

        self.dept = Department.objects.create(name="Mechanical Engineering", code="ME")
        self.program = Program.objects.create(name="B.Tech Mechanical", code="BTME", department=self.dept)
        self.ay = AcademicYear.objects.create(label="2024-2025", start_date=date(2024, 8, 1), end_date=date(2025, 5, 31))
        self.sem = Semester.objects.create(academic_year=self.ay, number=3, start_date=date(2024, 8, 1), end_date=date(2024, 12, 31))
        self.batch = Batch.objects.create(department=self.dept, academic_year=self.ay, name="2024-ME")
        self.scheme = Scheme.objects.create(program=self.program, name="ME Scheme 2024", code="SCH_ME", effective_from_year=self.ay)

        self.subj = Subject.objects.create(name="Thermodynamics", code="ME301")
        self.ss = SchemeSubject.objects.create(
            scheme=self.scheme,
            subject=self.subj,
            semester_number=self.sem.number,
            max_internal_marks=40,
            max_marks=100
        )

        self.student = Student.objects.create(
            candidate_name="Aakash Verma",
            gender="MALE",
            date_of_birth=date(2005, 3, 15),
            enrollment_no="ENR2024301",
            application_id="APP2024301",
            email="aakash@student.edu"
        )
        StudentEnrollment.objects.create(
            student=self.student,
            academic_year=self.ay,
            semester=self.sem,
            department=self.dept,
            program=self.program,
            batch=self.batch,
            scheme=self.scheme,
            status='ACTIVE'
        )

    def _setup_validated_batch(self):
        batch = ResultService.create_import_batch(
            academic_year_id=str(self.ay.id),
            semester_id=str(self.sem.id),
            department_id=str(self.dept.id),
            program_id=str(self.program.id),
            file_name="me_sem3_results.csv",
            uploaded_by=self.staff
        )
        csv_text = f"student_identifier,subject_code,internal_marks,external_marks\n{self.student.enrollment_no},ME301,36,54\n"
        rows_data = ResultService.parse_csv_content(csv_text)
        ResultService.extract_and_stage_rows(batch, rows_data)
        ResultService.validate_and_associate_rows(batch)
        batch.refresh_from_db()
        return batch

    def test_11_2_1_state_machine_and_draft_generation(self):
        """11.2.1: Validated batch generates DRAFT StudentResult records."""
        batch = self._setup_validated_batch()
        self.assertEqual(batch.status, 'VALIDATED')

        draft_result = StudentResult.objects.filter(student=self.student, academic_year=self.ay, semester=self.sem).first()
        self.assertIsNotNone(draft_result)
        self.assertEqual(draft_result.status, 'DRAFT')
        self.assertEqual(draft_result.total_marks_obtained, Decimal('90.00'))
        self.assertEqual(draft_result.percentage, Decimal('90.00'))
        self.assertEqual(draft_result.result_status, 'PASS')

        # Invalid transition attempt directly from VALIDATED to PUBLISHED without approval
        with self.assertRaises(InvalidLifecycleTransitionError):
            ResultService.publish_result_batch(batch, self.staff)

    def test_11_2_2_and_3_approval_publication_and_student_visibility(self):
        """11.2.2 & 11.2.3: Approval transitions to APPROVED, publication to PUBLISHED, exposing marks."""
        batch = self._setup_validated_batch()

        # Before approval, student query returns nothing
        hidden_results = ResultService.get_student_published_results(self.student)
        self.assertEqual(len(hidden_results), 0)

        # Step 1: Approve batch
        approved_batch = ResultService.approve_result_batch(batch, self.approver)
        self.assertEqual(approved_batch.status, 'APPROVED')
        self.assertEqual(approved_batch.approved_by, self.approver)
        self.assertIsNotNone(approved_batch.approved_at)

        # Result is now APPROVED, but still not visible to student
        res = StudentResult.objects.get(student=self.student, academic_year=self.ay, semester=self.sem)
        self.assertEqual(res.status, 'APPROVED')
        still_hidden = ResultService.get_student_published_results(self.student)
        self.assertEqual(len(still_hidden), 0)

        # Step 2: Publish batch
        published_batch = ResultService.publish_result_batch(approved_batch, self.approver)
        self.assertEqual(published_batch.status, 'PUBLISHED')
        self.assertEqual(published_batch.published_by, self.approver)

        res.refresh_from_db()
        self.assertEqual(res.status, 'PUBLISHED')
        self.assertIsNotNone(res.published_at)

        # Now visible in student self-portal query
        visible_results = ResultService.get_student_published_results(self.student)
        self.assertEqual(len(visible_results), 1)
        self.assertEqual(visible_results[0].id, res.id)
        self.assertEqual(visible_results[0].total_marks_obtained, Decimal('90.00'))

    def test_11_2_4_published_result_immutability(self):
        """11.2.4: Published result immutability: deletion and alteration must be rejected."""
        batch = self._setup_validated_batch()
        ResultService.approve_result_batch(batch, self.approver)
        ResultService.publish_result_batch(batch, self.approver)

        res = StudentResult.objects.get(student=self.student, academic_year=self.ay, semester=self.sem)
        self.assertEqual(res.status, 'PUBLISHED')

        # Attempting direct delete must raise ResultImmutabilityViolation
        with self.assertRaises(ResultImmutabilityViolation):
            res.delete()

        # Detail deletion must also raise ResultImmutabilityViolation
        detail = res.details.first()
        self.assertIsNotNone(detail)
        with self.assertRaises(ResultImmutabilityViolation):
            detail.delete()

        # Domain guard check
        with self.assertRaises(ResultImmutabilityViolation):
            validate_result_immutability(res)
