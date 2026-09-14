from datetime import date
from django.test import TestCase
from apps.register.services.register_query_service import RegisterQueryService
from apps.students.models import Student, StudentCategory
from apps.verification.models import VerificationRequest
from apps.identity.models import User


class AdministrativeViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('admin@inst.edu', 'AdminPass123!')

        # Student 1: MALE, OPEN, Verification APPROVED
        self.s1 = Student.objects.create(candidate_name='User A', enrollment_no='U1', gender='MALE', date_of_birth=date(2005, 1, 1))
        StudentCategory.objects.create(student=self.s1, category='OPEN')
        VerificationRequest.objects.create(
            student=self.s1, entity_type='DOCUMENT', status='APPROVED', submitted_by=self.user
        )

        # Student 2: FEMALE, OBC, Verification PENDING
        self.s2 = Student.objects.create(candidate_name='User B', enrollment_no='U2', gender='FEMALE', date_of_birth=date(2005, 2, 1))
        StudentCategory.objects.create(student=self.s2, category='OBC')
        VerificationRequest.objects.create(
            student=self.s2, entity_type='DOCUMENT', status='PENDING', submitted_by=self.user
        )

        # Student 3: FEMALE, SC, Verification NEEDS_CORRECTION
        self.s3 = Student.objects.create(candidate_name='User C', enrollment_no='U3', gender='FEMALE', date_of_birth=date(2005, 3, 1))
        StudentCategory.objects.create(student=self.s3, category='SC')
        VerificationRequest.objects.create(
            student=self.s3, entity_type='GOVERNMENT_CORRECTION', status='NEEDS_CORRECTION', submitted_by=self.user
        )

        # Student 4: MALE, OPEN, No verification request (UNSUBMITTED)
        self.s4 = Student.objects.create(candidate_name='User D', enrollment_no='U4', gender='MALE', date_of_birth=date(2005, 4, 1))
        StudentCategory.objects.create(student=self.s4, category='OPEN')

    def test_category_filtering(self):
        res_open = RegisterQueryService.query_student_register(self.user, filters={'category': 'OPEN'})
        self.assertEqual(res_open['total_count'], 2)

        res_obc = RegisterQueryService.query_student_register(self.user, filters={'category': 'OBC'})
        self.assertEqual(res_obc['total_count'], 1)
        self.assertEqual(res_obc['results'][0]['candidate_name'], 'User B')

    def test_gender_filtering(self):
        res_female = RegisterQueryService.query_student_register(self.user, filters={'gender': 'FEMALE'})
        self.assertEqual(res_female['total_count'], 2)

        res_male = RegisterQueryService.query_student_register(self.user, filters={'gender': 'MALE'})
        self.assertEqual(res_male['total_count'], 2)

    def test_verification_status_filtering(self):
        # APPROVED
        res_app = RegisterQueryService.query_student_register(self.user, filters={'verification_status': 'APPROVED'})
        self.assertEqual(res_app['total_count'], 1)
        self.assertEqual(res_app['results'][0]['candidate_name'], 'User A')

        # PENDING
        res_pen = RegisterQueryService.query_student_register(self.user, filters={'verification_status': 'PENDING'})
        self.assertEqual(res_pen['total_count'], 1)
        self.assertEqual(res_pen['results'][0]['candidate_name'], 'User B')

        # NEEDS_CORRECTION
        res_corr = RegisterQueryService.query_student_register(self.user, filters={'verification_status': 'NEEDS_CORRECTION'})
        self.assertEqual(res_corr['total_count'], 1)
        self.assertEqual(res_corr['results'][0]['candidate_name'], 'User C')

        # UNSUBMITTED
        res_unsub = RegisterQueryService.query_student_register(self.user, filters={'verification_status': 'UNSUBMITTED'})
        self.assertEqual(res_unsub['total_count'], 1)
        self.assertEqual(res_unsub['results'][0]['candidate_name'], 'User D')
