from datetime import date
from django.test import TestCase
from apps.faculty.models import Faculty, FacultyAcademicItem, AcademicItemType
from apps.faculty.services.faculty_service import FacultyService
from apps.academic.models import Department
from common.exceptions import InvariantViolationError


class FacultyAcademicItemsTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name='Computer Science & Engineering', code='CSE')
        self.faculty = FacultyService.create_faculty(
            faculty_id='FAC-301',
            first_name='Tim',
            last_name='Berners-Lee',
            email='timbl@institution.edu',
            department=self.dept,
            date_of_joining=date(2015, 1, 1)
        )

    def test_all_seven_academic_categories(self):
        # 1. Publication
        pub = FacultyService.add_academic_item(
            faculty=self.faculty,
            item_type=AcademicItemType.PUBLICATION,
            title='Information Management: A Proposal',
            year=1989,
            details={'journal': 'CERN Technical Report', 'doi': '10.1000/182'},
            reference_url='https://www.w3.org/History/1989/proposal.html'
        )
        self.assertEqual(pub.item_type, AcademicItemType.PUBLICATION)

        # 2. Patent
        pat = FacultyService.add_academic_item(
            faculty=self.faculty,
            item_type=AcademicItemType.PATENT,
            title='Method for Hypertext Distribution',
            year=1995,
            details={'patent_number': 'US-9876543-A', 'status': 'GRANTED'}
        )
        self.assertEqual(pat.item_type, AcademicItemType.PATENT)

        # 3. Book
        book = FacultyService.add_academic_item(
            faculty=self.faculty,
            item_type=AcademicItemType.BOOK,
            title='Weaving the Web',
            year=1999,
            details={'publisher': 'HarperCollins', 'isbn': '978-0062515865'}
        )
        self.assertEqual(book.item_type, AcademicItemType.BOOK)

        # 4. Award
        award = FacultyService.add_academic_item(
            faculty=self.faculty,
            item_type=AcademicItemType.AWARD,
            title='ACM A.M. Turing Award',
            year=2016,
            details={'awarding_body': 'Association for Computing Machinery'}
        )
        self.assertEqual(award.item_type, AcademicItemType.AWARD)

        # 5. Membership
        mem = FacultyService.add_academic_item(
            faculty=self.faculty,
            item_type=AcademicItemType.MEMBERSHIP,
            title='Fellow of the Royal Society',
            year=2001,
            details={'organization': 'Royal Society', 'membership_id': 'FRS-2001'}
        )
        self.assertEqual(mem.item_type, AcademicItemType.MEMBERSHIP)

        # 6. Consultancy
        con = FacultyService.add_academic_item(
            faculty=self.faculty,
            item_type=AcademicItemType.CONSULTANCY,
            title='Open Data Standardization Strategy',
            year=2021,
            details={'client': 'World Wide Web Consortium', 'grant_amount': 50000}
        )
        self.assertEqual(con.item_type, AcademicItemType.CONSULTANCY)

        # 7. Guidance
        guidance = FacultyService.add_academic_item(
            faculty=self.faculty,
            item_type=AcademicItemType.GUIDANCE,
            title='Doctoral Dissertation: Decentralized Semantic Graphs',
            year=2023,
            details={'student_name': 'Jane Doe', 'degree': 'Ph.D.', 'status': 'COMPLETED'}
        )
        self.assertEqual(guidance.item_type, AcademicItemType.GUIDANCE)

        # Total items = 7
        self.assertEqual(self.faculty.academic_items.count(), 7)

    def test_academic_item_validation(self):
        # Empty title rejected
        with self.assertRaises(InvariantViolationError):
            FacultyService.add_academic_item(
                faculty=self.faculty,
                item_type=AcademicItemType.PUBLICATION,
                title='   ',
                year=2024
            )

        # Invalid year rejected
        with self.assertRaises(InvariantViolationError):
            FacultyService.add_academic_item(
                faculty=self.faculty,
                item_type=AcademicItemType.AWARD,
                title='Valid Title',
                year=1850  # before 1950
            )
