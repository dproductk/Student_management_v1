"""
Faculty domain invariants and lifecycle validation rules.
Implements domain integrity guards for Section 7: Faculty & Academic Assignment.
"""

from typing import Optional
from datetime import date
from common.exceptions import InvariantViolationError


def validate_faculty_lifecycle(
    status: str,
    date_of_joining: Optional[date],
    date_of_relieving: Optional[date]
) -> None:
    """
    Validates faculty lifecycle consistency between status and dates.
    """
    if not date_of_joining:
        raise InvariantViolationError("Faculty must have a valid date of joining.")

    if date_of_relieving:
        if date_of_relieving < date_of_joining:
            raise InvariantViolationError(
                f"Date of relieving ({date_of_relieving}) cannot precede date of joining ({date_of_joining})."
            )

    inactive_statuses = {'RESIGNED', 'RETIRED', 'TERMINATED'}
    if status in inactive_statuses and not date_of_relieving:
        raise InvariantViolationError(
            f"Faculty with status '{status}' must specify a valid date of relieving."
        )


def validate_faculty_assignment(
    faculty_status: str,
    academic_year_id,
    semester_academic_year_id,
    batch_academic_year_id=None
) -> None:
    """
    Validates teaching assignment consistency across academic year, semester, and batch.
    """
    if faculty_status != 'ACTIVE':
        raise InvariantViolationError(
            f"Cannot assign subjects to faculty with non-active status '{faculty_status}'."
        )

    if str(semester_academic_year_id) != str(academic_year_id):
        raise InvariantViolationError(
            "Semester does not belong to the specified academic year."
        )

    if batch_academic_year_id and str(batch_academic_year_id) != str(academic_year_id):
        raise InvariantViolationError(
            "Batch academic year does not match the assignment academic year."
        )


def validate_academic_item(item_type: str, title: str, year: Optional[int] = None) -> None:
    """
    Validates faculty academic items (publications, patents, books, awards, etc.).
    """
    if not title or not title.strip():
        raise InvariantViolationError("Academic item title cannot be empty.")

    valid_types = {
        'PUBLICATION',
        'PATENT',
        'BOOK',
        'AWARD',
        'MEMBERSHIP',
        'CONSULTANCY',
        'GUIDANCE'
    }
    if item_type not in valid_types:
        raise InvariantViolationError(f"Invalid academic item type: '{item_type}'. Must be one of {valid_types}.")

    if year is not None:
        if year < 1950 or year > 2100:
            raise InvariantViolationError(f"Academic item year must be between 1950 and 2100. Got: {year}.")
