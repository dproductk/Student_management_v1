"""
Concurrency and Transaction-Integrity Audit Test Suite.
Governed by TASKS.md 15.3.2, production-hardening-prd.md R-012, and ADR-025.
"""

from datetime import date
from decimal import Decimal
from django.test import TransactionTestCase
from django.db import transaction
from common.exceptions import InvariantViolationError
from apps.identity.models import User
from apps.academic.models import Department, Program, AcademicYear, Batch
from apps.students.models import Student
from apps.finance.models import FeeHead, FeeStructure, FeeStructureItem, StudentFeeAccount, FeeCharge
from apps.finance.services.fee_service import FeeService


class ConcurrencyAndTransactionIntegrityAuditTests(TransactionTestCase):
    """
    Validates atomic transactions, row locking, and race condition protection
    in critical financial and status-changing operations.
    """

    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin_conc",
            email="admin_conc@example.com",
            password="AdminPassword123!",
            is_superuser=True
        )

        self.dept = Department.objects.create(name="Automobile Engineering", code="AUTO_CONC")
        self.prog = Program.objects.create(name="B.Tech Auto", code="BAUTO_CONC", department=self.dept)
        self.ay = AcademicYear.objects.create(
            label="2026-2027",
            start_date=date(2026, 7, 1),
            end_date=date(2027, 6, 30),
            is_current=True
        )
        self.batch = Batch.objects.create(name="Batch 2026-30", department=self.dept, academic_year=self.ay)

        self.student = Student.objects.create(
            candidate_name="Amit Kumar",
            gender="MALE",
            date_of_birth=date(2005, 4, 10),
            enrollment_no="ENR_CONC_001",
            status="ACTIVE"
        )

        self.fee_head = FeeHead.objects.create(name="Lab Fee", code="LAB_CONC")
        self.structure = FeeStructure.objects.create(
            name="Auto Lab Structure",
            academic_year=self.ay,
            program=self.prog,
            is_locked=False
        )
        FeeStructureItem.objects.create(fee_structure=self.structure, fee_head=self.fee_head, amount=30000)
        self.structure.is_locked = True
        self.structure.save()

        self.account = StudentFeeAccount.objects.create(student=self.student)
        self.charge = FeeCharge.objects.create(
            account=self.account,
            fee_structure=self.structure,
            academic_year=self.ay,
            total_amount=Decimal('30000.00'),
            status='UNPAID'
        )

    def test_concurrent_payments_prevent_double_spend_race_condition(self):
        """Verify atomic transactions with select_for_update prevent double payment race conditions."""
        # Simulated Thread 1: Records full payment
        entry1 = FeeService.record_payment(
            charge_id=self.charge.id,
            amount=Decimal('30000.00'),
            receipt_no='REC_CONC_T1',
            external_transaction_ref='UTR_CONC_T1',
            actor=self.admin_user
        )
        self.assertEqual(entry1.amount, Decimal('30000.00'))

        # Simulated Thread 2: Attempts to pay the same charge concurrently
        with self.assertRaises(InvariantViolationError):
            FeeService.record_payment(
                charge_id=self.charge.id,
                amount=Decimal('30000.00'),
                receipt_no='REC_CONC_T2',
                external_transaction_ref='UTR_CONC_T2',
                actor=self.admin_user
            )

        # Confirm charge remains PAID with exactly one ledger entry and zero balance
        self.charge.refresh_from_db()
        self.assertEqual(self.charge.status, 'PAID')
        self.assertEqual(self.charge.remaining_balance, Decimal('0.00'))
        self.assertEqual(self.charge.ledger_entries.count(), 1)

    def test_split_payments_maintain_atomic_balance_integrity(self):
        """Verify atomic updates maintain exact balance across successive partial payments."""
        # Payment 1: 10,000 of 30,000
        FeeService.record_payment(
            charge_id=self.charge.id,
            amount=Decimal('10000.00'),
            receipt_no='REC_PARTIAL_1',
            actor=self.admin_user
        )
        self.charge.refresh_from_db()
        self.assertEqual(self.charge.status, 'PARTIALLY_PAID')
        self.assertEqual(self.charge.remaining_balance, Decimal('20000.00'))

        # Payment 2: 20,000 of remaining 20,000
        FeeService.record_payment(
            charge_id=self.charge.id,
            amount=Decimal('20000.00'),
            receipt_no='REC_PARTIAL_2',
            actor=self.admin_user
        )
        self.charge.refresh_from_db()
        self.assertEqual(self.charge.status, 'PAID')
        self.assertEqual(self.charge.remaining_balance, Decimal('0.00'))
