from datetime import date
from django.test import TestCase
from apps.faculty.models import Faculty, AssignmentRole
from apps.faculty.services.faculty_service import FacultyService
from apps.faculty.services.faculty_scope_service import FacultyScopeService
from apps.academic.models import Department, Program, AcademicYear, Semester, Batch, Scheme, Subject, SchemeSubject
from apps.students.models import Student, StudentEnrollment
from apps.identity.models import User, UserRole, Role, Permission
from apps.identity.domain.rbac import RoleScopeType


class ScopedStudentVisibilityTests(TestCase):
    def setUp(self):
        # Master academic structure
        self.dept_cse = Department.objects.create(name='Computer Science & Engineering', code='CSE')
        self.dept_mech = Department.objects.create(name='Mechanical Engineering', code='MECH')

        self.prog_cse = Program.objects.create(department=self.dept_cse, name='B.Tech CSE', code='BTECH-CSE')
        self.prog_mech = Program.objects.create(department=self.dept_mech, name='B.Tech MECH', code='BTECH-MECH')

        self.ay = AcademicYear.objects.create(
            label='2026-2027',
            start_date=date(2026, 7, 1),
            end_date=date(2027, 6, 30),
            is_current=True
        )
        self.sem = Semester.objects.create(academic_year=self.ay, number=3, label='Sem 3')

        self.batch_cse_a = Batch.objects.create(department=self.dept_cse, name='CSE-A', academic_year=self.ay)
        self.batch_cse_b = Batch.objects.create(department=self.dept_cse, name='CSE-B', academic_year=self.ay)
        self.batch_mech = Batch.objects.create(department=self.dept_mech, name='MECH-A', academic_year=self.ay)

        self.scheme_cse = Scheme.objects.create(program=self.prog_cse, name='CSE 2026', code='SCH-CSE', effective_from_year=self.ay)
        self.scheme_mech = Scheme.objects.create(program=self.prog_mech, name='MECH 2026', code='SCH-MECH', effective_from_year=self.ay)

        self.sub_os = Subject.objects.create(name='Operating Systems', code='CS302')
        self.ss_os = SchemeSubject.objects.create(
            scheme=self.scheme_cse,
            subject=self.sub_os,
            semester_number=3
        )

        # Create Students
        self.student_cse_a = Student.objects.create(
            candidate_name='Alice Smith',
            enrollment_no='CSE2026001',
            date_of_birth=date(2005, 5, 12),
            gender='FEMALE',
            email='alice@institution.edu'
        )
        StudentEnrollment.objects.create(
            student=self.student_cse_a,
            academic_year=self.ay,
            semester=self.sem,
            department=self.dept_cse,
            program=self.prog_cse,
            batch=self.batch_cse_a,
            scheme=self.scheme_cse
        )

        self.student_cse_b = Student.objects.create(
            candidate_name='Bob Jones',
            enrollment_no='CSE2026002',
            date_of_birth=date(2005, 8, 20),
            gender='MALE',
            email='bob@institution.edu'
        )
        StudentEnrollment.objects.create(
            student=self.student_cse_b,
            academic_year=self.ay,
            semester=self.sem,
            department=self.dept_cse,
            program=self.prog_cse,
            batch=self.batch_cse_b,
            scheme=self.scheme_cse
        )

        self.student_mech = Student.objects.create(
            candidate_name='Charlie Brown',
            enrollment_no='MECH2026001',
            date_of_birth=date(2005, 3, 15),
            gender='MALE',
            email='charlie@institution.edu'
        )
        StudentEnrollment.objects.create(
            student=self.student_mech,
            academic_year=self.ay,
            semester=self.sem,
            department=self.dept_mech,
            program=self.prog_mech,
            batch=self.batch_mech,
            scheme=self.scheme_mech
        )

        # Users and Faculty profiles
        self.user_super = User.objects.create_superuser('admin@inst.edu', 'AdminPass123!')

        self.user_hod = User.objects.create_user('hod.cse@inst.edu', 'HodPass123!')
        self.faculty_hod = FacultyService.create_faculty(
            faculty_id='FAC-HOD-CSE',
            first_name='HOD',
            last_name='CSE',
            email='hod.cse@inst.edu',
            department=self.dept_cse,
            date_of_joining=date(2018, 1, 1),
            user=self.user_hod,
            is_hod=True
        )

        self.user_teacher_a = User.objects.create_user('teacher.a@inst.edu', 'TeacherPass123!')
        self.faculty_teacher_a = FacultyService.create_faculty(
            faculty_id='FAC-TEA-A',
            first_name='Teacher',
            last_name='Alpha',
            email='teacher.a@inst.edu',
            department=self.dept_cse,
            date_of_joining=date(2020, 1, 1),
            user=self.user_teacher_a
        )
        # Assigned to CSE-A batch as Class Teacher
        FacultyService.assign_subject(
            faculty=self.faculty_teacher_a,
            academic_year=self.ay,
            semester=self.sem,
            scheme_subject=self.ss_os,
            batch=self.batch_cse_a,
            role=AssignmentRole.CLASS_TEACHER
        )

        self.user_unassigned = User.objects.create_user('unassigned@inst.edu', 'Unassigned123!')

    def test_superuser_has_global_visibility(self):
        visible = FacultyScopeService.get_scoped_students_queryset(self.user_super)
        self.assertEqual(visible.count(), 3)
        self.assertTrue(FacultyScopeService.can_user_view_student(self.user_super, self.student_cse_a))
        self.assertTrue(FacultyScopeService.can_user_view_student(self.user_super, self.student_cse_b))
        self.assertTrue(FacultyScopeService.can_user_view_student(self.user_super, self.student_mech))

    def test_hod_scoped_department_visibility(self):
        # HOD CSE can see students in CSE (both Batch A and Batch B), but NOT Mech
        visible = FacultyScopeService.get_scoped_students_queryset(self.user_hod)
        self.assertEqual(visible.count(), 2)
        self.assertIn(self.student_cse_a, visible)
        self.assertIn(self.student_cse_b, visible)
        self.assertNotIn(self.student_mech, visible)

        self.assertTrue(FacultyScopeService.can_user_view_student(self.user_hod, self.student_cse_a))
        self.assertFalse(FacultyScopeService.can_user_view_student(self.user_hod, self.student_mech))

    def test_class_teacher_scoped_batch_visibility(self):
        # Teacher A is assigned only to Batch CSE-A
        visible = FacultyScopeService.get_scoped_students_queryset(self.user_teacher_a)
        self.assertEqual(visible.count(), 1)
        self.assertIn(self.student_cse_a, visible)
        self.assertNotIn(self.student_cse_b, visible)
        self.assertNotIn(self.student_mech, visible)

        self.assertTrue(FacultyScopeService.can_user_view_student(self.user_teacher_a, self.student_cse_a))
        self.assertFalse(FacultyScopeService.can_user_view_student(self.user_teacher_a, self.student_cse_b))

    def test_unauthorized_user_visibility_denied(self):
        visible = FacultyScopeService.get_scoped_students_queryset(self.user_unassigned)
        self.assertEqual(visible.count(), 0)
        self.assertFalse(FacultyScopeService.can_user_view_student(self.user_unassigned, self.student_cse_a))
