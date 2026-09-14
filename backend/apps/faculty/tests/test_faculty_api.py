from datetime import date
from rest_framework.test import APITestCase
from rest_framework import status
from apps.faculty.models import Faculty, FacultyStatus, AssignmentRole, AcademicItemType
from apps.faculty.services.faculty_service import FacultyService
from apps.academic.models import Department, Program, AcademicYear, Semester, Batch, Scheme, Subject, SchemeSubject
from apps.students.models import Student, StudentEnrollment
from apps.identity.models import User


class FacultyAPITests(APITestCase):
    def setUp(self):
        self.dept = Department.objects.create(name='Computer Science & Engineering', code='CSE')
        self.prog = Program.objects.create(department=self.dept, name='B.Tech CSE', code='BTECH-CSE')

        self.ay = AcademicYear.objects.create(
            label='2026-2027',
            start_date=date(2026, 7, 1),
            end_date=date(2027, 6, 30),
            is_current=True
        )
        self.sem = Semester.objects.create(academic_year=self.ay, number=3, label='Sem 3')
        self.batch = Batch.objects.create(department=self.dept, name='CSE-Batch-1', academic_year=self.ay)

        self.scheme = Scheme.objects.create(program=self.prog, name='CSE 2026', code='SCH-CSE-26', effective_from_year=self.ay)
        self.sub = Subject.objects.create(name='Computer Networks', code='CS303')
        self.ss = SchemeSubject.objects.create(scheme=self.scheme, subject=self.sub, semester_number=3)

        self.user_admin = User.objects.create_superuser('admin@inst.edu', 'AdminPass123!')
        self.client.force_authenticate(user=self.user_admin)

    def test_faculty_crud_and_status_transition_api(self):
        # 1. Create Faculty
        payload = {
            'faculty_id': 'FAC-API-001',
            'first_name': 'Margaret',
            'last_name': 'Hamilton',
            'email': 'margaret.hamilton@inst.edu',
            'department': str(self.dept.id),
            'designation': 'Professor',
            'date_of_joining': '2020-08-01',
            'cabin_number': 'CS-204',
            'is_hod': True
        }
        res = self.client.post('/api/v1/faculty/members/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        faculty_id = res.data['id']

        # 2. Get Detail
        res_detail = self.client.get(f'/api/v1/faculty/members/{faculty_id}/')
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(res_detail.data['full_name'], 'Margaret Hamilton')
        self.assertTrue(res_detail.data['is_hod'])

        # 3. Transition status via action
        transition_payload = {
            'status': 'ON_LEAVE'
        }
        res_trans = self.client.post(f'/api/v1/faculty/members/{faculty_id}/transition-status/', transition_payload, format='json')
        self.assertEqual(res_trans.status_code, status.HTTP_200_OK)
        self.assertEqual(res_trans.data['status'], 'ON_LEAVE')

    def test_faculty_assignment_and_retire_api(self):
        faculty = FacultyService.create_faculty(
            faculty_id='FAC-API-002',
            first_name='Leslie',
            last_name='Lamport',
            email='lamport@inst.edu',
            department=self.dept,
            date_of_joining=date(2019, 1, 1)
        )

        # Create Assignment
        payload = {
            'faculty': str(faculty.id),
            'academic_year': str(self.ay.id),
            'semester': str(self.sem.id),
            'scheme_subject': str(self.ss.id),
            'batch': str(self.batch.id),
            'role': AssignmentRole.PRIMARY_INSTRUCTOR
        }
        res = self.client.post('/api/v1/faculty/assignments/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        assignment_id = res.data['id']
        self.assertTrue(res.data['is_active'])

        # Retire Assignment
        res_retire = self.client.post(f'/api/v1/faculty/assignments/{assignment_id}/retire/', {'end_date': '2026-12-15'}, format='json')
        self.assertEqual(res_retire.status_code, status.HTTP_200_OK)
        self.assertFalse(res_retire.data['is_active'])
        self.assertEqual(res_retire.data['effective_end_date'], '2026-12-15')

    def test_faculty_academic_item_api(self):
        faculty = FacultyService.create_faculty(
            faculty_id='FAC-API-003',
            first_name='Vint',
            last_name='Cerf',
            email='cerf@inst.edu',
            department=self.dept,
            date_of_joining=date(2016, 1, 1)
        )

        payload = {
            'item_type': AcademicItemType.PUBLICATION,
            'title': 'A Protocol for Packet Network Intercommunication',
            'year': 1974,
            'details': {'journal': 'IEEE Transactions on Communications'}
        }
        res = self.client.post(f'/api/v1/faculty/members/{faculty.id}/academic-items/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['title'], 'A Protocol for Packet Network Intercommunication')

        # List via member
        res_list = self.client.get(f'/api/v1/faculty/members/{faculty.id}/academic-items/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_list.data), 1)
