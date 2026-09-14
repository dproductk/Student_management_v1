"""
User lifecycle application service.
Orchestrates user creation, state transitions (active, suspended, inactive),
and password updates according to domain invariants.
"""

from typing import Optional
from django.db import transaction
from common.exceptions import EntityNotFoundError, InvariantViolationError
from apps.identity.models import User
from apps.audit.services.audit_service import AuditService
from apps.identity.domain.state_machines import (
    UserStatus,
    UserLifecycleStateMachine,
    validate_username,
    validate_password_strength,
)


class UserService:
    """
    Application service managing the lifecycle of canonical User accounts.
    """

    @classmethod
    @transaction.atomic
    def create_user(
        cls,
        username: str,
        password: Optional[str] = None,
        email: Optional[str] = None,
        must_change_password: bool = True
    ) -> User:
        """
        Creates a new canonical User account with domain validation.
        """
        validate_username(username)
        if password:
            validate_password_strength(password)

        if User.objects.filter(username=username).exists():
            raise InvariantViolationError(f"A user with username '{username}' already exists.")

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            must_change_password=must_change_password,
            status=UserStatus.ACTIVE.value,
            is_active=True
        )
        return user

    @classmethod
    @transaction.atomic
    def suspend_user(cls, user_id: str, reason: Optional[str] = None, actor: Optional[User] = None) -> User:
        """
        Transitions user account to SUSPENDED status.
        Disallows authentication while suspended.
        """
        try:
            user = User.objects.select_for_update().get(id=user_id)
        except User.DoesNotExist:
            raise EntityNotFoundError("User", user_id)

        current_status = UserStatus(user.status)
        UserLifecycleStateMachine.validate_transition(current_status, UserStatus.SUSPENDED)

        user.status = UserStatus.SUSPENDED.value
        user.is_active = False
        user.save(update_fields=['status', 'is_active', 'updated_at'])

        AuditService.record_audit(
            action="USER_SUSPENDED",
            target_type="USER",
            module="identity",
            actor=actor,
            target_id=user.id,
            old_value={"status": current_status.value},
            new_value={"status": UserStatus.SUSPENDED.value},
            reason=reason
        )
        return user

    @classmethod
    @transaction.atomic
    def reactivate_user(cls, user_id: str, actor: Optional[User] = None) -> User:
        """
        Transitions a SUSPENDED user account back to ACTIVE.
        """
        try:
            user = User.objects.select_for_update().get(id=user_id)
        except User.DoesNotExist:
            raise EntityNotFoundError("User", user_id)

        current_status = UserStatus(user.status)
        UserLifecycleStateMachine.validate_transition(current_status, UserStatus.ACTIVE)

        user.status = UserStatus.ACTIVE.value
        user.is_active = True
        user.save(update_fields=['status', 'is_active', 'updated_at'])

        AuditService.record_audit(
            action="USER_REACTIVATED",
            target_type="USER",
            module="identity",
            actor=actor,
            target_id=user.id,
            old_value={"status": current_status.value},
            new_value={"status": UserStatus.ACTIVE.value},
            reason="User reactivated"
        )
        return user

    @classmethod
    @transaction.atomic
    def deactivate_user(cls, user_id: str, reason: Optional[str] = None, actor: Optional[User] = None) -> User:
        """
        Transitions user account to INACTIVE (terminal archived state).
        """
        try:
            user = User.objects.select_for_update().get(id=user_id)
        except User.DoesNotExist:
            raise EntityNotFoundError("User", user_id)

        current_status = UserStatus(user.status)
        UserLifecycleStateMachine.validate_transition(current_status, UserStatus.INACTIVE)

        user.status = UserStatus.INACTIVE.value
        user.is_active = False
        user.save(update_fields=['status', 'is_active', 'updated_at'])

        AuditService.record_audit(
            action="USER_DEACTIVATED",
            target_type="USER",
            module="identity",
            actor=actor,
            target_id=user.id,
            old_value={"status": current_status.value},
            new_value={"status": UserStatus.INACTIVE.value},
            reason=reason
        )
        return user

    @classmethod
    @transaction.atomic
    def set_user_password(cls, user_id: str, new_password: str) -> User:
        """
        Sets a new password and clears the must_change_password flag.
        """
        validate_password_strength(new_password)
        try:
            user = User.objects.select_for_update().get(id=user_id)
        except User.DoesNotExist:
            raise EntityNotFoundError("User", user_id)

        user.set_password(new_password)
        user.must_change_password = False
        user.save(update_fields=['password', 'must_change_password', 'updated_at'])
        return user
