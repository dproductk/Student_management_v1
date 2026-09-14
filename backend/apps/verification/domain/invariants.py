"""
Verification domain invariants and state-machine transitions.
Governed by Deliverable D.5 of DATABASE_ARCHITECTURE.md and verification-prd.md.
"""

from common.exceptions import InvariantViolationError, StateTransitionError

VERIFICATION_STATUS_CHOICES = [
    ('PENDING', 'Pending Verification'),
    ('APPROVED', 'Approved'),
    ('REJECTED', 'Rejected'),
    ('NEEDS_CORRECTION', 'Needs Correction'),
]

ENTITY_TYPE_CHOICES = [
    ('PERSONAL_INFO', 'Personal Information'),
    ('DOCUMENT', 'Student Document'),
    ('BANK_DETAILS', 'Bank Details'),
    ('ADDRESS', 'Address Information'),
    ('GOVERNMENT_CORRECTION', 'Government Record Correction'),
]

ALLOWED_DECISIONS = {'APPROVED', 'REJECTED', 'NEEDS_CORRECTION'}


def validate_verification_status(status_val: str) -> None:
    valid = {k for k, _ in VERIFICATION_STATUS_CHOICES}
    if status_val not in valid:
        raise InvariantViolationError(f"Invalid verification status '{status_val}'. Allowed: {sorted(valid)}")


def validate_entity_type(entity_type: str) -> None:
    valid = {k for k, _ in ENTITY_TYPE_CHOICES}
    if entity_type not in valid:
        raise InvariantViolationError(f"Invalid entity type '{entity_type}'. Allowed: {sorted(valid)}")


def validate_state_transition(current_status: str, new_status: str) -> None:
    """Guards verification state transitions according to PRD section 5.2."""
    if current_status == new_status:
        return

    allowed_transitions = {
        'PENDING': {'APPROVED', 'REJECTED', 'NEEDS_CORRECTION'},
        'NEEDS_CORRECTION': {'PENDING'},  # Re-submission
        'REJECTED': {'PENDING'},          # Re-submission
        'APPROVED': set(),                # Approved records cannot transition directly; new version required
    }

    allowed = allowed_transitions.get(current_status, set())
    if new_status not in allowed:
        raise StateTransitionError(
            current_state=current_status,
            attempted_state=new_status,
            allowed_states=sorted(list(allowed))
        )


def validate_decision_payload(decision: str, rejection_reason: str) -> None:
    if decision not in ALLOWED_DECISIONS:
        raise InvariantViolationError(f"Decision '{decision}' is not allowed. Choose from: {sorted(ALLOWED_DECISIONS)}")

    if decision in {'REJECTED', 'NEEDS_CORRECTION'}:
        if not rejection_reason or not rejection_reason.strip():
            raise InvariantViolationError(f"A mandatory reason must be provided when decision is {decision}.")
