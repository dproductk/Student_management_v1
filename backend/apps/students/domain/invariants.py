"""
Domain invariants and validation rules for Student Management.
"""

from common.exceptions import InvariantViolationError, StateTransitionError


VALID_STUDENT_STATUSES = ['ACTIVE', 'DETAINED', 'PASSED_OUT', 'DROPPED', 'TRANSFERRED', 'CANCELLED']
VALID_GENDERS = ['MALE', 'FEMALE', 'OTHER']
VALID_ENROLLMENT_STATUSES = ['ACTIVE', 'COMPLETED', 'DETAINED', 'DROPPED', 'TRANSFERRED']

ALLOWED_CORRECTION_FIELDS = [
    'candidate_name',
    'father_name',
    'mother_name',
    'date_of_birth',
    'gender',
    'student_mobile',
    'parent_mobile',
    'email',
    'religion',
    'mother_tongue',
    'candidature_type',
    'admission_type',
    'admission_category',
    'seat_type',
    'allotted_seat_type',
]


def validate_student_status(status: str):
    if status not in VALID_STUDENT_STATUSES:
        raise InvariantViolationError(f"Invalid student status '{status}'. Allowed: {VALID_STUDENT_STATUSES}")


def validate_gender(gender: str):
    if gender not in VALID_GENDERS:
        raise InvariantViolationError(f"Invalid gender '{gender}'. Allowed: {VALID_GENDERS}")


def validate_enrollment_transition(current_status: str, next_status: str):
    if next_status not in VALID_ENROLLMENT_STATUSES:
        raise StateTransitionError(current_status, next_status, VALID_ENROLLMENT_STATUSES)
    if current_status == 'COMPLETED' and next_status == 'ACTIVE':
        raise StateTransitionError(current_status, next_status, [])


def validate_correction_request(field_name: str, new_value: str, reason: str, approver_id):
    if field_name not in ALLOWED_CORRECTION_FIELDS:
        raise InvariantViolationError(f"Field '{field_name}' is not permitted for additive student correction.")
    if not reason or not reason.strip():
        raise InvariantViolationError("Correction reason is required for administrative audit integrity.")
    if not approver_id:
        raise InvariantViolationError("Accountable approver is required for additive student correction (ADR-013).")
