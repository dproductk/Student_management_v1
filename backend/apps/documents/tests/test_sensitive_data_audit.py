"""
Cross-Cutting Sensitive-Data Exposure and Masking Audit Test Suite.
Governed by TASKS.md 15.1.2, production-hardening-prd.md R-002, R-005, and ADR-015.
"""

from datetime import date
from rest_framework.test import APITestCase
from rest_framework import status
from apps.identity.models import User, Role, Permission, RolePermission, UserRole
from apps.identity.domain.rbac import RoleScopeType
from apps.students.models import Student, StudentBankAccount
from apps.students.services.student_service import StudentService
from apps.audit.models import SensitiveDataAccessLog
from common.security import mask_aadhaar, mask_bank_account


class SensitiveDataExposureAndMaskingAuditTests(APITestCase):
    """
    Audits sensitive student data boundaries to ensure cleartext PII (Aadhaar, Bank Account)
    is masked by default and only exposed through controlled, auditable reveal operations.
    """

    def setUp(self):
        # Create student with encrypted Aadhaar
        self.student = StudentService.create_student(
            candidate_name="Sarthak Sensitive",
            gender="MALE",
            date_of_birth=date(2005, 1, 1),
            aadhaar_number="987654321098"
        )
        # Create bank account with encrypted account number
        self.bank_acc = StudentService.set_bank_account(
            student_id=self.student.id,
            account_number="123456789012",
            bank_name="State Bank of India",
            branch_name="Shivaji Nagar",
            ifsc_code="SBIN0001234"
        )

        # Standard staff user without reveal permission
        self.staff_user = User.objects.create_user(
            username="staff_no_reveal",
            email="staff_no_reveal@example.com",
            password="TestPassword123!",
            is_active=True
        )
        self.view_perm, _ = Permission.objects.get_or_create(
            codename='students.view_directory',
            defaults={'description': 'View students directory', 'module': 'students'}
        )
        self.staff_role = Role.objects.create(name="StandardStaff", scope_type=RoleScopeType.SYSTEM.value)
        RolePermission.objects.create(role=self.staff_role, permission=self.view_perm)
        UserRole.objects.create(user=self.staff_user, role=self.staff_role, assigned_by=self.staff_user)

        # Compliance officer with reveal permission
        self.reveal_perm, _ = Permission.objects.get_or_create(
            codename='students.reveal_sensitive',
            defaults={'description': 'Reveal masked sensitive data', 'module': 'students'}
        )
        self.compliance_user = User.objects.create_user(
            username="compliance_officer",
            email="compliance@example.com",
            password="TestPassword123!",
            is_active=True
        )
        self.compliance_role = Role.objects.create(name="ComplianceOfficer", scope_type=RoleScopeType.SYSTEM.value)
        RolePermission.objects.create(role=self.compliance_role, permission=self.view_perm)
        RolePermission.objects.create(role=self.compliance_role, permission=self.reveal_perm)
        UserRole.objects.create(user=self.compliance_user, role=self.compliance_role, assigned_by=self.compliance_user)

    def test_masking_algorithms_strictly_hide_leading_digits(self):
        """Verify mask functions protect leading digits and leave only last 4."""
        self.assertEqual(mask_aadhaar("987654321098"), "XXXX XXXX 1098")
        self.assertEqual(mask_bank_account("123456789012"), "XXXXXXXX9012")

        # Edge cases
        self.assertEqual(mask_aadhaar(""), "")
        self.assertEqual(mask_bank_account(""), "")
        self.assertEqual(mask_aadhaar("123"), "XXXX")

    def test_student_endpoints_strictly_return_masked_values_by_default(self):
        """Verify student list and detail endpoints return masked Aadhaar and bank details."""
        self.client.force_authenticate(user=self.staff_user)

        # Detail endpoint
        res = self.client.get(f'/api/v1/students/{self.student.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Cleartext must never appear in default payload
        self.assertNotIn("987654321098", str(res.content))
        self.assertNotIn("123456789012", str(res.content))

        # Must have masked representation
        self.assertEqual(res.data.get('aadhaar_masked'), "XXXX XXXX 1098")
        bank_acc = res.data.get('bank_account')
        if bank_acc:
            self.assertEqual(bank_acc.get('account_number_masked'), "XXXXXXXX9012")

    def test_unauthorized_user_cannot_reveal_sensitive_data(self):
        """Verify user without 'students.reveal_sensitive' receives 403 Forbidden."""
        self.client.force_authenticate(user=self.staff_user)

        res = self.client.post(f'/api/v1/students/{self.student.id}/reveal-sensitive/', {
            'field_name': 'aadhaar',
            'reason': 'Routine audit check'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error", res.data)

    def test_reveal_without_mandatory_reason_is_rejected(self):
        """Verify revealing without justification raises validation error."""
        self.client.force_authenticate(user=self.compliance_user)

        res = self.client.post(f'/api/v1/students/{self.student.id}/reveal-sensitive/', {
            'field_name': 'aadhaar',
            'reason': ''
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authorized_reveal_returns_cleartext_and_records_immutable_audit(self):
        """Verify authorized reveal yields cleartext and creates audit trail in SensitiveDataAccessLog."""
        self.client.force_authenticate(user=self.compliance_user)

        initial_audit_count = SensitiveDataAccessLog.objects.count()

        # Reveal Aadhaar
        res = self.client.post(f'/api/v1/students/{self.student.id}/reveal-sensitive/', {
            'field_name': 'aadhaar',
            'reason': 'Statutory verification by compliance team'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get('value'), "987654321098")

        # Verify audit log entry created
        self.assertEqual(SensitiveDataAccessLog.objects.count(), initial_audit_count + 1)
        audit_entry = SensitiveDataAccessLog.objects.latest('accessed_at')
        self.assertEqual(audit_entry.accessor, self.compliance_user)
        self.assertEqual(audit_entry.field_name, 'aadhaar')
        self.assertEqual(audit_entry.reason, 'Statutory verification by compliance team')
