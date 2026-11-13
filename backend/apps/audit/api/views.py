"""
Read-only views for Audit & Observability.
Exposed at /api/v1/audit/logs/ and /api/v1/audit/sensitive-access/.
Restricted to authenticated users; System Admin / Compliance use.
"""

from rest_framework import generics, permissions
from apps.audit.models import AuditLog, SensitiveDataAccessLog
from apps.audit.api.serializers import (
    AuditLogSerializer,
    SensitiveDataAccessLogSerializer,
)


class AuditLogListView(generics.ListAPIView):
    """
    GET /api/v1/audit/logs/
    Read-only, paginated audit trail. Filter via query params:
    ?module=identity&action=LOGIN_SUCCESS&target_type=USER&actor_id=<uuid>
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        qs = AuditLog.objects.select_related('actor').all().order_by('-occurred_at')
        module = self.request.query_params.get('module')
        action = self.request.query_params.get('action')
        target_type = self.request.query_params.get('target_type')
        actor_id = self.request.query_params.get('actor_id')
        if module:
            qs = qs.filter(module=module)
        if action:
            qs = qs.filter(action=action)
        if target_type:
            qs = qs.filter(target_type=target_type)
        if actor_id:
            qs = qs.filter(actor_id=actor_id)
        return qs


class SensitiveDataAccessLogListView(generics.ListAPIView):
    """
    GET /api/v1/audit/sensitive-access/
    Read-only log of sensitive-data reveals (Aadhaar, bank details).
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SensitiveDataAccessLogSerializer

    def get_queryset(self):
        qs = SensitiveDataAccessLog.objects.select_related('accessor').all().order_by('-accessed_at')
        student_id = self.request.query_params.get('student_id')
        field_name = self.request.query_params.get('field_name')
        if student_id:
            qs = qs.filter(student_id=student_id)
        if field_name:
            qs = qs.filter(field_name=field_name)
        return qs
