"""
Tests for Sensitive Financial & Identity Data Boundary (ADR-015).
Covers encryption, masking, authorization enforcement, and access logging for Bank Accounts & Aadhaar.
"""

from datetime import date
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.identity.models import User, Role, Permission, UserRole, RolePermission
from apps.identity.domain.rbac import RoleScopeType
from apps.audit.models import SensitiveDataAccessLog
from apps.students.models import Student, StudentBankAccount
from apps.students.services.student_service import StudentService


class SensitiveDataBoundaryTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # User with reveal_sensitive permission
        self.compliance_officer = User.objects.create_user(username='compliance_off', password='CompPass123!')
        self.reveal_perm = Permission.objects.create(
            codename='students.reveal_sensitive',
            description='Reveal masked sensitive data',
            module='students'
        )
        self.view_perm = Permission.objects.create(
            codename='students.view_directory',
            description='View students directory',
            module='students'
        )
        self.officer_role = Role.objects.create(name='COMPLIANCE_OFFICER', scope_type=RoleScopeType.SYSTEM.value)
        RolePermission.objects.create(role=self.officer_role, permission=self.reveal_perm)
        RolePermission.objects.create(role=self.officer_role, permission=self.view_perm)
        UserRole.objects.create(user=self.compliance_officer, role=self.officer_role, assigned_by=self.compliance_officer)

        # Standard staff user without reveal permission
        self.regular_staff = User.objects.create_user(username='staff_user', password='StaffPass123!')
        self.staff_role = Role.objects.create(name='REGULAR_STAFF', scope_type=RoleScopeType.SYSTEM.value)
        RolePermission.objects.create(role=self.staff_role, permission=self.view_perm)
        UserRole.objects.create(user=self.regular_staff, role=self.staff_role, assigned_by=self.compliance_officer)

        # Create student with encrypted Aadhaar
        self.student = StudentService.create_student(
            candidate_name="Ananya Roy",
            gender="FEMALE",
            date_of_birth=date(2005, 9, 14),
            aadhaar_number="987654321098"
        )
        # Create bank account with encrypted account number
        self.bank_acc = StudentService.set_bank_account(
            student_id=self.student.id,
            account_number="1234567890123456",
            bank_name="State Bank of India",
            branch_name="Kothrud Branch",
            ifsc_code="SBIN0001234"
        )

    def test_sensitive_data_stored_encrypted_and_masked(self):
        self.student.refresh_from_db()
        self.bank_acc.refresh_from_db()

        # Plain text is NOT stored in the database
        self.assertNotEqual(bytes(self.student.aadhaar_encrypted), b"987654321098")
        self.assertNotEqual(bytes(self.bank_acc.account_number_encrypted), b"1234567890123456")

        # Masked values are correctly populated
        self.assertEqual(self.student.aadhaar_masked, "XXXX XXXX 1098")
        self.assertEqual(self.bank_acc.account_number_masked, "XXXXXXXXXXXX3456")

    def test_default_api_returns_only_masked_data(self):
        self.client.force_authenticate(user=self.regular_staff)
        res = self.client.get(f'/api/v1/students/{self.student.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = res.data
        self.assertEqual(data['aadhaar_masked'], "XXXX XXXX 1098")
        self.assertEqual(data['bank_account']['account_number_masked'], "XXXXXXXXXXXX3456")
        
        # Ensure raw encrypted bytes are never leaked in payload
        self.assertNotIn('aadhaar_encrypted', data)
        self.assertNotIn('account_number_encrypted', data['bank_account'])

    def test_unauthorized_user_forbidden_from_reveal(self):
        self.client.force_authenticate(user=self.regular_staff)
        res = self.client.post(f'/api/v1/students/{self.student.id}/reveal-sensitive/', {
            'field_name': 'bank_account',
            'reason': 'Audit review of student banking documents'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(SensitiveDataAccessLog.objects.count(), 0)

    def test_authorized_user_reveals_cleartext_with_audit_log(self):
        self.client.force_authenticate(user=self.compliance_officer)
        
        # Reveal Bank Account
        res_bank = self.client.post(f'/api/v1/students/{self.student.id}/reveal-sensitive/', {
            'field_name': 'bank_account',
            'reason': 'Scholarship fee reimbursement verification'
        })
        self.assertEqual(res_bank.status_code, status.HTTP_200_OK)
        self.assertEqual(res_bank.data['value'], "1234567890123456")

        # Reveal Aadhaar
        res_aadhaar = self.client.post(f'/api/v1/students/{self.student.id}/reveal-sensitive/', {
            'field_name': 'aadhaar',
            'reason': 'Government portal identity reconciliation'
        })
        self.assertEqual(res_aadhaar.status_code, status.HTTP_200_OK)
        self.assertEqual(res_aadhaar.data['value'], "987654321098")

        # Verify access audit log entries
        self.assertEqual(SensitiveDataAccessLog.objects.count(), 2)
        logs = list(SensitiveDataAccessLog.objects.order_by('accessed_at'))
        self.assertEqual(logs[0].accessor, self.compliance_officer)
        self.assertEqual(logs[0].field_name, 'bank_account')
        self.assertEqual(logs[0].reason, 'Scholarship fee reimbursement verification')
        self.assertEqual(logs[1].field_name, 'aadhaar')
