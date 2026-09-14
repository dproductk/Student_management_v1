"""
Verification Service Orchestrator.
Fulfills Section 6 of doc/TASKS.md:
- Verification submission, pending state, and state machine (Tasks 6.1.1, 6.1.2)
- Review, approval, rejection, and needs-correction decisions (Tasks 6.1.3, 6.1.4)
- Student record correction propagation upon approval (Task 6.2.1)
- Accountable-actor audit and decision history (Task 6.2.2)
"""

from typing import Tuple, Optional, List, Dict, Any
from django.db import transaction
from django.utils import timezone

from apps.verification.models import VerificationRequest, VerificationDecision, VerificationRequirement
from apps.verification.domain.invariants import (
    validate_decision_payload,
    validate_entity_type,
)
from apps.students.models import Student
from apps.students.services.correction_service import CorrectionService
from apps.documents.models import StudentDocument
from apps.audit.models import AuditLog
from common.exceptions import InvariantViolationError, StateTransitionError


class VerificationService:
    """Core domain logic for verification workflow and decision processing."""

    @classmethod
    @transaction.atomic
    def submit_for_verification(
        cls,
        student: Student,
        entity_type: str,
        entity_id: Optional[str] = None,
        field_name: Optional[str] = None,
        submitted_value: Optional[str] = None,
        submitted_by = None
    ) -> VerificationRequest:
        """
        Task 6.1.2: Submits an item for administrative verification in PENDING state.
        """
        validate_entity_type(entity_type)

        req = VerificationRequest.objects.create(
            student=student,
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            submitted_value=submitted_value,
            status='PENDING',
            current_version=1,
            submitted_by=submitted_by,
            submitted_at=timezone.now()
        )

        AuditLog.objects.create(
            actor=submitted_by,
            action="VERIFICATION_SUBMITTED",
            target_type="VERIFICATION_REQUEST",
            target_id=req.id,
            module="verification",
            new_value={"entity_type": entity_type, "field_name": field_name, "submitted_value": submitted_value},
            reason="Submitted for administrative verification"
        )

        return req

    @classmethod
    @transaction.atomic
    def record_decision(
        cls,
        verification_request: VerificationRequest,
        decision: str,
        reviewer,
        rejection_reason: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[VerificationRequest, VerificationDecision]:
        """
        Tasks 6.1.3, 6.1.4, 6.2.1, 6.2.2:
        Record an immutable decision, update request status, propagate approved student record updates,
        and write accountable audit trails.
        """
        validate_decision_payload(decision, rejection_reason)

        # 1. Create Immutable Verification Decision History Record (Task 6.2.2)
        dec = VerificationDecision.objects.create(
            verification_request=verification_request,
            version=verification_request.current_version,
            decision=decision,
            reviewer=reviewer,
            reviewed_at=timezone.now(),
            rejection_reason=rejection_reason.strip() if rejection_reason else None,
            notes=notes.strip() if notes else None
        )

        # 2. Transition Verification Request State
        old_status = verification_request.status
        verification_request.status = decision
        verification_request.save(update_fields=['status', 'updated_at'])

        # 3. Propagate to Owned Module Boundaries
        if decision == 'APPROVED':
            # Task 6.2.1: Approved correction -> update student record via Student Management
            if verification_request.entity_type in ['GOVERNMENT_CORRECTION', 'PERSONAL_INFO', 'ADDRESS'] and verification_request.field_name:
                CorrectionService.apply_student_correction(
                    student_id=verification_request.student_id,
                    field_name=verification_request.field_name,
                    new_value=verification_request.submitted_value or '',
                    reason=notes or f"Approved via Verification Request {verification_request.id}",
                    approver_user=reviewer,
                    source='VERIFICATION_APPROVED'
                )

            # Document verification update
            if verification_request.entity_type == 'DOCUMENT' and verification_request.entity_id:
                doc = StudentDocument.objects.filter(id=verification_request.entity_id).first()
                if doc:
                    doc.verification_status = 'APPROVED'
                    doc.reviewed_by = reviewer
                    doc.reviewed_at = timezone.now()
                    doc.save(update_fields=['verification_status', 'reviewed_by', 'reviewed_at'])

        elif decision in ['REJECTED', 'NEEDS_CORRECTION']:
            # Update Document if applicable
            if verification_request.entity_type == 'DOCUMENT' and verification_request.entity_id:
                doc = StudentDocument.objects.filter(id=verification_request.entity_id).first()
                if doc:
                    doc.verification_status = decision
                    doc.rejection_reason = rejection_reason
                    doc.reviewed_by = reviewer
                    doc.reviewed_at = timezone.now()
                    doc.save(update_fields=['verification_status', 'rejection_reason', 'reviewed_by', 'reviewed_at'])

        # 4. Accountable-Actor Audit Log (Task 6.2.2)
        AuditLog.objects.create(
            actor=reviewer,
            action=f"VERIFICATION_{decision}",
            target_type="VERIFICATION_REQUEST",
            target_id=verification_request.id,
            module="verification",
            old_value={"status": old_status, "version": dec.version},
            new_value={"status": decision, "version": dec.version},
            reason=rejection_reason or notes or f"Decision {decision} made by reviewer"
        )

        return verification_request, dec

    @classmethod
    @transaction.atomic
    def resubmit_correction(
        cls,
        verification_request: VerificationRequest,
        new_submitted_value: Optional[str] = None,
        new_entity_id: Optional[str] = None,
        submitted_by = None
    ) -> VerificationRequest:
        """
        Task 6.1.4: Re-submission after rejection or needs_correction.
        Increments current_version, transitions back to PENDING.
        """
        if verification_request.status not in ['REJECTED', 'NEEDS_CORRECTION']:
            raise InvariantViolationError("Only rejected or needs-correction items can be re-submitted.")

        verification_request.current_version += 1
        verification_request.status = 'PENDING'
        if new_submitted_value is not None:
            verification_request.submitted_value = new_submitted_value
        if new_entity_id is not None:
            verification_request.entity_id = new_entity_id
        if submitted_by:
            verification_request.submitted_by = submitted_by

        verification_request.submitted_at = timezone.now()
        verification_request.save()

        AuditLog.objects.create(
            actor=submitted_by,
            action="VERIFICATION_RESUBMITTED",
            target_type="VERIFICATION_REQUEST",
            target_id=verification_request.id,
            module="verification",
            new_value={"version": verification_request.current_version, "submitted_value": verification_request.submitted_value},
            reason=f"Re-submitted correction v{verification_request.current_version}"
        )

        return verification_request
