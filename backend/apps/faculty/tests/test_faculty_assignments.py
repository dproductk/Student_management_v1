from datetime import date
from django.test import TestCase
from apps.faculty.models import Faculty, FacultyAssignment, AssignmentRole, FacultyStatus
from apps.faculty.services.faculty_service import FacultyService
from apps.academic.models import Department, Program, AcademicYear, Semester, Batch, Scheme, Subject, SchemeSubject
from common.exceptions import InvariantViolationError


class FacultyAssignmentTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name='Computer Science & Engineering', code='CSE')
        self.prog = Program.objects.create(department=self.dept, name='B.Tech CSE', code='BTECH-CSE')

        self.ay2025 = AcademicYear.objects.create(
            label='2025-2026',
            start_date=date(2025, 7, 1),
            end_date=date(2026, 6, 30),
            is_current=False
        )
        self.ay2026 = AcademicYear.objects.create(
            label='2026-2027',
            start_date=date(2026, 7, 1),
            end_date=date(2027, 6, 30),
            is_current=True
        )

        self.sem1 = Semester.objects.create(academic_year=self.ay2025, number=1, label='Fall 2025')
        self.sem3 = Semester.objects.create(academic_year=self.ay2026, number=3, label='Fall 2026')

        self.batch_a = Batch.objects.create(department=self.dept, name='Batch-A', academic_year=self.ay2026)
        self.batch_b = Batch.objects.create(department=self.dept, name='Batch-B', academic_year=self.ay2026)

        self.scheme = Scheme.objects.create(
            program=self.prog,
            name='Scheme 2025',
            code='SCH-2025',
            effective_from_year=self.ay2025
        )

        self.sub_dsa = Subject.objects.create(name='Data Structures & Algorithms', code='CS201')
        self.sub_dbms = Subject.objects.create(name='Database Management Systems', code='CS301')

        self.ss_dsa = SchemeSubject.objects.create(
            scheme=self.scheme,
            subject=self.sub_dsa,
            semester_number=1,
            subject_type=SchemeSubject.SubjectType.THEORY,
            credits=4
        )
        self.ss_dbms = SchemeSubject.objects.create(
            scheme=self.scheme,
            subject=self.sub_dbms,
            semester_number=3,
            subject_type=SchemeSubject.SubjectType.THEORY,
            credits=4
        )

        self.faculty = FacultyService.create_faculty(
            faculty_id='FAC-201',
            first_name='Edsger',
            last_name='Dijkstra',
            email='dijkstra@institution.edu',
            department=self.dept,
            date_of_joining=date(2020, 1, 1)
        )

    def test_subject_assignment_vertical_slice(self):
        # 1. Authoritative teaching assignment linking Faculty -> SchemeSubject + Year + Semester + Batch
        assignment = FacultyService.assign_subject(
            faculty=self.faculty,
            academic_year=self.ay2026,
            semester=self.sem3,
            scheme_subject=self.ss_dbms,
            batch=self.batch_a,
            role=AssignmentRole.PRIMARY_INSTRUCTOR,
            remarks='Course coordinator and primary lecture instructor'
        )

        self.assertEqual(assignment.faculty.id, self.faculty.id)
        self.assertEqual(assignment.scheme_subject.id, self.ss_dbms.id)
        self.assertEqual(assignment.academic_year.id, self.ay2026.id)
        self.assertEqual(assignment.semester.id, self.sem3.id)
        self.assertEqual(assignment.batch.id, self.batch_a.id)
        self.assertTrue(assignment.is_active)
        self.assertEqual(assignment.role, AssignmentRole.PRIMARY_INSTRUCTOR)

        # Ensure subjects taught are not stored as comma-separated values (PRD requirement 17)
        self.assertIsInstance(assignment.scheme_subject, SchemeSubject)

    def test_historical_assignment_preservation(self):
        # Term 1 assignment (historical)
        a1 = FacultyService.assign_subject(
            faculty=self.faculty,
            academic_year=self.ay2025,
            semester=self.sem1,
            scheme_subject=self.ss_dsa,
            role=AssignmentRole.PRIMARY_INSTRUCTOR
        )

        # Retire term 1 assignment historically
        FacultyService.retire_assignment(a1, end_date=date(2025, 12, 20))
        a1.refresh_from_db()
        self.assertFalse(a1.is_active)
        self.assertEqual(a1.effective_end_date, date(2025, 12, 20))

        # Term 2 assignment (active)
        a2 = FacultyService.assign_subject(
            faculty=self.faculty,
            academic_year=self.ay2026,
            semester=self.sem3,
            scheme_subject=self.ss_dbms,
            batch=self.batch_a,
            role=AssignmentRole.PRIMARY_INSTRUCTOR
        )

        # Historical records remain explainable and queryable
        all_assignments = self.faculty.assignments.all()
        self.assertEqual(all_assignments.count(), 2)
        active_assignments = self.faculty.assignments.filter(is_active=True)
        self.assertEqual(active_assignments.count(), 1)
        self.assertEqual(active_assignments.first().id, a2.id)

    def test_assignment_validation_invariants(self):
        # Mismatch between academic year and semester
        with self.assertRaises(InvariantViolationError):
            FacultyService.assign_subject(
                faculty=self.faculty,
                academic_year=self.ay2026,
                semester=self.sem1,  # sem1 belongs to ay2025!
                scheme_subject=self.ss_dbms
            )

        # Inactive faculty cannot accept new assignments
        FacultyService.transition_status(self.faculty, FacultyStatus.ON_LEAVE)
        with self.assertRaises(InvariantViolationError):
            FacultyService.assign_subject(
                faculty=self.faculty,
                academic_year=self.ay2026,
                semester=self.sem3,
                scheme_subject=self.ss_dbms
            )
