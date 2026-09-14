"""
Results & Eligibility Reporting Query Interface.

Implements Task 14.1.4: Results and eligibility reporting interface vertical slice.
Exposes authoritative, read-only query contracts for academic exam results,
grade distributions, SGPA/CGPA stats, and promotion/detention eligibility decisions.
"""
from typing import Dict, Any, Optional
from decimal import Decimal
from django.db.models import Avg, Count, Q
from apps.results.models import StudentResult, EligibilityDecision


class ResultsReportingQueryService:
    """Read-only reporting query interface owned by apps.results."""

    @staticmethod
    def get_academic_performance_summary(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculates authoritative pass/fail, SGPA/CGPA, and class distributions from published results."""
        filters = filters or {}
        qs = StudentResult.objects.filter(status='PUBLISHED', is_latest=True)

        if filters.get('academic_year_id'):
            qs = qs.filter(academic_year_id=filters['academic_year_id'])
        if filters.get('department_id'):
            qs = qs.filter(batch__department_id=filters['department_id'])
        if filters.get('semester_id'):
            qs = qs.filter(semester_id=filters['semester_id'])

        total = qs.count()
        if total == 0:
            return {
                'total_results': 0,
                'passed_count': 0,
                'failed_count': 0,
                'atkt_count': 0,
                'pass_percentage': 0.0,
                'average_sgpa': 0.0,
                'average_cgpa': 0.0,
                'distinction_count': 0,
                'first_class_count': 0,
                'second_class_count': 0,
                'pass_class_count': 0,
            }

        agg = qs.aggregate(
            passed=Count('id', filter=Q(result_status='PASS')),
            failed=Count('id', filter=Q(result_status='FAIL')),
            atkt=Count('id', filter=Q(result_status='ATKT')),
            avg_sgpa=Avg('sgpa'),
            avg_cgpa=Avg('cgpa'),
            distinction=Count('id', filter=Q(percentage__gte=Decimal('75.00'))),
            first_class=Count('id', filter=Q(percentage__gte=Decimal('60.00'), percentage__lt=Decimal('75.00'))),
            second_class=Count('id', filter=Q(percentage__gte=Decimal('50.00'), percentage__lt=Decimal('60.00'))),
            pass_class=Count('id', filter=Q(percentage__lt=Decimal('50.00'), result_status='PASS')),
        )

        passed = agg['passed']
        pass_pct = round((passed / total * 100), 2) if total > 0 else 0.0

        return {
            'total_results': total,
            'passed_count': passed,
            'failed_count': agg['failed'],
            'atkt_count': agg['atkt'],
            'pass_percentage': pass_pct,
            'average_sgpa': round(float(agg['avg_sgpa'] or 0.0), 2),
            'average_cgpa': round(float(agg['avg_cgpa'] or 0.0), 2),
            'distinction_count': agg['distinction'],
            'first_class_count': agg['first_class'],
            'second_class_count': agg['second_class'],
            'pass_class_count': agg['pass_class'],
        }

    @staticmethod
    def get_eligibility_status_summary(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculates promotion, non-eligibility, and detention rates."""
        filters = filters or {}
        qs = EligibilityDecision.objects.filter(is_latest=True)

        if filters.get('academic_year_id'):
            qs = qs.filter(academic_year_id=filters['academic_year_id'])
        if filters.get('program_id'):
            qs = qs.filter(program_id=filters['program_id'])

        total = qs.count()
        if total == 0:
            return {
                'total_decisions': 0,
                'eligible_count': 0,
                'not_eligible_count': 0,
                'detained_count': 0,
                'eligibility_rate': 0.0,
            }

        agg = qs.aggregate(
            eligible=Count('id', filter=Q(decision='ELIGIBLE')),
            not_eligible=Count('id', filter=Q(decision='NOT_ELIGIBLE')),
            detained=Count('id', filter=Q(decision='DETAINED')),
        )

        eligible = agg['eligible']
        rate = round((eligible / total * 100), 2) if total > 0 else 0.0

        return {
            'total_decisions': total,
            'eligible_count': eligible,
            'not_eligible_count': agg['not_eligible'],
            'detained_count': agg['detained'],
            'eligibility_rate': rate,
        }

    @staticmethod
    def get_results_reporting_records(
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Provides paginated, bounded query for tabular academic results reporting."""
        filters = filters or {}
        qs = StudentResult.objects.filter(status='PUBLISHED', is_latest=True).select_related(
            'student', 'batch__department', 'semester', 'academic_year'
        )

        if filters.get('academic_year_id'):
            qs = qs.filter(academic_year_id=filters['academic_year_id'])
        if filters.get('department_id'):
            qs = qs.filter(batch__department_id=filters['department_id'])
        if filters.get('status'):
            qs = qs.filter(result_status=filters['status'])
        if filters.get('search'):
            s = filters['search']
            qs = qs.filter(
                Q(student__candidate_name__icontains=s) |
                Q(student__enrollment_no__icontains=s)
            )

        total_count = qs.count()
        records = [
            {
                'result_id': str(r.id),
                'student_id': str(r.student.id),
                'candidate_name': r.student.candidate_name,
                'enrollment_no': r.student.enrollment_no or '',
                'department_name': r.batch.department.name if r.batch and r.batch.department else '',
                'program_name': r.batch.department.code if r.batch and r.batch.department else '',
                'semester_number': r.semester.number if r.semester else None,
                'total_marks_obtained': float(r.total_marks_obtained),
                'total_max_marks': float(r.total_max_marks),
                'percentage': float(r.percentage),
                'sgpa': float(r.sgpa or 0.0),
                'cgpa': float(r.cgpa or 0.0),
                'status': r.result_status,
            }
            for r in qs[offset:offset + limit]
        ]

        return {
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'records': records,
        }
