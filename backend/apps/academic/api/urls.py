"""
URL Routing for Academic Foundation API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.academic.api.views import (
    DepartmentViewSet,
    ProgramViewSet,
    AcademicYearViewSet,
    SemesterViewSet,
    BatchViewSet,
    DepartmentIntakeViewSet,
    SubjectViewSet,
    SchemeViewSet,
    SchemeSubjectViewSet,
    AcademicMasterSearchAPIView,
)

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'programs', ProgramViewSet, basename='program')
router.register(r'academic-years', AcademicYearViewSet, basename='academic-year')
router.register(r'semesters', SemesterViewSet, basename='semester')
router.register(r'batches', BatchViewSet, basename='batch')
router.register(r'intakes', DepartmentIntakeViewSet, basename='department-intake')
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'schemes', SchemeViewSet, basename='scheme')
router.register(r'scheme-subjects', SchemeSubjectViewSet, basename='scheme-subject')

urlpatterns = [
    path('search/', AcademicMasterSearchAPIView.as_view(), name='academic-master-search'),
    path('', include(router.urls)),
]
