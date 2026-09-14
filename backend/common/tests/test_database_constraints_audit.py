"""
Database Constraint and Foreign-Key Integrity Audit Test Suite.
Governed by TASKS.md 15.2.1, production-hardening-prd.md R-006, and ARCHITECTURE.md Section 6.
"""

from datetime import date
from django.test import TestCase
from django.db import IntegrityError
from django.db.models import ProtectedError
from apps.academic.models import Department, Program, AcademicYear, Semester, Batch, Scheme, Subject, SchemeSubject
from apps.students.models import Student
from apps.finance.models import FeeHead, FeeStructure, FeeStructureItem


class DatabaseConstraintAndIntegrityAuditTests(TestCase):
    """
    Audits database constraints, unique indexes, and foreign-key deletion protection
    across core domain models.
    """

    def setUp(self):
        self.dept = Department.objects.create(name="Computer Engineering", code="CE_AUDIT")
        self.prog = Program.objects.create(name="B.Tech CE", code="BCE_AUDIT", department=self.dept)
        self.ay = AcademicYear.objects.create(
            label="2026-2027",
            start_date=date(2026, 7, 1),
            end_date=date(2027, 6, 30),
            is_current=True
        )
        self.batch = Batch.objects.create(name="Batch 2026-30", department=self.dept, academic_year=self.ay)

    def test_department_code_unique_constraint(self):
        """Verify duplicate department codes raise database IntegrityError."""
        from django.db import transaction
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Department.objects.create(name="Duplicate Dept", code="CE_AUDIT")

    def test_program_code_unique_constraint(self):
        """Verify duplicate program codes raise database IntegrityError."""
        from django.db import transaction
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Program.objects.create(name="Duplicate Prog", code="BCE_AUDIT", department=self.dept)

    def test_student_unique_identity_constraints(self):
        """Verify student enrollment_no and board_enrollment_no enforce uniqueness."""
        from django.db import transaction
        Student.objects.create(
            candidate_name="First Student",
            gender="FEMALE",
            date_of_birth=date(2005, 5, 5),
            enrollment_no="ENR_AUDIT_001",
            board_enrollment_no="BRD_AUDIT_001",
            application_id="APP_AUDIT_001"
        )

        # Duplicate enrollment_no
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Student.objects.create(
                    candidate_name="Second Student",
                    gender="MALE",
                    date_of_birth=date(2005, 6, 6),
                    enrollment_no="ENR_AUDIT_001"
                )

        # Duplicate board_enrollment_no
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Student.objects.create(
                    candidate_name="Third Student",
                    gender="MALE",
                    date_of_birth=date(2005, 7, 7),
                    board_enrollment_no="BRD_AUDIT_001"
                )

    def test_foreign_key_protection_prevents_accidental_cascade(self):
        """Verify deleting academic entities protected by active relations raises ProtectedError."""
        # Deleting Department with linked Program must be PROTECT-blocked
        with self.assertRaises(ProtectedError):
            self.dept.delete()

        # Deleting AcademicYear with linked Batch must be PROTECT-blocked
        with self.assertRaises(ProtectedError):
            self.ay.delete()

    def test_fee_structure_item_protects_fee_head(self):
        """Verify deleting a FeeHead linked to active FeeStructureItems raises ProtectedError."""
        fee_head = FeeHead.objects.create(name="Tuition Fee", code="TUIT_AUDIT")
        fee_structure = FeeStructure.objects.create(
            name="Tuition Structure 2026",
            academic_year=self.ay,
            program=self.prog,
            is_locked=False
        )
        FeeStructureItem.objects.create(
            fee_structure=fee_structure,
            fee_head=fee_head,
            amount=50000
        )

        with self.assertRaises(ProtectedError):
            fee_head.delete()
