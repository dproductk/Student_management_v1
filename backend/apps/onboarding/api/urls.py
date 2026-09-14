"""
URL routing for onboarding and batch import API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.onboarding.api.views import ImportBatchViewSet, ImportStagingRowViewSet

router = DefaultRouter()
router.register('batches', ImportBatchViewSet, basename='import-batch')
router.register('staging-rows', ImportStagingRowViewSet, basename='staging-row')

urlpatterns = [
    path('', include(router.urls)),
]
