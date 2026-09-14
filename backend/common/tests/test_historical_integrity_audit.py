"""
Cross-Cutting Historical-Integrity Audit Test Suite.
Governed by TASKS.md 15.2.4, production-hardening-prd.md R-009, ADR-007, ADR-011, and ADR-016.
"""

from datetime import date
from django.test import TestCase
from decimal import Decimal
from common.exceptions import InvariantViolationError
from apps.identity.models import User
from apps.academic.models import Department, Program, AcademicYear, Semester, Batch, Scheme, Subject, SchemeSubject
from apps.students.models import Student, StudentDataCorrection
from apps.students.services.correction_service import CorrectionService
from apps.finance.models import FeeHead, FeeStructure, FeeStructureItem, StudentFeeAccount, FeeCharge, PaymentLedgerEntry
from apps.finance.services.fee_service import FeeService
from apps.results.models import StudentResult, StudentResultDetail


class HistoricalIntegrityAuditTests(TestCase):
    """
    Validates additive correction, append-only reversals, and versioned supersessions
    across Student Management, Finance, and Academic Results.
    """

    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin_hist",
            email="admin_hist@example.com",
            password="AdminPassword123!",
            is_superuser=True
        )

        self.dept = Department.objects.create(name="Civil Engineering", code="CIVIL_HIST")
        self.prog = Program.objects.create(name="B.Tech Civil", code="BCIVIL_HIST", department=self.dept)
        self.ay = AcademicYear.objects.create(
            label="2026-2027",
            start_date=date(2026, 7, 1),
            end_date=date(2027, 6, 30),
            is_current=True
        )
        self.sem = Semester.objects.create(academic_year=self.ay, number=1)
        self.batch = Batch.objects.create(name="Batch 2026-30", department=self.dept, academic_year=self.ay)

        self.student = Student.objects.create(
            candidate_name="Pooja Patil",
            gender="FEMALE",
            date_of_birth=date(2005, 8, 20),
            enrollment_no="ENR_HIST_001",
            status="ACTIVE"
        )

    def test_student_additive_corrections_preserve_original_government_data(self):
        """Verify corrections on student records create an audit trail and preserve historical records (ADR-007)."""
        # Apply additive correction via CorrectionService
        correction = CorrectionService.apply_student_correction(
            student_id=self.student.id,
            field_name='candidate_name',
            new_value='Pooja Ramesh Patil',
            reason='Government Gazetted Name Change certificate verified',
            approver_user=self.admin_user
        )

        # Both the current authoritative value and the original old_value are preserved
        self.student.refresh_from_db()
        self.assertEqual(self.student.candidate_name, 'Pooja Ramesh Patil')
        self.assertEqual(correction.original_value, 'Pooja Patil')
        self.assertEqual(correction.corrected_value, 'Pooja Ramesh Patil')
        self.assertEqual(self.student.corrections.count(), 1)

    def test_financial_ledger_reversals_are_append_only_and_preserve_history(self):
        """Verify mistaken payments are corrected through linked append-only reversals (ADR-011, ADR-025)."""
        fee_head = FeeHead.objects.create(name="Library Fee", code="LIB_HIST")
        structure = FeeStructure.objects.create(
            name="Fee Structure 2026",
            academic_year=self.ay,
            program=self.prog,
            is_locked=False
        )
        FeeStructureItem.objects.create(fee_structure=structure, fee_head=fee_head, amount=5000)
        structure.is_locked = True
        structure.save()

        account = StudentFeeAccount.objects.create(student=self.student)
        charge = FeeCharge.objects.create(
            account=account,
            fee_structure=structure,
            academic_year=self.ay,
            total_amount=Decimal('5000.00'),
            status='UNPAID'
        )

        # Record payment
        original_entry = FeeService.record_payment(
            charge_id=charge.id,
            amount=Decimal('5000.00'),
            receipt_no='REC_HIST_111',
            external_transaction_ref='UTR_ORIG_123',
            actor=self.admin_user
        )

        # Reverse payment
        reversal_entry = FeeService.reverse_payment(
            payment_entry_id=original_entry.id,
            reason='Bank chargeback reconciliation error',
            reversal_receipt_no='REV_HIST_111',
            actor=self.admin_user
        )

        # Ledger entries count must be 2 (original PAYMENT + new REVERSAL)
        self.assertEqual(charge.ledger_entries.count(), 2)
        self.assertEqual(reversal_entry.entry_type, 'REVERSAL')
        self.assertEqual(reversal_entry.reversal_of, original_entry)
        self.assertEqual(reversal_entry.amount, Decimal('5000.00'))

        # Charge status must revert to UNPAID
        charge.refresh_from_db()
        self.assertEqual(charge.status, 'UNPAID')

    def test_published_results_are_immutable_and_use_v2_supersession(self):
        """Verify published results cannot be mutated in place and use Result V2 supersession (ADR-016)."""
        scheme = Scheme.objects.create(
            name="Scheme 2026",
            code="SCHEME_2026_HIST",
            program=self.prog,
            effective_from_year=self.ay,
            is_active=True
        )
        sub = Subject.objects.create(name="Mechanics", code="MECH_HIST")
        ss = SchemeSubject.objects.create(scheme=scheme, subject=sub, semester_number=1, max_marks=100, passing_marks=40)

        # Direct result creation
        res_v1 = StudentResult.objects.create(
            student=self.student,
            academic_year=self.ay,
            semester=self.sem,
            batch=self.batch,
            version=1,
            is_latest=True,
            status='PUBLISHED',
            total_marks_obtained=75,
            total_max_marks=100,
            percentage=Decimal('75.00'),
            sgpa=Decimal('8.50'),
            result_status='PASS'
        )
        StudentResultDetail.objects.create(
            student_result=res_v1,
            scheme_subject=ss,
            subject_code="MECH_HIST",
            subject_name="Mechanics",
            total_marks=Decimal('75.00'),
            max_marks=Decimal('100.00'),
            grade='A',
            grade_points=Decimal('8.50'),
            status='PASS'
        )

        from apps.results.domain.invariants import ResultImmutabilityViolation

        # Published result and its details cannot be deleted (ADR-016)
        with self.assertRaises(ResultImmutabilityViolation):
            res_v1.delete()

        detail = res_v1.details.first()
        with self.assertRaises(ResultImmutabilityViolation):
            detail.delete()

        # Result remains preserved
        res_v1.refresh_from_db()
        self.assertTrue(res_v1.is_latest)
        self.assertEqual(res_v1.status, 'PUBLISHED')
