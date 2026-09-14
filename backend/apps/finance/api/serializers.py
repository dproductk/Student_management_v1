"""
Serializers for Fees & Finance module.
"""

from decimal import Decimal
from rest_framework import serializers
from apps.finance.models import (
    FeeHead,
    FeeStructure,
    FeeStructureItem,
    StudentFeeAccount,
    FeeCharge,
    PaymentLedgerEntry,
    ChargeStatus,
    LedgerEntryType,
)
from apps.students.models import Student
from apps.academic.models import AcademicYear, Department, Program


class FeeHeadSerializer(serializers.ModelSerializer):
    academic_year_label = serializers.CharField(source='academic_year.label', read_only=True, default='')

    class Meta:
        model = FeeHead
        fields = [
            'id', 'name', 'code', 'description', 'academic_year', 'academic_year_label',
            'allowed_amounts', 'display_order', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FeeStructureItemSerializer(serializers.ModelSerializer):
    fee_head_name = serializers.CharField(source='fee_head.name', read_only=True)
    fee_head_code = serializers.CharField(source='fee_head.code', read_only=True)

    class Meta:
        model = FeeStructureItem
        fields = ['id', 'fee_head', 'fee_head_name', 'fee_head_code', 'amount']
        read_only_fields = ['id', 'fee_head_name', 'fee_head_code']


class FeeStructureSerializer(serializers.ModelSerializer):
    items = FeeStructureItemSerializer(many=True, read_only=True)
    academic_year_label = serializers.CharField(source='academic_year.label', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)
    program_name = serializers.CharField(source='program.name', read_only=True, default=None)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = FeeStructure
        fields = [
            'id',
            'name',
            'academic_year',
            'academic_year_label',
            'department',
            'department_name',
            'program',
            'program_name',
            'category',
            'total_amount',
            'is_locked',
            'created_by',
            'created_by_name',
            'items',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'total_amount', 'is_locked', 'created_by', 'created_at', 'updated_at']


class StudentFeeAccountSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.candidate_name', read_only=True)
    student_enrollment_no = serializers.CharField(source='student.enrollment_no', read_only=True, default='')
    student_application_id = serializers.CharField(source='student.application_id', read_only=True, default='')

    class Meta:
        model = StudentFeeAccount
        fields = [
            'id',
            'student',
            'student_name',
            'student_enrollment_no',
            'student_application_id',
            'total_billed',
            'total_paid',
            'outstanding_balance',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'total_billed', 'total_paid', 'outstanding_balance', 'created_at', 'updated_at']


class FeeChargeSerializer(serializers.ModelSerializer):
    fee_structure_name = serializers.CharField(source='fee_structure.name', read_only=True, default='Admission Fee')
    academic_year_label = serializers.CharField(source='academic_year.label', read_only=True)
    remaining_balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    student_name = serializers.CharField(source='account.student.candidate_name', read_only=True)
    student_enrollment_no = serializers.CharField(source='account.student.enrollment_no', read_only=True, default='')
    student_application_id = serializers.CharField(source='account.student.application_id', read_only=True, default='')
    student_id = serializers.CharField(source='account.student.id', read_only=True, default='')

    class Meta:
        model = FeeCharge
        fields = [
            'id',
            'account',
            'student_id',
            'student_name',
            'student_enrollment_no',
            'student_application_id',
            'fee_structure',
            'fee_structure_name',
            'fee_breakdown',
            'academic_year',
            'academic_year_label',
            'due_date',
            'total_amount',
            'paid_amount',
            'remaining_balance',
            'status',
            'remarks',
            'created_at'
        ]
        read_only_fields = ['id', 'paid_amount', 'status', 'created_at']


class PaymentLedgerEntrySerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='charge.account.student.candidate_name', read_only=True)
    student_enrollment_no = serializers.CharField(source='charge.account.student.enrollment_no', read_only=True, default='')
    student_id = serializers.CharField(source='charge.account.student.id', read_only=True, default='')
    fee_structure_name = serializers.SerializerMethodField()
    recorded_by_name = serializers.CharField(source='recorded_by.username', read_only=True, default='')

    class Meta:
        model = PaymentLedgerEntry
        fields = [
            'id',
            'charge',
            'student_id',
            'student_name',
            'student_enrollment_no',
            'fee_structure_name',
            'amount',
            'entry_type',
            'reversal_of',
            'receipt_no',
            'external_transaction_ref',
            'payment_mode',
            'payment_date',
            'recorded_by',
            'recorded_by_name',
            'reason',
            'created_at'
        ]
        read_only_fields = ['id', 'recorded_by', 'created_at']

    def get_fee_structure_name(self, obj):
        if obj.charge and obj.charge.fee_structure:
            return obj.charge.fee_structure.name
        return "Admission Fee"


class StudentFeeAccountSerializer(serializers.ModelSerializer):
    student_id = serializers.UUIDField(source='student.id', read_only=True)
    candidate_name = serializers.CharField(source='student.candidate_name', read_only=True)
    enrollment_no = serializers.CharField(source='student.enrollment_no', read_only=True, default='')
    application_id = serializers.CharField(source='student.application_id', read_only=True, default='')
    category = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    program_name = serializers.SerializerMethodField()
    charges = FeeChargeSerializer(many=True, read_only=True)

    class Meta:
        model = StudentFeeAccount
        fields = [
            'id',
            'student_id',
            'candidate_name',
            'enrollment_no',
            'application_id',
            'category',
            'department_name',
            'program_name',
            'total_billed',
            'total_paid',
            'outstanding_balance',
            'charges',
            'updated_at'
        ]
        read_only_fields = ['id', 'total_billed', 'total_paid', 'outstanding_balance', 'updated_at']

    def get_category(self, obj):
        if hasattr(obj.student, 'category_info') and obj.student.category_info:
            return obj.student.category_info.category
        return 'OPEN'

    def get_department_name(self, obj):
        enr = obj.student.enrollments.order_by('-created_at').first()
        return enr.department.name if enr and enr.department else ''

    def get_program_name(self, obj):
        enr = obj.student.enrollments.order_by('-created_at').first()
        return enr.program.name if enr and enr.program else ''


class AssessAnnualFeesSerializer(serializers.Serializer):
    academic_year_id = serializers.UUIDField(required=True)
    department_id = serializers.UUIDField(required=False, allow_null=True)
    program_id = serializers.UUIDField(required=False, allow_null=True)
    due_date = serializers.DateField(required=False, allow_null=True)


class RecordPaymentRequestSerializer(serializers.Serializer):
    charge_id = serializers.UUIDField(required=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    receipt_no = serializers.CharField(max_length=100, required=True)
    external_transaction_ref = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    payment_mode = serializers.CharField(max_length=50, default='UNIVERSITY_PORTAL_QR')
    payment_date = serializers.DateField(required=False, allow_null=True)
    reason = serializers.CharField(required=False, allow_blank=True, default='')


class ReversePaymentRequestSerializer(serializers.Serializer):
    payment_entry_id = serializers.UUIDField(required=True)
    reason = serializers.CharField(required=True, min_length=5)
    reversal_receipt_no = serializers.CharField(max_length=100, required=True)


class SaveStudentFeeSerializer(serializers.Serializer):
    student_id = serializers.UUIDField(required=True)
    academic_year_id = serializers.UUIDField(required=True)
    fee_breakdown = serializers.DictField(child=serializers.DecimalField(max_digits=10, decimal_places=2), required=True)
