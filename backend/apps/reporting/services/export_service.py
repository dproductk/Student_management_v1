"""
Reporting Export Service.

Implements Task 14.3.1: Bounded report export in CSV format.
Enforces maximum row bounds to prevent unbounded extraction and memory exhaustion.
"""
import csv
import io
from typing import Dict, Any, Optional
from django.http import HttpResponse
from apps.reporting.domain.contracts import MAX_EXPORT_LIMIT, ReportingValidationError
from apps.students.services.student_reporting import StudentReportingQueryService
from apps.finance.services.finance_reporting import FinanceReportingQueryService
from apps.results.services.results_reporting import ResultsReportingQueryService


class ReportingExportService:
    """Read-only export engine generating bounded CSV files."""

    @staticmethod
    def export_dataset_to_csv(
        report_type: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 1000
    ) -> HttpResponse:
        """Generates a bounded CSV HTTP response for the requested report type."""
        if limit > MAX_EXPORT_LIMIT:
            raise ReportingValidationError(f"Export limit cannot exceed {MAX_EXPORT_LIMIT} records.")
        if limit < 1:
            raise ReportingValidationError("Export limit must be at least 1.")

        filters = filters or {}
        output = io.StringIO()
        writer = csv.writer(output)

        filename = f"report_{report_type}.csv"

        if report_type == 'students':
            # Header
            writer.writerow([
                'ID', 'Candidate Name', 'Enrollment No', 'Application ID',
                'Gender', 'Status', 'Department', 'Program', 'Batch', 'Semester'
            ])
            data = StudentReportingQueryService.get_student_reporting_records(filters, limit=limit, offset=0)
            for r in data['records']:
                writer.writerow([
                    r['id'], r['candidate_name'], r['enrollment_no'], r['application_id'],
                    r['gender'], r['status'], r['department_name'], r['program_name'],
                    r['batch_name'], r['semester_number'] or ''
                ])

        elif report_type == 'fee_defaulters':
            writer.writerow([
                'Student ID', 'Candidate Name', 'Enrollment No', 'Department',
                'Program', 'Batch', 'Total Billed (INR)', 'Total Paid (INR)', 'Outstanding Balance (INR)'
            ])
            data = FinanceReportingQueryService.get_defaulters_reporting_records(filters, limit=limit, offset=0)
            for r in data['records']:
                writer.writerow([
                    r['student_id'], r['candidate_name'], r['enrollment_no'],
                    r['department_name'], r['program_name'], r['batch_name'],
                    f"{r['total_billed']:.2f}", f"{r['total_paid']:.2f}", f"{r['outstanding_balance']:.2f}"
                ])

        elif report_type == 'academic_results':
            writer.writerow([
                'Result ID', 'Student ID', 'Candidate Name', 'Enrollment No',
                'Department', 'Program', 'Semester', 'Marks Obtained', 'Max Marks',
                'Percentage', 'SGPA', 'CGPA', 'Status'
            ])
            data = ResultsReportingQueryService.get_results_reporting_records(filters, limit=limit, offset=0)
            for r in data['records']:
                writer.writerow([
                    r['result_id'], r['student_id'], r['candidate_name'], r['enrollment_no'],
                    r['department_name'], r['program_name'], r['semester_number'] or '',
                    f"{r['total_marks_obtained']:.2f}", f"{r['total_max_marks']:.2f}",
                    f"{r['percentage']:.2f}%", f"{r['sgpa']:.2f}", f"{r['cgpa']:.2f}", r['status']
                ])

        else:
            raise ReportingValidationError(f"Invalid report type: '{report_type}'. Allowed types: ['students', 'fee_defaulters', 'academic_results']")

        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
