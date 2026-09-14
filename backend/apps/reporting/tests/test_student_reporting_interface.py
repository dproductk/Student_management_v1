"""
Unit tests for Student Management reporting interface (Task 14.1.2, 14.2.1, 14.2.2).
"""
from datetime import date
from django.test import TestCase
from apps.students.models import Student, StudentEnrollment, StudentCategory
from apps.academic.models import Department, Program, AcademicYear, Semester, Batch, Scheme
from apps.students.services.student_reporting import StudentReportingQueryService


class StudentReportingInterfaceTestCase(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Computer Engineering", code="COMP")
        self.prog = Program.objects.create(name="B.Tech Computer Science", code="BT_CS", department=self.dept)
        self.ay = AcademicYear.objects.create(label="2024-2025", start_date=date(2024, 7, 1), end_date=date(2025, 6, 30))
        self.sem = Semester.objects.create(academic_year=self.ay, number=1)
        self.batch = Batch.objects.create(name="Batch 2024-28", department=self.dept, academic_year=self.ay)
        self.scheme = Scheme.objects.create(name="Scheme 2024", code="SCH_2024", program=self.prog, effective_from_year=self.ay)

        self.s1 = Student.objects.create(
            candidate_name="Alice Wonder",
            gender="FEMALE",
            date_of_birth=date(2004, 1, 1),
            enrollment_no="ENR_ST_01",
            application_id="APP_ST_01",
            status="ACTIVE"
        )
        self.s2 = Student.objects.create(
            candidate_name="Bob Builder",
            gender="MALE",
            date_of_birth=date(2004, 2, 2),
            enrollment_no="ENR_ST_02",
            application_id="APP_ST_02",
            status="ACTIVE"
        )
        self.s3 = Student.objects.create(
            candidate_name="Charlie Chaplin",
            gender="MALE",
            date_of_birth=date(2003, 3, 3),
            enrollment_no="ENR_ST_03",
            application_id="APP_ST_03",
            status="DETAINED"
        )

        StudentCategory.objects.create(student=self.s1, category="OBC")
        StudentCategory.objects.create(student=self.s2, category="OPEN")

        StudentEnrollment.objects.create(
            student=self.s1,
            academic_year=self.ay,
            department=self.dept,
            program=self.prog,
            batch=self.batch,
            semester=self.sem,
            scheme=self.scheme,
            status="ACTIVE"
        )
        StudentEnrollment.objects.create(
            student=self.s2,
            academic_year=self.ay,
            department=self.dept,
            program=self.prog,
            batch=self.batch,
            semester=self.sem,
            scheme=self.scheme,
            status="ACTIVE"
        )

    def test_population_summary(self):
        """14.2.1: Student population analytics."""
        summary = StudentReportingQueryService.get_population_summary()
        self.assertEqual(summary['total_students'], 3)
        self.assertEqual(summary['active_students'], 2)
        self.assertEqual(summary['detained_students'], 1)
        self.assertEqual(summary['total_enrolled'], 2)

    def test_demographics_breakdown(self):
        """14.2.2: Department/program/batch/category/gender analytics."""
        demo = StudentReportingQueryService.get_demographics_breakdown()
        gender_map = {g['gender']: g['count'] for g in demo['by_gender']}
        self.assertEqual(gender_map['FEMALE'], 1)
        self.assertEqual(gender_map['MALE'], 2)

        cat_map = {c['category']: c['count'] for c in demo['by_category']}
        self.assertEqual(cat_map['OBC'], 1)
        self.assertEqual(cat_map['OPEN'], 1)

        self.assertEqual(len(demo['by_department']), 1)
        self.assertEqual(demo['by_department'][0]['department__code'], 'COMP')
        self.assertEqual(demo['by_department'][0]['count'], 2)

    def test_student_reporting_records(self):
        """Paginated tabular records query."""
        res = StudentReportingQueryService.get_student_reporting_records(limit=2, offset=0)
        self.assertEqual(res['total_count'], 3)
        self.assertEqual(len(res['records']), 2)
        self.assertTrue(all('candidate_name' in r for r in res['records']))
