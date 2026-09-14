"""
Reporting & Analytics URL routing.
"""
from django.urls import path
from apps.reporting.api.views import (
    ExecutiveKPIView,
    StudentPopulationAnalyticsView,
    DemographicsAnalyticsView,
    VerificationAnalyticsView,
    FeeStatusAnalyticsView,
    AcademicAnalyticsView,
    UserActivityAnalyticsView,
    ReportExportView,
)

urlpatterns = [
    path('analytics/kpis/', ExecutiveKPIView.as_view(), name='reporting-kpis'),
    path('analytics/population/', StudentPopulationAnalyticsView.as_view(), name='reporting-population'),
    path('analytics/demographics/', DemographicsAnalyticsView.as_view(), name='reporting-demographics'),
    path('analytics/verification/', VerificationAnalyticsView.as_view(), name='reporting-verification'),
    path('analytics/fees/', FeeStatusAnalyticsView.as_view(), name='reporting-fees'),
    path('analytics/academic/', AcademicAnalyticsView.as_view(), name='reporting-academic'),
    path('analytics/activity/', UserActivityAnalyticsView.as_view(), name='reporting-activity'),
    path('export/', ReportExportView.as_view(), name='reporting-export'),
]
