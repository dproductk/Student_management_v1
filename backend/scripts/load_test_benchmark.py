"""
Load Testing & Performance Benchmark Script.
Simulates high-volume institutional datasets (large student cohorts, fee accounts, results)
and validates that search queries, analytics aggregations, and CSV exports remain performant.
Governed by TASKS.md 15.3.4, production-hardening-prd.md R-014, and ADR-030.
"""

import os
import sys
import time
from datetime import date
from decimal import Decimal
from pathlib import Path

# Setup Django standalone environment
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.db import connection, transaction
from apps.academic.models import Department, Program, AcademicYear, Semester, Batch
from apps.students.models import Student, StudentEnrollment
from apps.finance.models import FeeHead, FeeStructure, FeeStructureItem, StudentFeeAccount, FeeCharge
from apps.results.models import StudentResult
from apps.reporting.services.analytics_service import ReportingAnalyticsService
from apps.reporting.services.export_service import ReportingExportService


def run_load_benchmark(cohort_size: int = 200) -> dict:
    """
    Runs benchmark against a simulated cohort of students.
    Returns metrics dictionary with latencies and query counts.
    """
    print(f"\n[BENCHMARK] Generating test dataset: {cohort_size} students...")
    t0 = time.perf_counter()

    with transaction.atomic():
        ay, _ = AcademicYear.objects.get_or_create(
            label="2026-2027",
            defaults={'start_date': date(2026, 7, 1), 'end_date': date(2027, 6, 30), 'is_current': True}
        )
        dept, _ = Department.objects.get_or_create(name="Computer Engineering", defaults={'code': "CE_LOAD"})
        prog, _ = Program.objects.get_or_create(name="B.Tech CE", defaults={'code': "BCE_LOAD", 'department': dept})
        batch, _ = Batch.objects.get_or_create(name="Batch 2026-30", defaults={'department': dept, 'academic_year': ay})
        sem, _ = Semester.objects.get_or_create(academic_year=ay, number=1)

        # Batch create students
        students = [
            Student(
                candidate_name=f"Cohort Student {i}",
                gender="MALE" if i % 2 == 0 else "FEMALE",
                date_of_birth=date(2005, 1, 1),
                enrollment_no=f"LOAD_ENR_{i:05d}",
                application_id=f"LOAD_APP_{i:05d}",
                status="ACTIVE"
            )
            for i in range(cohort_size)
        ]
        Student.objects.bulk_create(students, ignore_conflicts=True)

        saved_students = list(Student.objects.filter(enrollment_no__startswith="LOAD_ENR_"))

        from apps.academic.models import Scheme
        scheme, _ = Scheme.objects.get_or_create(
            code="SCHEME_LOAD",
            defaults={'name': "Scheme Load", 'program': prog, 'effective_from_year': ay, 'is_active': True}
        )

        # Batch create enrollments
        enrollments = [
            StudentEnrollment(
                student=st,
                academic_year=ay,
                department=dept,
                program=prog,
                batch=batch,
                semester=sem,
                scheme=scheme,
                status="ACTIVE"
            )
            for st in saved_students
        ]
        StudentEnrollment.objects.bulk_create(enrollments, ignore_conflicts=True)

    setup_time = time.perf_counter() - t0
    print(f"[BENCHMARK] Dataset generated in {setup_time:.3f}s.")

    metrics = {}

    # Test 1: Student Directory Search and Pagination
    t1 = time.perf_counter()
    initial_queries = len(connection.queries)
    students_page = list(
        Student.objects.filter(status='ACTIVE')
        .select_related('user')
        .prefetch_related('enrollments', 'enrollments__program', 'enrollments__batch')[:50]
    )
    metrics['directory_query_time_ms'] = (time.perf_counter() - t1) * 1000
    metrics['directory_query_count'] = len(connection.queries) - initial_queries
    print(f"[BENCHMARK] Student Directory (50 rows): {metrics['directory_query_time_ms']:.2f}ms ({metrics['directory_query_count']} queries)")

    # Test 2: Cross-Module KPI Aggregation
    t2 = time.perf_counter()
    initial_queries = len(connection.queries)
    kpis = ReportingAnalyticsService.get_executive_kpis()
    metrics['kpi_aggregation_time_ms'] = (time.perf_counter() - t2) * 1000
    metrics['kpi_aggregation_query_count'] = len(connection.queries) - initial_queries
    print(f"[BENCHMARK] Executive KPIs Aggregation: {metrics['kpi_aggregation_time_ms']:.2f}ms ({metrics['kpi_aggregation_query_count']} queries)")

    # Test 3: Tabular CSV Export Streaming
    t3 = time.perf_counter()
    csv_response = ReportingExportService.export_dataset_to_csv(
        report_type='students',
        filters={'academic_year_id': str(ay.id)},
        limit=500
    )
    metrics['csv_export_time_ms'] = (time.perf_counter() - t3) * 1000
    print(f"[BENCHMARK] Bounded CSV Export (500 rows): {metrics['csv_export_time_ms']:.2f}ms")

    # Assertions / Pass Criteria
    assert metrics['directory_query_time_ms'] < 250, "Directory query exceeds 250ms SLA"
    assert metrics['kpi_aggregation_time_ms'] < 300, "KPI aggregation exceeds 300ms SLA"
    assert metrics['csv_export_time_ms'] < 1500, "CSV export exceeds 1500ms SLA"

    print("[BENCHMARK] ALL PERFORMANCE SLA CRITERIA PASSED!")
    return metrics


if __name__ == '__main__':
    run_load_benchmark(cohort_size=300)
