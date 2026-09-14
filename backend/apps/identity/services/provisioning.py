"""
Student account provisioning service and policies.
Governed by ADR-009, ARCHITECTURE.md, and identity-and-access-prd.md.

Establishes the Identity-side provisioning contract for student accounts:
- Username = Enrollment Number (trimmed)
- Initial Password = Enrollment Number (trimmed)
- must_change_password = True
- Automatic canonical STUDENT role assignment (scope OWN)
- Idempotent: returns existing user without error or duplication
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, List, Dict, Any
from django.db import transaction

from common.exceptions import InvariantViolationError
from apps.identity.models import User, Role, UserRole
from apps.identity.domain.state_machines import UserStatus
from apps.identity.domain.rbac import CANONICAL_ROLES, RoleScopeType


class StudentProvisioningPolicy(ABC):
    """
    Abstract strategy for student credential generation.
    Allows future activation strategies (e.g. OTP activation, invitation links)
    to be introduced without modifying Student Management or caller code.
    """

    @abstractmethod
    def generate_credentials(self, enrollment_number: str) -> Tuple[str, str, bool]:
        """
        Generates initial credentials for the given enrollment number.
        Returns: (username, initial_password, must_change_password)
        """
        pass


class EnrollmentNumberProvisioningPolicy(StudentProvisioningPolicy):
    """
    Canonical initial provisioning policy per ADR-009:
    - Username = Enrollment Number
    - Initial Password = Enrollment Number
    - must_change_password = True
    """

    def generate_credentials(self, enrollment_number: str) -> Tuple[str, str, bool]:
        if not enrollment_number or not enrollment_number.strip():
            raise InvariantViolationError("Enrollment number cannot be empty.")
        normalized = enrollment_number.strip()
        return normalized, normalized, True


class StudentAccountProvisioningService:
    """
    Identity domain application service orchestrating student user creation
    and role assignment according to the active provisioning policy.
    """

    DEFAULT_POLICY = EnrollmentNumberProvisioningPolicy()

    @classmethod
    def _ensure_student_role(cls, user: User, assigned_by: Optional[User] = None) -> None:
        """
        Ensures the canonical STUDENT role (scope OWN) exists and is assigned to the user.
        """
        student_role, _ = Role.objects.get_or_create(
            name="STUDENT",
            defaults={
                'scope_type': RoleScopeType.OWN.value,
                'description': CANONICAL_ROLES.get("STUDENT", {}).get(
                    "description",
                    "Student user with self-service access to own profile, fees, and results."
                )
            }
        )
        assigner = assigned_by or user
        UserRole.objects.get_or_create(
            user=user,
            role=student_role,
            defaults={'assigned_by': assigner}
        )

    @classmethod
    @transaction.atomic
    def provision_student_account(
        cls,
        enrollment_number: str,
        email: Optional[str] = None,
        assigned_by: Optional[User] = None,
        policy: Optional[StudentProvisioningPolicy] = None
    ) -> Tuple[User, bool]:
        """
        Provisions a student User account per the active provisioning policy.
        Idempotent: if a user with the generated username already exists, ensures
        the STUDENT role is assigned and returns (user, False).

        Returns: (User, created: bool)
        """
        active_policy = policy or cls.DEFAULT_POLICY
        username, initial_password, must_change = active_policy.generate_credentials(enrollment_number)

        existing_user = User.objects.filter(username=username).first()
        if existing_user:
            cls._ensure_student_role(existing_user, assigned_by=assigned_by)
            return existing_user, False

        user = User.objects.create_user(
            username=username,
            password=initial_password,
            email=email,
            must_change_password=must_change,
            status=UserStatus.ACTIVE.value,
            is_active=True
        )
        cls._ensure_student_role(user, assigned_by=assigned_by)
        return user, True

    @classmethod
    def bulk_provision_student_accounts(
        cls,
        student_records: List[Dict[str, Any]],
        assigned_by: Optional[User] = None,
        policy: Optional[StudentProvisioningPolicy] = None
    ) -> Dict[str, Any]:
        """
        Provisions multiple student accounts in batch.
        Safe against partial failures: processes each record and returns full status summary.
        """
        created_list: List[Dict[str, str]] = []
        existing_list: List[Dict[str, str]] = []
        errors_list: List[Dict[str, str]] = []

        for record in student_records:
            enrollment_number = record.get("enrollment_number", "")
            email = record.get("email")
            try:
                user, created = cls.provision_student_account(
                    enrollment_number=enrollment_number,
                    email=email,
                    assigned_by=assigned_by,
                    policy=policy
                )
                record_info = {
                    "user_id": str(user.id),
                    "username": user.username,
                    "email": user.email or "",
                }
                if created:
                    created_list.append(record_info)
                else:
                    existing_list.append(record_info)
            except Exception as exc:
                errors_list.append({
                    "enrollment_number": str(enrollment_number),
                    "error": str(exc)
                })

        return {
            "total": len(student_records),
            "created_count": len(created_list),
            "existing_count": len(existing_list),
            "failed_count": len(errors_list),
            "created": created_list,
            "existing": existing_list,
            "errors": errors_list
        }
