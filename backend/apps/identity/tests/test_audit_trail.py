"""
Automated tests for Identity Audit Trail vertical slice.
Governed by identity-and-access-prd.md Requirements 21, 25, 26, 27,
DATABASE_ARCHITECTURE.md Deliverable D.11 & N, and ADR-015.
"""

from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework import status
from django.urls import reverse

from common.exceptions import InvariantViolationError
from apps.identity.models import User, Role, UserRole, Permission, RolePermission
from apps.audit.models import AuditLog
from apps.audit.services.audit_service import AuditService
from apps.identity.services.auth_service import AuthService
from apps.identity.services.user_service import UserService
from apps.identity.services.role_service import RoleService
from apps.identity.domain.state_machines import UserStatus
from apps.identity.api.views import IdentityAuditLogView


class IdentityAuditTrailTests(APITestCase):
    """
    Tests automated audit log generation, credential sanitization, immutability,
    and audit query endpoint access.
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        RoleService.seed_canonical_roles_and_permissions()

        # Create auditor admin with identity.view_audit permission
        self.auditor_admin = User.objects.create_user(
            username="auditor_admin",
            password="AdminPassword123!",
            email="auditor@college.edu",
            must_change_password=False,
            status=UserStatus.ACTIVE.value,
            is_active=True,
        )
        admin_role = Role.objects.get(name="SYSTEM_ADMIN")
        UserRole.objects.create(
            user=self.auditor_admin,
            role=admin_role,
            assigned_by=self.auditor_admin
        )

        # Create regular user to perform audited actions on
        self.regular_user = User.objects.create_user(
            username="test_student_audit",
            password="InitialPassword123!",
            email="student_audit@college.edu",
            must_change_password=True,
            status=UserStatus.ACTIVE.value,
            is_active=True,
        )

    def test_login_success_creates_audit_entry(self):
        """
        Validates that successful authentication records a LOGIN_SUCCESS audit log.
        """
        initial_count = AuditLog.objects.filter(action="LOGIN_SUCCESS").count()

        AuthService.authenticate_and_issue_tokens(
            username="test_student_audit",
            password="InitialPassword123!"
        )

        self.assertEqual(AuditLog.objects.filter(action="LOGIN_SUCCESS").count(), initial_count + 1)
        log = AuditLog.objects.filter(action="LOGIN_SUCCESS").latest('occurred_at')
        self.assertEqual(log.actor, self.regular_user)
        self.assertEqual(log.target_type, "USER")
        self.assertEqual(log.module, "identity")
        self.assertEqual(log.target_id, self.regular_user.id)

    def test_login_failed_creates_audit_entry_without_password(self):
        """
        Validates that failed authentication creates LOGIN_FAILED entry
        WITHOUT logging the entered password string (Requirement 25).
        """
        bad_password = "TotallyWrongSecretPassword!"
        try:
            AuthService.authenticate_and_issue_tokens(
                username="test_student_audit",
                password=bad_password
            )
        except Exception:
            pass

        log = AuditLog.objects.filter(action="LOGIN_FAILED").latest('occurred_at')
        self.assertIsNotNone(log)
        self.assertEqual(log.module, "identity")

        # Verify bad_password string is nowhere in the audit entry
        raw_dump = f"{log.old_value} {log.new_value} {log.reason}"
        self.assertNotIn(bad_password, raw_dump)

    def test_password_changed_creates_audit_entry_without_passwords(self):
        """
        Validates that password changes record PASSWORD_CHANGED without storing credentials.
        """
        AuthService.change_password(
            user=self.regular_user,
            current_password="InitialPassword123!",
            new_password="BrandNewSecurePassword123!",
            confirm_password="BrandNewSecurePassword123!"
        )

        log = AuditLog.objects.filter(action="PASSWORD_CHANGED").latest('occurred_at')
        self.assertIsNotNone(log)
        self.assertEqual(log.actor, self.regular_user)
        self.assertEqual(log.target_id, self.regular_user.id)

        # Confirm no passwords appear in snapshots
        raw_dump = f"{log.old_value} {log.new_value} {log.reason}"
        self.assertNotIn("InitialPassword123!", raw_dump)
        self.assertNotIn("BrandNewSecurePassword123!", raw_dump)

    def test_user_lifecycle_state_transitions_create_audit_entries(self):
        """
        Validates that account suspension, reactivation, and deactivation
        record accountable audit entries with reasons.
        """
        # 1. Suspend
        UserService.suspend_user(
            user_id=str(self.regular_user.id),
            reason="Violation of college policy",
            actor=self.auditor_admin
        )
        suspend_log = AuditLog.objects.filter(action="USER_SUSPENDED").latest('occurred_at')
        self.assertEqual(suspend_log.actor, self.auditor_admin)
        self.assertEqual(suspend_log.target_id, self.regular_user.id)
        self.assertEqual(suspend_log.reason, "Violation of college policy")

        # 2. Reactivate
        UserService.reactivate_user(
            user_id=str(self.regular_user.id),
            actor=self.auditor_admin
        )
        reactivate_log = AuditLog.objects.filter(action="USER_REACTIVATED").latest('occurred_at')
        self.assertEqual(reactivate_log.actor, self.auditor_admin)
        self.assertEqual(reactivate_log.target_id, self.regular_user.id)

        # 3. Deactivate
        UserService.deactivate_user(
            user_id=str(self.regular_user.id),
            reason="Student graduated",
            actor=self.auditor_admin
        )
        deactivate_log = AuditLog.objects.filter(action="USER_DEACTIVATED").latest('occurred_at')
        self.assertEqual(deactivate_log.actor, self.auditor_admin)
        self.assertEqual(deactivate_log.target_id, self.regular_user.id)
        self.assertEqual(deactivate_log.reason, "Student graduated")

    def test_role_and_permission_assignment_audit_entries(self):
        """
        Validates audit logging on role assignments, revocations, and permissions.
        """
        student_role = Role.objects.get(name="STUDENT")

        # 1. Assign Role
        ur = RoleService.assign_role_to_user(
            user_id=str(self.regular_user.id),
            role_id=str(student_role.id),
            assigned_by=self.auditor_admin
        )
        assign_log = AuditLog.objects.filter(action="ROLE_ASSIGNED").latest('occurred_at')
        self.assertEqual(assign_log.actor, self.auditor_admin)
        self.assertEqual(assign_log.target_id, self.regular_user.id)

        # 2. Revoke Role
        RoleService.revoke_role_from_user(
            user_id=str(self.regular_user.id),
            role_id=str(student_role.id)
        )
        revoke_log = AuditLog.objects.filter(action="ROLE_REVOKED").latest('occurred_at')
        self.assertEqual(revoke_log.target_id, self.regular_user.id)

    def test_audit_log_immutability_enforcement(self):
        """
        Enforces that AuditLog records cannot be modified or deleted.
        """
        log = AuditService.record_audit(
            action="TEST_IMMUTABLE",
            target_type="TEST",
            module="identity",
            actor=self.auditor_admin
        )

        # Attempt to modify
        log.action = "TAMPERED_ACTION"
        with self.assertRaises(InvariantViolationError):
            log.save()

        # Attempt to delete
        with self.assertRaises(InvariantViolationError):
            log.delete()

    def test_sensitive_scrubbing_sanitizer(self):
        """
        Validates that AuditService automatically scrubs sensitive dictionary keys.
        """
        dirty_payload = {
            "username": "john_doe",
            "password": "super_secret_password",
            "token": "jwt.bearer.token",
            "nested": {
                "access": "secret_access_key",
                "normal_field": "public_info"
            }
        }

        log = AuditService.record_audit(
            action="TEST_SCRUBBING",
            target_type="TEST",
            module="identity",
            new_value=dirty_payload
        )

        self.assertEqual(log.new_value["password"], "[REDACTED]")
        self.assertEqual(log.new_value["token"], "[REDACTED]")
        self.assertEqual(log.new_value["nested"]["access"], "[REDACTED]")
        self.assertEqual(log.new_value["nested"]["normal_field"], "public_info")

    def test_audit_api_endpoint_permissions(self):
        """
        GET /api/v1/auth/audit/
        Only users with identity.view_audit permission may query audit logs.
        """
        # Create an event to query
        AuditService.record_audit(
            action="QUERY_TEST_ACTION",
            target_type="USER",
            module="identity",
            actor=self.auditor_admin,
            target_id=self.regular_user.id
        )

        url = reverse('identity-audit-log')

        # 1. Auditor Admin with identity.view_audit succeeds
        req = self.factory.get(url, {'action': 'QUERY_TEST_ACTION'})
        force_authenticate(req, user=self.auditor_admin)
        resp = IdentityAuditLogView.as_view()(req)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(len(resp.data) >= 1)
        self.assertEqual(resp.data[0]['action'], 'QUERY_TEST_ACTION')

        # 2. Regular user without identity.view_audit is denied
        req_unauth = self.factory.get(url)
        force_authenticate(req_unauth, user=self.regular_user)
        resp_unauth = IdentityAuditLogView.as_view()(req_unauth)
        self.assertEqual(resp_unauth.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Anonymous user is denied
        req_anon = self.factory.get(url)
        resp_anon = IdentityAuditLogView.as_view()(req_anon)
        self.assertEqual(resp_anon.status_code, status.HTTP_401_UNAUTHORIZED)
