from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.academic.models import Department, Program, AcademicYear, Semester, Scheme, Subject, SchemeSubject, Batch
from apps.students.models import Student, StudentEnrollment
from apps.results.models import ResultImportBatch, StudentResult, StudentResultDetail, StudentCredit
from apps.results.services.result_service import ResultService
from apps.results.services.credit_eligibility_service import CreditEligibilityService
from apps.results.domain.invariants import (
    CreditCalculationError,
    ResultImmutabilityViolation,
)

User = get_user_model()


class CreditsCalculationTestCase(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="staff_exam", email="exam@test.com", password="pass")
        self.approver = User.objects.create_user(username="dean_academic", email="dean@test.com", password="pass")

        self.dept = Department.objects.create(name="Computer Science", code="CS")
        self.program = Program.objects.create(name="B.Tech Computer Science", code="BTCS", department=self.dept)
        self.ay = AcademicYear.objects.create(label="2024-2025", start_date=date(2024, 8, 1), end_date=date(2025, 5, 31))
        self.sem = Semester.objects.create(academic_year=self.ay, number=1, start_date=date(2024, 8, 1), end_date=date(2024, 12, 31))
        self.batch = Batch.objects.create(department=self.dept, academic_year=self.ay, name="2024-CS")
        self.scheme = Scheme.objects.create(program=self.program, name="CS Scheme 2024", code="SCH_CS", effective_from_year=self.ay)

        # 3 Subjects with distinct credits
        self.subj1 = Subject.objects.create(name="Programming in Python", code="CS101")
        self.ss1 = SchemeSubject.objects.create(
            scheme=self.scheme, subject=self.subj1, semester_number=1, credits=4, max_marks=100
        )

        self.subj2 = Subject.objects.create(name="Discrete Mathematics", code="CS102")
        self.ss2 = SchemeSubject.objects.create(
            scheme=self.scheme, subject=self.subj2, semester_number=1, credits=3, max_marks=100
        )

        self.subj3 = Subject.objects.create(name="Digital Electronics", code="CS103")
        self.ss3 = SchemeSubject.objects.create(
            scheme=self.scheme, subject=self.subj3, semester_number=1, credits=3, max_marks=100
        )

        self.student = Student.objects.create(
            candidate_name="Priya Sharma",
            gender="FEMALE",
            date_of_birth=date(2005, 4, 10),
            enrollment_no="ENR2024101",
            application_id="APP2024101",
            email="priya@test.com"
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

    def test_result_to_credit_calculation_vertical_slice(self):
        """12.1.1: Result-to-credit calculation from published results."""
        # Create and stage a result batch
        batch = ResultService.create_import_batch(
            academic_year_id=str(self.ay.id),
            semester_id=str(self.sem.id),
            department_id=str(self.dept.id),
            program_id=str(self.program.id),
            file_name="sem1_results.csv",
            uploaded_by=self.staff
        )
        rows_data = [
            {'student_identifier': self.student.enrollment_no, 'subject_code': 'CS101', 'internal_marks': '35', 'external_marks': '50'},
            {'student_identifier': self.student.enrollment_no, 'subject_code': 'CS102', 'internal_marks': '30', 'external_marks': '45'},
            {'student_identifier': self.student.enrollment_no, 'subject_code': 'CS103', 'internal_marks': '10', 'external_marks': '15'}, # Fail
        ]
        ResultService.extract_and_stage_rows(batch, rows_data)
        ResultService.validate_and_associate_rows(batch)

        # Attempting credit calculation before publication must fail
        student_res = StudentResult.objects.get(student=self.student, semester=self.sem)
        with self.assertRaises(CreditCalculationError):
            CreditEligibilityService.calculate_credits_for_result(student_res)

        # Approve and publish batch
        ResultService.approve_result_batch(batch, self.approver)
        ResultService.publish_result_batch(batch, self.approver)

        # Verify Credit was automatically generated upon publication
        credit = StudentCredit.objects.get(student=self.student, semester=self.sem, is_latest=True)
        self.assertEqual(credit.credits_attempted, Decimal('10.0')) # 4 + 3 + 3
        self.assertEqual(credit.credits_earned, Decimal('7.0')) # CS101 (4) + CS102 (3) passed; CS103 failed
        self.assertEqual(credit.backlogs_count, 1)
        self.assertIsNotNone(credit.sgpa)
        self.assertTrue(credit.is_latest)
        self.assertEqual(credit.version, 1)

    def test_historical_credit_calculation_integrity_vertical_slice(self):
        """12.1.2: Historical credit calculation integrity preserved across supersession."""
        # 1. Publish batch with 1 backlog
        batch = ResultService.create_import_batch(
            academic_year_id=str(self.ay.id),
            semester_id=str(self.sem.id),
            department_id=str(self.dept.id),
            program_id=str(self.program.id),
            file_name="sem1_results.csv",
            uploaded_by=self.staff
        )
        rows_data = [
            {'student_identifier': self.student.enrollment_no, 'subject_code': 'CS101', 'internal_marks': '35', 'external_marks': '50'},
            {'student_identifier': self.student.enrollment_no, 'subject_code': 'CS102', 'internal_marks': '30', 'external_marks': '45'},
            {'student_identifier': self.student.enrollment_no, 'subject_code': 'CS103', 'internal_marks': '10', 'external_marks': '15'},
        ]
        ResultService.extract_and_stage_rows(batch, rows_data)
        ResultService.validate_and_associate_rows(batch)
        ResultService.approve_result_batch(batch, self.approver)
        ResultService.publish_result_batch(batch, self.approver)

        v1_credit = StudentCredit.objects.get(student=self.student, semester=self.sem, version=1)
        self.assertEqual(v1_credit.credits_earned, Decimal('7.0'))
        self.assertTrue(v1_credit.is_latest)

        # 2. Re-evaluation / Correction request for CS103 mark rectification
        res_v1 = StudentResult.objects.get(student=self.student, semester=self.sem, version=1)
        corr_req = ResultService.request_result_correction(
            target_result=res_v1,
            requested_by=self.staff,
            reason="Revaluation pass for CS103",
            proposed_changes={'subjects': {'CS103': {'internal_marks': 35, 'external_marks': 45}}}
        )
        ResultService.review_result_correction(corr_req, reviewer=self.approver, approved=True)

        # 3. Verify V1 credit calculation record is PRESERVED historically
        v1_credit.refresh_from_db()
        self.assertFalse(v1_credit.is_latest)
        self.assertEqual(v1_credit.credits_earned, Decimal('7.0'))
        self.assertEqual(v1_credit.backlogs_count, 1)

        # 4. Verify V2 credit calculation record accurately reflects corrected marks
        v2_credit = StudentCredit.objects.get(student=self.student, semester=self.sem, version=2)
        self.assertTrue(v2_credit.is_latest)
        self.assertEqual(v2_credit.credits_earned, Decimal('10.0')) # all 3 passed now!
        self.assertEqual(v2_credit.backlogs_count, 0)
        self.assertEqual(v2_credit.result_version, 2)

        # 5. Immutability guard: Attempting to delete historical credit record must be rejected
        with self.assertRaises(ResultImmutabilityViolation):
            v1_credit.delete()
