"""
Unit tests for Assessment Foundation & Definitions (Tasks 10.1.1, 10.1.2).
Verifies:
- Extensible assessment types (Unit Test, In-Sem, Practical, etc.)
- Assessment definition connected to academic foundation and subject context
- Structured mark storage and association with student and subject
"""

from decimal import Decimal
from datetime import date
from django.test import TestCase
from apps.identity.models import User
from apps.academic.models import AcademicYear, Semester, Department, Program, Batch, Scheme, Subject, SchemeSubject
from apps.students.models import Student, StudentEnrollment
from apps.assessments.models import AssessmentType, Assessment, AssessmentMark, AssessmentStatus
from apps.assessments.services.assessment_service import AssessmentService
from common.exceptions import InvariantViolationError


class AssessmentDefinitionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='prof_sharma',
            email='sharma@college.edu',
            password='TestPassword123!'
        )
        self.ay = AcademicYear.objects.create(
            label='2024-25',
            start_date=date(2024, 7, 1),
            end_date=date(2025, 6, 30)
        )
        self.dept = Department.objects.create(name='Computer Engineering', code='CE')
        self.prog = Program.objects.create(name='B.Tech Computer Engineering', code='BTCE', department=self.dept)
        self.sem = Semester.objects.create(academic_year=self.ay, number=3, label='Semester 3', start_date=date(2024, 7, 1), end_date=date(2024, 12, 31))
        self.batch = Batch.objects.create(name='CE-Batch-A', department=self.dept, academic_year=self.ay)
        self.scheme = Scheme.objects.create(name='2024 Scheme', code='SCH-CE-2024', program=self.prog, effective_from_year=self.ay)
        self.subject = Subject.objects.create(name='Data Structures & Algorithms', code='CS301')
        self.scheme_sub = SchemeSubject.objects.create(
            scheme=self.scheme,
            subject=self.subject,
            semester_number=3,
            credits=4,
            max_marks=100,
            passing_marks=40
        )

        self.student = Student.objects.create(
            candidate_name='Aarav Patel',
            enrollment_no='ENR2024501',
            application_id='APP2024501',
            date_of_birth=date(2005, 6, 12),
            gender='MALE'
        )
        self.enrollment = StudentEnrollment.objects.create(
            student=self.student,
            academic_year=self.ay,
            department=self.dept,
            program=self.prog,
            semester=self.sem,
            batch=self.batch,
            scheme=self.scheme
        )

    def test_assessment_type_creation_and_extensibility(self):
        """Assessment model must remain extensible beyond Unit Tests (PRD Section 5.1 Requirement 4)."""
        ut1 = AssessmentService.create_assessment_type(
            code='UNIT_TEST_1',
            name='Unit Test 1',
            description='First unit test evaluated in-semester'
        )
        self.assertEqual(ut1.code, 'UNIT_TEST_1')

        # Also support assignments / continuous evaluation
        asgn = AssessmentService.create_assessment_type(
            code='ASSIGNMENT',
            name='Continuous Assignment',
            description='Take-home assignment'
        )
        self.assertEqual(asgn.code, 'ASSIGNMENT')

    def test_assessment_definition_creation(self):
        """Creates assessment linked to academic foundation and subject."""
        ut1_type = AssessmentService.create_assessment_type(code='UNIT_TEST_1', name='Unit Test 1')

        assessment = AssessmentService.create_assessment(
            title='DSA Unit Test 1',
            assessment_type=ut1_type,
            academic_year=self.ay,
            semester=self.sem,
            department=self.dept,
            program=self.prog,
            scheme_subject=self.scheme_sub,
            batch=self.batch,
            max_marks=Decimal('25.00'),
            passing_marks=Decimal('10.00'),
            assessment_date=date(2024, 9, 15),
            actor=self.user
        )

        self.assertEqual(assessment.title, 'DSA Unit Test 1')
        self.assertEqual(assessment.max_marks, Decimal('25.00'))
        self.assertEqual(assessment.status, AssessmentStatus.DRAFT)
        self.assertEqual(assessment.scheme_subject.subject.code, 'CS301')

    def test_structured_mark_storage_and_association(self):
        """Stores structured mark associated with student and assessment."""
        ut1_type = AssessmentService.create_assessment_type(code='UNIT_TEST_1', name='Unit Test 1')
        assessment = AssessmentService.create_assessment(
            title='DSA Unit Test 1',
            assessment_type=ut1_type,
            academic_year=self.ay,
            semester=self.sem,
            department=self.dept,
            scheme_subject=self.scheme_sub,
            max_marks=Decimal('25.00'),
            actor=self.user
        )

        mark = AssessmentMark.objects.create(
            assessment=assessment,
            student=self.student,
            enrollment=self.enrollment,
            marks_obtained=Decimal('22.50'),
            is_absent=False,
            remarks='Excellent performance in Trees',
            entered_by=self.user
        )

        self.assertEqual(mark.marks_obtained, Decimal('22.50'))
        self.assertEqual(mark.student.candidate_name, 'Aarav Patel')
        self.assertFalse(mark.is_absent)
