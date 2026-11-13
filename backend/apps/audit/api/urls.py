"""
URL routes for Audit & Observability.
Mounted at /api/v1/audit/ by config/urls.py.
"""

from django.urls import path
from apps.audit.api.views import (
    AuditLogListView,
    SensitiveDataAccessLogListView,
)

urlpatterns = [
    path('logs/', AuditLogListView.as_view(), name='audit-logs'),
    path('sensitive-access/', SensitiveDataAccessLogListView.as_view(), name='audit-sensitive-access'),
]
