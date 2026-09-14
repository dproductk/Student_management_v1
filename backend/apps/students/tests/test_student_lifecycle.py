"""
Tests for Student Identity, Core Record, Address, Category, and Educational History.
"""

from datetime import date
from django.test import TestCase
from django.db.utils import IntegrityError
from common.exceptions import InvariantViolationError
from apps.identity.models import User
from apps.students.models import (
    Student,
    StudentAddress,
    StudentCategory,
    StudentEducationalHistory,
)
from apps.students.services.student_service import StudentService


class StudentLifecycleTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='stud_admin', password='AdminPass123!')

    def test_student_creation_and_unique_identifiers(self):
        student = StudentService.create_student(
            candidate_name="Aarav Sharma",
            gender="MALE",
            date_of_birth=date(2005, 4, 15),
            enrollment_no="ENR2026001",
            application_id="APP2026001",
            board_enrollment_no="BRD2026001",
            created_by=self.admin
        )
        self.assertEqual(student.candidate_name, "Aarav Sharma")
        self.assertEqual(student.status, "ACTIVE")

        # Duplicate enrollment_no must fail
        with self.assertRaises(IntegrityError):
            StudentService.create_student(
                candidate_name="Another Student",
                gender="MALE",
                date_of_birth=date(2005, 5, 20),
                enrollment_no="ENR2026001"
            )

        # Duplicate application_id must fail
        with self.assertRaises(IntegrityError):
            StudentService.create_student(
                candidate_name="Another Student 2",
                gender="FEMALE",
                date_of_birth=date(2005, 6, 25),
                application_id="APP2026001"
            )

    def test_student_invalid_status_and_gender(self):
        with self.assertRaises(InvariantViolationError):
            Student.objects.create(
                candidate_name="Invalid Gender",
                gender="UNKNOWN",
                date_of_birth=date(2005, 1, 1)
            )

        with self.assertRaises(InvariantViolationError):
            Student.objects.create(
                candidate_name="Invalid Status",
                gender="FEMALE",
                date_of_birth=date(2005, 1, 1),
                status="NON_EXISTENT_STATUS"
            )

    def test_student_address_and_category_relations(self):
        student = StudentService.create_student(
            candidate_name="Priya Patel",
            gender="FEMALE",
            date_of_birth=date(2005, 8, 12)
        )

        addr = StudentAddress.objects.create(
            student=student,
            address_line="123 River View Apartments",
            state="Maharashtra",
            district="Pune",
            pincode="411001"
        )
        self.assertEqual(student.address.district, "Pune")

        cat = StudentCategory.objects.create(
            student=student,
            category="OBC",
            caste="Kunbi"
        )
        self.assertEqual(student.category_info.category, "OBC")

    def test_student_educational_history_uniqueness(self):
        student = StudentService.create_student(
            candidate_name="Rohan Joshi",
            gender="MALE",
            date_of_birth=date(2004, 11, 2)
        )

        StudentEducationalHistory.objects.create(
            student=student,
            exam_type="SSC",
            passing_year=2020,
            board_name="State Board",
            total_percentage=88.50
        )

        # Duplicate exam_type for same student must fail
        with self.assertRaises(IntegrityError):
            StudentEducationalHistory.objects.create(
                student=student,
                exam_type="SSC",
                passing_year=2021,
                total_percentage=90.00
            )
