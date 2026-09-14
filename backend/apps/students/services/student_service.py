"""
Service layer for student lifecycle, demographic records, sensitive reveal, and enrollments.
"""

from django.db import transaction
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from common.exceptions import InvariantViolationError, EntityNotFoundError
from common.security import (
    encrypt_sensitive_value,
    decrypt_sensitive_value,
    mask_aadhaar,
    mask_bank_account,
)
from apps.audit.models import SensitiveDataAccessLog
from apps.identity.services.role_service import RoleService
from apps.academic.models import AcademicYear, Semester, Department, Program, Batch, Scheme
from apps.students.models import (
    Student,
    StudentAdmission,
    StudentAddress,
    StudentCategory,
    StudentBankAccount,
    StudentEnrollment,
)


class StudentService:
    @staticmethod
    @transaction.atomic
    def create_student(
        candidate_name: str,
        gender: str,
        date_of_birth,
        enrollment_no: str = None,
        application_id: str = None,
        board_enrollment_no: str = None,
        aadhaar_number: str = None,
        created_by=None,
        **kwargs
    ) -> Student:
        aadhaar_enc = encrypt_sensitive_value(aadhaar_number) if aadhaar_number else None
        aadhaar_msk = mask_aadhaar(aadhaar_number) if aadhaar_number else None

        student = Student.objects.create(
            candidate_name=candidate_name.strip(),
            gender=gender.upper(),
            date_of_birth=date_of_birth,
            enrollment_no=enrollment_no.strip() if enrollment_no else None,
            application_id=application_id.strip() if application_id else None,
            board_enrollment_no=board_enrollment_no.strip() if board_enrollment_no else None,
            aadhaar_encrypted=aadhaar_enc,
            aadhaar_masked=aadhaar_msk,
            created_by=created_by,
            **kwargs
        )
        return student

    @staticmethod
    @transaction.atomic
    def set_bank_account(
        student_id,
        account_number: str,
        bank_name: str,
        branch_name: str = None,
        ifsc_code: str = None,
        account_holder_name: str = None,
    ) -> StudentBankAccount:
        student = Student.objects.filter(id=student_id).first()
        if not student:
            raise EntityNotFoundError("Student not found.")

        acc_enc = encrypt_sensitive_value(account_number)
        acc_msk = mask_bank_account(account_number)

        bank_acc, _ = StudentBankAccount.objects.update_or_create(
            student=student,
            defaults={
                'bank_name': bank_name,
                'branch_name': branch_name,
                'account_number_encrypted': acc_enc,
                'account_number_masked': acc_msk,
                'ifsc_code': ifsc_code,
                'account_holder_name': account_holder_name or student.candidate_name,
            }
        )
        return bank_acc

    @staticmethod
    @transaction.atomic
    def reveal_sensitive_field(student_id, field_name: str, requesting_user, reason: str, ip_address: str = None) -> str:
        """
        Reveal cleartext sensitive data (Aadhaar or Bank Account).
        Enforces permission 'students.reveal_sensitive' and logs access to SensitiveDataAccessLog (ADR-015).
        """
        if not requesting_user or not requesting_user.is_authenticated:
            raise PermissionDenied("Authentication required to reveal sensitive data.")

        if not requesting_user.is_superuser and not RoleService.user_has_permission(requesting_user, 'students.reveal_sensitive'):
            raise PermissionDenied("You do not possess the required permission 'students.reveal_sensitive'.")

        if not reason or not reason.strip():
            raise InvariantViolationError("A mandatory business justification reason is required to reveal sensitive data.")

        student = Student.objects.filter(id=student_id).first()
        if not student:
            raise EntityNotFoundError("Student not found.")

        cleartext = ""
        if field_name == 'aadhaar':
            if not student.aadhaar_encrypted:
                return ""
            cleartext = decrypt_sensitive_value(student.aadhaar_encrypted)
        elif field_name == 'bank_account':
            bank_acc = getattr(student, 'bank_account', None)
            if not bank_acc or not bank_acc.account_number_encrypted:
                return ""
            cleartext = decrypt_sensitive_value(bank_acc.account_number_encrypted)
        else:
            raise InvariantViolationError(f"Field '{field_name}' is not an audited sensitive field.")

        # Log access audit
        SensitiveDataAccessLog.objects.create(
            accessor=requesting_user,
            student_id=student.id,
            field_name=field_name,
            reason=reason.strip(),
            ip_address=ip_address
        )

        return cleartext

    @staticmethod
    @transaction.atomic
    def enroll_student(
        student_id,
        academic_year_id,
        semester_id,
        department_id,
        program_id,
        batch_id,
        scheme_id,
        created_by=None
    ) -> StudentEnrollment:
        student = Student.objects.filter(id=student_id).first()
        if not student:
            raise EntityNotFoundError("Student not found.")
        ay = AcademicYear.objects.filter(id=academic_year_id).first()
        sem = Semester.objects.filter(id=semester_id, academic_year=ay).first()
        dept = Department.objects.filter(id=department_id).first()
        prog = Program.objects.filter(id=program_id, department=dept).first()
        batch = Batch.objects.filter(id=batch_id, department=dept, academic_year=ay).first()
        scheme = Scheme.objects.filter(id=scheme_id, program=prog).first()

        if not all([ay, sem, dept, prog, batch, scheme]):
            raise InvariantViolationError("Invalid academic references for enrollment.")

        enrollment, created = StudentEnrollment.objects.get_or_create(
            student=student,
            academic_year=ay,
            semester=sem,
            defaults={
                'department': dept,
                'program': prog,
                'batch': batch,
                'scheme': scheme,
                'status': 'ACTIVE',
                'created_by': created_by
            }
        )
        return enrollment
