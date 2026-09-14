"""
Unit tests for Results & Eligibility reporting interface (Task 14.1.4 & 14.2.5).
"""
from datetime import date
from decimal import Decimal
from django.test import TestCase
from apps.students.models import Student
from apps.academic.models import AcademicYear, Department, Program, Semester, Batch
from apps.results.models import StudentResult, EligibilityDecision, EligibilityRule
from apps.results.services.results_reporting import ResultsReportingQueryService


class ResultsReportingInterfaceTestCase(TestCase):
    def setUp(self):
        self.ay = AcademicYear.objects.create(label="2024-2025", start_date=date(2024, 7, 1), end_date=date(2025, 6, 30))
        self.dept = Department.objects.create(name="Mechanical", code="MECH")
        self.prog = Program.objects.create(name="B.Tech Mechanical", code="BT_MECH", department=self.dept)
        self.sem = Semester.objects.create(academic_year=self.ay, number=2)

        self.s1 = Student.objects.create(
            candidate_name="Res Student 1",
            gender="MALE",
            date_of_birth=date(2004, 8, 8),
            enrollment_no="ENR_RES_01",
            application_id="APP_RES_01"
        )
        self.s2 = Student.objects.create(
            candidate_name="Res Student 2",
            gender="FEMALE",
            date_of_birth=date(2004, 9, 9),
            enrollment_no="ENR_RES_02",
            application_id="APP_RES_02"
        )

        self.batch = Batch.objects.create(name="Batch Mech", department=self.dept, academic_year=self.ay)

        # Result 1: Distinction PASS
        StudentResult.objects.create(
            student=self.s1,
            academic_year=self.ay,
            semester=self.sem,
            batch=self.batch,
            total_marks_obtained=Decimal('640.00'),
            total_max_marks=Decimal('800.00'),
            percentage=Decimal('80.00'),
            sgpa=Decimal('8.50'),
            cgpa=Decimal('8.50'),
            status='PUBLISHED',
            result_status='PASS',
            is_latest=True
        )

        # Result 2: FAIL
        StudentResult.objects.create(
            student=self.s2,
            academic_year=self.ay,
            semester=self.sem,
            batch=self.batch,
            total_marks_obtained=Decimal('320.00'),
            total_max_marks=Decimal('800.00'),
            percentage=Decimal('40.00'),
            sgpa=Decimal('4.00'),
            cgpa=Decimal('4.00'),
            status='PUBLISHED',
            result_status='FAIL',
            is_latest=True
        )

        self.rule = EligibilityRule.objects.create(
            name="General Promotion Rule",
            code="GEN_PROM",
            academic_year=self.ay,
            program=self.prog,
            version=1
        )

        # Eligibility decisions
        EligibilityDecision.objects.create(
            student=self.s1,
            academic_year=self.ay,
            semester=self.sem,
            rule=self.rule,
            rule_version=1,
            decision='ELIGIBLE',
            backlogs_count=0,
            is_latest=True
        )
        EligibilityDecision.objects.create(
            student=self.s2,
            academic_year=self.ay,
            semester=self.sem,
            rule=self.rule,
            rule_version=1,
            decision='DETAINED',
            backlogs_count=5,
            is_latest=True
        )

    def test_academic_performance_summary(self):
        """14.2.5: Academic/result analytics."""
        perf = ResultsReportingQueryService.get_academic_performance_summary()
        self.assertEqual(perf['total_results'], 2)
        self.assertEqual(perf['passed_count'], 1)
        self.assertEqual(perf['failed_count'], 1)
        self.assertEqual(perf['pass_percentage'], 50.0)
        self.assertEqual(perf['distinction_count'], 1)
        self.assertEqual(perf['average_sgpa'], 6.25)

    def test_eligibility_status_summary(self):
        """14.2.5: Eligibility decisions summary."""
        elig = ResultsReportingQueryService.get_eligibility_status_summary()
        self.assertEqual(elig['total_decisions'], 2)
        self.assertEqual(elig['eligible_count'], 1)
        self.assertEqual(elig['detained_count'], 1)
        self.assertEqual(elig['eligibility_rate'], 50.0)

    def test_results_reporting_records(self):
        """Tabular results query."""
        res = ResultsReportingQueryService.get_results_reporting_records()
        self.assertEqual(res['total_count'], 2)
        self.assertEqual(len(res['records']), 2)
