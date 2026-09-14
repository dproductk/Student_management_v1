import csv
import io
from datetime import date
from django.test import TestCase
from apps.register.services.export_service import RegisterExportService
from apps.academic.models import Department, Program, AcademicYear, Semester, Batch, Scheme
from apps.students.models import Student, StudentEnrollment, StudentCategory
from apps.identity.models import User


class RegisterExportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('admin@inst.edu', 'AdminPass123!')

        self.dept = Department.objects.create(name='Civil Engineering', code='CIVIL')
        self.prog = Program.objects.create(department=self.dept, name='B.Tech Civil', code='BTECH-CIVIL')
        self.ay = AcademicYear.objects.create(label='2026-2027', start_date=date(2026, 7, 1), end_date=date(2027, 6, 30), is_current=True)
        self.sem = Semester.objects.create(academic_year=self.ay, number=1)
        self.batch = Batch.objects.create(department=self.dept, name='CIVIL-A', academic_year=self.ay)
        self.scheme = Scheme.objects.create(program=self.prog, name='CIVIL Sch', code='CIVIL-SCH', effective_from_year=self.ay)

        self.student = Student.objects.create(
            candidate_name='Neha Gupta',
            enrollment_no='CIVIL2026001',
            application_id='APP-CIVIL-001',
            gender='FEMALE',
            date_of_birth=date(2005, 5, 20),
            aadhaar_masked='XXXX-XXXX-4321',
            email='neha.gupta@inst.edu',
            student_mobile='9876543210',
            status='ACTIVE'
        )
        StudentEnrollment.objects.create(
            student=self.student, department=self.dept, program=self.prog, batch=self.batch,
            academic_year=self.ay, semester=self.sem, scheme=self.scheme
        )
        StudentCategory.objects.create(student=self.student, category='OBC')

    def test_csv_export_format_and_data_protection(self):
        csv_text = RegisterExportService.export_register_csv(self.user)
        self.assertIsInstance(csv_text, str)

        reader = csv.reader(io.StringIO(csv_text))
        rows = list(reader)

        # Header row
        header = rows[0]
        self.assertIn('Application ID', header)
        self.assertIn('Candidate Name', header)
        self.assertIn('Masked Aadhaar', header)
        self.assertIn('Verification Status', header)

        # Ensure sensitive bank info is NOT in header
        self.assertNotIn('Bank Account Number', header)
        self.assertNotIn('IFSC Code', header)

        # Data row
        data_row = rows[1]
        self.assertEqual(data_row[0], 'APP-CIVIL-001')
        self.assertEqual(data_row[1], 'CIVIL2026001')
        self.assertEqual(data_row[2], 'Neha Gupta')
        self.assertEqual(data_row[3], 'FEMALE')
        self.assertEqual(data_row[5], 'OBC')
        self.assertEqual(data_row[6], 'CIVIL')
        # Masked Aadhaar preserved
        self.assertIn('XXXX-XXXX-4321', data_row)

    def test_export_preserves_filters(self):
        # Filter matching student
        csv_matched = RegisterExportService.export_register_csv(self.user, filters={'gender': 'FEMALE'})
        matched_rows = list(csv.reader(io.StringIO(csv_matched)))
        self.assertEqual(len(matched_rows), 2)  # 1 header + 1 student

        # Filter not matching
        csv_unmatched = RegisterExportService.export_register_csv(self.user, filters={'gender': 'MALE'})
        unmatched_rows = list(csv.reader(io.StringIO(csv_unmatched)))
        self.assertEqual(len(unmatched_rows), 1)  # header only
