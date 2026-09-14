"""
Reporting Analytics Aggregator Service.

Implements Section 14.2 analytics requirements by orchestrating module-owned
query interfaces while preserving source-of-truth boundaries.
"""
from typing import Dict, Any, Optional
from apps.students.services.student_reporting import StudentReportingQueryService
from apps.finance.services.finance_reporting import FinanceReportingQueryService
from apps.results.services.results_reporting import ResultsReportingQueryService
from apps.verification.services.verification_reporting import VerificationReportingQueryService
from apps.audit.services.audit_reporting import AuditReportingQueryService


class ReportingAnalyticsService:
    """Read-only cross-module analytics aggregator service."""

    @staticmethod
    def get_executive_kpis(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Provides high-level institutional KPI summary cards."""
        pop = StudentReportingQueryService.get_population_summary(filters)
        fin = FinanceReportingQueryService.get_fee_status_summary(filters)
        res = ResultsReportingQueryService.get_academic_performance_summary(filters)
        ver = VerificationReportingQueryService.get_verification_status_summary(filters)

        return {
            'total_students': pop['total_students'],
            'active_students': pop['active_students'],
            'total_enrolled': pop['total_enrolled'],
            'total_billed_fees': fin['total_billed'],
            'total_collected_fees': fin['total_collected'],
            'outstanding_fees': fin['total_outstanding'],
            'collection_percentage': fin['collection_percentage'],
            'academic_pass_percentage': res['pass_percentage'],
            'average_cgpa': res['average_cgpa'],
            'pending_verifications': ver['pending_count'],
            'verification_approval_rate': ver['approval_rate'],
        }

    @staticmethod
    def get_student_population_analytics(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """14.2.1: Student population analytics vertical slice."""
        return StudentReportingQueryService.get_population_summary(filters)

    @staticmethod
    def get_demographics_analytics(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """14.2.2: Department/program/batch/category/gender analytics vertical slice."""
        return StudentReportingQueryService.get_demographics_breakdown(filters)

    @staticmethod
    def get_verification_analytics(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """14.2.3: Verification analytics vertical slice."""
        return VerificationReportingQueryService.get_verification_status_summary(filters)

    @staticmethod
    def get_fee_status_analytics(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """14.2.4: Fee-status analytics vertical slice."""
        summary = FinanceReportingQueryService.get_fee_status_summary(filters)
        heads = FinanceReportingQueryService.get_fee_heads_breakdown(filters)
        return {
            'summary': summary,
            'fee_heads': heads,
        }

    @staticmethod
    def get_academic_results_analytics(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """14.2.5: Academic/result/eligibility analytics vertical slice."""
        performance = ResultsReportingQueryService.get_academic_performance_summary(filters)
        eligibility = ResultsReportingQueryService.get_eligibility_status_summary(filters)
        return {
            'performance': performance,
            'eligibility': eligibility,
        }

    @staticmethod
    def get_user_activity_analytics(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """14.2.6: Administrative/user activity analytics vertical slice."""
        return AuditReportingQueryService.get_activity_analytics_summary(filters)
