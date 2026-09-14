"""
Unit tests for Report filtering, sorting, pagination, and export (Task 14.3.1).
"""
from datetime import date
from django.test import TestCase
from apps.students.models import Student
from apps.reporting.services.export_service import ReportingExportService
from apps.reporting.domain.contracts import ReportingValidationError, MAX_EXPORT_LIMIT


class FilteringSortingExportTestCase(TestCase):
    def setUp(self):
        self.s1 = Student.objects.create(
            candidate_name="Export Student 1",
            gender="MALE",
            date_of_birth=date(2004, 1, 1),
            enrollment_no="ENR_EXP_01",
            application_id="APP_EXP_01"
        )
        self.s2 = Student.objects.create(
            candidate_name="Export Student 2",
            gender="FEMALE",
            date_of_birth=date(2004, 2, 2),
            enrollment_no="ENR_EXP_02",
            application_id="APP_EXP_02"
        )

    def test_csv_export_generation(self):
        """14.3.1: Validates CSV headers, row data, and content type."""
        response = ReportingExportService.export_dataset_to_csv('students', limit=10)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="report_students.csv"', response['Content-Disposition'])

        content = response.content.decode('utf-8')
        lines = content.strip().split('\r\n')
        self.assertGreaterEqual(len(lines), 3)  # Header + 2 students
        self.assertIn('Candidate Name', lines[0])
        self.assertIn('Export Student 1', content)
        self.assertIn('Export Student 2', content)

    def test_export_bounds_enforcement(self):
        """Validates that export ceiling cannot exceed MAX_EXPORT_LIMIT."""
        with self.assertRaises(ReportingValidationError):
            ReportingExportService.export_dataset_to_csv('students', limit=MAX_EXPORT_LIMIT + 1)

    def test_invalid_report_type_raises_error(self):
        """Validates rejection of unknown report types."""
        with self.assertRaises(ReportingValidationError):
            ReportingExportService.export_dataset_to_csv('unknown_dataset')
