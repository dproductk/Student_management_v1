"""
URL configuration for documents API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.documents.api.views import StudentDocumentViewSet

router = DefaultRouter()
router.register('', StudentDocumentViewSet, basename='document')

urlpatterns = [
    path('', include(router.urls)),
]
