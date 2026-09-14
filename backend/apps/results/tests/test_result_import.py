import uuid
from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.academic.models import Department, Program, AcademicYear, Semester, Scheme, Subject, SchemeSubject, Batch
from apps.students.models import Student, StudentEnrollment
from apps.results.models import ResultImportBatch, ResultImportRow
from apps.results.services.result_service import ResultService
from apps.results.domain.invariants import ResultValidationError, InvalidLifecycleTransitionError

User = get_user_model()


class ResultImportTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="exam_controller",
            email="exam@college.edu",
            password="testpassword123"
        )

        self.dept = Department.objects.create(name="Computer Engineering", code="CE")
        self.program = Program.objects.create(name="B.Tech Computer Engineering", code="BTCE", department=self.dept)
        self.ay = AcademicYear.objects.create(
            label="2024-2025",
            start_date=date(2024, 8, 1),
            end_date=date(2025, 5, 31)
        )
        self.sem = Semester.objects.create(
            academic_year=self.ay,
            number=4,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 5, 31)
        )
        self.batch = Batch.objects.create(
            department=self.dept,
            academic_year=self.ay,
            name="2024-B1"
        )
        self.scheme = Scheme.objects.create(
            program=self.program,
            name="2024 Revised Scheme",
            code="SCH2024",
            effective_from_year=self.ay
        )
        self.subj1 = Subject.objects.create(name="Data Structures", code="CS401")
        self.subj2 = Subject.objects.create(name="Computer Networks", code="CS402")

        self.ss1 = SchemeSubject.objects.create(
            scheme=self.scheme,
            subject=self.subj1,
            semester_number=self.sem.number,
            max_internal_marks=40,
            max_marks=100
        )
        self.ss2 = SchemeSubject.objects.create(
            scheme=self.scheme,
            subject=self.subj2,
            semester_number=self.sem.number,
            max_internal_marks=40,
            max_marks=100
        )

        # Create two enrolled students
        self.s1 = Student.objects.create(
            candidate_name="Rohan Sharma",
            gender="MALE",
            date_of_birth=date(2005, 1, 1),
            enrollment_no="ENR2024401",
            application_id="APP2024401",
            email="rohan@student.edu"
        )
        StudentEnrollment.objects.create(
            student=self.s1,
            academic_year=self.ay,
            semester=self.sem,
            department=self.dept,
            program=self.program,
            batch=self.batch,
            scheme=self.scheme,
            status='ACTIVE'
        )

        self.s2 = Student.objects.create(
            candidate_name="Priya Patel",
            gender="FEMALE",
            date_of_birth=date(2005, 2, 2),
            enrollment_no="ENR2024402",
            application_id="APP2024402",
            email="priya@student.edu"
        )
        StudentEnrollment.objects.create(
            student=self.s2,
            academic_year=self.ay,
            semester=self.sem,
            department=self.dept,
            program=self.program,
            batch=self.batch,
            scheme=self.scheme,
            status='ACTIVE'
        )

    def test_11_1_1_import_batch_and_row_foundation(self):
        """11.1.1: Verify import batch and staging row schema foundation."""
        batch = ResultService.create_import_batch(
            academic_year_id=str(self.ay.id),
            semester_id=str(self.sem.id),
            department_id=str(self.dept.id),
            program_id=str(self.program.id),
            file_name="sem4_results.csv",
            uploaded_by=self.user,
            remarks="Initial upload"
        )
        self.assertIsNotNone(batch.id)
        self.assertEqual(batch.status, 'PENDING')
        self.assertEqual(batch.total_rows, 0)

        # Direct staging row creation
        row = ResultImportRow.objects.create(
            batch=batch,
            row_number=1,
            student_identifier="ENR2024401",
            subject_code="CS401",
            internal_marks=Decimal('35.00'),
            external_marks=Decimal('52.00'),
            total_marks=Decimal('87.00'),
            status='PENDING'
        )
        self.assertIsNotNone(row.id)
        self.assertEqual(row.batch, batch)
        self.assertEqual(row.student_identifier, "ENR2024401")

    def test_11_1_2_csv_parsing_and_staging(self):
        """11.1.2: Verify CSV parsing and staging row creation."""
        batch = ResultService.create_import_batch(
            academic_year_id=str(self.ay.id),
            semester_id=str(self.sem.id),
            department_id=str(self.dept.id),
            program_id=str(self.program.id),
            file_name="sem4_results.csv",
            uploaded_by=self.user
        )

        csv_content = """student_identifier,subject_code,internal_marks,external_marks
ENR2024401,CS401,34,50
ENR2024401,CS402,32,48
ENR2024402,CS401,38,55
ENR2024402,CS402,36,52
"""
        rows_data = ResultService.parse_csv_content(csv_content)
        self.assertEqual(len(rows_data), 4)

        staged_rows = ResultService.extract_and_stage_rows(batch, rows_data)
        batch.refresh_from_db()

        self.assertEqual(len(staged_rows), 4)
        self.assertEqual(batch.total_rows, 4)
        self.assertEqual(batch.status, 'PROCESSING')

    def test_11_1_3_and_4_extraction_validation_and_deterministic_matching(self):
        """11.1.3 & 11.1.4: Validation and student/scheme association."""
        batch = ResultService.create_import_batch(
            academic_year_id=str(self.ay.id),
            semester_id=str(self.sem.id),
            department_id=str(self.dept.id),
            program_id=str(self.program.id),
            file_name="sem4_results.csv",
            uploaded_by=self.user
        )

        # One matched by enrollment_no, one matched by application_id
        csv_content = f"""student_identifier,subject_code,internal_marks,external_marks
{self.s1.enrollment_no},CS401,35,50
{self.s2.application_id},CS402,30,45
"""
        rows_data = ResultService.parse_csv_content(csv_content)
        ResultService.extract_and_stage_rows(batch, rows_data)

        val_result = ResultService.validate_and_associate_rows(batch)
        self.assertTrue(val_result['success'])
        self.assertEqual(val_result['valid_rows'], 2)
        self.assertEqual(val_result['error_rows'], 0)

        batch.refresh_from_db()
        self.assertEqual(batch.status, 'VALIDATED')

        rows = list(batch.rows.all().order_by('row_number'))
        # First row matched to s1 by enrollment_no
        self.assertEqual(rows[0].matched_student, self.s1)
        self.assertEqual(rows[0].matched_scheme_subject, self.ss1)
        self.assertEqual(rows[0].status, 'VALID')
        self.assertEqual(rows[0].total_marks, Decimal('85.00'))
        self.assertEqual(rows[0].grade, 'A+')

        # Second row matched to s2 by application_id
        self.assertEqual(rows[1].matched_student, self.s2)
        self.assertEqual(rows[1].matched_scheme_subject, self.ss2)
        self.assertEqual(rows[1].status, 'VALID')
        self.assertEqual(rows[1].total_marks, Decimal('75.00'))
        self.assertEqual(rows[1].grade, 'A')

    def test_validation_failure_on_invalid_marks_and_unmatched_student(self):
        """Verify that invalid rows are flagged and prevent batch validation."""
        batch = ResultService.create_import_batch(
            academic_year_id=str(self.ay.id),
            semester_id=str(self.sem.id),
            department_id=str(self.dept.id),
            program_id=str(self.program.id),
            file_name="invalid_results.csv",
            uploaded_by=self.user
        )

        csv_content = """student_identifier,subject_code,internal_marks,external_marks
UNKNOWN_STU,CS401,35,50
ENR2024401,INVALID_SUBJ,35,50
ENR2024401,CS401,60,70
"""
        rows_data = ResultService.parse_csv_content(csv_content)
        ResultService.extract_and_stage_rows(batch, rows_data)

        val_result = ResultService.validate_and_associate_rows(batch)
        self.assertFalse(val_result['success'])
        self.assertEqual(val_result['error_rows'], 3)

        batch.refresh_from_db()
        self.assertEqual(batch.status, 'FAILED')

        rows = list(batch.rows.all().order_by('row_number'))
        self.assertEqual(rows[0].status, 'INVALID')
        self.assertIn("No student record matched", str(rows[0].validation_errors))

        self.assertEqual(rows[1].status, 'INVALID')
        self.assertIn("Subject code 'INVALID_SUBJ' not found", str(rows[1].validation_errors))

        self.assertEqual(rows[2].status, 'INVALID')
        self.assertIn("Total marks (130.00) exceed maximum", str(rows[2].validation_errors))
