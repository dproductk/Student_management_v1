"""
Unit tests for Unit-Test Persistence, Student View, and Lock Lifecycle (Tasks 10.2.3, 10.2.4).
"""

from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.core.exceptions import PermissionDenied
from apps.identity.models import User
from apps.academic.models import AcademicYear, Semester, Department, Program, Batch, Scheme, Subject, SchemeSubject
from apps.students.models import Student, StudentEnrollment
from apps.faculty.models import Faculty, FacultyAssignment, AssignmentRole
from apps.assessments.models import AssessmentType, Assessment, AssessmentMark, AssessmentStatus
from apps.assessments.services.assessment_service import AssessmentService
from common.exceptions import InvariantViolationError


class PersistenceAndStudentViewTestCase(TestCase):
    def setUp(self):
        # 1. Teachers
        self.teacher1_user = User.objects.create_user(username='teacher1', password='TestPassword123!')
        self.teacher2_user = User.objects.create_user(username='teacher2', password='TestPassword123!')

        # 2. Student User
        self.student_user = User.objects.create_user(username='student1', password='TestPassword123!')

        # 3. Academic Structure
        self.ay = AcademicYear.objects.create(
            label='2024-25',
            start_date=date(2024, 7, 1),
            end_date=date(2025, 6, 30)
        )
        self.dept = Department.objects.create(name='Information Technology', code='IT')
        self.prog = Program.objects.create(name='B.Tech IT', code='BTIT', department=self.dept)
        self.sem = Semester.objects.create(academic_year=self.ay, number=5, label='Semester 5', start_date=date(2024, 7, 1), end_date=date(2024, 12, 31))
        self.batch = Batch.objects.create(name='IT-Batch-A', department=self.dept, academic_year=self.ay)
        self.scheme = Scheme.objects.create(name='2024 Scheme', code='SCH-IT-2024', program=self.prog, effective_from_year=self.ay)
        self.sub = Subject.objects.create(name='Web Technologies', code='IT501')
        self.scheme_sub = SchemeSubject.objects.create(
            scheme=self.scheme,
            subject=self.sub,
            semester_number=5,
            credits=3,
            max_marks=100,
            passing_marks=40
        )

        # Faculty Profiles
        self.fac1 = Faculty.objects.create(
            user=self.teacher1_user,
            faculty_id='FAC001',
            first_name='Sunil',
            last_name='Deshmukh',
            email='sunil@college.edu',
            department=self.dept,
            date_of_joining=date(2020, 1, 1)
        )
        self.fac2 = Faculty.objects.create(
            user=self.teacher2_user,
            faculty_id='FAC002',
            first_name='Anil',
            last_name='Verma',
            email='anil@college.edu',
            department=self.dept,
            date_of_joining=date(2021, 1, 1)
        )

        # Teacher 1 is assigned to teach Web Technologies
        self.assignment = FacultyAssignment.objects.create(
            faculty=self.fac1,
            academic_year=self.ay,
            semester=self.sem,
            scheme_subject=self.scheme_sub,
            batch=self.batch,
            role=AssignmentRole.PRIMARY_INSTRUCTOR
        )

        # Student Profile
        self.student = Student.objects.create(
            user=self.student_user,
            candidate_name='Priya Nair',
            enrollment_no='ENR2024701',
            application_id='APP2024701',
            date_of_birth=date(2004, 11, 5),
            gender='FEMALE'
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

        self.ut_type = AssessmentService.create_assessment_type(code='UNIT_TEST_1', name='Unit Test 1')
        self.assessment = AssessmentService.create_assessment(
            title='Web Tech Unit Test 1',
            assessment_type=self.ut_type,
            academic_year=self.ay,
            semester=self.sem,
            department=self.dept,
            scheme_subject=self.scheme_sub,
            batch=self.batch,
            faculty_assignment=self.assignment,
            max_marks=Decimal('25.00'),
            passing_marks=Decimal('10.00'),
            actor=self.teacher1_user
        )

    def test_assigned_faculty_can_upload_marks_unassigned_cannot(self):
        """Teacher 1 (assigned) can upload; Teacher 2 (unassigned) is denied."""
        rows = [{'enrollment_no': 'ENR2024701', 'marks_obtained': '21.0'}]

        # Teacher 2 attempt
        with self.assertRaises(PermissionDenied):
            AssessmentService.upload_unit_test_marks(
                assessment_id=str(self.assessment.id),
                mark_rows=rows,
                actor=self.teacher2_user
            )

        # Teacher 1 attempt succeeds
        res = AssessmentService.upload_unit_test_marks(
            assessment_id=str(self.assessment.id),
            mark_rows=rows,
            actor=self.teacher1_user
        )
        self.assertEqual(res['created_marks'], 1)

    def test_student_view_lifecycle_draft_hidden_published_visible(self):
        """Marks in DRAFT are hidden from student; visible once PUBLISHED."""
        rows = [{'enrollment_no': 'ENR2024701', 'marks_obtained': '23.5'}]
        AssessmentService.upload_unit_test_marks(
            assessment_id=str(self.assessment.id),
            mark_rows=rows,
            actor=self.teacher1_user
        )

        # While assessment is in DRAFT, student sees 0 marks
        self.assertEqual(len(AssessmentService.get_student_marks(self.student_user)), 0)

        # Publish assessment
        AssessmentService.publish_assessment(str(self.assessment.id), actor=self.teacher1_user)

        # Now student can see their published mark
        student_marks = AssessmentService.get_student_marks(self.student_user)
        self.assertEqual(len(student_marks), 1)
        self.assertEqual(student_marks[0].marks_obtained, Decimal('23.50'))
        self.assertEqual(student_marks[0].assessment.title, 'Web Tech Unit Test 1')

    def test_locked_assessment_rejects_modifications(self):
        """Locked assessment protects historical marks against edits."""
        rows = [{'enrollment_no': 'ENR2024701', 'marks_obtained': '20.0'}]
        AssessmentService.upload_unit_test_marks(
            assessment_id=str(self.assessment.id),
            mark_rows=rows,
            actor=self.teacher1_user
        )

        # Lock assessment
        AssessmentService.lock_assessment(str(self.assessment.id), actor=self.teacher1_user)
        self.assessment.refresh_from_db()
        self.assertTrue(self.assessment.is_locked)

        # Attempting further uploads must raise InvariantViolationError
        with self.assertRaises(InvariantViolationError) as ctx:
            AssessmentService.upload_unit_test_marks(
                assessment_id=str(self.assessment.id),
                mark_rows=[{'enrollment_no': 'ENR2024701', 'marks_obtained': '25.0'}],
                actor=self.teacher1_user
            )
        self.assertIn("Assessment is locked", str(ctx.exception))
