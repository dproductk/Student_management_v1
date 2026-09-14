from typing import Optional, Set

class ServiceValidationError(Exception):
    """Raised when service request data or payload is invalid."""
    pass


class InvalidServiceStateTransitionError(Exception):
    """Raised when an invalid lifecycle state transition is attempted on a ServiceRequest."""
    pass


class ServicePermissionDeniedError(Exception):
    """Raised when an unauthorized actor attempts an administrative service operation."""
    pass


# Workflow state machine definitions
SERVICE_ALLOWED_TRANSITIONS = {
    'SUBMITTED': {'IN_PROGRESS', 'CANCELLED'},
    'IN_PROGRESS': {'APPROVED', 'REJECTED', 'CANCELLED'},
    'APPROVED': {'COMPLETED'},
    'REJECTED': set(),   # Terminal state
    'COMPLETED': set(),  # Terminal state
    'CANCELLED': set(),  # Terminal state
}


def validate_service_transition(current_status: str, next_status: str) -> None:
    """Validates that a service request moves through legal lifecycle states."""
    allowed: Set[str] = SERVICE_ALLOWED_TRANSITIONS.get(current_status, set())
    if next_status not in allowed:
        raise InvalidServiceStateTransitionError(
            f"Cannot transition ServiceRequest from '{current_status}' to '{next_status}'. "
            f"Allowed next states: {sorted(list(allowed)) or 'None (Terminal state)'}."
        )


def validate_rejection_reason(reason: Optional[str]) -> None:
    """Ensures a mandatory rejection justification is provided when rejecting a request."""
    if not reason or not str(reason).strip():
        raise ServiceValidationError(
            "A mandatory rejection reason must be provided when rejecting a service request."
        )


def validate_service_document_requirement(service_type, attached_document) -> None:
    """Validates document requirements if mandated by the service type."""
    if getattr(service_type, 'requires_document', False):
        if not attached_document:
            raise ServiceValidationError(
                f"Service type '{service_type.name}' requires a supporting document attachment."
            )
        allowed_types = getattr(service_type, 'allowed_document_types', [])
        if allowed_types and hasattr(attached_document, 'document_type'):
            if attached_document.document_type not in allowed_types:
                raise ServiceValidationError(
                    f"Document type '{attached_document.document_type}' is not permitted for '{service_type.name}'. "
                    f"Allowed document types: {allowed_types}."
                )
