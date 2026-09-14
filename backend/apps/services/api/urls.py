from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.services.api.views import (
    ServiceRequestTypeViewSet,
    ServiceRequestViewSet,
    ServiceRequestAuditViewSet,
)

router = DefaultRouter()
router.register(r'types', ServiceRequestTypeViewSet, basename='service-type')
router.register(r'requests', ServiceRequestViewSet, basename='service-request')
router.register(r'audits', ServiceRequestAuditViewSet, basename='service-audit')

urlpatterns = [
    path('', include(router.urls)),
]
