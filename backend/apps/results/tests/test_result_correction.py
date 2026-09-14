from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.academic.models import Department, Program, AcademicYear, Semester, Scheme, Subject, SchemeSubject, Batch
from apps.students.models import Student, StudentEnrollment
from apps.results.models import (
    ResultImportBatch,
    StudentResult,
    ResultCorrectionRequest,
    ResultCorrectionAudit,
)
from apps.results.services.result_service import ResultService
from apps.results.domain.invariants import ResultValidationError, ResultImmutabilityViolation

User = get_user_model()


class ResultCorrectionTestCase(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="faculty_user", email="faculty@test.com", password="pass")
        self.approver = User.objects.create_user(username="dean_academic", email="dean@test.com", password="pass")

        self.dept = Department.objects.create(name="Civil Engineering", code="CE_DEPT")
        self.program = Program.objects.create(name="B.Tech Civil", code="BTCE", department=self.dept)
        self.ay = AcademicYear.objects.create(label="2024-2025", start_date=date(2024, 8, 1), end_date=date(2025, 5, 31))
        self.sem = Semester.objects.create(academic_year=self.ay, number=5, start_date=date(2024, 8, 1), end_date=date(2024, 12, 31))
        self.batch = Batch.objects.create(department=self.dept, academic_year=self.ay, name="2024-CE")
        self.scheme = Scheme.objects.create(program=self.program, name="Civil Scheme 2024", code="SCH_CE", effective_from_year=self.ay)

        self.subj1 = Subject.objects.create(name="Structural Analysis", code="CE501")
        self.ss1 = SchemeSubject.objects.create(
            scheme=self.scheme,
            subject=self.subj1,
            semester_number=self.sem.number,
            max_internal_marks=40,
            max_marks=100
        )

        self.student = Student.objects.create(
            candidate_name="Neha Singh",
            gender="FEMALE",
            date_of_birth=date(2005, 4, 20),
            enrollment_no="ENR2024501",
            application_id="APP2024501",
            email="neha@student.edu"
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

        # Setup and publish a result V1 with total marks = 35 + 20 = 55 (Grade B)
        batch = ResultService.create_import_batch(
            academic_year_id=str(self.ay.id),
            semester_id=str(self.sem.id),
            department_id=str(self.dept.id),
            program_id=str(self.program.id),
            file_name="ce_sem5_results.csv",
            uploaded_by=self.staff
        )
        csv_text = f"student_identifier,subject_code,internal_marks,external_marks\n{self.student.enrollment_no},CE501,35,20\n"
        rows_data = ResultService.parse_csv_content(csv_text)
        ResultService.extract_and_stage_rows(batch, rows_data)
        ResultService.validate_and_associate_rows(batch)
        ResultService.approve_result_batch(batch, self.approver)
        ResultService.publish_result_batch(batch, self.approver)

        self.published_v1 = StudentResult.objects.get(
            student=self.student,
            academic_year=self.ay,
            semester=self.sem,
            version=1
        )

    def test_11_3_1_correction_request_and_review(self):
        """11.3.1: Correction request on published result and review rejection."""
        # 1. Reject empty reason
        with self.assertRaises(ResultValidationError):
            ResultService.request_result_correction(
                target_result=self.published_v1,
                requested_by=self.staff,
                reason="",
                proposed_changes={}
            )

        # 2. Valid correction request
        req = ResultService.request_result_correction(
            target_result=self.published_v1,
            requested_by=self.staff,
            reason="External marks re-evaluation revealed retotalling error (+15 marks in CE501)",
            proposed_changes={'subjects': {'CE501': {'external_marks': 35}}}
        )
        self.assertEqual(req.status, 'PENDING')
        self.assertEqual(req.requested_by, self.staff)

        # 3. Reject review flow
        rejected_req = ResultService.review_result_correction(
            correction_request=req,
            reviewer=self.approver,
            approved=False,
            review_remarks="Insufficient documentary evidence provided."
        )
        self.assertEqual(rejected_req.status, 'REJECTED')
        self.assertEqual(rejected_req.reviewed_by, self.approver)

        # Published V1 remains latest and published
        self.published_v1.refresh_from_db()
        self.assertTrue(self.published_v1.is_latest)
        self.assertEqual(self.published_v1.status, 'PUBLISHED')
        self.assertIsNone(self.published_v1.superseded_by)

    def test_11_3_2_and_3_result_v2_supersession_and_audit(self):
        """11.3.2 & 11.3.3: Approved correction creates Result V2, preserves V1, and creates audit."""
        req = ResultService.request_result_correction(
            target_result=self.published_v1,
            requested_by=self.staff,
            reason="Official university revaluation answer-sheet verification: external marks corrected to 45.",
            proposed_changes={'subjects': {'CE501': {'external_marks': 45}}}
        )

        # Approve correction
        approved_req = ResultService.review_result_correction(
            correction_request=req,
            reviewer=self.approver,
            approved=True,
            review_remarks="Revaluation marks approved as per university gazette."
        )
        self.assertEqual(approved_req.status, 'APPROVED')

        # Check V1: preserved, superseded, no longer latest
        self.published_v1.refresh_from_db()
        self.assertFalse(self.published_v1.is_latest)
        self.assertEqual(self.published_v1.status, 'SUPERSEDED')
        self.assertIsNotNone(self.published_v1.superseded_by)

        # Check V2: new record with version 2
        v2 = self.published_v1.superseded_by
        self.assertEqual(v2.version, 2)
        self.assertTrue(v2.is_latest)
        self.assertEqual(v2.status, 'PUBLISHED')
        self.assertEqual(v2.student, self.student)
        # 35 internal + 45 external = 80 total
        self.assertEqual(v2.total_marks_obtained, Decimal('80.00'))
        self.assertEqual(v2.percentage, Decimal('80.00'))

        v2_detail = v2.details.first()
        self.assertEqual(v2_detail.external_marks, Decimal('45.00'))
        self.assertEqual(v2_detail.total_marks, Decimal('80.00'))
        self.assertEqual(v2_detail.grade, 'A+')

        # Historical V1 is immutable
        with self.assertRaises(ResultImmutabilityViolation):
            self.published_v1.delete()

        # Check ResultCorrectionAudit entry (11.3.3)
        audits = ResultCorrectionAudit.objects.filter(original_result=self.published_v1)
        self.assertEqual(audits.count(), 1)
        audit_entry = audits.first()
        self.assertEqual(audit_entry.original_result, self.published_v1)
        self.assertEqual(audit_entry.superseding_result, v2)
        self.assertEqual(audit_entry.actor, self.approver)
        self.assertEqual(audit_entry.action, 'RESULT_SUPERSEDED')
        self.assertIn("Official university revaluation", audit_entry.reason)

        # Student query strictly returns V2 (latest), concealing superseded V1 from active summary
        student_results = ResultService.get_student_published_results(self.student)
        self.assertEqual(len(student_results), 1)
        self.assertEqual(student_results[0].version, 2)
        self.assertEqual(student_results[0].total_marks_obtained, Decimal('80.00'))
