from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.academic.models import Department, Program, AcademicYear, Semester, Scheme, Subject, SchemeSubject, Batch
from apps.students.models import Student, StudentEnrollment
from apps.results.models import (
    StudentResult,
    EligibilityRule,
    EligibilityDecision,
    NextYearEligibilityList,
)
from apps.results.services.result_service import ResultService
from apps.results.services.credit_eligibility_service import CreditEligibilityService
from apps.results.domain.invariants import ResultImmutabilityViolation

User = get_user_model()


class NextYearEligibilityTestCase(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="admin_registrar", email="registrar@test.com", password="pass")
        self.dean = User.objects.create_user(username="dean_academic", email="dean@test.com", password="pass")

        self.dept = Department.objects.create(name="Electrical Engineering", code="EE")
        self.program = Program.objects.create(name="B.Tech Electrical", code="BTEE", department=self.dept)
        self.ay = AcademicYear.objects.create(label="2024-2025", start_date=date(2024, 8, 1), end_date=date(2025, 5, 31))
        self.next_ay = AcademicYear.objects.create(label="2025-2026", start_date=date(2025, 8, 1), end_date=date(2026, 5, 31))
        self.sem = Semester.objects.create(academic_year=self.ay, number=2, start_date=date(2025, 1, 1), end_date=date(2025, 5, 31))
        self.batch = Batch.objects.create(department=self.dept, academic_year=self.ay, name="2024-EE")
        self.scheme = Scheme.objects.create(program=self.program, name="EE Scheme 2024", code="SCH_EE", effective_from_year=self.ay)

        # 3 Subjects, 4 credits each
        self.subj1 = Subject.objects.create(name="Circuits", code="EE201")
        self.ss1 = SchemeSubject.objects.create(scheme=self.scheme, subject=self.subj1, semester_number=2, credits=4, max_marks=100)
        self.subj2 = Subject.objects.create(name="Electromagnetics", code="EE202")
        self.ss2 = SchemeSubject.objects.create(scheme=self.scheme, subject=self.subj2, semester_number=2, credits=4, max_marks=100)
        self.subj3 = Subject.objects.create(name="Signals", code="EE203")
        self.ss3 = SchemeSubject.objects.create(scheme=self.scheme, subject=self.subj3, semester_number=2, credits=4, max_marks=100)

        self.rule = CreditEligibilityService.create_or_version_rule(
            name="EE Promotion Rule",
            code="RULE_EE_PROMO",
            min_credits=Decimal('8.0'),
            min_attendance=Decimal('75.00'),
            max_backlogs=1,
            detention_max_backlogs=1,
            detention_min_attendance=Decimal('50.00'),
            program_id=str(self.program.id),
            academic_year_id=str(self.ay.id),
            user=self.staff
        )

    def _setup_student(self, name, enr, marks_list):
        student = Student.objects.create(
            candidate_name=name, gender="MALE", date_of_birth=date(2005, 2, 1),
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
        rows_data = [
            {'student_identifier': enr, 'subject_code': 'EE201', 'internal_marks': str(marks_list[0][0]), 'external_marks': str(marks_list[0][1])},
            {'student_identifier': enr, 'subject_code': 'EE202', 'internal_marks': str(marks_list[1][0]), 'external_marks': str(marks_list[1][1])},
            {'student_identifier': enr, 'subject_code': 'EE203', 'internal_marks': str(marks_list[2][0]), 'external_marks': str(marks_list[2][1])},
        ]
        ResultService.extract_and_stage_rows(batch, rows_data)
        ResultService.validate_and_associate_rows(batch)
        ResultService.approve_result_batch(batch, self.dean)
        ResultService.publish_result_batch(batch, self.dean)

        return student

    def test_next_year_eligibility_list_generation_vertical_slice(self):
        """12.2.4: Next-year eligibility list generation connects StudentEnrollment and EligibilityDecisions."""
        # Student 1: Passes all -> ELIGIBLE (12 credits)
        std1 = self._setup_student("Vikram Roy", "ENR_V1", [(40, 50), (35, 45), (40, 50)])
        # Student 2: 2 backlogs -> DETAINED (> 1 detention limit is 2 backlogs)
        std2 = self._setup_student("Sunil Kumar", "ENR_S2", [(40, 50), (10, 10), (10, 10)])
        # Student 3: 1 backlog (8 credits) -> ELIGIBLE (min credits 8, max backlogs 1)
        std3 = self._setup_student("Manish Rao", "ENR_M3", [(40, 50), (35, 45), (10, 10)])

        promotion_list = CreditEligibilityService.generate_next_year_eligibility_list(
            academic_year=self.ay,
            semester=self.sem,
            program=self.program,
            target_academic_year=self.next_ay,
            target_semester_number=3,
            user=self.staff
        )

        self.assertEqual(promotion_list.total_students, 3)
        self.assertEqual(promotion_list.eligible_count, 2) # std1, std3
        self.assertEqual(promotion_list.detained_count, 1) # std2
        self.assertEqual(promotion_list.not_eligible_count, 0)
        self.assertEqual(promotion_list.target_semester_number, 3)
        self.assertEqual(len(promotion_list.items), 3)

        # Snapshot check: enrollment details are captured accurately
        items_map = {item['enrollment_no']: item['decision'] for item in promotion_list.items}
        self.assertEqual(items_map['ENR_V1'], 'ELIGIBLE')
        self.assertEqual(items_map['ENR_S2'], 'DETAINED')
        self.assertEqual(items_map['ENR_M3'], 'ELIGIBLE')

    def test_eligibility_decision_history_and_correction_integrity(self):
        """12.2.5: Decision history preserved when results are corrected (V1 -> V2)."""
        # 1. Student initially has 2 backlogs -> DETAINED
        std = self._setup_student("Anjali Nair", "ENR_HIST_01", [(40, 50), (10, 10), (10, 10)])
        dec_v1 = CreditEligibilityService.evaluate_student_eligibility(
            student=std, academic_year=self.ay, semester=self.sem, rule=self.rule, user=self.staff
        )
        self.assertEqual(dec_v1.decision, 'DETAINED')
        self.assertEqual(dec_v1.version, 1)
        self.assertTrue(dec_v1.is_latest)

        # 2. Result correction approved: EE202 marks corrected from 20 (fail) to 80 (pass)
        res_v1 = StudentResult.objects.get(student=std, semester=self.sem, version=1)
        corr_req = ResultService.request_result_correction(
            target_result=res_v1,
            requested_by=self.staff,
            reason="Rechecking rectification for EE202",
            proposed_changes={'subjects': {'EE202': {'internal_marks': 35, 'external_marks': 45}}}
        )
        ResultService.review_result_correction(corr_req, reviewer=self.dean, approved=True)

        # 3. Re-evaluate eligibility for the student
        dec_v2 = CreditEligibilityService.evaluate_student_eligibility(
            student=std, academic_year=self.ay, semester=self.sem, rule=self.rule, user=self.staff
        )

        # 4. Verify Decision V2 is ELIGIBLE (now only 1 backlog, 8 credits earned)
        self.assertEqual(dec_v2.decision, 'ELIGIBLE')
        self.assertEqual(dec_v2.version, 2)
        self.assertTrue(dec_v2.is_latest)
        self.assertEqual(dec_v2.credits_earned, Decimal('8.0'))
        self.assertEqual(dec_v2.backlogs_count, 1)

        # 5. Verify Decision V1 remains historically preserved
        dec_v1.refresh_from_db()
        self.assertFalse(dec_v1.is_latest)
        self.assertEqual(dec_v1.decision, 'DETAINED')
        self.assertEqual(dec_v1.version, 1)
        self.assertEqual(dec_v1.superseded_by.id, dec_v2.id)

        # 6. Immutability check: historical decision cannot be deleted
        with self.assertRaises(ResultImmutabilityViolation):
            dec_v1.delete()
