"""
Tests for Additive Corrections and Government-Source Preservation (ADR-007, ADR-011).
"""

from datetime import date
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from common.exceptions import InvariantViolationError
from apps.identity.models import User, Role, Permission, UserRole, RolePermission
from apps.identity.domain.rbac import RoleScopeType
from apps.students.models import Student, StudentDataCorrection
from apps.students.services.student_service import StudentService
from apps.students.services.correction_service import CorrectionService


class AdditiveCorrectionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.approver = User.objects.create_user(username='dean_approver', password='DeanPass123!')
        
        self.manage_perm = Permission.objects.create(
            codename='students.manage_profile',
            description='Manage and correct student profiles',
            module='students'
        )
        self.view_perm = Permission.objects.create(
            codename='students.view_directory',
            description='View student directory',
            module='students'
        )
        self.approver_role = Role.objects.create(name='STUDENT_APPROVER', scope_type=RoleScopeType.SYSTEM.value)
        RolePermission.objects.create(role=self.approver_role, permission=self.manage_perm)
        RolePermission.objects.create(role=self.approver_role, permission=self.view_perm)
        UserRole.objects.create(user=self.approver, role=self.approver_role, assigned_by=self.approver)

        self.student = StudentService.create_student(
            candidate_name="Kunal Singhania",
            gender="MALE",
            date_of_birth=date(2004, 5, 20),
            student_mobile="9823001122"
        )

    def test_additive_correction_preserves_original_value(self):
        # Apply correction via service
        correction = CorrectionService.apply_student_correction(
            student_id=self.student.id,
            field_name="student_mobile",
            new_value="9988776655",
            reason="Student updated primary mobile number per affidavit",
            approver_user=self.approver
        )

        self.assertEqual(correction.original_value, "9823001122")
        self.assertEqual(correction.corrected_value, "9988776655")
        self.assertEqual(correction.approved_by, self.approver)

        # Authoritative field on student updated
        self.student.refresh_from_db()
        self.assertEqual(self.student.student_mobile, "9988776655")

        # History preserved in corrections relation
        self.assertEqual(self.student.corrections.count(), 1)
        self.assertEqual(self.student.corrections.first().original_value, "9823001122")

    def test_correction_api_endpoint(self):
        self.client.force_authenticate(user=self.approver)
        res = self.client.post(f'/api/v1/students/{self.student.id}/corrections/', {
            'field_name': 'candidate_name',
            'new_value': 'Kunal S. Singhania',
            'reason': 'Legal name change per Gazette Notification'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['original_value'], 'Kunal Singhania')
        self.assertEqual(res.data['corrected_value'], 'Kunal S. Singhania')

        self.student.refresh_from_db()
        self.assertEqual(self.student.candidate_name, 'Kunal S. Singhania')

    def test_unauthorized_user_cannot_apply_correction(self):
        regular_user = User.objects.create_user(username='random_user', password='Pass123!User')
        self.client.force_authenticate(user=regular_user)

        res = self.client.post(f'/api/v1/students/{self.student.id}/corrections/', {
            'field_name': 'candidate_name',
            'new_value': 'Hacked Name',
            'reason': 'No reason'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
