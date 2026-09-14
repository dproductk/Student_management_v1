"""
Finance Reporting Query Interface.

Implements Task 14.1.3: Finance reporting interface vertical slice.
Exposes authoritative, read-only query contracts for fee statuses, collections,
and outstanding dues without mutating financial ledger entries.
"""
from typing import Dict, Any, Optional, List
from decimal import Decimal
from django.db.models import Sum, Count, Q
from apps.finance.models import FeeCharge, StudentFeeAccount, ChargeStatus, FeeStructureItem


class FinanceReportingQueryService:
    """Read-only reporting query interface owned by apps.finance."""

    @staticmethod
    def get_fee_status_summary(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculates authoritative aggregate financial metrics."""
        filters = filters or {}
        charges_qs = FeeCharge.objects.exclude(status=ChargeStatus.CANCELLED)

        if filters.get('academic_year_id'):
            charges_qs = charges_qs.filter(academic_year_id=filters['academic_year_id'])
        if filters.get('department_id'):
            charges_qs = charges_qs.filter(
                account__student__enrollments__department_id=filters['department_id'],
                account__student__enrollments__status='ACTIVE'
            )

        agg = charges_qs.aggregate(
            total_billed=Sum('total_amount'),
            total_paid=Sum('paid_amount'),
            unpaid_count=Count('id', filter=Q(status=ChargeStatus.UNPAID)),
            partial_count=Count('id', filter=Q(status=ChargeStatus.PARTIALLY_PAID)),
            paid_count=Count('id', filter=Q(status=ChargeStatus.PAID)),
        )

        total_billed = agg['total_billed'] or Decimal('0.00')
        total_collected = agg['total_paid'] or Decimal('0.00')
        total_outstanding = total_billed - total_collected
        collection_percentage = round((float(total_collected) / float(total_billed) * 100), 2) if total_billed > 0 else 0.0

        return {
            'total_billed': float(total_billed),
            'total_collected': float(total_collected),
            'total_outstanding': float(total_outstanding),
            'collection_percentage': collection_percentage,
            'unpaid_charges_count': agg['unpaid_count'],
            'partially_paid_charges_count': agg['partial_count'],
            'paid_charges_count': agg['paid_count'],
            'total_charges_count': agg['unpaid_count'] + agg['partial_count'] + agg['paid_count'],
        }

    @staticmethod
    def get_fee_heads_breakdown(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Aggregates billed revenue contribution across active fee heads."""
        filters = filters or {}
        items_qs = FeeStructureItem.objects.select_related('fee_head', 'fee_structure')

        if filters.get('academic_year_id'):
            items_qs = items_qs.filter(fee_structure__academic_year_id=filters['academic_year_id'])

        head_agg = (
            items_qs.values('fee_head__code', 'fee_head__name')
            .annotate(total_allocation=Sum('amount'), structures_count=Count('fee_structure_id', distinct=True))
            .order_by('-total_allocation')
        )

        return [
            {
                'code': h['fee_head__code'],
                'name': h['fee_head__name'],
                'amount': float(h['total_allocation'] or Decimal('0.00')),
                'structures_count': h['structures_count'],
            }
            for h in head_agg
        ]

    @staticmethod
    def get_defaulters_reporting_records(
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Provides a paginated list of student accounts with unpaid balances."""
        filters = filters or {}
        qs = StudentFeeAccount.objects.filter(outstanding_balance__gt=Decimal('0.00')).select_related(
            'student'
        ).prefetch_related(
            'student__enrollments__department',
            'student__enrollments__program',
            'student__enrollments__batch'
        )

        if filters.get('department_id'):
            qs = qs.filter(
                student__enrollments__department_id=filters['department_id'],
                student__enrollments__status='ACTIVE'
            )
        if filters.get('search'):
            s = filters['search']
            qs = qs.filter(
                Q(student__candidate_name__icontains=s) |
                Q(student__enrollment_no__icontains=s)
            )

        qs = qs.distinct().order_by('-outstanding_balance')
        total_count = qs.count()

        records = []
        for fa in qs[offset:offset + limit]:
            active_enr = fa.student.enrollments.filter(status='ACTIVE').first()
            records.append({
                'account_id': str(fa.id),
                'student_id': str(fa.student.id),
                'candidate_name': fa.student.candidate_name,
                'enrollment_no': fa.student.enrollment_no or '',
                'department_name': active_enr.department.name if active_enr and active_enr.department else '',
                'program_name': active_enr.program.name if active_enr and active_enr.program else '',
                'batch_name': active_enr.batch.name if active_enr and active_enr.batch else '',
                'total_billed': float(fa.total_billed),
                'total_paid': float(fa.total_paid),
                'outstanding_balance': float(fa.outstanding_balance),
            })

        return {
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'records': records,
        }
