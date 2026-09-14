"""
Domain state machine and lifecycle rules for User identity.
Governed by ARCHITECTURE.md, AGENT.md, and identity-and-access-prd.md.
"""

from enum import Enum
from common.exceptions import StateTransitionError, InvariantViolationError


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    INACTIVE = "INACTIVE"


class UserLifecycleStateMachine:
    """
    Guards state transitions for User accounts:
    ACTIVE <-> SUSPENDED
    ACTIVE -> INACTIVE
    SUSPENDED -> INACTIVE
    INACTIVE is terminal (archived/deactivated).
    """

    ALLOWED_TRANSITIONS = {
        UserStatus.ACTIVE: [UserStatus.SUSPENDED, UserStatus.INACTIVE],
        UserStatus.SUSPENDED: [UserStatus.ACTIVE, UserStatus.INACTIVE],
        UserStatus.INACTIVE: [],  # Terminal state
    }

    @classmethod
    def can_transition(cls, from_status: UserStatus, to_status: UserStatus) -> bool:
        return to_status in cls.ALLOWED_TRANSITIONS.get(from_status, [])

    @classmethod
    def validate_transition(cls, from_status: UserStatus, to_status: UserStatus) -> None:
        if from_status == to_status:
            return
        allowed = cls.ALLOWED_TRANSITIONS.get(from_status, [])
        if to_status not in allowed:
            raise StateTransitionError(
                current_state=from_status.value,
                attempted_state=to_status.value,
                allowed_states=[s.value for s in allowed]
            )


def validate_username(username: str) -> None:
    """
    Validates username format invariant.
    Must be non-empty string, length <= 150.
    """
    if not username or not username.strip():
        raise InvariantViolationError("Username cannot be empty.")
    if len(username.strip()) > 150:
        raise InvariantViolationError("Username cannot exceed 150 characters.")


def validate_password_strength(password: str) -> None:
    """
    Validates password strength requirement (minimum 8 characters).
    """
    if not password or len(password) < 8:
        raise InvariantViolationError("Password must be at least 8 characters long.")
