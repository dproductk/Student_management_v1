"""
Student Document lifecycle, versioning, replacement, and sensitive reveal orchestrator.
Fulfills Section 5 of doc/TASKS.md:
- Document types, metadata, and secure upload (Tasks 5.1.1 - 5.1.3)
- Document versioning & supersession lifecycle (Task 5.2.1)
- Controlled allotment-letter replacement/reset (Task 5.2.2)
- Sensitive document masking and restricted access (Task 5.3.1)
- Explicit sensitive reveal with audit logging (Task 5.3.2)
"""

from typing import Optional, List, Dict, Any
from django.db import transaction
from django.utils import timezone
from common.exceptions import InvariantViolationError, StateTransitionError
from apps.documents.models import StudentDocument
from apps.documents.domain.invariants import (
    validate_document_type,
    SENSITIVE_DOCUMENT_TYPES,
)
from apps.documents.services.storage_service import StorageService
from apps.students.models import Student
from apps.audit.models import AuditLog, SensitiveDataAccessLog


class DocumentService:
    """Core domain service for document management."""

    @classmethod
    @transaction.atomic
    def upload_student_document(
        cls,
        student: Student,
        document_type: str,
        file_obj,
        filename: str,
        uploaded_by
    ) -> StudentDocument:
        """
        Uploads and registers a student document.
        If an active document of this type already exists, supersedes it into version history.
        """
        validate_document_type(document_type)

        # Store binary file in object store
        storage_key, checksum, file_size, mime_type = StorageService.store_student_document(
            student_id=str(student.id),
            file_obj=file_obj,
            original_filename=filename
        )

        # Look for existing active document
        current_doc = StudentDocument.objects.filter(
            student=student,
            document_type=document_type,
            version_status='CURRENT'
        ).first()

        next_version = 1
        if current_doc:
            next_version = current_doc.version + 1
            current_doc.version_status = 'SUPERSEDED'

        new_doc = StudentDocument.objects.create(
            student=student,
            document_type=document_type,
            storage_key=storage_key,
            original_filename=filename,
            file_size_bytes=file_size,
            mime_type=mime_type,
            checksum=checksum,
            version=next_version,
            version_status='CURRENT',
            uploaded_by=uploaded_by,
            uploaded_at=timezone.now(),
            verification_status='PENDING'
        )

        if current_doc:
            current_doc.superseded_by = new_doc
            current_doc.save(update_fields=['version_status', 'superseded_by'])

        return new_doc

    @classmethod
    @transaction.atomic
    def replace_allotment_letter(
        cls,
        student: Student,
        file_obj,
        filename: str,
        uploaded_by,
        reason: str
    ) -> StudentDocument:
        """
        Task 5.2.2: Controlled allotment-letter replacement/reset.
        Enforces supersession lifecycle and records mandatory audit log.
        """
        if not reason or not reason.strip():
            raise InvariantViolationError("A mandatory replacement reason must be provided for allotment letter updates.")

        old_doc = StudentDocument.objects.filter(
            student=student,
            document_type='ALLOTMENT_LETTER',
            version_status='CURRENT'
        ).first()

        new_doc = cls.upload_student_document(
            student=student,
            document_type='ALLOTMENT_LETTER',
            file_obj=file_obj,
            filename=filename,
            uploaded_by=uploaded_by
        )

        # Record accountable audit event
        AuditLog.objects.create(
            actor=uploaded_by,
            action="DOCUMENT_REPLACED_ALLOTMENT_LETTER",
            target_type="STUDENT_DOCUMENT",
            target_id=new_doc.id,
            module="documents",
            old_value={"version": old_doc.version, "document_id": str(old_doc.id)} if old_doc else None,
            new_value={"version": new_doc.version, "document_id": str(new_doc.id)},
            reason=reason
        )

        return new_doc

    @classmethod
    @transaction.atomic
    def reveal_sensitive_document(
        cls,
        document: StudentDocument,
        user,
        reason: str,
        ip_address: Optional[str] = None
    ) -> StudentDocument:
        """
        Tasks 5.3.1 & 5.3.2: Controlled explicit sensitive document reveal.
        Checks authorization, verifies mandatory reason, and logs to SensitiveDataAccessLog.
        """
        if document.document_type not in SENSITIVE_DOCUMENT_TYPES:
            # Non-sensitive documents do not require reveal logging
            return document

        # Authorization: Must be staff/admin or the student themselves
        is_own_doc = False
        if hasattr(user, 'student_profile') and user.student_profile and user.student_profile.id == document.student_id:
            is_own_doc = True

        if not user.is_staff and not user.is_superuser and not is_own_doc:
            raise InvariantViolationError("You do not have permission to reveal this sensitive document.")

        # If administrative actor, mandatory reason is enforced
        if not is_own_doc and (not reason or len(reason.strip()) < 5):
            raise InvariantViolationError("A valid business reason (at least 5 characters) is required to access sensitive document.")

        # Log sensitive reveal to immutable audit trail (ADR-015)
        SensitiveDataAccessLog.objects.create(
            accessor=user,
            student_id=document.student_id,
            field_name=document.document_type,
            reason=reason if reason else "Self student access",
            ip_address=ip_address
        )

        return document
