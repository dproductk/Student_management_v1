"""
Tests for Scheme, Subject, Scheme-Subject, and Historical Curriculum Integrity.
"""

from datetime import date
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from common.exceptions import InvariantViolationError
from apps.identity.models import User, Role, Permission, UserRole, RolePermission
from apps.identity.domain.rbac import RoleScopeType
from apps.academic.models import Department, Program, AcademicYear, Scheme, Subject, SchemeSubject
from apps.academic.services.academic_service import AcademicService


class CurriculumTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(username='curriculum_admin', password='AdminPass123!', email='curr@test.com')
        self.manage_perm, _ = Permission.objects.get_or_create(
            codename='academic.manage_curriculum',
            defaults={'description': 'Manage Curriculum', 'module': 'academic'}
        )
        self.admin_role = Role.objects.create(name='CURRICULUM_ADMIN', scope_type=RoleScopeType.SYSTEM.value)
        RolePermission.objects.create(role=self.admin_role, permission=self.manage_perm)
        UserRole.objects.create(user=self.admin, role=self.admin_role, assigned_by=self.admin)

        self.dept = AcademicService.create_department(name="Computer Science", code="CSE")
        self.prog = AcademicService.create_program(department_id=self.dept.id, name="B.Tech CSE", code="CS")
        self.ay = AcademicService.create_academic_year(
            label="2026-2027",
            start_date=date(2026, 6, 1),
            end_date=date(2027, 5, 31)
        )

    def test_scheme_and_subject_creation(self):
        scheme = AcademicService.create_scheme(
            program_id=self.prog.id,
            effective_from_year_id=self.ay.id,
            name="2026 Choice Based Credit Scheme",
            code="SCHEME-2026"
        )
        self.assertEqual(scheme.code, "SCHEME-2026")

        subj = AcademicService.create_subject(name="Data Structures & Algorithms", code="CS201")
        self.assertEqual(subj.code, "CS201")

        # Duplicate subject code should fail
        with self.assertRaises(InvariantViolationError):
            AcademicService.create_subject(name="Different Title", code="CS201")

    def test_scheme_subject_mapping_and_marks_invariants(self):
        scheme = AcademicService.create_scheme(
            program_id=self.prog.id,
            effective_from_year_id=self.ay.id,
            name="2026 Scheme",
            code="SCHEME-26"
        )
        subj = AcademicService.create_subject(name="Database Systems", code="CS202")

        # Invalid: passing marks > max marks
        with self.assertRaises(InvariantViolationError):
            AcademicService.add_scheme_subject(
                scheme_id=scheme.id,
                subject_id=subj.id,
                semester_number=3,
                credits=4,
                max_marks=100,
                passing_marks=105
            )

        # Valid scheme subject creation
        ss = AcademicService.add_scheme_subject(
            scheme_id=scheme.id,
            subject_id=subj.id,
            semester_number=3,
            credits=4,
            max_marks=100,
            passing_marks=40,
            max_internal_marks=30,
            passing_internal_marks=12
        )
        self.assertEqual(ss.credits, 4)

        # Duplicate subject in same scheme and semester should fail
        with self.assertRaises(InvariantViolationError):
            AcademicService.add_scheme_subject(
                scheme_id=scheme.id,
                subject_id=subj.id,
                semester_number=3,
                credits=4,
                max_marks=100,
                passing_marks=40
            )

    def test_historical_integrity_preservation_on_locked_scheme_subject(self):
        """Historical integrity rule: locked scheme subjects cannot be modified or deleted."""
        scheme = AcademicService.create_scheme(
            program_id=self.prog.id,
            effective_from_year_id=self.ay.id,
            name="Locked Scheme",
            code="SCHEME-LOCK"
        )
        subj = AcademicService.create_subject(name="Operating Systems", code="CS203")
        ss = AcademicService.add_scheme_subject(
            scheme_id=scheme.id,
            subject_id=subj.id,
            semester_number=4,
            credits=4,
            max_marks=100,
            passing_marks=40
        )
        # Lock the scheme subject as if results/enrollments were recorded against it
        ss.is_locked = True
        ss.save()

        # Attempt to modify credits or marks distribution on locked record must fail
        ss.credits = 5
        with self.assertRaises(InvariantViolationError):
            ss.save()

        # Reload clean state
        ss.refresh_from_db()
        self.assertEqual(ss.credits, 4)

        # Attempt to delete locked scheme subject must fail
        with self.assertRaises(InvariantViolationError):
            ss.delete()
