"""
Fees & Finance domain models.
Implements Section 9 of TASKS.md:
- 9.1 Fee-head, fee-structure, and historical protection.
- 9.2 Student fee-account and applicable fee charge generation.
- 9.3 Append-only payment ledger, duplicate-payment protection, reversals, and accountable actor audit.
Per ADR-010 & ARCHITECTURE.md: Finance is the sole source of truth for fee status. No external reconciliation.
"""

from decimal import Decimal
from django.db import models
from django.utils import timezone
from common.models import TimeStampedUUIDModel
from apps.finance.domain.invariants import (
    validate_fee_structure_lock,
    validate_fee_amount,
    validate_payment_recording,
    validate_reversal,
)


class ChargeStatus(models.TextChoices):
    UNPAID = 'UNPAID', 'Unpaid'
    PARTIALLY_PAID = 'PARTIALLY_PAID', 'Partially Paid'
    PAID = 'PAID', 'Paid'
    CANCELLED = 'CANCELLED', 'Cancelled'


class LedgerEntryType(models.TextChoices):
    PAYMENT = 'PAYMENT', 'Payment'
    REVERSAL = 'REVERSAL', 'Reversal'


class FeeHead(TimeStampedUUIDModel):
    """Configurable head of fee (e.g. Tuition, Development, Exam, Library)."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    description = models.TextField(blank=True, default='')
    academic_year = models.ForeignKey(
        'academic.AcademicYear',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fee_heads',
        db_column='academic_year_id'
    )
    allowed_amounts = models.JSONField(default=list, blank=True)
    display_order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'fee_heads'
        ordering = ['display_order', 'code']
        verbose_name = 'Fee Head'
        verbose_name_plural = 'Fee Heads'

    def __str__(self):
        yr = f" ({self.academic_year.label})" if self.academic_year else ""
        return f"{self.code} - {self.name}{yr}"


class FeeStructure(TimeStampedUUIDModel):
    """
    Annual or periodic fee package mapped to academic year, program, and category.
    Once student charges are generated, is_locked=True protects historical structures.
    """
    name = models.CharField(max_length=200)
    academic_year = models.ForeignKey(
        'academic.AcademicYear',
        on_delete=models.PROTECT,
        related_name='fee_structures',
        db_column='academic_year_id'
    )
    department = models.ForeignKey(
        'academic.Department',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='fee_structures',
        db_column='department_id'
    )
    program = models.ForeignKey(
        'academic.Program',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='fee_structures',
        db_column='program_id'
    )
    category = models.CharField(
        max_length=30,
        blank=True,
        default='ALL',
        help_text="Applicable category (e.g. OPEN, OBC, SC, ST, ALL)"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    is_locked = models.BooleanField(
        default=False,
        help_text="Protected against edits once charges are assessed."
    )
    created_by = models.ForeignKey(
        'identity.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_fee_structures',
        db_column='created_by'
    )

    class Meta:
        db_table = 'fee_structures'
        ordering = ['-academic_year__start_date', 'name']
        verbose_name = 'Fee Structure'
        verbose_name_plural = 'Fee Structures'

    def clean(self):
        if self.pk:
            orig = FeeStructure.objects.filter(pk=self.pk).first()
            if orig and orig.is_locked:
                validate_fee_structure_lock(True)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def recalculate_total(self):
        total = sum((item.amount for item in self.items.all()), Decimal('0.00'))
        self.total_amount = total
        self.save(update_fields=['total_amount'])

    def __str__(self):
        return f"{self.name} ({self.academic_year.label})"


class FeeStructureItem(TimeStampedUUIDModel):
    """Component head line item within a fee structure."""
    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.CASCADE,
        related_name='items',
        db_column='fee_structure_id'
    )
    fee_head = models.ForeignKey(
        FeeHead,
        on_delete=models.PROTECT,
        related_name='structure_items',
        db_column='fee_head_id'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'fee_structure_items'
        unique_together = (('fee_structure', 'fee_head'),)
        verbose_name = 'Fee Structure Item'
        verbose_name_plural = 'Fee Structure Items'

    def clean(self):
        validate_fee_structure_lock(self.fee_structure.is_locked)
        validate_fee_amount(self.amount)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        self.fee_structure.recalculate_total()

    def __str__(self):
        return f"{self.fee_structure.name}: {self.fee_head.name} - ₹{self.amount}"


class StudentFeeAccount(TimeStampedUUIDModel):
    """Authoritative student fee account summary."""
    student = models.OneToOneField(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='fee_account',
        db_column='student_id'
    )
    total_billed = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    outstanding_balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        db_table = 'student_fee_accounts'
        verbose_name = 'Student Fee Account'
        verbose_name_plural = 'Student Fee Accounts'

    def update_totals(self):
        active_charges = self.charges.exclude(status=ChargeStatus.CANCELLED)
        billed = sum((c.total_amount for c in active_charges), Decimal('0.00'))
        paid = sum((c.paid_amount for c in active_charges), Decimal('0.00'))
        self.total_billed = billed
        self.total_paid = paid
        self.outstanding_balance = billed - paid
        self.save()

    def __str__(self):
        return f"Fee Account: {self.student.candidate_name} (Balance: ₹{self.outstanding_balance})"


class FeeCharge(TimeStampedUUIDModel):
    """
    Authoritative student charge assessed for an academic year/term.
    Flow: Fee Structure -> Applicable Fee -> Charge -> Payment Ledger Entry
    """
    account = models.ForeignKey(
        StudentFeeAccount,
        on_delete=models.CASCADE,
        related_name='charges',
        db_column='account_id'
    )
    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='charges',
        db_column='fee_structure_id'
    )
    fee_breakdown = models.JSONField(default=dict, blank=True)
    academic_year = models.ForeignKey(
        'academic.AcademicYear',
        on_delete=models.PROTECT,
        related_name='fee_charges',
        db_column='academic_year_id'
    )
    due_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(
        max_length=30,
        choices=ChargeStatus.choices,
        default=ChargeStatus.UNPAID
    )
    remarks = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'fee_charges'
        ordering = ['-academic_year__start_date', '-created_at']
        verbose_name = 'Fee Charge'
        verbose_name_plural = 'Fee Charges'

    @property
    def remaining_balance(self) -> Decimal:
        return self.total_amount - self.paid_amount

    def __str__(self):
        st_name = self.fee_structure.name if self.fee_structure else "Admission Fee"
        return f"Charge {st_name} - ₹{self.total_amount} ({self.status})"


class PaymentLedgerEntry(TimeStampedUUIDModel):
    """
    Append-only financial event ledger.
    Never edited or deleted. Mistaken entries are corrected via a REVERSAL entry.
    Records accountable actor, timestamp, payment mode, and external university UTR/transaction ref.
    """
    charge = models.ForeignKey(
        FeeCharge,
        on_delete=models.PROTECT,
        related_name='ledger_entries',
        db_column='charge_id'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    entry_type = models.CharField(
        max_length=30,
        choices=LedgerEntryType.choices,
        default=LedgerEntryType.PAYMENT
    )
    reversal_of = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='reversals',
        db_column='reversal_of_id'
    )
    receipt_no = models.CharField(max_length=100, unique=True, db_index=True)
    external_transaction_ref = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="University Portal UTR / Gateway confirmation reference"
    )
    payment_mode = models.CharField(
        max_length=50,
        default='UNIVERSITY_PORTAL_QR'
    )
    payment_date = models.DateField(default=timezone.now)
    recorded_by = models.ForeignKey(
        'identity.User',
        on_delete=models.RESTRICT,
        related_name='recorded_payments',
        db_column='recorded_by'
    )
    reason = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'payment_ledger_entries'
        ordering = ['-created_at']
        verbose_name = 'Payment Ledger Entry'
        verbose_name_plural = 'Payment Ledger Entries'

    def __str__(self):
        return f"[{self.entry_type}] Receipt {self.receipt_no}: ₹{self.amount} ({self.charge.account.student.candidate_name})"
