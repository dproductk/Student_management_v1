"""
Tests for Department and Program management vertical slices.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from common.exceptions import InvariantViolationError
from apps.identity.models import User, Role, Permission, UserRole, RolePermission
from apps.identity.domain.rbac import RoleScopeType
from apps.academic.models import Department, Program
from apps.academic.services.academic_service import AcademicService


class DepartmentProgramTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Setup Admin user with academic permissions
        self.admin = User.objects.create_user(username='acad_admin', password='AdminPass123!', email='acad@test.com')
        self.manage_perm, _ = Permission.objects.get_or_create(
            codename='academic.manage_structure',
            defaults={'description': 'Manage Academic Structure', 'module': 'academic'}
        )
        self.view_perm, _ = Permission.objects.get_or_create(
            codename='academic.view_structure',
            defaults={'description': 'View Academic Structure', 'module': 'academic'}
        )
        self.admin_role = Role.objects.create(name='ACADEMIC_ADMIN', scope_type=RoleScopeType.SYSTEM.value)
        RolePermission.objects.create(role=self.admin_role, permission=self.manage_perm)
        RolePermission.objects.create(role=self.admin_role, permission=self.view_perm)
        UserRole.objects.create(user=self.admin, role=self.admin_role, assigned_by=self.admin)

        # Setup regular user with only view permissions
        self.viewer = User.objects.create_user(username='acad_viewer', password='ViewPass123!', email='viewer@test.com')
        self.viewer_role = Role.objects.create(name='ACADEMIC_VIEWER', scope_type=RoleScopeType.SYSTEM.value)
        RolePermission.objects.create(role=self.viewer_role, permission=self.view_perm)
        UserRole.objects.create(user=self.viewer, role=self.viewer_role, assigned_by=self.admin)

        # Setup unprivileged student user
        self.student = User.objects.create_user(username='student_user', password='StudentPass123!', email='stud@test.com')

    def test_department_creation_and_uniqueness(self):
        dept = AcademicService.create_department(name="Computer Science & Engineering", code="CSE")
        self.assertEqual(dept.code, "CSE")
        self.assertTrue(dept.is_active)

        # Duplicate code should fail
        with self.assertRaises(InvariantViolationError):
            AcademicService.create_department(name="Different Dept", code="CSE")

        # Duplicate name should fail
        with self.assertRaises(InvariantViolationError):
            AcademicService.create_department(name="Computer Science & Engineering", code="CS")

    def test_program_creation_and_department_scoped_uniqueness(self):
        dept1 = AcademicService.create_department(name="Computer Science", code="CS")
        dept2 = AcademicService.create_department(name="Electronics", code="EC")

        prog1 = AcademicService.create_program(
            department_id=dept1.id,
            name="Bachelor of Technology in CS",
            code="BTECH-CS",
            duration_years=4,
            degree_type="B.Tech"
        )
        self.assertEqual(prog1.department, dept1)

        # Duplicate program code in same department fails
        with self.assertRaises(InvariantViolationError):
            AcademicService.create_program(
                department_id=dept1.id,
                name="Duplicate Code",
                code="BTECH-CS"
            )

        # Same code in another department is permitted
        prog2 = AcademicService.create_program(
            department_id=dept2.id,
            name="Bachelor of Technology in EC",
            code="BTECH-CS"
        )
        self.assertEqual(prog2.department, dept2)

    def test_department_api_rbac_enforcement(self):
        # Admin creates department
        self.client.force_authenticate(user=self.admin)
        res = self.client.post('/api/v1/academic/departments/', {
            'name': 'Mechanical Engineering',
            'code': 'MECH'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        dept_id = res.data['id']

        # Viewer can read but cannot create or update
        self.client.force_authenticate(user=self.viewer)
        get_res = self.client.get('/api/v1/academic/departments/')
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(get_res.data['results']), 1)

        post_res = self.client.post('/api/v1/academic/departments/', {
            'name': 'Civil Engineering',
            'code': 'CIVIL'
        })
        self.assertEqual(post_res.status_code, status.HTTP_403_FORBIDDEN)

        # Unprivileged student receives 403 on read and write
        self.client.force_authenticate(user=self.student)
        stud_get = self.client.get('/api/v1/academic/departments/')
        self.assertEqual(stud_get.status_code, status.HTTP_403_FORBIDDEN)
