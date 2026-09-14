"""
URL routing for Verification APIs.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.verification.api.views import VerificationRequestViewSet

router = DefaultRouter()
router.register('requests', VerificationRequestViewSet, basename='verification-request')

urlpatterns = [
    path('', include(router.urls)),
]
