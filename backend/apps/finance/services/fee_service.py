"""
Fees & Finance Service Layer.
Implements:
- Fee head & structure management with historical protection (Tasks 9.1.1, 9.1.2, 9.1.3)
- Student fee accounts & annual charge generation (Tasks 9.2.1, 9.2.2, 9.2.3)
- Append-only payment recording & duplicate protection (Tasks 9.3.1, 9.3.2)
- Controlled financial reversals and accountable actor audit (Tasks 9.3.3, 9.3.4)
"""

from decimal import Decimal
from datetime import date
from typing import Optional, List, Dict, Any
from django.db import transaction
from django.utils import timezone

from apps.finance.models import (
    FeeHead,
    FeeStructure,
    FeeStructureItem,
    StudentFeeAccount,
    FeeCharge,
    ChargeStatus,
    PaymentLedgerEntry,
    LedgerEntryType,
)
from apps.finance.domain.invariants import (
    validate_fee_structure_lock,
    validate_fee_amount,
    validate_payment_recording,
    validate_reversal,
)
from apps.students.models import Student, StudentEnrollment
from apps.academic.models import AcademicYear, Department, Program
from common.exceptions import InvariantViolationError


class FeeService:
    """Core domain service for fee assessment, ledger recording, and financial reversals."""

    # ── 1. Configuration & Structure ───────────────────────────────────

    @classmethod
    @transaction.atomic
    def create_fee_head(
        cls,
        name: str,
        code: str,
        description: str = '',
        is_active: bool = True
    ) -> FeeHead:
        head = FeeHead(name=name, code=code.upper(), description=description, is_active=is_active)
        head.save()
        return head

    @classmethod
    @transaction.atomic
    def create_fee_structure(
        cls,
        name: str,
        academic_year: AcademicYear,
        department: Optional[Department] = None,
        program: Optional[Program] = None,
        category: str = 'ALL',
        items: Optional[List[Dict[str, Any]]] = None,
        actor=None
    ) -> FeeStructure:
        structure = FeeStructure(
            name=name,
            academic_year=academic_year,
            department=department,
            program=program,
            category=category or 'ALL',
            created_by=actor
        )
        structure.save()

        if items:
            for itm in items:
                FeeStructureItem.objects.create(
                    fee_structure=structure,
                    fee_head=itm['fee_head'],
                    amount=Decimal(str(itm['amount']))
                )
            structure.recalculate_total()

        return structure

    # ── 2. Annual Charge Assessment ────────────────────────────────────

    @classmethod
    @transaction.atomic
    def assess_annual_fees(
        cls,
        academic_year: AcademicYear,
        department: Optional[Department] = None,
        program: Optional[Program] = None,
        due_date: Optional[date] = None,
        actor=None
    ) -> Dict[str, Any]:
        """
        Assesses annual fees for all currently enrolled students in the academic year.
        Flow: Fee Structure -> Applicable Fee -> Charge.
        Automatically locks historical fee structures used to assess charges.
        """
        enrollments_qs = StudentEnrollment.objects.filter(
            academic_year=academic_year
        ).select_related('student', 'student__category_info', 'department', 'program')

        if department:
            enrollments_qs = enrollments_qs.filter(department=department)
        if program:
            enrollments_qs = enrollments_qs.filter(program=program)

        structures = FeeStructure.objects.filter(academic_year=academic_year)
        if department:
            structures = structures.filter(department=department)
        if program:
            structures = structures.filter(program=program)

        created_count = 0
        skipped_count = 0
        structures_to_lock = set()

        for enr in enrollments_qs:
            student = enr.student
            student_category = student.category_info.category if hasattr(student, 'category_info') and student.category_info else 'OPEN'

            # Find matching fee structure: first matching specific category, else matching 'ALL'
            matching_structure = structures.filter(category=student_category).first()
            if not matching_structure:
                matching_structure = structures.filter(category='ALL').first()

            if not matching_structure:
                skipped_count += 1
                continue

            fee_account, _ = StudentFeeAccount.objects.get_or_create(student=student)

            # Prevent duplicate assessment for same student, structure, and year
            existing_charge = FeeCharge.objects.filter(
                account=fee_account,
                fee_structure=matching_structure,
                academic_year=academic_year
            ).first()

            if existing_charge:
                skipped_count += 1
                continue

            # Create charge
            charge = FeeCharge.objects.create(
                account=fee_account,
                fee_structure=matching_structure,
                academic_year=academic_year,
                due_date=due_date,
                total_amount=matching_structure.total_amount,
                status=ChargeStatus.UNPAID,
                remarks=f"Annual fee charge for {academic_year.label}"
            )
            fee_account.update_totals()
            structures_to_lock.add(matching_structure)
            created_count += 1

        # Lock historical fee structures (Task 9.1.3)
        for st in structures_to_lock:
            if not st.is_locked:
                st.is_locked = True
                st.save(update_fields=['is_locked'])

        return {
            'created_charges': created_count,
            'skipped_enrollments': skipped_count,
            'academic_year': academic_year.label
        }

    # ── 3. Append-Only Payments & Reversals ──────────────────────────────

    @classmethod
    @transaction.atomic
    def record_payment(
        cls,
        charge_id: str,
        amount: Decimal,
        receipt_no: str,
        external_transaction_ref: str = '',
        payment_mode: str = 'UNIVERSITY_PORTAL_QR',
        payment_date: Optional[date] = None,
        actor=None,
        reason: str = ''
    ) -> PaymentLedgerEntry:
        """
        Records an append-only payment against a student charge.
        Rejects recording if charge is already PAID (Task 9.3.2).
        Transitions UNPAID -> PARTIALLY_PAID -> PAID.
        """
        charge = FeeCharge.objects.select_for_update().get(id=charge_id)
        validate_payment_recording(charge.status, charge.remaining_balance, amount)

        if PaymentLedgerEntry.objects.filter(receipt_no=receipt_no).exists():
            raise InvariantViolationError(f"Duplicate receipt number '{receipt_no}' already exists.")

        entry = PaymentLedgerEntry.objects.create(
            charge=charge,
            amount=amount,
            entry_type=LedgerEntryType.PAYMENT,
            receipt_no=receipt_no,
            external_transaction_ref=external_transaction_ref,
            payment_mode=payment_mode,
            payment_date=payment_date or timezone.now().date(),
            recorded_by=actor,
            reason=reason
        )

        # Update charge paid amount
        charge.paid_amount += amount
        if charge.paid_amount >= charge.total_amount:
            charge.status = ChargeStatus.PAID
        else:
            charge.status = ChargeStatus.PARTIALLY_PAID
        charge.save()

        # Update account totals
        charge.account.update_totals()
        return entry

    @classmethod
    @transaction.atomic
    def reverse_payment(
        cls,
        payment_entry_id: str,
        reason: str,
        reversal_receipt_no: str,
        actor=None
    ) -> PaymentLedgerEntry:
        """
        Mistaken payments are corrected through an append-only reversal entry (ADR-011).
        Original payment remains preserved for audit integrity.
        """
        payment_entry = PaymentLedgerEntry.objects.select_for_update().get(id=payment_entry_id)
        validate_reversal(payment_entry, reason)

        if PaymentLedgerEntry.objects.filter(receipt_no=reversal_receipt_no).exists():
            raise InvariantViolationError(f"Duplicate receipt number '{reversal_receipt_no}' already exists.")

        charge = FeeCharge.objects.select_for_update().get(id=payment_entry.charge_id)

        # Create reversal entry
        reversal = PaymentLedgerEntry.objects.create(
            charge=charge,
            amount=payment_entry.amount,
            entry_type=LedgerEntryType.REVERSAL,
            reversal_of=payment_entry,
            receipt_no=reversal_receipt_no,
            external_transaction_ref=payment_entry.external_transaction_ref,
            payment_mode=payment_entry.payment_mode,
            payment_date=timezone.now().date(),
            recorded_by=actor,
            reason=reason
        )

        # Re-adjust charge
        charge.paid_amount = max(Decimal('0.00'), charge.paid_amount - payment_entry.amount)
        if charge.paid_amount == Decimal('0.00'):
            charge.status = ChargeStatus.UNPAID
        elif charge.paid_amount < charge.total_amount:
            charge.status = ChargeStatus.PARTIALLY_PAID
        else:
            charge.status = ChargeStatus.PAID
        charge.save()

        # Update account
        charge.account.update_totals()
        return reversal
