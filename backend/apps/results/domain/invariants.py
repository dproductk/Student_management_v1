from decimal import Decimal
from typing import Dict, Any, Tuple


class ResultValidationError(Exception):
    """Raised when result data or marks violate domain rules."""
    pass


class ResultImmutabilityViolation(Exception):
    """Raised when an attempt is made to alter or delete an immutable published result."""
    pass


class InvalidLifecycleTransitionError(Exception):
    """Raised when an invalid lifecycle state transition is attempted."""
    pass


class CreditCalculationError(Exception):
    """Raised when credit calculation encounters inconsistent state or unpublished result."""
    pass


class EligibilityValidationError(Exception):
    """Raised when eligibility rules or evaluation data violate domain constraints."""
    pass


# Batch allowed transitions
BATCH_ALLOWED_TRANSITIONS = {
    'PENDING': {'PROCESSING', 'FAILED'},
    'PROCESSING': {'VALIDATED', 'FAILED'},
    'VALIDATED': {'APPROVED', 'REJECTED', 'PROCESSING'},
    'APPROVED': {'PUBLISHED', 'REJECTED'},
    'REJECTED': {'PROCESSING'},
    'FAILED': {'PROCESSING'},
    'PUBLISHED': set(),  # Terminal state
}

# Student Result allowed transitions
RESULT_ALLOWED_TRANSITIONS = {
    'DRAFT': {'APPROVED', 'REJECTED'},
    'APPROVED': {'PUBLISHED', 'REJECTED'},
    'REJECTED': {'DRAFT'},
    'PUBLISHED': {'SUPERSEDED'},  # Only via official approved correction
    'SUPERSEDED': set(),  # Historical immutable archive
}


def validate_batch_transition(current_status: str, next_status: str) -> None:
    """Ensures ResultImportBatch moves through valid lifecycle states."""
    allowed = BATCH_ALLOWED_TRANSITIONS.get(current_status, set())
    if next_status not in allowed:
        raise InvalidLifecycleTransitionError(
            f"Cannot transition ResultImportBatch from '{current_status}' to '{next_status}'. "
            f"Allowed next states: {sorted(list(allowed)) or 'None (Terminal)'}"
        )


def validate_result_transition(current_status: str, next_status: str) -> None:
    """Ensures StudentResult moves through valid lifecycle states."""
    allowed = RESULT_ALLOWED_TRANSITIONS.get(current_status, set())
    if next_status not in allowed:
        raise InvalidLifecycleTransitionError(
            f"Cannot transition StudentResult from '{current_status}' to '{next_status}'. "
            f"Allowed next states: {sorted(list(allowed)) or 'None (Terminal)'}"
        )


def validate_result_immutability(instance) -> None:
    """
    Prevents modifying or deleting a StudentResult or StudentResultDetail
    that is in PUBLISHED or SUPERSEDED state.
    """
    if hasattr(instance, 'student_result') and instance.student_result:
        status = getattr(instance.student_result, 'status', None)
    else:
        status = getattr(instance, 'status', None)

    if status in ('PUBLISHED', 'SUPERSEDED'):
        raise ResultImmutabilityViolation(
            f"Operation rejected: Published results are immutable historical records. "
            f"Current status is '{status}'. Changes must be processed via official correction "
            f"requests spawning versioned supersession (Result V2)."
        )


def validate_mark_values(
    internal_marks: Decimal,
    external_marks: Decimal,
    max_marks: Decimal = Decimal('100.00'),
    is_absent: bool = False
) -> Decimal:
    """
    Validates mark entries for a subject.
    Returns total_marks.
    """
    if is_absent:
        return Decimal('0.00')

    if internal_marks is not None and internal_marks < 0:
        raise ResultValidationError(f"Internal marks cannot be negative: {internal_marks}")

    if external_marks is not None and external_marks < 0:
        raise ResultValidationError(f"External marks cannot be negative: {external_marks}")

    total = (internal_marks or Decimal('0.00')) + (external_marks or Decimal('0.00'))
    if total > max_marks:
        raise ResultValidationError(
            f"Total marks ({total}) exceed maximum configured marks ({max_marks})"
        )

    return total


def calculate_grade_and_points(
    total_marks: Decimal,
    max_marks: Decimal = Decimal('100.00'),
    is_absent: bool = False
) -> Tuple[str, Decimal, str]:
    """
    Derives standard UGC 10-point scale:
    Returns (grade_letter, grade_point, status).
    """
    if is_absent:
        return ('AB', Decimal('0.00'), 'ABSENT')

    if max_marks <= Decimal('0.00'):
        return ('F', Decimal('0.00'), 'FAIL')

    percentage = (total_marks / max_marks) * Decimal('100.00')

    if percentage >= Decimal('90.00'):
        return ('O', Decimal('10.00'), 'PASS')
    elif percentage >= Decimal('80.00'):
        return ('A+', Decimal('9.00'), 'PASS')
    elif percentage >= Decimal('70.00'):
        return ('A', Decimal('8.00'), 'PASS')
    elif percentage >= Decimal('60.00'):
        return ('B+', Decimal('7.00'), 'PASS')
    elif percentage >= Decimal('55.00'):
        return ('B', Decimal('6.00'), 'PASS')
    elif percentage >= Decimal('50.00'):
        return ('C', Decimal('5.00'), 'PASS')
    elif percentage >= Decimal('40.00'):
        return ('P', Decimal('4.00'), 'PASS')
    else:
        return ('F', Decimal('0.00'), 'FAIL')


def validate_eligibility_rule_invariants(
    min_credits: Decimal,
    min_attendance: Decimal,
    max_backlogs: int,
    detention_max_backlogs: int,
    detention_min_attendance: Decimal
) -> None:
    """
    Validates logical invariants for eligibility rules:
    - Thresholds cannot be negative.
    - Attendance percentages must be between 0 and 100.
    - Detention backlogs must be >= max allowable normal backlogs.
    - Detention attendance threshold must be <= normal attendance threshold.
    """
    if min_credits < Decimal('0.0'):
        raise EligibilityValidationError(f"Minimum credits cannot be negative: {min_credits}")

    if min_attendance < Decimal('0.0') or min_attendance > Decimal('100.0'):
        raise EligibilityValidationError(f"Minimum attendance must be between 0% and 100%: {min_attendance}")

    if detention_min_attendance < Decimal('0.0') or detention_min_attendance > Decimal('100.0'):
        raise EligibilityValidationError(f"Detention attendance must be between 0% and 100%: {detention_min_attendance}")

    if detention_min_attendance > min_attendance:
        raise EligibilityValidationError(
            f"Detention attendance threshold ({detention_min_attendance}%) cannot exceed "
            f"normal minimum attendance ({min_attendance}%)."
        )

    if max_backlogs < 0:
        raise EligibilityValidationError(f"Maximum backlogs cannot be negative: {max_backlogs}")

    if detention_max_backlogs < max_backlogs:
        raise EligibilityValidationError(
            f"Detention backlog threshold ({detention_max_backlogs}) must be greater than or equal to "
            f"allowable backlogs ({max_backlogs})."
        )


def validate_decision_immutability(decision) -> None:
    """
    Prevents modifying or deleting an existing historical EligibilityDecision.
    Corrections must spawn a new version linked by superseded_by.
    """
    if decision and getattr(decision, 'pk', None):
        if not getattr(decision, 'is_latest', True):
            raise ResultImmutabilityViolation(
                "Historical eligibility decisions are immutable records and cannot be altered or deleted."
            )
