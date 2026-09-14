"""
URL routing for Fees & Finance module API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.finance.api.views import (
    FeeHeadViewSet,
    FeeStructureViewSet,
    StudentFeeAccountViewSet,
    FeeChargeViewSet,
    PaymentLedgerViewSet,
    AssessAnnualFeesView,
    RecordPaymentView,
    ReversePaymentView,
    SaveStudentFeeView,
)

router = DefaultRouter()
router.register(r'heads', FeeHeadViewSet, basename='fee-head')
router.register(r'fee-heads', FeeHeadViewSet, basename='fee-heads')
router.register(r'structures', FeeStructureViewSet, basename='fee-structure')
router.register(r'accounts', StudentFeeAccountViewSet, basename='fee-account')
router.register(r'charges', FeeChargeViewSet, basename='fee-charge')
router.register(r'ledger', PaymentLedgerViewSet, basename='payment-ledger')

urlpatterns = [
    path('', include(router.urls)),
    path('assess-annual-fees/', AssessAnnualFeesView.as_view(), name='assess-annual-fees'),
    path('save-student-fee/', SaveStudentFeeView.as_view(), name='save-student-fee'),
    path('record-payment/', RecordPaymentView.as_view(), name='record-payment'),
    path('reverse-payment/', ReversePaymentView.as_view(), name='reverse-payment'),
]
