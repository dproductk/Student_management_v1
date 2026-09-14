"""
Common domain and application exceptions.
"""


class DomainException(Exception):
    """Base exception for all domain logic violations."""
    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


class EntityNotFoundError(DomainException):
    """Raised when an entity is not found in the persistence store."""
    def __init__(self, entity_name: str, identifier: str):
        super().__init__(f"{entity_name} with identifier '{identifier}' was not found.", code="NOT_FOUND")


class InvariantViolationError(DomainException):
    """Raised when a business rule or invariant is violated."""
    def __init__(self, message: str):
        super().__init__(message, code="INVARIANT_VIOLATION")


class StateTransitionError(DomainException):
    """Raised when an invalid state machine transition is attempted."""
    def __init__(self, current_state: str, attempted_state: str, allowed_states: list):
        message = (
            f"Cannot transition from '{current_state}' to '{attempted_state}'. "
            f"Allowed transitions from '{current_state}': {allowed_states}."
        )
        super().__init__(message, code="INVALID_STATE_TRANSITION")
