"""
Unit tests for Student Charges & Annual Assessment (Tasks 9.2.1, 9.2.2, 9.2.3).
Verifies that fee accountant once a year assesses fees to enrolled students.
"""

from decimal import Decimal
from datetime import date
from django.test import TestCase
from apps.identity.models import User
from apps.academic.models import AcademicYear, Department, Program, Semester, Batch, Scheme
from apps.students.models import Student, StudentEnrollment, StudentCategory
from apps.finance.models import FeeHead, FeeStructure, StudentFeeAccount, FeeCharge, ChargeStatus
from apps.finance.services.fee_service import FeeService


class ChargeGenerationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='accountant2',
            email='accountant2@college.edu',
            password='TestPassword123!'
        )
        self.ay = AcademicYear.objects.create(
            label='2024-25',
            start_date=date(2024, 7, 1),
            end_date=date(2025, 6, 30)
        )
        self.dept = Department.objects.create(name='Mechanical Engineering', code='ME')
        self.prog = Program.objects.create(name='B.Tech Mechanical', code='BTME', department=self.dept)
        self.sem = Semester.objects.create(academic_year=self.ay, number=1, label='Semester 1', start_date=date(2024, 7, 1), end_date=date(2024, 12, 31))
        self.batch = Batch.objects.create(name='Batch 2024', department=self.dept, academic_year=self.ay)
        self.scheme = Scheme.objects.create(name='ME Scheme 2024', code='ME-SCH-2024', program=self.prog, effective_from_year=self.ay)

        # Create Fee Heads
        self.tuit_head = FeeService.create_fee_head(name='Tuition', code='TUIT_GEN')
        self.dev_head = FeeService.create_fee_head(name='Development', code='DEV_GEN')

        # Create Fee Structures: one OPEN (₹80,000) and one SC (₹10,000)
        self.open_struct = FeeService.create_fee_structure(
            name='B.Tech ME Open 2024-25',
            academic_year=self.ay,
            department=self.dept,
            program=self.prog,
            category='OPEN',
            items=[
                {'fee_head': self.tuit_head, 'amount': Decimal('70000.00')},
                {'fee_head': self.dev_head, 'amount': Decimal('10000.00')},
            ],
            actor=self.user
        )

        self.sc_struct = FeeService.create_fee_structure(
            name='B.Tech ME SC 2024-25',
            academic_year=self.ay,
            department=self.dept,
            program=self.prog,
            category='SC',
            items=[
                {'fee_head': self.dev_head, 'amount': Decimal('10000.00')},
            ],
            actor=self.user
        )

        # Create 2 Students
        self.s1 = Student.objects.create(
            candidate_name='Rahul Sharma',
            enrollment_no='ENR2024001',
            application_id='APP2024001',
            date_of_birth=date(2005, 1, 1),
            gender='MALE'
        )
        StudentCategory.objects.create(student=self.s1, category='OPEN')
        StudentEnrollment.objects.create(
            student=self.s1,
            academic_year=self.ay,
            department=self.dept,
            program=self.prog,
            semester=self.sem,
            batch=self.batch,
            scheme=self.scheme
        )

        self.s2 = Student.objects.create(
            candidate_name='Amit Kamble',
            enrollment_no='ENR2024002',
            application_id='APP2024002',
            date_of_birth=date(2005, 3, 15),
            gender='MALE'
        )
        StudentCategory.objects.create(student=self.s2, category='SC')
        StudentEnrollment.objects.create(
            student=self.s2,
            academic_year=self.ay,
            department=self.dept,
            program=self.prog,
            semester=self.sem,
            batch=self.batch,
            scheme=self.scheme
        )

    def test_annual_fee_assessment_for_all_students(self):
        """Accountant triggers annual fee assessment across all enrolled students."""
        result = FeeService.assess_annual_fees(
            academic_year=self.ay,
            department=self.dept,
            program=self.prog,
            due_date=date(2024, 9, 30),
            actor=self.user
        )

        self.assertEqual(result['created_charges'], 2)
        self.assertEqual(result['skipped_enrollments'], 0)

        # Check Rahul (OPEN) charge
        acc1 = StudentFeeAccount.objects.get(student=self.s1)
        charge1 = acc1.charges.first()
        self.assertEqual(charge1.fee_structure, self.open_struct)
        self.assertEqual(charge1.total_amount, Decimal('80000.00'))
        self.assertEqual(charge1.status, ChargeStatus.UNPAID)
        self.assertEqual(acc1.total_billed, Decimal('80000.00'))
        self.assertEqual(acc1.outstanding_balance, Decimal('80000.00'))

        # Check Amit (SC) charge
        acc2 = StudentFeeAccount.objects.get(student=self.s2)
        charge2 = acc2.charges.first()
        self.assertEqual(charge2.fee_structure, self.sc_struct)
        self.assertEqual(charge2.total_amount, Decimal('10000.00'))
        self.assertEqual(charge2.status, ChargeStatus.UNPAID)
        self.assertEqual(acc2.total_billed, Decimal('10000.00'))
        self.assertEqual(acc2.outstanding_balance, Decimal('10000.00'))

        # Check that applied structures were automatically locked
        self.open_struct.refresh_from_db()
        self.sc_struct.refresh_from_db()
        self.assertTrue(self.open_struct.is_locked)
        self.assertTrue(self.sc_struct.is_locked)

    def test_duplicate_annual_assessment_skips_existing_charges(self):
        """Re-running annual assessment does not duplicate charges."""
        FeeService.assess_annual_fees(academic_year=self.ay, actor=self.user)
        # Run again
        result2 = FeeService.assess_annual_fees(academic_year=self.ay, actor=self.user)
        self.assertEqual(result2['created_charges'], 0)
        self.assertEqual(result2['skipped_enrollments'], 2)
        self.assertEqual(FeeCharge.objects.count(), 2)
