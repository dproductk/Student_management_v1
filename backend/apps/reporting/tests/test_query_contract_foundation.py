"""
Unit tests for Reporting Query Contract Foundation (Task 14.1.1).
"""
from django.test import TestCase
from apps.reporting.domain.contracts import (
    ReportFilterSpec,
    PaginationSpec,
    ReportQueryResult,
    ReportingValidationError,
    MAX_EXPORT_LIMIT
)


class QueryContractFoundationTestCase(TestCase):
    def test_filter_spec_initialization(self):
        """Validates filter spec DTO behavior and dictionary export."""
        spec = ReportFilterSpec(
            department_id="dept-123",
            gender="FEMALE",
            status="ACTIVE"
        )
        d = spec.to_dict()
        self.assertEqual(d['department_id'], "dept-123")
        self.assertEqual(d['gender'], "FEMALE")
        self.assertEqual(d['status'], "ACTIVE")
        self.assertNotIn('academic_year_id', d)

    def test_pagination_bounds_validation(self):
        """Validates upper and lower bounds enforcement for pagination."""
        # Valid bounds
        p = PaginationSpec(limit=100, offset=50)
        self.assertEqual(p.limit, 100)
        self.assertEqual(p.offset, 50)

        # Exceeds max limit
        with self.assertRaises(ReportingValidationError):
            PaginationSpec(limit=MAX_EXPORT_LIMIT + 1)

        # Invalid zero or negative limit
        with self.assertRaises(ReportingValidationError):
            PaginationSpec(limit=0)

        # Invalid negative offset
        with self.assertRaises(ReportingValidationError):
            PaginationSpec(offset=-1)

    def test_report_query_result_envelope(self):
        """Validates envelope structure for query results."""
        res = ReportQueryResult(
            total_count=2,
            items=[{'id': 1}, {'id': 2}],
            filters_applied={'status': 'ACTIVE'},
            summary_metrics={'avg_score': 88.5}
        )
        self.assertEqual(res.total_count, 2)
        self.assertEqual(len(res.items), 2)
        self.assertEqual(res.summary_metrics['avg_score'], 88.5)
