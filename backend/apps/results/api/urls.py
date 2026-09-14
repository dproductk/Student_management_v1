from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.results.api.views import (
    ResultImportBatchViewSet,
    StudentResultViewSet,
    StudentResultSelfView,
    ResultCorrectionRequestViewSet,
    ResultCorrectionAuditViewSet,
    StudentCreditViewSet,
    EligibilityRuleViewSet,
    EligibilityDecisionViewSet,
    NextYearEligibilityListViewSet,
)

router = DefaultRouter()
router.register(r'batches', ResultImportBatchViewSet, basename='result-batch')
router.register(r'records', StudentResultViewSet, basename='student-result')
router.register(r'corrections', ResultCorrectionRequestViewSet, basename='result-correction')
router.register(r'audits', ResultCorrectionAuditViewSet, basename='result-audit')
router.register(r'credits', StudentCreditViewSet, basename='student-credit')
router.register(r'eligibility-rules', EligibilityRuleViewSet, basename='eligibility-rule')
router.register(r'eligibility-decisions', EligibilityDecisionViewSet, basename='eligibility-decision')
router.register(r'next-year-eligibility', NextYearEligibilityListViewSet, basename='next-year-eligibility')

urlpatterns = [
    path('student-portal/', StudentResultSelfView.as_view(), name='student-results-self'),
    path('', include(router.urls)),
]
