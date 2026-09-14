"""
Tests for Academic Year, Semester, Batch, and Department Intake slices.
"""

from datetime import date
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from common.exceptions import InvariantViolationError
from apps.identity.models import User, Role, Permission, UserRole, RolePermission
from apps.identity.domain.rbac import RoleScopeType
from apps.academic.models import Department, Program, AcademicYear, Semester, Batch, DepartmentIntake
from apps.academic.services.academic_service import AcademicService


class AcademicCalendarTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(username='calendar_admin', password='AdminPass123!', email='cal@test.com')
        self.manage_perm, _ = Permission.objects.get_or_create(
            codename='academic.manage_structure',
            defaults={'description': 'Manage Academic Structure', 'module': 'academic'}
        )
        self.admin_role = Role.objects.create(name='ACADEMIC_ADMIN', scope_type=RoleScopeType.SYSTEM.value)
        RolePermission.objects.create(role=self.admin_role, permission=self.manage_perm)
        UserRole.objects.create(user=self.admin, role=self.admin_role, assigned_by=self.admin)

        self.dept = AcademicService.create_department(name="Computer Science", code="CSE")
        self.prog = AcademicService.create_program(department_id=self.dept.id, name="B.Tech CSE", code="CS")

    def test_academic_year_dates_and_current_year_exclusivity(self):
        # Invalid date range (end before start)
        with self.assertRaises(InvariantViolationError):
            AcademicService.create_academic_year(
                label="2025-2026",
                start_date=date(2026, 6, 1),
                end_date=date(2025, 5, 31)
            )

        ay1 = AcademicService.create_academic_year(
            label="2025-2026",
            start_date=date(2025, 6, 1),
            end_date=date(2026, 5, 31),
            is_current=True
        )
        self.assertTrue(ay1.is_current)

        # Creating a second academic year with is_current=True should clear ay1's current flag
        ay2 = AcademicService.create_academic_year(
            label="2026-2027",
            start_date=date(2026, 6, 1),
            end_date=date(2027, 5, 31),
            is_current=True
        )
        ay1.refresh_from_db()
        self.assertFalse(ay1.is_current)
        self.assertTrue(ay2.is_current)

    def test_semester_ordering_and_uniqueness(self):
        ay = AcademicService.create_academic_year(
            label="2026-2027",
            start_date=date(2026, 6, 1),
            end_date=date(2027, 5, 31)
        )
        sem1 = AcademicService.create_semester(
            academic_year_id=ay.id,
            number=1,
            label="Fall Semester 2026",
            start_date=date(2026, 7, 1),
            end_date=date(2026, 12, 15)
        )
        self.assertEqual(sem1.number, 1)

        # Duplicate semester number in same academic year should fail
        with self.assertRaises(InvariantViolationError):
            AcademicService.create_semester(academic_year_id=ay.id, number=1)

    def test_batch_creation_and_uniqueness(self):
        ay = AcademicService.create_academic_year(
            label="2026-2027",
            start_date=date(2026, 6, 1),
            end_date=date(2027, 5, 31)
        )
        batch = AcademicService.create_batch(
            department_id=self.dept.id,
            academic_year_id=ay.id,
            name="Batch-A"
        )
        self.assertEqual(batch.name, "Batch-A")

        # Duplicate batch in same dept & year should fail
        with self.assertRaises(InvariantViolationError):
            AcademicService.create_batch(
                department_id=self.dept.id,
                academic_year_id=ay.id,
                name="Batch-A"
            )

    def test_department_intake_capacities(self):
        ay = AcademicService.create_academic_year(
            label="2026-2027",
            start_date=date(2026, 6, 1),
            end_date=date(2027, 5, 31)
        )
        intake = AcademicService.create_intake(
            department_id=self.dept.id,
            academic_year_id=ay.id,
            program_id=self.prog.id,
            sanctioned_intake=120,
            actual_intake=115
        )
        self.assertEqual(intake.sanctioned_intake, 120)
        self.assertEqual(intake.actual_intake, 115)

        # Negative sanctioned intake should fail
        with self.assertRaises(InvariantViolationError):
            AcademicService.create_intake(
                department_id=self.dept.id,
                academic_year_id=ay.id,
                program_id=self.prog.id,
                sanctioned_intake=-10
            )
