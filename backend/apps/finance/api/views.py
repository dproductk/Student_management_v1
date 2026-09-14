"""
Views and ViewSets for Fees & Finance module.
Enforces permissions, audit logging, and domain service workflows.
"""

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db.models import Q

from apps.finance.models import (
    FeeHead,
    FeeStructure,
    FeeStructureItem,
    StudentFeeAccount,
    FeeCharge,
    PaymentLedgerEntry,
    ChargeStatus,
)
from apps.finance.services.fee_service import FeeService
from apps.finance.api.serializers import (
    FeeHeadSerializer,
    FeeStructureSerializer,
    FeeStructureItemSerializer,
    StudentFeeAccountSerializer,
    FeeChargeSerializer,
    PaymentLedgerEntrySerializer,
    AssessAnnualFeesSerializer,
    RecordPaymentRequestSerializer,
    ReversePaymentRequestSerializer,
)
from apps.academic.models import AcademicYear, Department, Program
from common.exceptions import InvariantViolationError


class FeeHeadViewSet(viewsets.ModelViewSet):
    queryset = FeeHead.objects.all()
    serializer_class = FeeHeadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        ay = self.request.query_params.get('academic_year') or self.request.query_params.get('academic_year_id')
        if ay:
            qs = qs.filter(Q(academic_year_id=ay) | Q(academic_year__isnull=True))
        return qs.order_by('display_order', 'code')


class FeeStructureViewSet(viewsets.ModelViewSet):
    queryset = FeeStructure.objects.all().select_related('academic_year', 'department', 'program', 'created_by').prefetch_related('items__fee_head')
    serializer_class = FeeStructureSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='add-item')
    def add_item(self, request, pk=None):
        structure = self.get_object()
        fee_head_id = request.data.get('fee_head')
        amount = request.data.get('amount')

        if not fee_head_id or amount is None:
            return Response({'error': 'fee_head and amount are required'}, status=status.HTTP_400_BAD_REQUEST)

        fee_head = get_object_or_404(FeeHead, id=fee_head_id)
        try:
            item = FeeStructureItem.objects.create(
                fee_structure=structure,
                fee_head=fee_head,
                amount=amount
            )
            return Response(FeeStructureItemSerializer(item).data, status=status.HTTP_201_CREATED)
        except InvariantViolationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StudentFeeAccountViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Search and filter student fee accounts for accountant monitoring.
    Supports filtering by search query (name, PRN, roll_number), outstanding status, etc.
    """
    serializer_class = StudentFeeAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = StudentFeeAccount.objects.all().select_related(
            'student',
            'student__category_info'
        ).prefetch_related(
            'charges__fee_structure',
            'charges__academic_year',
            'student__enrollments__department',
            'student__enrollments__program'
        )

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(student__candidate_name__icontains=search) |
                Q(student__enrollment_no__icontains=search) |
                Q(student__application_id__icontains=search)
            )

        status_filter = self.request.query_params.get('status')
        if status_filter == 'PAID':
            qs = qs.filter(outstanding_balance=0, total_billed__gt=0)
        elif status_filter == 'UNPAID':
            qs = qs.filter(outstanding_balance__gt=0, total_paid=0)
        elif status_filter == 'PARTIAL':
            qs = qs.filter(outstanding_balance__gt=0, total_paid__gt=0)

        return qs


class FeeChargeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FeeCharge.objects.all().select_related(
        'account__student',
        'fee_structure',
        'academic_year'
    )
    serializer_class = FeeChargeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        account_id = self.request.query_params.get('account')
        if account_id:
            qs = qs.filter(account_id=account_id)
        student_id = self.request.query_params.get('student')
        if student_id:
            qs = qs.filter(account__student_id=student_id)
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        academic_year = self.request.query_params.get('academic_year')
        if academic_year:
            qs = qs.filter(academic_year_id=academic_year)
        return qs


class PaymentLedgerViewSet(viewsets.ReadOnlyModelViewSet):
    """Append-only ledger entries."""
    queryset = PaymentLedgerEntry.objects.all().select_related(
        'charge__account__student',
        'charge__fee_structure',
        'recorded_by'
    )
    serializer_class = PaymentLedgerEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        charge_id = self.request.query_params.get('charge')
        if charge_id:
            qs = qs.filter(charge_id=charge_id)
        student_id = self.request.query_params.get('student')
        if student_id:
            qs = qs.filter(charge__account__student_id=student_id)
        entry_type = self.request.query_params.get('entry_type')
        if entry_type:
            qs = qs.filter(entry_type=entry_type)
        return qs


class AssessAnnualFeesView(APIView):
    """
    Accountant triggers annual fee assessment for enrolled students in an academic year.
    Once assessed, historical fee structures are locked automatically.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AssessAnnualFeesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        academic_year = get_object_or_404(AcademicYear, id=data['academic_year_id'])
        department = None
        if data.get('department_id'):
            department = get_object_or_404(Department, id=data['department_id'])
        program = None
        if data.get('program_id'):
            program = get_object_or_404(Program, id=data['program_id'])

        try:
            result = FeeService.assess_annual_fees(
                academic_year=academic_year,
                department=department,
                program=program,
                due_date=data.get('due_date'),
                actor=request.user
            )
            return Response(result, status=status.HTTP_200_OK)
        except InvariantViolationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RecordPaymentView(APIView):
    """
    Fee Accountant records an append-only payment upon verifying student's
    university portal QR payment confirmation / UTR.
    Transitions charge UNPAID -> PAID.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RecordPaymentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            entry = FeeService.record_payment(
                charge_id=str(data['charge_id']),
                amount=data['amount'],
                receipt_no=data['receipt_no'],
                external_transaction_ref=data.get('external_transaction_ref', ''),
                payment_mode=data.get('payment_mode', 'UNIVERSITY_PORTAL_QR'),
                payment_date=data.get('payment_date'),
                actor=request.user,
                reason=data.get('reason', '')
            )
            return Response(PaymentLedgerEntrySerializer(entry).data, status=status.HTTP_201_CREATED)
        except InvariantViolationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ReversePaymentView(APIView):
    """
    Fee Accountant creates an append-only reversal entry for mistake correction.
    Preserves original payment in the ledger for full audit accountability.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReversePaymentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            reversal = FeeService.reverse_payment(
                payment_entry_id=str(data['payment_entry_id']),
                reason=data['reason'],
                reversal_receipt_no=data['reversal_receipt_no'],
                actor=request.user
            )
            return Response(PaymentLedgerEntrySerializer(reversal).data, status=status.HTTP_201_CREATED)
        except InvariantViolationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SaveStudentFeeView(APIView):
    """
    POST /api/v1/finance/save-student-fee/
    Allows Accountant to set up and save the fee breakdown for an eligible student.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from decimal import Decimal
        from apps.students.models import Student
        from apps.academic.models import AcademicYear
        from apps.finance.api.serializers import SaveStudentFeeSerializer
        serializer = SaveStudentFeeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student_id = serializer.validated_data['student_id']
        ay_id = serializer.validated_data['academic_year_id']
        breakdown = serializer.validated_data['fee_breakdown']

        student = get_object_or_404(Student, id=student_id)
        ay = get_object_or_404(AcademicYear, id=ay_id)

        # Ensure student fee account exists
        account, _ = StudentFeeAccount.objects.get_or_create(student=student)

        total = sum(Decimal(str(v)) for v in breakdown.values())

        # Check existing charge for THIS student + academic year only.
        # Each student has their own StudentFeeAccount, so this never touches
        # any other student's charge. Different categories / students can have
        # completely different totals and breakdowns.
        charge = FeeCharge.objects.filter(account=account, academic_year=ay).first()
        is_new = charge is None
        if is_new:
            charge = FeeCharge(
                account=account,
                academic_year=ay,
                status=ChargeStatus.UNPAID,
                paid_amount=Decimal('0.00'),
            )

        charge.fee_breakdown = {k: float(v) for k, v in breakdown.items()}
        charge.total_amount = total
        charge.remarks = f"Admission Fee for FY ({ay.label})"

        # Re-derive status from already-paid amount so editing a fee after a
        # (partial) payment keeps history consistent:
        # - no payment yet -> UNPAID
        # - paid >= new total -> PAID
        # - 0 < paid < total -> PARTIALLY_PAID
        paid_so_far = charge.paid_amount if charge.paid_amount is not None else Decimal('0.00')
        if paid_so_far <= Decimal('0.00'):
            charge.status = ChargeStatus.UNPAID
        elif paid_so_far >= total:
            charge.status = ChargeStatus.PAID
        else:
            charge.status = ChargeStatus.PARTIALLY_PAID
        charge.save()

        account.update_totals()

        # Record audit log
        from apps.audit.services.audit_service import AuditService
        AuditService.record_audit(
            action="STUDENT_FEE_CONFIGURED",
            target_type="FEE_CHARGE",
            module="finance",
            actor=request.user,
            target_id=charge.id,
            new_value={"student_id": str(student_id), "total_amount": float(total), "breakdown": charge.fee_breakdown},
            reason=f"Accountant {request.user.username} configured admission fee breakdown for {student.candidate_name}"
        )

        return Response(FeeChargeSerializer(charge).data, status=status.HTTP_200_OK)
