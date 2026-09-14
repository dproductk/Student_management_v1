"""
Unit tests for Payment Ledger & Duplicate Payment Protection (Tasks 9.3.1, 9.3.2).
Verifies:
- Student pays on university portal via QR code.
- Accountant confirms external transaction UTR and records payment.
- Charge transitions UNPAID -> PAID.
- Duplicate payment protection rejects payments on already PAID charges.
"""

from decimal import Decimal
from datetime import date
from django.test import TestCase
from apps.identity.models import User
from apps.academic.models import AcademicYear, Department, Program, Semester, Batch
from apps.students.models import Student, StudentEnrollment
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


class PaymentLedgerTestCase(TestCase):
    def setUp(self):
        self.accountant = User.objects.create_user(
            username='accountant3',
            email='accountant3@college.edu',
            password='TestPassword123!'
        )
        self.ay = AcademicYear.objects.create(
            label='2024-25',
            start_date=date(2024, 7, 1),
            end_date=date(2025, 6, 30)
        )
        self.dept = Department.objects.create(name='Civil Engineering', code='CIVIL')
        self.prog = Program.objects.create(name='B.Tech Civil', code='BTCIVIL', department=self.dept)

        self.head = FeeService.create_fee_head(name='College Annual Fee', code='ANNUAL_FEE')
        self.struct = FeeService.create_fee_structure(
            name='Civil Annual 2024-25',
            academic_year=self.ay,
            items=[{'fee_head': self.head, 'amount': Decimal('50000.00')}],
            actor=self.accountant
        )

        self.student = Student.objects.create(
            candidate_name='Pooja Patil',
            enrollment_no='ENR2024099',
            application_id='APP2024099',
            date_of_birth=date(2005, 5, 20),
            gender='FEMALE'
        )
        self.account = StudentFeeAccount.objects.create(student=self.student)
        self.charge = FeeCharge.objects.create(
            account=self.account,
            fee_structure=self.struct,
            academic_year=self.ay,
            total_amount=Decimal('50000.00'),
            status=ChargeStatus.UNPAID
        )
        self.account.update_totals()

    def test_record_full_payment_via_university_portal_qr(self):
        """
        Flow: Student pays ₹50,000 on University Portal via QR code.
        Accountant verifies UTR and records payment.
        Charge transitions UNPAID -> PAID.
        """
        self.assertEqual(self.charge.status, ChargeStatus.UNPAID)

        entry = FeeService.record_payment(
            charge_id=str(self.charge.id),
            amount=Decimal('50000.00'),
            receipt_no='REC-2024-001',
            external_transaction_ref='UTR9876543210',
            payment_mode='UNIVERSITY_PORTAL_QR',
            actor=self.accountant,
            reason='Verified against university portal payment confirmation'
        )

        self.assertEqual(entry.entry_type, LedgerEntryType.PAYMENT)
        self.assertEqual(entry.amount, Decimal('50000.00'))
        self.assertEqual(entry.external_transaction_ref, 'UTR9876543210')
        self.assertEqual(entry.payment_mode, 'UNIVERSITY_PORTAL_QR')
        self.assertEqual(entry.recorded_by, self.accountant)

        # Check charge status transition
        self.charge.refresh_from_db()
        self.assertEqual(self.charge.status, ChargeStatus.PAID)
        self.assertEqual(self.charge.paid_amount, Decimal('50000.00'))
        self.assertEqual(self.charge.remaining_balance, Decimal('0.00'))

        # Check student account balance
        self.account.refresh_from_db()
        self.assertEqual(self.account.total_paid, Decimal('50000.00'))
        self.assertEqual(self.account.outstanding_balance, Decimal('0.00'))

    def test_duplicate_payment_protection_on_paid_charge(self):
        """Cannot record another payment once charge is marked PAID (Task 9.3.2)."""
        FeeService.record_payment(
            charge_id=str(self.charge.id),
            amount=Decimal('50000.00'),
            receipt_no='REC-2024-002',
            external_transaction_ref='UTR111',
            actor=self.accountant
        )

        self.charge.refresh_from_db()
        self.assertEqual(self.charge.status, ChargeStatus.PAID)

        # Attempt duplicate payment
        with self.assertRaises(InvariantViolationError) as ctx:
            FeeService.record_payment(
                charge_id=str(self.charge.id),
                amount=Decimal('1000.00'),
                receipt_no='REC-2024-003',
                external_transaction_ref='UTR222',
                actor=self.accountant
            )
        self.assertIn("already-paid charge", str(ctx.exception))

    def test_overpayment_protection(self):
        """Cannot pay more than the remaining charge balance."""
        with self.assertRaises(InvariantViolationError) as ctx:
            FeeService.record_payment(
                charge_id=str(self.charge.id),
                amount=Decimal('55000.00'),  # 50,000 total
                receipt_no='REC-2024-OVER',
                actor=self.accountant
            )
        self.assertIn("exceeds the remaining charge balance", str(ctx.exception))

    def test_duplicate_receipt_number_rejected(self):
        """Unique receipt number required for all ledger entries."""
        FeeService.record_payment(
            charge_id=str(self.charge.id),
            amount=Decimal('20000.00'),
            receipt_no='REC-UNIQUE-01',
            actor=self.accountant
        )

        with self.assertRaises(InvariantViolationError) as ctx:
            FeeService.record_payment(
                charge_id=str(self.charge.id),
                amount=Decimal('10000.00'),
                receipt_no='REC-UNIQUE-01',  # Duplicate
                actor=self.accountant
            )
        self.assertIn("Duplicate receipt number", str(ctx.exception))
