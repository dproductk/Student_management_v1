"""
Tests for Student Admissions and Authoritative Semester Enrollments (ADR-005).
"""

from datetime import date
from django.test import TestCase
from django.db.utils import IntegrityError
from common.exceptions import StateTransitionError
from apps.identity.models import User
from apps.academic.models import Department, Program, AcademicYear, Semester, Batch, Scheme
from apps.students.models import Student, StudentAdmission, StudentEnrollment
from apps.students.services.student_service import StudentService


class AdmissionEnrollmentTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admission_officer', password='AdminPass123!')
        
        # Setup Academic Foundation master data
        self.dept = Department.objects.create(name="Computer Engineering", code="CE")
        self.prog = Program.objects.create(department=self.dept, name="B.Tech CE", code="CE-BTECH", duration_years=4)
        self.ay = AcademicYear.objects.create(
            label="2026-2027",
            start_date=date(2026, 6, 1),
            end_date=date(2027, 5, 31),
            is_current=True
        )
        self.sem1 = Semester.objects.create(academic_year=self.ay, number=1, label="Fall 2026")
        self.sem2 = Semester.objects.create(academic_year=self.ay, number=2, label="Spring 2027")
        self.batch = Batch.objects.create(department=self.dept, academic_year=self.ay, name="CE-2026-A")
        self.scheme = Scheme.objects.create(program=self.prog, effective_from_year=self.ay, name="2026 Scheme", code="SCH-CE-26")

        self.student = StudentService.create_student(
            candidate_name="Vikram Verma",
            gender="MALE",
            date_of_birth=date(2005, 3, 10),
            enrollment_no="CE2026001"
        )

    def test_student_admission_record(self):
        adm = StudentAdmission.objects.create(
            student=self.student,
            program=self.prog,
            admission_date=date(2026, 7, 1),
            admission_type="CAP",
            seat_type="OPEN",
            cet_percentile=94.50,
            starting_semester=1
        )
        self.assertEqual(adm.program, self.prog)
        self.assertEqual(adm.starting_semester, 1)

    def test_authoritative_semester_enrollment(self):
        enrollment = StudentService.enroll_student(
            student_id=self.student.id,
            academic_year_id=self.ay.id,
            semester_id=self.sem1.id,
            department_id=self.dept.id,
            program_id=self.prog.id,
            batch_id=self.batch.id,
            scheme_id=self.scheme.id,
            created_by=self.admin
        )
        self.assertEqual(enrollment.status, "ACTIVE")
        self.assertEqual(enrollment.batch, self.batch)
        self.assertEqual(enrollment.scheme, self.scheme)

        # Unique enrollment constraint: same student cannot have duplicate enrollment for same semester & year
        with self.assertRaises(IntegrityError):
            StudentEnrollment.objects.create(
                student=self.student,
                academic_year=self.ay,
                semester=self.sem1,
                department=self.dept,
                program=self.prog,
                batch=self.batch,
                scheme=self.scheme
            )

    def test_enrollment_status_transitions(self):
        enrollment = StudentService.enroll_student(
            student_id=self.student.id,
            academic_year_id=self.ay.id,
            semester_id=self.sem1.id,
            department_id=self.dept.id,
            program_id=self.prog.id,
            batch_id=self.batch.id,
            scheme_id=self.scheme.id
        )
        # Transition to COMPLETED
        enrollment.status = "COMPLETED"
        enrollment.save()
        self.assertEqual(enrollment.status, "COMPLETED")

        # Invalid transition from COMPLETED back to ACTIVE must raise StateTransitionError
        enrollment.status = "ACTIVE"
        with self.assertRaises(StateTransitionError):
            enrollment.save()
