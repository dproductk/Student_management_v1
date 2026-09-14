"""
Correction Service for government-sourced student data.
Governed by ADR-007 (Additive Corrections) and ADR-011 (Context-Owned Corrections).
"""

from django.db import transaction
from common.exceptions import InvariantViolationError, EntityNotFoundError
from apps.students.models import Student, StudentAdmission, StudentDataCorrection
from apps.students.domain.invariants import validate_correction_request


class CorrectionService:
    @staticmethod
    @transaction.atomic
    def apply_student_correction(
        student_id,
        field_name: str,
        new_value: str,
        reason: str,
        approver_user,
        source: str = 'ADMIN_CORRECTION'
    ) -> StudentDataCorrection:
        validate_correction_request(field_name, new_value, reason, approver_user.id if approver_user else None)

        student = Student.objects.filter(id=student_id).first()
        if not student:
            raise EntityNotFoundError("Student not found.")

        # Check where the field lives (Student core or StudentAdmission)
        target_obj = student
        if not hasattr(student, field_name):
            admission = student.admissions.first()
            if admission and hasattr(admission, field_name):
                target_obj = admission
            else:
                raise InvariantViolationError(f"Field '{field_name}' not found on Student record.")

        old_val = str(getattr(target_obj, field_name, '') or '')
        
        # Create additive correction history record
        correction = StudentDataCorrection.objects.create(
            student=student,
            field_name=field_name,
            original_value=old_val,
            corrected_value=new_value,
            correction_reason=reason.strip(),
            approved_by=approver_user,
            source=source
        )

        # Update current authoritative state
        setattr(target_obj, field_name, new_value)
        target_obj.save()

        return correction
