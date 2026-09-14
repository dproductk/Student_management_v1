from datetime import date
from django.test import TestCase
from apps.register.services.register_query_service import RegisterQueryService
from apps.academic.models import Department, Program, AcademicYear, Semester, Batch, Scheme
from apps.students.models import Student, StudentEnrollment
from apps.identity.models import User


class AcademicFilteringTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('admin@inst.edu', 'AdminPass123!')

        self.dept_cse = Department.objects.create(name='Computer Science', code='CSE')
        self.dept_ece = Department.objects.create(name='Electronics', code='ECE')

        self.prog_cse = Program.objects.create(department=self.dept_cse, name='B.Tech CSE', code='BTECH-CSE')
        self.prog_ece = Program.objects.create(department=self.dept_ece, name='B.Tech ECE', code='BTECH-ECE')

        self.ay2025 = AcademicYear.objects.create(label='2025-2026', start_date=date(2025, 7, 1), end_date=date(2026, 6, 30))
        self.ay2026 = AcademicYear.objects.create(label='2026-2027', start_date=date(2026, 7, 1), end_date=date(2027, 6, 30), is_current=True)

        self.sem1 = Semester.objects.create(academic_year=self.ay2026, number=1, label='Sem 1')
        self.batch_cse_a = Batch.objects.create(department=self.dept_cse, name='CSE-A', academic_year=self.ay2026)
        self.batch_cse_b = Batch.objects.create(department=self.dept_cse, name='CSE-B', academic_year=self.ay2026)
        self.batch_ece = Batch.objects.create(department=self.dept_ece, name='ECE-1', academic_year=self.ay2026)

        self.scheme_cse = Scheme.objects.create(program=self.prog_cse, name='Sch CSE', code='SC-CSE', effective_from_year=self.ay2026)
        self.scheme_ece = Scheme.objects.create(program=self.prog_ece, name='Sch ECE', code='SC-ECE', effective_from_year=self.ay2026)

        # Student 1: CSE, Batch-A, 2026
        self.s1 = Student.objects.create(candidate_name='Student One', enrollment_no='S1', gender='MALE', date_of_birth=date(2005, 1, 1))
        StudentEnrollment.objects.create(
            student=self.s1, department=self.dept_cse, program=self.prog_cse,
            batch=self.batch_cse_a, academic_year=self.ay2026, semester=self.sem1, scheme=self.scheme_cse
        )

        # Student 2: CSE, Batch-B, 2026
        self.s2 = Student.objects.create(candidate_name='Student Two', enrollment_no='S2', gender='FEMALE', date_of_birth=date(2005, 2, 1))
        StudentEnrollment.objects.create(
            student=self.s2, department=self.dept_cse, program=self.prog_cse,
            batch=self.batch_cse_b, academic_year=self.ay2026, semester=self.sem1, scheme=self.scheme_cse
        )

        # Student 3: ECE, Batch-ECE, 2026
        self.s3 = Student.objects.create(candidate_name='Student Three', enrollment_no='S3', gender='MALE', date_of_birth=date(2005, 3, 1))
        StudentEnrollment.objects.create(
            student=self.s3, department=self.dept_ece, program=self.prog_ece,
            batch=self.batch_ece, academic_year=self.ay2026, semester=self.sem1, scheme=self.scheme_ece
        )

    def test_department_filtering(self):
        res_cse = RegisterQueryService.query_student_register(self.user, filters={'department': str(self.dept_cse.id)})
        self.assertEqual(res_cse['total_count'], 2)
        candidate_names = [r['candidate_name'] for r in res_cse['results']]
        self.assertIn('Student One', candidate_names)
        self.assertIn('Student Two', candidate_names)
        self.assertNotIn('Student Three', candidate_names)

        res_ece = RegisterQueryService.query_student_register(self.user, filters={'department': str(self.dept_ece.id)})
        self.assertEqual(res_ece['total_count'], 1)
        self.assertEqual(res_ece['results'][0]['candidate_name'], 'Student Three')

    def test_program_filtering(self):
        res = RegisterQueryService.query_student_register(self.user, filters={'program': str(self.prog_ece.id)})
        self.assertEqual(res['total_count'], 1)
        self.assertEqual(res['results'][0]['candidate_name'], 'Student Three')

    def test_batch_filtering(self):
        res = RegisterQueryService.query_student_register(self.user, filters={'batch': str(self.batch_cse_a.id)})
        self.assertEqual(res['total_count'], 1)
        self.assertEqual(res['results'][0]['candidate_name'], 'Student One')

    def test_academic_year_filtering(self):
        # 2026 matches all 3
        res_2026 = RegisterQueryService.query_student_register(self.user, filters={'academic_year': str(self.ay2026.id)})
        self.assertEqual(res_2026['total_count'], 3)

        # 2025 matches 0
        res_2025 = RegisterQueryService.query_student_register(self.user, filters={'academic_year': str(self.ay2025.id)})
        self.assertEqual(res_2025['total_count'], 0)
