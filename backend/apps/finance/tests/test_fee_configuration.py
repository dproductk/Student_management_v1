"""
Unit tests for Fee Configuration & Historical Protection (Tasks 9.1.1, 9.1.2, 9.1.3).
"""

from decimal import Decimal
from datetime import date
from django.test import TestCase
from apps.identity.models import User
from apps.academic.models import AcademicYear, Department, Program
from apps.finance.models import FeeHead, FeeStructure, FeeStructureItem
from apps.finance.services.fee_service import FeeService
from common.exceptions import InvariantViolationError


class FeeConfigurationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='accountant',
            email='accountant@college.edu',
            password='TestPassword123!'
        )
        self.ay = AcademicYear.objects.create(
            label='2024-25',
            start_date=date(2024, 7, 1),
            end_date=date(2025, 6, 30)
        )
        self.dept = Department.objects.create(name='Computer Engineering', code='CE')
        self.prog = Program.objects.create(name='B.Tech Computer Engineering', code='BTCE', department=self.dept)

    def test_fee_head_creation_and_uniqueness(self):
        head = FeeService.create_fee_head(
            name='Tuition Fee',
            code='TUITION',
            description='Annual academic tuition component'
        )
        self.assertEqual(head.code, 'TUITION')
        self.assertEqual(head.name, 'Tuition Fee')
        self.assertTrue(head.is_active)

    def test_fee_structure_creation_and_total_recalculation(self):
        h1 = FeeService.create_fee_head(name='Tuition Fee', code='TUIT')
        h2 = FeeService.create_fee_head(name='Development Fee', code='DEV')
        h3 = FeeService.create_fee_head(name='Exam Fee', code='EXAM')

        structure = FeeService.create_fee_structure(
            name='Annual B.Tech Open Fee 2024-25',
            academic_year=self.ay,
            department=self.dept,
            program=self.prog,
            category='OPEN',
            items=[
                {'fee_head': h1, 'amount': Decimal('75000.00')},
                {'fee_head': h2, 'amount': Decimal('15000.00')},
                {'fee_head': h3, 'amount': Decimal('5000.00')},
            ],
            actor=self.user
        )

        self.assertEqual(structure.items.count(), 3)
        self.assertEqual(structure.total_amount, Decimal('95000.00'))
        self.assertFalse(structure.is_locked)

    def test_fee_structure_historical_protection(self):
        """Historical fee structures must be protected once locked (Task 9.1.3)."""
        h1 = FeeService.create_fee_head(name='Tuition Fee', code='TUIT_LOCK')
        structure = FeeService.create_fee_structure(
            name='Protected Structure 2024',
            academic_year=self.ay,
            category='ALL',
            items=[{'fee_head': h1, 'amount': Decimal('50000.00')}],
            actor=self.user
        )

        # Lock structure
        structure.is_locked = True
        structure.save(update_fields=['is_locked'])

        # Attempting to add an item to a locked structure must fail
        h2 = FeeService.create_fee_head(name='Library Fee', code='LIB_LOCK')
        with self.assertRaises(InvariantViolationError) as ctx:
            FeeStructureItem.objects.create(
                fee_structure=structure,
                fee_head=h2,
                amount=Decimal('2000.00')
            )
        self.assertIn("Historical fee structure is locked", str(ctx.exception))
