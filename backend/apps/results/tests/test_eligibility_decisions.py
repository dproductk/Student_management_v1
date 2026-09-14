from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.academic.models import Department, Program, AcademicYear, Semester, Scheme, Subject, SchemeSubject, Batch
from apps.students.models import Student, StudentEnrollment
from apps.results.models import (
    ResultImportBatch,
    StudentResult,
    EligibilityRule,
    EligibilityDecision,
)
from apps.results.services.result_service import ResultService
from apps.results.services.credit_eligibility_service import CreditEligibilityService

User = get_user_model()


class EligibilityDecisionsTestCase(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="academic_admin", email="admin@test.com", password="pass")
        self.approver = User.objects.create_user(username="controller_exam", email="coe@test.com", password="pass")

        self.dept = Department.objects.create(name="Civil Engineering", code="CE")
        self.program = Program.objects.create(name="B.Tech Civil", code="BTCE", department=self.dept)
        self.ay = AcademicYear.objects.create(label="2024-2025", start_date=date(2024, 8, 1), end_date=date(2025, 5, 31))
        self.sem = Semester.objects.create(academic_year=self.ay, number=2, start_date=date(2025, 1, 1), end_date=date(2025, 5, 31))
        self.batch = Batch.objects.create(department=self.dept, academic_year=self.ay, name="2024-CE")
        self.scheme = Scheme.objects.create(program=self.program, name="CE Scheme 2024", code="SCH_CE", effective_from_year=self.ay)

        # 4 Subjects, 5 credits each -> Total 20 credits
        self.subjects = []
        for i in range(1, 5):
            subj = Subject.objects.create(name=f"Civil Course {i}", code=f"CE20{i}")
            ss = SchemeSubject.objects.create(scheme=self.scheme, subject=subj, semester_number=2, credits=5, max_marks=100)
            self.subjects.append((subj, ss))

        # Configured Institutional Rule
        # Requires: >= 15 credits (3 subjects), <= 1 backlog, >= 75% attendance.
        # Detention if: > 2 backlogs OR < 50% attendance.
        self.rule = CreditEligibilityService.create_or_version_rule(
            name="Civil B.Tech Promotion Rule",
            code="RULE_CE_PROMO",
            min_credits=Decimal('15.0'),
            min_attendance=Decimal('75.00'),
            max_backlogs=1,
            detention_max_backlogs=2,
            detention_min_attendance=Decimal('50.00'),
            program_id=str(self.program.id),
            academic_year_id=str(self.ay.id),
            user=self.staff
        )

    def _setup_student_with_results(self, name, enr, marks_list):
        """Helper to create student, enrollment, publish batch results."""
        student = Student.objects.create(
            candidate_name=name, gender="MALE", date_of_birth=date(2005, 1, 1),
            enrollment_no=enr, application_id=f"APP_{enr}"
        )
        StudentEnrollment.objects.create(
            student=student, academic_year=self.ay, semester=self.sem,
            department=self.dept, program=self.program, batch=self.batch,
            scheme=self.scheme, status='ACTIVE'
        )
        batch = ResultService.create_import_batch(
            academic_year_id=str(self.ay.id), semester_id=str(self.sem.id),
            department_id=str(self.dept.id), program_id=str(self.program.id),
            file_name=f"{enr}_res.csv", uploaded_by=self.staff
        )
        rows_data = []
        for idx, (subj, ss) in enumerate(self.subjects):
            im, em = marks_list[idx]
            rows_data.append({
                'student_identifier': enr,
                'subject_code': subj.code,
                'internal_marks': str(im),
                'external_marks': str(em)
            })

        ResultService.extract_and_stage_rows(batch, rows_data)
        ResultService.validate_and_associate_rows(batch)
        ResultService.approve_result_batch(batch, self.approver)
        ResultService.publish_result_batch(batch, self.approver)

        return student

    def test_eligible_decision_vertical_slice(self):
        """12.2.2 & 12.2.3: Student meeting all criteria is marked ELIGIBLE."""
        # Student passes all 4 courses: 20 credits, 0 backlogs
        std = self._setup_student_with_results("Karan Patel", "ENR_EL_01", [(40, 50), (35, 45), (38, 52), (40, 48)])
        decision = CreditEligibilityService.evaluate_student_eligibility(
            student=std, academic_year=self.ay, semester=self.sem, rule=self.rule,
            attendance_percentage=Decimal('85.00'), user=self.staff
        )

        self.assertEqual(decision.decision, 'ELIGIBLE')
        self.assertEqual(decision.credits_earned, Decimal('20.0'))
        self.assertEqual(decision.backlogs_count, 0)
        self.assertEqual(decision.rule.id, self.rule.id)
        self.assertEqual(decision.rule_version, self.rule.version)
        self.assertTrue(decision.is_latest)
        self.assertEqual(decision.detention_reason, '')

    def test_not_eligible_decision_vertical_slice(self):
        """12.2.3: Student with insufficient credits or backlogs is NOT_ELIGIBLE (not detained)."""
        # Student fails 2 courses (CE203, CE204): 10 credits earned (< 15 min), 2 backlogs (> 1 allowed, <= 2 detention limit)
        std = self._setup_student_with_results("Rahul Mehra", "ENR_NE_01", [(40, 50), (35, 45), (10, 15), (12, 18)])
        decision = CreditEligibilityService.evaluate_student_eligibility(
            student=std, academic_year=self.ay, semester=self.sem, rule=self.rule,
            attendance_percentage=Decimal('80.00'), user=self.staff
        )

        self.assertEqual(decision.decision, 'NOT_ELIGIBLE')
        self.assertEqual(decision.credits_earned, Decimal('10.0'))
        self.assertEqual(decision.backlogs_count, 2)
        self.assertIn("Earned credits", decision.remarks)
        self.assertIn("Backlogs", decision.remarks)
        self.assertEqual(decision.detention_reason, '')

    def test_detained_decision_due_to_excessive_backlogs(self):
        """12.2.3: Student with backlogs exceeding detention threshold is DETAINED."""
        # Student fails 3 courses (> 2 detention limit): 5 credits earned, 3 backlogs
        std = self._setup_student_with_results("Amit Sen", "ENR_DET_01", [(40, 50), (10, 15), (12, 18), (8, 10)])
        decision = CreditEligibilityService.evaluate_student_eligibility(
            student=std, academic_year=self.ay, semester=self.sem, rule=self.rule,
            attendance_percentage=Decimal('80.00'), user=self.staff
        )

        self.assertEqual(decision.decision, 'DETAINED')
        self.assertEqual(decision.backlogs_count, 3)
        self.assertIn("Backlogs (3) exceeded detention threshold (2)", decision.detention_reason)

    def test_detained_decision_due_to_low_attendance(self):
        """12.2.3: Student with attendance below detention threshold is DETAINED."""
        # Student passes all subjects but attendance is 42% (< 50% detention threshold)
        std = self._setup_student_with_results("Sneha Joshi", "ENR_DET_02", [(40, 50), (35, 45), (38, 52), (40, 48)])
        decision = CreditEligibilityService.evaluate_student_eligibility(
            student=std, academic_year=self.ay, semester=self.sem, rule=self.rule,
            attendance_percentage=Decimal('42.00'), user=self.staff
        )

        self.assertEqual(decision.decision, 'DETAINED')
        self.assertIn("Attendance (42.00%) below detention minimum (50.00%)", decision.detention_reason)

    def test_cohort_batch_evaluation(self):
        """12.2.3: Cohort evaluation processes all students in program semester."""
        std1 = self._setup_student_with_results("Cohort Student 1", "ENR_C1", [(40, 50), (35, 45), (38, 52), (40, 48)])
        std2 = self._setup_student_with_results("Cohort Student 2", "ENR_C2", [(10, 10), (10, 15), (12, 18), (8, 10)])

        decisions = CreditEligibilityService.evaluate_cohort_eligibility(
            academic_year=self.ay,
            semester=self.sem,
            program=self.program,
            rule=self.rule,
            user=self.staff
        )

        self.assertEqual(len(decisions), 2)
        dec_map = {d.student.enrollment_no: d.decision for d in decisions}
        self.assertEqual(dec_map['ENR_C1'], 'ELIGIBLE')
        self.assertEqual(dec_map['ENR_C2'], 'DETAINED')
