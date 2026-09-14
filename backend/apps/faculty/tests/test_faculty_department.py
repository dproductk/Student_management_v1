from datetime import date
from django.test import TestCase
from apps.faculty.models import Faculty
from apps.faculty.services.faculty_service import FacultyService
from apps.academic.models import Department


class FacultyDepartmentOrganizationalTests(TestCase):
    def setUp(self):
        self.dept_cse = Department.objects.create(name='Computer Science & Engineering', code='CSE')
        self.dept_ece = Department.objects.create(name='Electronics & Communication Engineering', code='ECE')

    def test_department_association_and_no_duplicate_master(self):
        # Faculty references authoritative Academic Foundation Department directly
        faculty = FacultyService.create_faculty(
            faculty_id='FAC-101',
            first_name='Barbara',
            last_name='Liskov',
            email='barbara.liskov@institution.edu',
            department=self.dept_cse,
            date_of_joining=date(2019, 7, 1),
            designation='Professor',
            is_hod=True,
            cabin_number='CS-302',
            contact_email='hod.cse@institution.edu',
            responsibilities='Head of Department, Curriculum Committee Chair'
        )

        self.assertEqual(faculty.department.id, self.dept_cse.id)
        self.assertTrue(faculty.is_hod)
        self.assertEqual(faculty.cabin_number, 'CS-302')
        self.assertEqual(faculty.contact_email, 'hod.cse@institution.edu')

        # Department reverse relation works without creating a duplicate department table
        cse_members = self.dept_cse.faculty_members.all()
        self.assertIn(faculty, cse_members)

    def test_update_organizational_info(self):
        faculty = FacultyService.create_faculty(
            faculty_id='FAC-102',
            first_name='Donald',
            last_name='Knuth',
            email='knuth@institution.edu',
            department=self.dept_cse,
            date_of_joining=date(2015, 1, 1),
            cabin_number='CS-101'
        )

        FacultyService.update_faculty(
            faculty,
            cabin_number='CS-405',
            responsibilities='Algorithms Research Group Lead'
        )
        faculty.refresh_from_db()
        self.assertEqual(faculty.cabin_number, 'CS-405')
        self.assertEqual(faculty.responsibilities, 'Algorithms Research Group Lead')
