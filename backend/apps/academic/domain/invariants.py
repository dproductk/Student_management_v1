"""
Domain invariants and business validation rules for Academic Foundation.
"""

from common.exceptions import InvariantViolationError


def validate_academic_year_dates(start_date, end_date):
    """Ensure academic year end_date is strictly after start_date."""
    if start_date and end_date and end_date <= start_date:
        raise InvariantViolationError("Academic year end date must be strictly after start date.")


def validate_semester_dates(start_date, end_date):
    """Ensure semester end_date is strictly after start_date if both are provided."""
    if start_date and end_date and end_date <= start_date:
        raise InvariantViolationError("Semester end date must be strictly after start date.")


def validate_scheme_subject_marks(max_marks, passing_marks, max_internal_marks=None, passing_internal_marks=None):
    """Validate subject credit, maximum, and passing mark distributions."""
    if max_marks <= 0:
        raise InvariantViolationError("Maximum marks must be greater than zero.")
    if passing_marks < 0 or passing_marks > max_marks:
        raise InvariantViolationError("Passing marks must be between 0 and maximum marks.")
    
    if max_internal_marks is not None:
        if max_internal_marks < 0 or max_internal_marks > max_marks:
            raise InvariantViolationError("Maximum internal marks cannot exceed total maximum marks.")
        if passing_internal_marks is not None:
            if passing_internal_marks < 0 or passing_internal_marks > max_internal_marks:
                raise InvariantViolationError("Passing internal marks must be between 0 and maximum internal marks.")


def validate_intake_capacities(sanctioned_intake, actual_intake=None):
    """Validate intake limits."""
    if sanctioned_intake < 0:
        raise InvariantViolationError("Sanctioned intake capacity cannot be negative.")
    if actual_intake is not None and actual_intake < 0:
        raise InvariantViolationError("Actual intake count cannot be negative.")
