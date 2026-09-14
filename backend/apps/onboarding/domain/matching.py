"""
Deterministic Identity Matching Precedence (ADR-003).
Precedence rules:
1. Application ID (Primary Government allotment key)
2. Enrollment Number (Institutional register)
3. State Board Enrollment Number
Detects conflicts when identifiers map to different existing students.
"""

from typing import Tuple, Optional, Dict, Any
from apps.students.models import Student


def match_staging_student(normalized_data: dict) -> Tuple[str, Optional[Student], Optional[Dict[str, Any]]]:
    """
    Evaluate deterministic identity matching rules against the database.
    Returns:
        (match_type, matched_student, conflict_details)
        match_type is one of: 'APPLICATION_ID', 'ENROLLMENT_NO', 'BOARD_ENROLLMENT_NO', 'NEW', 'CONFLICT'
    """
    app_id = normalized_data.get('application_id')
    enr_no = normalized_data.get('enrollment_no')
    brd_no = normalized_data.get('board_enrollment_no')

    student_by_app = Student.objects.filter(application_id=app_id).first() if app_id else None
    student_by_enr = Student.objects.filter(enrollment_no=enr_no).first() if enr_no else None
    student_by_brd = Student.objects.filter(board_enrollment_no=brd_no).first() if brd_no else None

    # Check for conflict: if two identifiers point to DIFFERENT students
    matched_students = {s for s in [student_by_app, student_by_enr, student_by_brd] if s is not None}
    if len(matched_students) > 1:
        conflict_info = {
            'message': 'Incoming identifiers point to different existing student records in the database.',
            'matched_student_ids': [str(s.id) for s in matched_students],
            'application_id': app_id,
            'enrollment_no': enr_no,
            'board_enrollment_no': brd_no,
        }
        return 'CONFLICT', None, conflict_info

    # 1. Precedence 1: Application ID
    if student_by_app:
        return 'APPLICATION_ID', student_by_app, None

    # 2. Precedence 2: Enrollment Number
    if student_by_enr:
        return 'ENROLLMENT_NO', student_by_enr, None

    # 3. Precedence 3: Board Enrollment Number
    if student_by_brd:
        return 'BOARD_ENROLLMENT_NO', student_by_brd, None

    # 4. No match found: Treat as new student
    return 'NEW', None, None
