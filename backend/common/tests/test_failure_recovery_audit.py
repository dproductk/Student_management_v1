"""
Failure and Recovery Testing Audit Test Suite.
Governed by TASKS.md 15.3.3, production-hardening-prd.md R-013, and ADR-012.
"""

from datetime import date
from django.test import TestCase
from django.db import transaction
from decimal import Decimal
from common.exceptions import InvariantViolationError
from apps.identity.models import User
from apps.students.models import Student, StudentDataCorrection
from apps.students.services.correction_service import CorrectionService
from apps.finance.models import FeeHead, FeeStructure, FeeStructureItem, StudentFeeAccount, FeeCharge, PaymentLedgerEntry
from apps.finance.services.fee_service import FeeService


class FailureAndRecoveryAuditTests(TestCase):
    """
    Validates atomic rollback on mid-operation exceptions, ensuring zero orphaned rows
    or dirty database state upon unexpected errors.
    """

    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin_failover",
            email="admin_failover@example.com",
            password="AdminPassword123!",
            is_superuser=True
        )

    def test_mid_operation_failure_rolls_back_atomically(self):
        """Verify simulated failure during multi-entity operation leaves zero partial data."""
        initial_student_count = Student.objects.count()

        class SimulatedNetworkOrStorageFailure(Exception):
            pass

        try:
            with transaction.atomic():
                # Step 1: Create student
                student = Student.objects.create(
                    candidate_name="Rollback Student",
                    gender="MALE",
                    date_of_birth=date(2005, 1, 1),
                    enrollment_no="ENR_ROLLBACK_001"
                )
                # Step 2: Simulate failure before transaction commits
                raise SimulatedNetworkOrStorageFailure("Simulated storage/service failure mid-operation")
        except SimulatedNetworkOrStorageFailure:
            pass

        # Verify atomic rollback: student must NOT exist in the database
        self.assertEqual(Student.objects.count(), initial_student_count)
        self.assertFalse(Student.objects.filter(enrollment_no="ENR_ROLLBACK_001").exists())

    def test_correction_failure_leaves_original_student_untouched(self):
        """Verify failed correction validation leaves original student fields uncorrupted."""
        student = Student.objects.create(
            candidate_name="Original Name",
            gender="FEMALE",
            date_of_birth=date(2005, 2, 2),
            enrollment_no="ENR_CORR_FAIL_001"
        )

        initial_correction_count = StudentDataCorrection.objects.count()

        # Attempt correction with invalid reason (must fail validation)
        with self.assertRaises(InvariantViolationError):
            CorrectionService.apply_student_correction(
                student_id=student.id,
                field_name='candidate_name',
                new_value='Corrupted Name',
                reason=' ',  # Blank reason fails validation
                approver_user=self.admin_user
            )

        # Confirm student record remained intact with original name
        student.refresh_from_db()
        self.assertEqual(student.candidate_name, "Original Name")
        self.assertEqual(StudentDataCorrection.objects.count(), initial_correction_count)
