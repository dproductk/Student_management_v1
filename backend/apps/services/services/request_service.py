from typing import Optional, Dict, Any
from django.db import transaction
from django.utils import timezone

from apps.students.models import Student
from apps.documents.models import StudentDocument
from apps.services.models import ServiceRequestType, ServiceRequest, ServiceRequestAudit
from apps.services.domain.invariants import (
    ServiceValidationError,
    validate_service_transition,
    validate_rejection_reason,
    validate_service_document_requirement,
)


class ServiceRequestService:
    """
    Application service managing the complete lifecycle of student service requests.
    Enforces domain invariants, role-based workflows, and accountable audit logging.
    """

    @staticmethod
    def _generate_request_number() -> str:
        """Generates sequential annual request identifiers: SR-YYYY-XXXX."""
        year = timezone.now().year
        count = ServiceRequest.objects.filter(created_at__year=year).count() + 1
        return f"SR-{year}-{count:04d}"

    @staticmethod
    def submit_request(
        student: Student,
        service_type: ServiceRequestType,
        request_data: Optional[Dict[str, Any]] = None,
        document: Optional[StudentDocument] = None,
        priority: str = 'NORMAL',
        actor=None
    ) -> ServiceRequest:
        """
        Submits a new student service request.
        Validates document requirements and records initial audit.
        """
        if not service_type.is_active:
            raise ServiceValidationError(f"Service type '{service_type.name}' is currently inactive.")

        validate_service_document_requirement(service_type, document)

        with transaction.atomic():
            req_num = ServiceRequestService._generate_request_number()
            req = ServiceRequest.objects.create(
                request_number=req_num,
                student=student,
                service_type=service_type,
                status='SUBMITTED',
                priority=priority,
                request_data=request_data or {},
                attached_document=document
            )

            ServiceRequestAudit.objects.create(
                service_request=req,
                actor=actor,
                action='SUBMITTED',
                previous_status=None,
                new_status='SUBMITTED',
                reason='Student service request submitted'
            )

        return req

    @staticmethod
    def assign_request(
        service_request: ServiceRequest,
        assignee_user,
        actor
    ) -> ServiceRequest:
        """Assigns request to a staff member for processing."""
        with transaction.atomic():
            service_request.assigned_to = assignee_user
            service_request.save(update_fields=['assigned_to', 'updated_at'])

            ServiceRequestAudit.objects.create(
                service_request=service_request,
                actor=actor,
                action='ASSIGNED',
                previous_status=service_request.status,
                new_status=service_request.status,
                reason=f"Assigned to {assignee_user.username}"
            )

        return service_request

    @staticmethod
    def process_request(
        service_request: ServiceRequest,
        actor,
        notes: str = ""
    ) -> ServiceRequest:
        """Transitions request to IN_PROGRESS when processing starts."""
        validate_service_transition(service_request.status, 'IN_PROGRESS')

        prev_status = service_request.status
        now = timezone.now()

        with transaction.atomic():
            service_request.status = 'IN_PROGRESS'
            service_request.processed_by = actor
            service_request.processed_at = now
            if notes:
                service_request.resolution_notes = notes
            service_request.save(update_fields=['status', 'processed_by', 'processed_at', 'resolution_notes', 'updated_at'])

            ServiceRequestAudit.objects.create(
                service_request=service_request,
                actor=actor,
                action='IN_PROGRESS',
                previous_status=prev_status,
                new_status='IN_PROGRESS',
                reason=notes or 'Administrative processing commenced'
            )

        return service_request

    @staticmethod
    def approve_request(
        service_request: ServiceRequest,
        actor,
        remarks: str = ""
    ) -> ServiceRequest:
        """Approves a service request."""
        validate_service_transition(service_request.status, 'APPROVED')

        prev_status = service_request.status
        now = timezone.now()

        with transaction.atomic():
            service_request.status = 'APPROVED'
            service_request.processed_by = actor
            service_request.processed_at = now
            if remarks:
                service_request.resolution_notes = remarks
            service_request.save(update_fields=['status', 'processed_by', 'processed_at', 'resolution_notes', 'updated_at'])

            ServiceRequestAudit.objects.create(
                service_request=service_request,
                actor=actor,
                action='APPROVED',
                previous_status=prev_status,
                new_status='APPROVED',
                reason=remarks or 'Approved by administrative authority'
            )

        return service_request

    @staticmethod
    def reject_request(
        service_request: ServiceRequest,
        actor,
        rejection_reason: str
    ) -> ServiceRequest:
        """Rejects a service request with a mandatory reason."""
        validate_service_transition(service_request.status, 'REJECTED')
        validate_rejection_reason(rejection_reason)

        prev_status = service_request.status
        now = timezone.now()

        with transaction.atomic():
            service_request.status = 'REJECTED'
            service_request.processed_by = actor
            service_request.processed_at = now
            service_request.rejection_reason = rejection_reason.strip()
            service_request.save(update_fields=['status', 'processed_by', 'processed_at', 'rejection_reason', 'updated_at'])

            ServiceRequestAudit.objects.create(
                service_request=service_request,
                actor=actor,
                action='REJECTED',
                previous_status=prev_status,
                new_status='REJECTED',
                reason=rejection_reason.strip()
            )

        return service_request

    @staticmethod
    def complete_request(
        service_request: ServiceRequest,
        actor,
        resolution_notes: str = ""
    ) -> ServiceRequest:
        """Finalizes an approved request to COMPLETED status."""
        validate_service_transition(service_request.status, 'COMPLETED')

        prev_status = service_request.status
        now = timezone.now()

        with transaction.atomic():
            service_request.status = 'COMPLETED'
            service_request.processed_by = actor
            service_request.processed_at = now
            if resolution_notes:
                service_request.resolution_notes = resolution_notes.strip()
            service_request.save(update_fields=['status', 'processed_by', 'processed_at', 'resolution_notes', 'updated_at'])

            ServiceRequestAudit.objects.create(
                service_request=service_request,
                actor=actor,
                action='COMPLETED',
                previous_status=prev_status,
                new_status='COMPLETED',
                reason=resolution_notes.strip() or 'Service request completed and resolved'
            )

        return service_request

    @staticmethod
    def cancel_request(
        service_request: ServiceRequest,
        actor,
        reason: str = ""
    ) -> ServiceRequest:
        """Cancels a pending or in-progress request."""
        validate_service_transition(service_request.status, 'CANCELLED')

        prev_status = service_request.status

        with transaction.atomic():
            service_request.status = 'CANCELLED'
            if reason:
                service_request.resolution_notes = f"Cancelled: {reason.strip()}"
            service_request.save(update_fields=['status', 'resolution_notes', 'updated_at'])

            ServiceRequestAudit.objects.create(
                service_request=service_request,
                actor=actor,
                action='CANCELLED',
                previous_status=prev_status,
                new_status='CANCELLED',
                reason=reason.strip() or 'Request cancelled'
            )

        return service_request

    @staticmethod
    def attach_document(
        service_request: ServiceRequest,
        document: StudentDocument,
        actor
    ) -> ServiceRequest:
        """Attaches or updates a supporting document for the service request."""
        validate_service_document_requirement(service_request.service_type, document)

        with transaction.atomic():
            service_request.attached_document = document
            service_request.save(update_fields=['attached_document', 'updated_at'])

            ServiceRequestAudit.objects.create(
                service_request=service_request,
                actor=actor,
                action='DOCUMENT_ATTACHED',
                previous_status=service_request.status,
                new_status=service_request.status,
                reason=f"Attached document {document.original_filename or document.id} ({document.document_type})"
            )

        return service_request
