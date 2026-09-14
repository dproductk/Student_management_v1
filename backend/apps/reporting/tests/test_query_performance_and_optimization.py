"""
Unit tests for Reporting query-performance validation and evidence-based optimization (Task 14.3.2).
"""
from datetime import date
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.db import connection
from apps.students.models import Student, StudentEnrollment
from apps.academic.models import Department, Program, AcademicYear, Semester, Batch, Scheme
from apps.students.services.student_reporting import StudentReportingQueryService


class QueryPerformanceOptimizationTestCase(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Performance Dept", code="PERF")
        self.prog = Program.objects.create(name="B.Tech Perf", code="BT_PERF", department=self.dept)
        self.ay = AcademicYear.objects.create(label="2024-2025", start_date=date(2024, 7, 1), end_date=date(2025, 6, 30))
        self.sem = Semester.objects.create(academic_year=self.ay, number=1)
        self.batch = Batch.objects.create(name="Batch 2024", department=self.dept, academic_year=self.ay)
        self.scheme = Scheme.objects.create(name="Scheme 2024", code="SCH_PERF_24", program=self.prog, effective_from_year=self.ay)

        # Create 15 students with enrollments
        for i in range(15):
            s = Student.objects.create(
                candidate_name=f"Perf Student {i}",
                gender="MALE" if i % 2 == 0 else "FEMALE",
                date_of_birth=date(2004, 1, 1),
                enrollment_no=f"ENR_PERF_{i:02d}",
                application_id=f"APP_PERF_{i:02d}",
                status="ACTIVE"
            )
            StudentEnrollment.objects.create(
                student=s,
                academic_year=self.ay,
                department=self.dept,
                program=self.prog,
                batch=self.batch,
                semester=self.sem,
                scheme=self.scheme,
                status="ACTIVE"
            )

    def test_population_query_performance(self):
        """14.3.2: Validates that summary aggregation executes in bounded constant queries."""
        with CaptureQueriesContext(connection) as ctx:
            summary = StudentReportingQueryService.get_population_summary()
            self.assertEqual(summary['total_students'], 15)

        # Count queries must be small and constant (<= 7 queries), not proportional to N (15)
        self.assertLessEqual(len(ctx.captured_queries), 7)

    def test_tabular_records_prefetch_optimization(self):
        """14.3.2: Validates no N+1 query explosion when fetching paginated student records."""
        with CaptureQueriesContext(connection) as ctx:
            records = StudentReportingQueryService.get_student_reporting_records(limit=10, offset=0)
            self.assertEqual(len(records['records']), 10)

        # Base query + count + prefetches: should be <= 8 queries, not 10+ queries per student row
        self.assertLessEqual(len(ctx.captured_queries), 8)
