"""
Unit tests for Financial Reversals & Accountable Actor Audit (Tasks 9.3.3, 9.3.4).
Verifies append-only corrections per ADR-011 and immutability of historical ledger entries.
"""

from decimal import Decimal
from datetime import date
from django.test import TestCase
from apps.identity.models import User
from apps.academic.models import AcademicYear
from apps.students.models import Student
from apps.finance.models import (
    FeeHead,
    FeeStructure,
    StudentFeeAccount,
    FeeCharge,
    ChargeStatus,
    PaymentLedgerEntry,
    LedgerEntryType,
)
from apps.finance.services.fee_service import FeeService
from common.exceptions import InvariantViolationError


class ReversalsAndAuditTestCase(TestCase):
    def setUp(self):
        self.accountant = User.objects.create_user(
            username='auditor',
            email='auditor@college.edu',
            password='TestPassword123!'
        )
        self.ay = AcademicYear.objects.create(
            label='2024-25',
            start_date=date(2024, 7, 1),
            end_date=date(2025, 6, 30)
        )
        self.head = FeeService.create_fee_head(name='Exam Fee', code='EXAM_REV')
        self.struct = FeeService.create_fee_structure(
            name='Exam Structure 2024-25',
            academic_year=self.ay,
            items=[{'fee_head': self.head, 'amount': Decimal('6000.00')}],
            actor=self.accountant
        )

        self.student = Student.objects.create(
            candidate_name='Vikram Singh',
            enrollment_no='ENR2024101',
            application_id='APP2024101',
            date_of_birth=date(2005, 7, 11),
            gender='MALE'
        )
        self.account = StudentFeeAccount.objects.create(student=self.student)
        self.charge = FeeCharge.objects.create(
            account=self.account,
            fee_structure=self.struct,
            academic_year=self.ay,
            total_amount=Decimal('6000.00'),
            status=ChargeStatus.UNPAID
        )
        self.account.update_totals()

    def test_payment_reversal_creates_append_only_correction_entry(self):
        """Reversal creates a new ledger entry with reference to original payment."""
        # 1. Record original payment
        payment = FeeService.record_payment(
            charge_id=str(self.charge.id),
            amount=Decimal('6000.00'),
            receipt_no='REC-ORIG-01',
            external_transaction_ref='UTR-MISMATCH-123',
            actor=self.accountant,
            reason='Initial student payment record'
        )

        self.charge.refresh_from_db()
        self.assertEqual(self.charge.status, ChargeStatus.PAID)

        # 2. Reverse payment due to incorrect bank slip / mistaken entry
        reversal = FeeService.reverse_payment(
            payment_entry_id=str(payment.id),
            reason='Student submitted wrong UTR slip from another university account',
            reversal_receipt_no='REV-REC-01',
            actor=self.accountant
        )

        # Verify reversal entry properties
        self.assertEqual(reversal.entry_type, LedgerEntryType.REVERSAL)
        self.assertEqual(reversal.reversal_of, payment)
        self.assertEqual(reversal.amount, Decimal('6000.00'))
        self.assertEqual(reversal.recorded_by, self.accountant)
        self.assertIn("Student submitted wrong UTR", reversal.reason)

        # Verify original payment remains preserved in ledger
        original = PaymentLedgerEntry.objects.get(id=payment.id)
        self.assertIsNotNone(original)
        self.assertEqual(original.entry_type, LedgerEntryType.PAYMENT)

        # Total entries in ledger must be 2 (audit integrity)
        self.assertEqual(PaymentLedgerEntry.objects.count(), 2)

        # Check charge status readjusted back to UNPAID
        self.charge.refresh_from_db()
        self.assertEqual(self.charge.status, ChargeStatus.UNPAID)
        self.assertEqual(self.charge.paid_amount, Decimal('0.00'))
        self.assertEqual(self.charge.remaining_balance, Decimal('6000.00'))

        # Check student account balance
        self.account.refresh_from_db()
        self.assertEqual(self.account.total_paid, Decimal('0.00'))
        self.assertEqual(self.account.outstanding_balance, Decimal('6000.00'))

    def test_double_reversal_is_prevented(self):
        """Cannot reverse an already reversed payment."""
        payment = FeeService.record_payment(
            charge_id=str(self.charge.id),
            amount=Decimal('6000.00'),
            receipt_no='REC-ORIG-02',
            actor=self.accountant
        )

        FeeService.reverse_payment(
            payment_entry_id=str(payment.id),
            reason='First reversal',
            reversal_receipt_no='REV-02-A',
            actor=self.accountant
        )

        with self.assertRaises(InvariantViolationError) as ctx:
            FeeService.reverse_payment(
                payment_entry_id=str(payment.id),
                reason='Second reversal attempt',
                reversal_receipt_no='REV-02-B',
                actor=self.accountant
            )
        self.assertIn("already been reversed", str(ctx.exception))

    def test_reversal_requires_justification(self):
        """Reversal cannot be recorded without a mandatory justification reason."""
        payment = FeeService.record_payment(
            charge_id=str(self.charge.id),
            amount=Decimal('6000.00'),
            receipt_no='REC-ORIG-03',
            actor=self.accountant
        )

        with self.assertRaises(InvariantViolationError) as ctx:
            FeeService.reverse_payment(
                payment_entry_id=str(payment.id),
                reason='',  # Empty reason
                reversal_receipt_no='REV-03',
                actor=self.accountant
            )
        self.assertIn("accountable justification", str(ctx.exception))
