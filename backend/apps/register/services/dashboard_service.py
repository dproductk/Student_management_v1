"""
Administrative Dashboard Service.
Implements Task 8.4: Administrative dashboard student-status vertical slice.
Produces aggregated, bounded metrics on student status, enrollment, categories, and verification health.
"""

from typing import Dict, Any, Optional
from django.db.models import Count
from apps.register.services.register_query_service import RegisterQueryService
from apps.verification.models import VerificationRequest


class DashboardService:
    """Service generating bounded administrative KPIs and status distributions."""

    @classmethod
    def get_dashboard_summary(
        cls,
        user,
        department_id: Optional[str] = None,
        academic_year_id: Optional[str] = None
    ) -> Dict[str, Any]:
        qs = RegisterQueryService.get_base_scoped_queryset(user)

        if department_id:
            qs = qs.filter(enrollments__department_id=department_id)
        if academic_year_id:
            qs = qs.filter(enrollments__academic_year_id=academic_year_id)

        qs = qs.distinct()
        total_students = qs.count()

        # 1. Student lifecycle status distribution
        status_counts = dict(
            qs.values('status').annotate(count=Count('id')).values_list('status', 'count')
        )

        # 2. Gender distribution
        gender_counts = dict(
            qs.values('gender').annotate(count=Count('id')).values_list('gender', 'count')
        )

        # 3. Category distribution (from authoritative StudentCategory)
        category_rows = (
            qs.filter(category_info__isnull=False)
            .values('category_info__category')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        category_counts = {
            r['category_info__category']: r['count'] for r in category_rows
        }

        # 4. Department distribution
        dept_rows = (
            qs.filter(enrollments__department__isnull=False)
            .values('enrollments__department__id', 'enrollments__department__code', 'enrollments__department__name')
            .annotate(count=Count('id', distinct=True))
            .order_by('-count')
        )
        department_distribution = [
            {
                'department_id': str(r['enrollments__department__id']),
                'code': r['enrollments__department__code'],
                'name': r['enrollments__department__name'],
                'student_count': r['count']
            }
            for r in dept_rows
        ]

        # 5. Verification status breakdown
        verif_counts = {
            'APPROVED': qs.filter(verification_requests__status='APPROVED').distinct().count(),
            'PENDING': qs.filter(verification_requests__status='PENDING').distinct().count(),
            'NEEDS_CORRECTION': qs.filter(verification_requests__status='NEEDS_CORRECTION').distinct().count(),
            'REJECTED': qs.filter(verification_requests__status='REJECTED').distinct().count(),
            'UNSUBMITTED': qs.filter(verification_requests__isnull=True).distinct().count(),
        }

        return {
            'total_students': total_students,
            'active_students': status_counts.get('ACTIVE', 0),
            'status_distribution': status_counts,
            'gender_distribution': gender_counts,
            'category_distribution': category_counts,
            'department_distribution': department_distribution,
            'verification_breakdown': verif_counts,
        }
