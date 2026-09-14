from datetime import date
from rest_framework.test import APITestCase
from rest_framework import status
from apps.academic.models import Department, Program, AcademicYear, Semester, Batch, Scheme
from apps.students.models import Student, StudentEnrollment, StudentCategory
from apps.identity.models import User


class RegisterAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('admin@inst.edu', 'AdminPass123!')
        self.client.force_authenticate(user=self.user)

        self.dept = Department.objects.create(name='Biotechnology', code='BIO')
        self.prog = Program.objects.create(department=self.dept, name='B.Tech Biotech', code='BTECH-BIO')
        self.ay = AcademicYear.objects.create(label='2026-2027', start_date=date(2026, 7, 1), end_date=date(2027, 6, 30), is_current=True)
        self.sem = Semester.objects.create(academic_year=self.ay, number=1)
        self.batch = Batch.objects.create(department=self.dept, name='BIO-1', academic_year=self.ay)
        self.scheme = Scheme.objects.create(program=self.prog, name='BIO Sch', code='BIO-SCH', effective_from_year=self.ay)

        self.student = Student.objects.create(
            candidate_name='Kavita Krishnan',
            enrollment_no='BIO2026001',
            gender='FEMALE',
            date_of_birth=date(2005, 7, 14),
            status='ACTIVE'
        )
        StudentEnrollment.objects.create(
            student=self.student, department=self.dept, program=self.prog, batch=self.batch,
            academic_year=self.ay, semester=self.sem, scheme=self.scheme
        )
        StudentCategory.objects.create(student=self.student, category='OPEN')

    def test_student_register_endpoint(self):
        res = self.client.get('/api/v1/register/students/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_count'], 1)
        self.assertEqual(res.data['results'][0]['candidate_name'], 'Kavita Krishnan')
        self.assertEqual(res.data['results'][0]['department_code'], 'BIO')

    def test_dashboard_endpoint(self):
        res = self.client.get('/api/v1/register/dashboard/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_students'], 1)
        self.assertEqual(res.data['gender_distribution']['FEMALE'], 1)
        self.assertEqual(res.data['category_distribution']['OPEN'], 1)

    def test_export_endpoint(self):
        res = self.client.get('/api/v1/register/export/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="student_administrative_register.csv"', res['Content-Disposition'])
        content = res.content.decode('utf-8')
        self.assertIn('Kavita Krishnan', content)
        self.assertIn('BIO2026001', content)

    def test_unauthenticated_access_rejected(self):
        self.client.logout()
        res = self.client.get('/api/v1/register/students/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
