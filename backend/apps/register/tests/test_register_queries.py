from datetime import date
from django.test import TestCase
from apps.register.services.register_query_service import RegisterQueryService
from apps.academic.models import Department, Program, AcademicYear, Semester, Batch, Scheme
from apps.students.models import Student, StudentEnrollment, StudentCategory
from apps.identity.models import User


class RegisterQueryTests(TestCase):
    def setUp(self):
        self.user_admin = User.objects.create_superuser('admin@inst.edu', 'AdminPass123!')

        self.dept = Department.objects.create(name='Computer Science', code='CSE')
        self.prog = Program.objects.create(department=self.dept, name='B.Tech CSE', code='BTECH-CSE')
        self.ay = AcademicYear.objects.create(label='2026-2027', start_date=date(2026, 7, 1), end_date=date(2027, 6, 30), is_current=True)
        self.sem = Semester.objects.create(academic_year=self.ay, number=1, label='Sem 1')
        self.batch = Batch.objects.create(department=self.dept, name='Batch-A', academic_year=self.ay)
        self.scheme = Scheme.objects.create(program=self.prog, name='Scheme 26', code='SCH26', effective_from_year=self.ay)

        # Create 3 students
        self.s1 = Student.objects.create(
            candidate_name='Aarav Sharma',
            enrollment_no='ENR2026001',
            application_id='APP2026001',
            gender='MALE',
            date_of_birth=date(2005, 1, 10),
            aadhaar_masked='XXXX-XXXX-1234',
            status='ACTIVE'
        )
        StudentEnrollment.objects.create(
            student=self.s1, academic_year=self.ay, semester=self.sem,
            department=self.dept, program=self.prog, batch=self.batch, scheme=self.scheme
        )
        StudentCategory.objects.create(student=self.s1, category='OPEN', caste='General')

        self.s2 = Student.objects.create(
            candidate_name='Diya Patel',
            enrollment_no='ENR2026002',
            application_id='APP2026002',
            gender='FEMALE',
            date_of_birth=date(2005, 4, 15),
            aadhaar_masked='XXXX-XXXX-5678',
            status='ACTIVE'
        )
        StudentEnrollment.objects.create(
            student=self.s2, academic_year=self.ay, semester=self.sem,
            department=self.dept, program=self.prog, batch=self.batch, scheme=self.scheme
        )
        StudentCategory.objects.create(student=self.s2, category='OBC', caste='Patel')

        self.s3 = Student.objects.create(
            candidate_name='Rohan Verma',
            enrollment_no='ENR2026003',
            application_id='APP2026003',
            gender='MALE',
            date_of_birth=date(2004, 11, 25),
            aadhaar_masked='XXXX-XXXX-9999',
            status='DROPPED'
        )

    def test_administrative_register_query_projection(self):
        result = RegisterQueryService.query_student_register(self.user_admin)
        self.assertEqual(result['total_count'], 3)
        self.assertEqual(len(result['results']), 3)

        first = next(r for r in result['results'] if r['enrollment_no'] == 'ENR2026001')
        self.assertEqual(first['candidate_name'], 'Aarav Sharma')
        self.assertEqual(first['department_code'], 'CSE')
        self.assertEqual(first['program_code'], 'BTECH-CSE')
        self.assertEqual(first['batch_name'], 'Batch-A')
        self.assertEqual(first['academic_year'], '2026-2027')
        self.assertEqual(first['category'], 'OPEN')
        # Ensure sensitive identity is masked
        self.assertEqual(first['aadhaar_masked'], 'XXXX-XXXX-1234')

    def test_search_by_name_enrollment_and_application_id(self):
        # By Name
        res1 = RegisterQueryService.query_student_register(self.user_admin, filters={'search': 'Patel'})
        self.assertEqual(res1['total_count'], 1)
        self.assertEqual(res1['results'][0]['candidate_name'], 'Diya Patel')

        # By Enrollment No
        res2 = RegisterQueryService.query_student_register(self.user_admin, filters={'search': 'ENR2026003'})
        self.assertEqual(res2['total_count'], 1)
        self.assertEqual(res2['results'][0]['candidate_name'], 'Rohan Verma')

        # By Application ID
        res3 = RegisterQueryService.query_student_register(self.user_admin, filters={'search': 'APP2026001'})
        self.assertEqual(res3['total_count'], 1)
        self.assertEqual(res3['results'][0]['candidate_name'], 'Aarav Sharma')

    def test_bounded_pagination(self):
        res_page = RegisterQueryService.query_student_register(self.user_admin, limit=2, offset=0)
        self.assertEqual(res_page['total_count'], 3)
        self.assertEqual(len(res_page['results']), 2)

        res_offset = RegisterQueryService.query_student_register(self.user_admin, limit=2, offset=2)
        self.assertEqual(len(res_offset['results']), 1)
