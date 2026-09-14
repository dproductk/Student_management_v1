from datetime import date, timedelta
from django.test import TestCase
from apps.faculty.models import Faculty, FacultyStatus, EmploymentType
from apps.faculty.services.faculty_service import FacultyService
from apps.academic.models import Department
from common.exceptions import InvariantViolationError


class FacultyLifecycleTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name='Computer Science & Engineering', code='CSE')

    def test_create_faculty_profile_and_types(self):
        # Permanent faculty
        f1 = FacultyService.create_faculty(
            faculty_id='FAC-001',
            first_name='Alan',
            last_name='Turing',
            email='alan.turing@institution.edu',
            department=self.dept,
            date_of_joining=date(2020, 1, 15),
            designation='Professor',
            employment_type=EmploymentType.PERMANENT
        )
        self.assertEqual(f1.status, FacultyStatus.ACTIVE)
        self.assertEqual(f1.full_name, 'Alan Turing')
        self.assertEqual(f1.employment_type, EmploymentType.PERMANENT)

        # Visiting faculty
        f2 = FacultyService.create_faculty(
            faculty_id='FAC-002',
            first_name='Grace',
            last_name='Hopper',
            email='grace.hopper@institution.edu',
            department=self.dept,
            date_of_joining=date(2021, 6, 1),
            designation='Visiting Professor',
            employment_type=EmploymentType.VISITING
        )
        self.assertEqual(f2.employment_type, EmploymentType.VISITING)

    def test_lifecycle_validation_invariants(self):
        # Relieving date before joining date must fail
        with self.assertRaises(InvariantViolationError):
            FacultyService.create_faculty(
                faculty_id='FAC-ERR-1',
                first_name='Test',
                last_name='Invalid',
                email='test.err1@institution.edu',
                department=self.dept,
                date_of_joining=date(2022, 1, 1),
                status=FacultyStatus.RESIGNED,
                # Invalid: date_of_relieving before joining
            )

        # Resigned status without relieving date must fail
        faculty = FacultyService.create_faculty(
            faculty_id='FAC-003',
            first_name='Claude',
            last_name='Shannon',
            email='shannon@institution.edu',
            department=self.dept,
            date_of_joining=date(2020, 1, 1)
        )
        with self.assertRaises(InvariantViolationError):
            faculty.status = FacultyStatus.RESIGNED
            faculty.date_of_relieving = None
            faculty.clean()

    def test_transition_status_and_historical_relieving(self):
        faculty = FacultyService.create_faculty(
            faculty_id='FAC-004',
            first_name='John',
            last_name='von Neumann',
            email='vonneumann@institution.edu',
            department=self.dept,
            date_of_joining=date(2018, 1, 1)
        )
        self.assertEqual(faculty.status, FacultyStatus.ACTIVE)

        # Transition to ON_LEAVE
        FacultyService.transition_status(faculty, FacultyStatus.ON_LEAVE)
        faculty.refresh_from_db()
        self.assertEqual(faculty.status, FacultyStatus.ON_LEAVE)

        # Transition to RETIRED with relieving date
        relieve_d = date(2024, 12, 31)
        FacultyService.transition_status(faculty, FacultyStatus.RETIRED, relieving_date=relieve_d)
        faculty.refresh_from_db()
        self.assertEqual(faculty.status, FacultyStatus.RETIRED)
        self.assertEqual(faculty.date_of_relieving, relieve_d)
