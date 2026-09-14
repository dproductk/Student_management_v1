"""
URL routing for Student Management API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.students.api.views import StudentViewSet, StudentCorrectionViewSet

router = DefaultRouter()
router.register(r'corrections', StudentCorrectionViewSet, basename='student-correction')
router.register(r'', StudentViewSet, basename='student')

urlpatterns = [
    path('', include(router.urls)),
]
