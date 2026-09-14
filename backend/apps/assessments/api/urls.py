"""
URL routing for Assessments & Unit Test Marks module.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.assessments.api.views import (
    AssessmentTypeViewSet,
    AssessmentViewSet,
    AssessmentMarkViewSet,
    StudentMarksView,
)

router = DefaultRouter()
router.register(r'types', AssessmentTypeViewSet, basename='assessment-type')
router.register(r'definitions', AssessmentViewSet, basename='assessment-definition')
router.register(r'marks', AssessmentMarkViewSet, basename='assessment-mark')

urlpatterns = [
    path('', include(router.urls)),
    path('my-marks/', StudentMarksView.as_view(), name='student-my-marks'),
]
