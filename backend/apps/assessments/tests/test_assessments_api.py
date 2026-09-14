"""
Integration tests for Assessments DRF API endpoints.
"""

from decimal import Decimal
from datetime import date
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.identity.models import User
from apps.academic.models import AcademicYear, Semester, Department, Program, Batch, Scheme, Subject, SchemeSubject
from apps.students.models import Student, StudentEnrollment
from apps.assessments.models import AssessmentType, Assessment, AssessmentMark, AssessmentStatus
from apps.assessments.services.assessment_service import AssessmentService


class AssessmentsAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.faculty_user = User.objects.create_user(
            username='api_teacher',
            password='TestPassword123!',
            is_superuser=True
        )
        self.client.force_authenticate(user=self.faculty_user)

        self.ay = AcademicYear.objects.create(
            label='2024-25',
            start_date=date(2024, 7, 1),
            end_date=date(2025, 6, 30)
        )
        self.dept = Department.objects.create(name='Computer Engineering', code='CE')
        self.prog = Program.objects.create(name='B.Tech Computer Engineering', code='BTCE', department=self.dept)
        self.sem = Semester.objects.create(academic_year=self.ay, number=3, label='Semester 3', start_date=date(2024, 7, 1), end_date=date(2024, 12, 31))
        self.batch = Batch.objects.create(name='Batch-CE-1', department=self.dept, academic_year=self.ay)
        self.scheme = Scheme.objects.create(name='2024 Scheme', code='SCH-CE-24', program=self.prog, effective_from_year=self.ay)
        self.subject = Subject.objects.create(name='Operating Systems', code='CS302')
        self.scheme_sub = SchemeSubject.objects.create(
            scheme=self.scheme,
            subject=self.subject,
            semester_number=3,
            credits=4,
            max_marks=100,
            passing_marks=40
        )

        self.student = Student.objects.create(
            candidate_name='Divya Rao',
            enrollment_no='ENR2024801',
            application_id='APP2024801',
            date_of_birth=date(2005, 3, 10),
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

        self.type = AssessmentService.create_assessment_type(code='UNIT_TEST_1', name='Unit Test 1')
        self.assessment = AssessmentService.create_assessment(
            title='OS Unit Test 1',
            assessment_type=self.type,
            academic_year=self.ay,
            semester=self.sem,
            department=self.dept,
            scheme_subject=self.scheme_sub,
            max_marks=Decimal('25.00'),
            passing_marks=Decimal('10.00'),
            actor=self.faculty_user
        )

    def test_upload_marks_api_and_validation(self):
        """POST /api/v1/assessments/definitions/{id}/upload-marks/"""
        payload = {
            'marks': [
                {
                    'enrollment_no': 'ENR2024801',
                    'marks_obtained': '21.50',
                    'is_absent': False,
                    'remarks': 'Good understanding of processes'
                }
            ]
        }

        res = self.client.post(f'/api/v1/assessments/definitions/{self.assessment.id}/upload-marks/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_processed'], 1)
        self.assertEqual(res.data['created_marks'], 1)

        # Retrieve marks via action
        marks_res = self.client.get(f'/api/v1/assessments/definitions/{self.assessment.id}/marks/')
        self.assertEqual(marks_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(marks_res.data), 1)
        self.assertEqual(marks_res.data[0]['student_name'], 'Divya Rao')
        self.assertEqual(Decimal(marks_res.data[0]['marks_obtained']), Decimal('21.50'))

    def test_publish_and_lock_actions_api(self):
        # 1. Publish
        pub_res = self.client.post(f'/api/v1/assessments/definitions/{self.assessment.id}/publish/')
        self.assertEqual(pub_res.status_code, status.HTTP_200_OK)
        self.assertEqual(pub_res.data['status'], AssessmentStatus.PUBLISHED)

        # 2. Lock
        lock_res = self.client.post(f'/api/v1/assessments/definitions/{self.assessment.id}/lock/')
        self.assertEqual(lock_res.status_code, status.HTTP_200_OK)
        self.assertEqual(lock_res.data['status'], AssessmentStatus.LOCKED)
