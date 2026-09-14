"""
Duplicate-Record and Idempotency Audit Test Suite.
Governed by TASKS.md 15.2.3, production-hardening-prd.md R-008, ADR-008, and ADR-025.
"""

from datetime import date
from django.test import TestCase
from decimal import Decimal
from common.exceptions import InvariantViolationError
from apps.academic.models import Department, Program, AcademicYear, Batch
from apps.students.models import Student
from apps.finance.models import FeeHead, FeeStructure, FeeStructureItem, StudentFeeAccount, FeeCharge
from apps.finance.services.fee_service import FeeService


class DuplicateRecordAndIdempotencyAuditTests(TestCase):
    """
    Audits duplicate-record protection and idempotency across financial payments,
    student imports, and result publishing.
    """

    def setUp(self):
        from apps.identity.models import User
        self.admin_user = User.objects.create_user(
            username="admin_idem",
            email="admin_idem@example.com",
            password="AdminPassword123!",
            is_superuser=True
        )

        self.dept = Department.objects.create(name="Mechanical Engineering", code="ME_IDEM")
        self.prog = Program.objects.create(name="B.Tech ME", code="BME_IDEM", department=self.dept)
        self.ay = AcademicYear.objects.create(
            label="2026-2027",
            start_date=date(2026, 7, 1),
            end_date=date(2027, 6, 30),
            is_current=True
        )
        self.batch = Batch.objects.create(name="Batch 2026-30", department=self.dept, academic_year=self.ay)

        self.student = Student.objects.create(
            candidate_name="Rahul Sharma",
            gender="MALE",
            date_of_birth=date(2005, 3, 15),
            enrollment_no="ENR_IDEM_001",
            status="ACTIVE"
        )

        # Setup fee structure and account
        self.fee_head = FeeHead.objects.create(name="Development Fee", code="DEV_IDEM")
        self.structure = FeeStructure.objects.create(
            name="Fee Structure 2026-27",
            academic_year=self.ay,
            program=self.prog,
            is_locked=False
        )
        FeeStructureItem.objects.create(fee_structure=self.structure, fee_head=self.fee_head, amount=25000)
        self.structure.is_locked = True
        self.structure.save()

        self.account = StudentFeeAccount.objects.create(student=self.student)
        self.charge = FeeCharge.objects.create(
            account=self.account,
            fee_structure=self.structure,
            academic_year=self.ay,
            total_amount=Decimal('25000.00'),
            status='UNPAID'
        )

    def test_fee_payment_on_already_paid_charge_strictly_rejected(self):
        """Verify attempting to record payment on a PAID charge raises error and prevents duplicate charge."""
        # First payment: marks charge PAID
        entry1 = FeeService.record_payment(
            charge_id=self.charge.id,
            amount=Decimal('25000.00'),
            receipt_no='REC_IDEM_111111',
            external_transaction_ref='UTR_IDEM_111111',
            actor=self.admin_user
        )
        self.charge.refresh_from_db()
        self.assertEqual(self.charge.status, 'PAID')

        # Duplicate payment attempt must fail with InvariantViolationError (ADR-025)
        with self.assertRaises(InvariantViolationError):
            FeeService.record_payment(
                charge_id=self.charge.id,
                amount=Decimal('25000.00'),
                receipt_no='REC_IDEM_222222',
                external_transaction_ref='UTR_IDEM_222222',
                actor=self.admin_user
            )

        # Ledger entries count must remain exactly 1
        self.assertEqual(self.charge.ledger_entries.count(), 1)

    def test_overpayment_beyond_charge_balance_strictly_rejected(self):
        """Verify recording an amount greater than the charge amount raises error."""
        charge2 = FeeCharge.objects.create(
            account=self.account,
            fee_structure=self.structure,
            academic_year=self.ay,
            total_amount=Decimal('10000.00'),
            status='UNPAID'
        )

        with self.assertRaises(InvariantViolationError):
            FeeService.record_payment(
                charge_id=charge2.id,
                amount=Decimal('15000.00'),  # Exceeds 10,000 balance
                receipt_no='REC_IDEM_333333',
                external_transaction_ref='UTR_OVERPAY_999',
                actor=self.admin_user
            )
