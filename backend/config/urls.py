"""
Root URL Configuration for Student Management & Administrative Data System.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Identity & Access endpoints
    path('api/v1/auth/', include('apps.identity.api.urls')),
    # Academic Foundation endpoints
    path('api/v1/academic/', include('apps.academic.api.urls')),
    # Student Management endpoints
    path('api/v1/students/', include('apps.students.api.urls')),
    # Student Onboarding & Import endpoints
    path('api/v1/onboarding/', include('apps.onboarding.api.urls')),
    # Documents endpoints
    path('api/v1/documents/', include('apps.documents.api.urls')),
    # Verification & Approvals endpoints
    path('api/v1/verification/', include('apps.verification.api.urls')),
    # Faculty & Academic Assignment endpoints
    path('api/v1/faculty/', include('apps.faculty.api.urls')),
    # Register & Administrative Dashboards endpoints
    path('api/v1/register/', include('apps.register.api.urls')),
    # Fees & Finance endpoints
    path('api/v1/finance/', include('apps.finance.api.urls')),
    # Assessments & Unit Test Marks endpoints
    path('api/v1/assessments/', include('apps.assessments.api.urls')),
    # Academic Results & Eligibility endpoints
    path('api/v1/results/', include('apps.results.api.urls')),
    # Student Services endpoints
    path('api/v1/services/', include('apps.services.api.urls')),
    # Reporting & Analytics endpoints
    path('api/v1/reporting/', include('apps.reporting.api.urls')),
    # Audit & Observability endpoints
    path('api/v1/audit/', include('apps.audit.api.urls')),
]
