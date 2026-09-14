"""
Query-Performance and Database Index Validation Audit Test Suite.
Governed by TASKS.md 15.3.1, production-hardening-prd.md R-010, R-011, and ADR-030.
"""

from datetime import date
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.identity.models import User, Role, UserRole
from apps.academic.models import Department, Program, AcademicYear, Semester, Batch, Scheme, Subject, SchemeSubject
from apps.students.models import Student
from apps.students.services.student_service import StudentService
from apps.finance.models import FeeHead, FeeStructure, FeeStructureItem, StudentFeeAccount, FeeCharge
from apps.results.models import StudentResult, StudentResultDetail


class QueryPerformanceAndIndexAuditTests(TestCase):
    """
    Validates index coverage, absence of N+1 queries, and bounded database query profiles
    across high-volume student, finance, and academic operations.
    """

    def setUp(self):
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            username="staff_perf",
            email="staff_perf@example.com",
            password="TestPassword123!",
            is_staff=True,
            is_superuser=True
        )
        self.client.force_authenticate(user=self.staff_user)

        self.dept = Department.objects.create(name="Electronics", code="EC_PERF")
        self.prog = Program.objects.create(name="B.Tech EC", code="BEC_PERF", department=self.dept)
        self.ay = AcademicYear.objects.create(
            label="2026-2027",
            start_date=date(2026, 7, 1),
            end_date=date(2027, 6, 30),
            is_current=True
        )
        self.sem = Semester.objects.create(academic_year=self.ay, number=1)
        self.batch = Batch.objects.create(name="Batch 2026-30", department=self.dept, academic_year=self.ay)

        # Create cohort of 15 students
        self.students = []
        for i in range(15):
            st = Student.objects.create(
                candidate_name=f"Student Perf {i}",
                gender="MALE" if i % 2 == 0 else "FEMALE",
                date_of_birth=date(2005, 1, 1),
                enrollment_no=f"ENR_PERF_{i:04d}",
                application_id=f"APP_PERF_{i:04d}",
                board_enrollment_no=f"BRD_PERF_{i:04d}",
                status="ACTIVE"
            )
            self.students.append(st)

    def test_high_frequency_lookup_fields_have_database_indexes(self):
        """Verify high-frequency query fields on Student have database indexes or uniqueness."""
        indexed_fields = ['enrollment_no', 'application_id', 'board_enrollment_no']
        for field_name in indexed_fields:
            field = Student._meta.get_field(field_name)
            has_index = field.db_index or field.unique
            self.assertTrue(
                has_index,
                f"Field '{field_name}' on Student model must be indexed or unique for fast lookups."
            )

    def test_student_directory_list_query_count_is_bounded(self):
        """Verify fetching student list does not incur N+1 queries per row."""
        # Querying 15 students should execute in exactly 5 bounded queries (count + students + prefetches)
        with self.assertNumQueries(5):
            response = self.client.get('/api/v1/students/?limit=15')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reporting_overview_kpis_query_count_is_bounded(self):
        """Verify cross-module analytics overview executes in bounded queries."""
        # Reporting overview aggregates cross-module KPIs in 9 bounded queries
        with self.assertNumQueries(9):
            response = self.client.get('/api/v1/reporting/analytics/kpis/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
