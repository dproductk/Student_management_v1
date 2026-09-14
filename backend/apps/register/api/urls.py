"""
URL routes for Register & Administrative Dashboards.
"""

from django.urls import path
from apps.register.api.views import (
    StudentRegisterView,
    AdministrativeDashboardView,
    RegisterExportView,
)

urlpatterns = [
    path('students/', StudentRegisterView.as_view(), name='register-students'),
    path('dashboard/', AdministrativeDashboardView.as_view(), name='register-dashboard'),
    path('export/', RegisterExportView.as_view(), name='register-export'),
]
