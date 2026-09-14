"""
Unit tests for Faculty Unit-Test Upload, Extraction, and Validation (Tasks 10.2.1, 10.2.2).
"""

from decimal import Decimal
from datetime import date
from django.test import TestCase
from apps.identity.models import User
from apps.academic.models import AcademicYear, Semester, Department, Program, Batch, Scheme, Subject, SchemeSubject
from apps.students.models import Student, StudentEnrollment
from apps.assessments.models import AssessmentType, Assessment, AssessmentMark
from apps.assessments.services.assessment_service import AssessmentService
from common.exceptions import InvariantViolationError


class MarksUploadAndValidationTestCase(TestCase):
    def setUp(self):
        self.faculty_user = User.objects.create_user(
            username='prof_patil',
            email='patil@college.edu',
            password='TestPassword123!',
            is_superuser=True  # Authorized faculty/admin
        )
        self.ay = AcademicYear.objects.create(
            label='2024-25',
            start_date=date(2024, 7, 1),
            end_date=date(2025, 6, 30)
        )
        self.dept = Department.objects.create(name='Electronics Engineering', code='EXTC')
        self.prog = Program.objects.create(name='B.Tech EXTC', code='BTEXTC', department=self.dept)
        self.sem = Semester.objects.create(academic_year=self.ay, number=1, label='Semester 1', start_date=date(2024, 7, 1), end_date=date(2024, 12, 31))
        self.batch = Batch.objects.create(name='EXTC-Batch-1', department=self.dept, academic_year=self.ay)
        self.scheme = Scheme.objects.create(name='2024 Scheme', code='SCH-EXTC-2024', program=self.prog, effective_from_year=self.ay)
        self.subject = Subject.objects.create(name='Basic Electrical Engineering', code='EE101')
        self.scheme_sub = SchemeSubject.objects.create(
            scheme=self.scheme,
            subject=self.subject,
            semester_number=1,
            credits=3,
            max_marks=100,
            passing_marks=40
        )

        # Create Students
        self.s1 = Student.objects.create(
            candidate_name='Neha Kulkarni',
            enrollment_no='ENR2024601',
            application_id='APP2024601',
            date_of_birth=date(2005, 8, 22),
            gender='FEMALE'
        )
        StudentEnrollment.objects.create(
            student=self.s1, academic_year=self.ay, department=self.dept, program=self.prog, semester=self.sem, batch=self.batch, scheme=self.scheme
        )

        self.s2 = Student.objects.create(
            candidate_name='Rohan Joshi',
            enrollment_no='ENR2024602',
            application_id='APP2024602',
            date_of_birth=date(2005, 9, 14),
            gender='MALE'
        )
        StudentEnrollment.objects.create(
            student=self.s2, academic_year=self.ay, department=self.dept, program=self.prog, semester=self.sem, batch=self.batch, scheme=self.scheme
        )

        self.ut_type = AssessmentService.create_assessment_type(code='UNIT_TEST_1', name='Unit Test 1')
        self.assessment = AssessmentService.create_assessment(
            title='BEE Unit Test 1',
            assessment_type=self.ut_type,
            academic_year=self.ay,
            semester=self.sem,
            department=self.dept,
            scheme_subject=self.scheme_sub,
            max_marks=Decimal('20.00'),
            passing_marks=Decimal('8.00'),
            actor=self.faculty_user
        )

    def test_successful_marks_upload_and_validation(self):
        """Faculty uploads valid marks for enrolled students."""
        rows = [
            {'enrollment_no': 'ENR2024601', 'marks_obtained': '18.5', 'is_absent': False, 'remarks': 'Good'},
            {'enrollment_no': 'ENR2024602', 'marks_obtained': None, 'is_absent': True, 'remarks': 'Medical leave'}
        ]

        result = AssessmentService.upload_unit_test_marks(
            assessment_id=str(self.assessment.id),
            mark_rows=rows,
            actor=self.faculty_user
        )

        self.assertEqual(result['total_processed'], 2)
        self.assertEqual(result['created_marks'], 2)

        # Verify Neha's mark
        m1 = AssessmentMark.objects.get(assessment=self.assessment, student=self.s1)
        self.assertEqual(m1.marks_obtained, Decimal('18.50'))
        self.assertFalse(m1.is_absent)

        # Verify Rohan's absent mark
        m2 = AssessmentMark.objects.get(assessment=self.assessment, student=self.s2)
        self.assertIsNone(m2.marks_obtained)
        self.assertTrue(m2.is_absent)

    def test_marks_exceeding_max_marks_rejected(self):
        """Marks exceeding max_marks (20.00) are rejected."""
        rows = [
            {'enrollment_no': 'ENR2024601', 'marks_obtained': '22.0', 'is_absent': False}
        ]

        with self.assertRaises(InvariantViolationError) as ctx:
            AssessmentService.upload_unit_test_marks(
                assessment_id=str(self.assessment.id),
                mark_rows=rows,
                actor=self.faculty_user
            )
        self.assertIn("exceeds the assessment maximum", str(ctx.exception))

    def test_negative_marks_rejected(self):
        """Negative marks are rejected."""
        rows = [
            {'enrollment_no': 'ENR2024601', 'marks_obtained': '-2.0', 'is_absent': False}
        ]

        with self.assertRaises(InvariantViolationError) as ctx:
            AssessmentService.upload_unit_test_marks(
                assessment_id=str(self.assessment.id),
                mark_rows=rows,
                actor=self.faculty_user
            )
        self.assertIn("cannot be negative", str(ctx.exception))

    def test_duplicate_student_in_payload_rejected(self):
        """Duplicate rows for the same student in an upload payload are rejected."""
        rows = [
            {'enrollment_no': 'ENR2024601', 'marks_obtained': '15.0', 'is_absent': False},
            {'enrollment_no': 'ENR2024601', 'marks_obtained': '17.0', 'is_absent': False},
        ]

        with self.assertRaises(InvariantViolationError) as ctx:
            AssessmentService.upload_unit_test_marks(
                assessment_id=str(self.assessment.id),
                mark_rows=rows,
                actor=self.faculty_user
            )
        self.assertIn("Duplicate student entries detected", str(ctx.exception))

    def test_unknown_student_rejected_atomically(self):
        """Unknown student rejects the batch atomically without persisting partial marks."""
        rows = [
            {'enrollment_no': 'ENR2024601', 'marks_obtained': '15.0', 'is_absent': False},
            {'enrollment_no': 'ENR_NON_EXISTENT', 'marks_obtained': '12.0', 'is_absent': False},
        ]

        with self.assertRaises(InvariantViolationError) as ctx:
            AssessmentService.upload_unit_test_marks(
                assessment_id=str(self.assessment.id),
                mark_rows=rows,
                actor=self.faculty_user
            )
        self.assertIn("does not exist in college records", str(ctx.exception))
        # Ensure no marks persisted due to atomic transaction rollback
        self.assertEqual(AssessmentMark.objects.filter(assessment=self.assessment).count(), 0)
