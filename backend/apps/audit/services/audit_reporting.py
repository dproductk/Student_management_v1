"""
Audit & Administrative Activity Reporting Query Interface.

Exposes authoritative read-only query contracts for system and user activity analytics (Task 14.2.6).
"""
from typing import Dict, Any, Optional, List
from django.db.models import Count
from apps.audit.models import AuditLog


class AuditReportingQueryService:
    """Read-only reporting query interface owned by apps.audit."""

    @staticmethod
    def get_activity_analytics_summary(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculates aggregate system activity counts by module and action."""
        filters = filters or {}
        qs = AuditLog.objects.all()

        if filters.get('module'):
            qs = qs.filter(module=filters['module'])
        if filters.get('actor_id'):
            qs = qs.filter(actor_id=filters['actor_id'])

        total_events = qs.count()

        # Distribution by module
        by_module = list(
            qs.values('module')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        # Distribution by action
        by_action = list(
            qs.values('action')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        return {
            'total_audit_events': total_events,
            'events_by_module': by_module,
            'events_by_action': by_action,
        }
