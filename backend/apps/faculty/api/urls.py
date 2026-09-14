"""
URL routing for Faculty bounded context.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.faculty.api.views import (
    FacultyViewSet,
    FacultyAssignmentViewSet,
    FacultyAcademicItemViewSet,
    FacultyScopedStudentViewSet,
)

router = DefaultRouter()
router.register(r'members', FacultyViewSet, basename='faculty')
router.register(r'assignments', FacultyAssignmentViewSet, basename='faculty-assignment')
router.register(r'academic-items', FacultyAcademicItemViewSet, basename='faculty-academic-item')
router.register(r'scoped-students', FacultyScopedStudentViewSet, basename='faculty-scoped-students')

urlpatterns = [
    path('', include(router.urls)),
]
