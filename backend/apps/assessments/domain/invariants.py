"""
Domain Invariants for Assessments & Unit Test Marks module.
Implements:
- Extensible assessment validation
- Marks range & absence consistency (0 <= marks <= max_marks)
- Assessment status locks (DRAFT -> PUBLISHED -> LOCKED)
- Duplicate row detection & enrollment boundaries
"""

from decimal import Decimal
from typing import Optional, List, Dict, Any, Set
from common.exceptions import InvariantViolationError


def validate_mark_entry(
    marks_obtained: Optional[Decimal],
    max_marks: Decimal,
    is_absent: bool = False
) -> None:
    """
    Validates mark consistency:
    - If student is marked absent, marks_obtained must be None or 0.
    - If student is present, marks_obtained is required, cannot be negative, and cannot exceed max_marks.
    """
    if max_marks <= Decimal('0.00'):
        raise InvariantViolationError(f"Assessment maximum marks must be strictly positive, got {max_marks}.")

    if is_absent:
        if marks_obtained is not None and marks_obtained > Decimal('0.00'):
            raise InvariantViolationError("A student marked absent cannot have marks greater than 0.")
        return

    if marks_obtained is None:
        raise InvariantViolationError("Marks obtained must be provided when student is present.")

    if marks_obtained < Decimal('0.00'):
        raise InvariantViolationError(f"Marks obtained cannot be negative: {marks_obtained}.")

    if marks_obtained > max_marks:
        raise InvariantViolationError(
            f"Marks obtained ({marks_obtained}) exceeds the assessment maximum ({max_marks})."
        )


def validate_assessment_lock(is_locked: bool) -> None:
    """Prevents modifying marks or definitions when assessment is locked."""
    if is_locked:
        raise InvariantViolationError("Assessment is locked. Historical marks cannot be modified.")


def validate_duplicate_entries(student_identifiers: List[str]) -> None:
    """Ensures no duplicate student rows exist in an upload payload."""
    seen: Set[str] = set()
    duplicates: Set[str] = set()
    for ident in student_identifiers:
        cleaned = ident.strip().upper()
        if cleaned in seen:
            duplicates.add(cleaned)
        seen.add(cleaned)

    if duplicates:
        raise InvariantViolationError(
            f"Duplicate student entries detected in upload payload: {', '.join(sorted(duplicates))}."
        )
