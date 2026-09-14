"""
Tests for Student Search, Filtering, Pagination, and Detail APIs.
"""

from datetime import date
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.identity.models import User, Role, Permission, UserRole, RolePermission
from apps.identity.domain.rbac import RoleScopeType
from apps.academic.models import Department, Program, AcademicYear, Semester, Batch, Scheme
from apps.students.models import Student
from apps.students.services.student_service import StudentService


class StudentSearchFilterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.viewer = User.objects.create_user(username='viewer_user', password='ViewPass123!')
        
        self.view_perm = Permission.objects.create(
            codename='students.view_directory',
            description='View student directory',
            module='students'
        )
        self.role = Role.objects.create(name='STUDENT_VIEWER', scope_type=RoleScopeType.SYSTEM.value)
        RolePermission.objects.create(role=self.role, permission=self.view_perm)
        UserRole.objects.create(user=self.viewer, role=self.role, assigned_by=self.viewer)
        self.client.force_authenticate(user=self.viewer)

        # Master Data
        self.dept_cs = Department.objects.create(name="Computer Science", code="CS")
        self.dept_me = Department.objects.create(name="Mechanical Engineering", code="ME")
        self.prog_cs = Program.objects.create(department=self.dept_cs, name="B.Tech CS", code="CS101", duration_years=4)
        self.ay = AcademicYear.objects.create(label="2026-2027", start_date=date(2026, 6, 1), end_date=date(2027, 5, 31))
        self.sem = Semester.objects.create(academic_year=self.ay, number=1)
        self.batch_cs = Batch.objects.create(department=self.dept_cs, academic_year=self.ay, name="CS-BATCH-A")
        self.batch_me = Batch.objects.create(department=self.dept_me, academic_year=self.ay, name="ME-BATCH-A")
        self.scheme_cs = Scheme.objects.create(program=self.prog_cs, effective_from_year=self.ay, name="CS Scheme", code="SCH-CS")

        # Students
        self.s1 = StudentService.create_student(
            candidate_name="Amit Kumar",
            gender="MALE",
            date_of_birth=date(2005, 1, 1),
            enrollment_no="ENR_CS_01",
            application_id="APP_01",
            status="ACTIVE"
        )
        StudentService.enroll_student(
            student_id=self.s1.id,
            academic_year_id=self.ay.id,
            semester_id=self.sem.id,
            department_id=self.dept_cs.id,
            program_id=self.prog_cs.id,
            batch_id=self.batch_cs.id,
            scheme_id=self.scheme_cs.id
        )

        self.s2 = StudentService.create_student(
            candidate_name="Rohit Verma",
            gender="MALE",
            date_of_birth=date(2005, 2, 2),
            enrollment_no="ENR_ME_01",
            application_id="APP_02",
            status="DETAINED"
        )

    def test_search_by_name(self):
        res = self.client.get('/api/v1/students/?search=Amit')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['results'][0]['candidate_name'], 'Amit Kumar')

    def test_search_by_enrollment_no(self):
        res = self.client.get('/api/v1/students/?search=ENR_ME_01')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['results'][0]['candidate_name'], 'Rohit Verma')

    def test_filter_by_status(self):
        res = self.client.get('/api/v1/students/?status=DETAINED')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['results'][0]['candidate_name'], 'Rohit Verma')

    def test_filter_by_department(self):
        res = self.client.get(f'/api/v1/students/?department={self.dept_cs.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['results'][0]['candidate_name'], 'Amit Kumar')

    def test_student_detail_representation(self):
        res = self.client.get(f'/api/v1/students/{self.s1.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data
        self.assertEqual(data['candidate_name'], 'Amit Kumar')
        self.assertEqual(len(data['enrollments']), 1)
        self.assertEqual(data['enrollments'][0]['batch_name'], 'CS-BATCH-A')
