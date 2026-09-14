from datetime import date
from django.test import TestCase
from apps.register.services.dashboard_service import DashboardService
from apps.academic.models import Department, Program, AcademicYear, Semester, Batch, Scheme
from apps.students.models import Student, StudentEnrollment, StudentCategory
from apps.verification.models import VerificationRequest
from apps.identity.models import User


class DashboardMetricsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('admin@inst.edu', 'AdminPass123!')

        self.dept = Department.objects.create(name='Information Technology', code='IT')
        self.prog = Program.objects.create(department=self.dept, name='B.Tech IT', code='BTECH-IT')
        self.ay = AcademicYear.objects.create(label='2026-2027', start_date=date(2026, 7, 1), end_date=date(2027, 6, 30), is_current=True)
        self.sem = Semester.objects.create(academic_year=self.ay, number=1)
        self.batch = Batch.objects.create(department=self.dept, name='IT-A', academic_year=self.ay)
        self.scheme = Scheme.objects.create(program=self.prog, name='IT Sch', code='IT-SCH', effective_from_year=self.ay)

        # 2 Students: 1 Male, 1 Female; 1 Active, 1 Admitted; 1 OPEN, 1 SC
        self.s1 = Student.objects.create(
            candidate_name='Candidate One', enrollment_no='E1', gender='MALE', status='ACTIVE', date_of_birth=date(2005, 1, 1)
        )
        StudentEnrollment.objects.create(
            student=self.s1, department=self.dept, program=self.prog, batch=self.batch,
            academic_year=self.ay, semester=self.sem, scheme=self.scheme
        )
        StudentCategory.objects.create(student=self.s1, category='OPEN')
        VerificationRequest.objects.create(student=self.s1, entity_type='DOCUMENT', status='APPROVED', submitted_by=self.user)

        self.s2 = Student.objects.create(
            candidate_name='Candidate Two', enrollment_no='E2', gender='FEMALE', status='DETAINED', date_of_birth=date(2005, 2, 1)
        )
        StudentEnrollment.objects.create(
            student=self.s2, department=self.dept, program=self.prog, batch=self.batch,
            academic_year=self.ay, semester=self.sem, scheme=self.scheme
        )
        StudentCategory.objects.create(student=self.s2, category='SC')
        VerificationRequest.objects.create(student=self.s2, entity_type='DOCUMENT', status='PENDING', submitted_by=self.user)

    def test_dashboard_summary_metrics(self):
        summary = DashboardService.get_dashboard_summary(self.user)

        self.assertEqual(summary['total_students'], 2)
        self.assertEqual(summary['active_students'], 1)

        # Status distribution
        self.assertEqual(summary['status_distribution'].get('ACTIVE'), 1)
        self.assertEqual(summary['status_distribution'].get('DETAINED'), 1)

        # Gender distribution
        self.assertEqual(summary['gender_distribution'].get('MALE'), 1)
        self.assertEqual(summary['gender_distribution'].get('FEMALE'), 1)

        # Category distribution
        self.assertEqual(summary['category_distribution'].get('OPEN'), 1)
        self.assertEqual(summary['category_distribution'].get('SC'), 1)

        # Department distribution
        self.assertEqual(len(summary['department_distribution']), 1)
        self.assertEqual(summary['department_distribution'][0]['code'], 'IT')
        self.assertEqual(summary['department_distribution'][0]['student_count'], 2)

        # Verification breakdown
        self.assertEqual(summary['verification_breakdown']['APPROVED'], 1)
        self.assertEqual(summary['verification_breakdown']['PENDING'], 1)
