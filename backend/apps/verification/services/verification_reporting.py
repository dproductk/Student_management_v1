"""
Verification Reporting Query Interface.

Exposes authoritative read-only query contracts for verification analytics (Task 14.2.3).
"""
from typing import Dict, Any, Optional
from django.db.models import Count, Q
from apps.verification.models import VerificationRequest, VerificationDecision


class VerificationReportingQueryService:
    """Read-only reporting query interface owned by apps.verification."""

    @staticmethod
    def get_verification_status_summary(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculates aggregate verification throughput and decision distribution."""
        filters = filters or {}
        qs = VerificationRequest.objects.all()

        if filters.get('entity_type'):
            qs = qs.filter(entity_type=filters['entity_type'])

        total = qs.count()
        if total == 0:
            return {
                'total_requests': 0,
                'pending_count': 0,
                'approved_count': 0,
                'rejected_count': 0,
                'correction_requested_count': 0,
                'approval_rate': 0.0,
            }

        agg = qs.aggregate(
            pending=Count('id', filter=Q(status='PENDING')),
            approved=Count('id', filter=Q(status='APPROVED')),
            rejected=Count('id', filter=Q(status='REJECTED')),
            correction=Count('id', filter=Q(status='CORRECTION_REQUESTED')),
        )

        approved = agg['approved']
        rate = round((approved / total * 100), 2) if total > 0 else 0.0

        return {
            'total_requests': total,
            'pending_count': agg['pending'],
            'approved_count': approved,
            'rejected_count': agg['rejected'],
            'correction_requested_count': agg['correction'],
            'approval_rate': rate,
        }
