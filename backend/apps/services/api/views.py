from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q

from apps.services.models import ServiceRequestType, ServiceRequest, ServiceRequestAudit
from apps.services.api.serializers import (
    ServiceRequestTypeSerializer,
    ServiceRequestSerializer,
    ServiceRequestAuditSerializer,
    SubmitServiceRequestSerializer,
)
from apps.services.services.request_service import ServiceRequestService
from apps.services.domain.invariants import (
    ServiceValidationError,
    InvalidServiceStateTransitionError,
    ServicePermissionDeniedError,
)
from apps.students.models import Student
from apps.documents.models import StudentDocument


class ServiceRequestTypeViewSet(viewsets.ModelViewSet):
    """
    CRUD management for institutional service request types.
    """
    queryset = ServiceRequestType.objects.all()
    serializer_class = ServiceRequestTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ('true', '1'))
        return qs


class ServiceRequestViewSet(viewsets.ModelViewSet):
    """
    Manages student administrative service requests.
    Enforces student isolation and staff workflow processing.
    """
    queryset = ServiceRequest.objects.all().select_related(
        'student', 'service_type', 'attached_document', 'assigned_to', 'processed_by'
    ).prefetch_related('audits__actor')
    serializer_class = ServiceRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        # Student scoping: If user is linked to a student profile, restrict to own requests
        student_id = self.request.query_params.get('student')
        if student_id:
            qs = qs.filter(student_id=student_id)
        elif hasattr(user, 'student_profile') and user.student_profile:
            qs = qs.filter(student=user.student_profile)

        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param.upper())

        service_type_id = self.request.query_params.get('service_type')
        if service_type_id:
            qs = qs.filter(service_type_id=service_type_id)

        priority = self.request.query_params.get('priority')
        if priority:
            qs = qs.filter(priority=priority.upper())

        return qs

    @action(detail=False, methods=['post'], url_path='submit')
    def submit_request(self, request):
        """Students submit a new service request."""
        serializer = SubmitServiceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        student = get_object_or_404(Student, id=data['student'])
        service_type = get_object_or_404(ServiceRequestType, id=data['service_type'])
        doc_id = data.get('document_id')
        document = get_object_or_404(StudentDocument, id=doc_id) if doc_id else None

        try:
            req = ServiceRequestService.submit_request(
                student=student,
                service_type=service_type,
                request_data=data.get('request_data', {}),
                document=document,
                priority=data.get('priority', 'NORMAL'),
                actor=request.user
            )
            return Response(ServiceRequestSerializer(req).data, status=status.HTTP_201_CREATED)
        except ServiceValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='process')
    def process_request(self, request, pk=None):
        """Staff user begins processing request (SUBMITTED -> IN_PROGRESS)."""
        req = self.get_object()
        notes = request.data.get('notes', '')
        try:
            updated = ServiceRequestService.process_request(req, actor=request.user, notes=notes)
            return Response(ServiceRequestSerializer(updated).data, status=status.HTTP_200_OK)
        except (InvalidServiceStateTransitionError, ServiceValidationError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_request(self, request, pk=None):
        """Staff user approves request (IN_PROGRESS -> APPROVED)."""
        req = self.get_object()
        remarks = request.data.get('remarks', '')
        try:
            updated = ServiceRequestService.approve_request(req, actor=request.user, remarks=remarks)
            return Response(ServiceRequestSerializer(updated).data, status=status.HTTP_200_OK)
        except (InvalidServiceStateTransitionError, ServiceValidationError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject_request(self, request, pk=None):
        """Staff user rejects request with mandatory reason (IN_PROGRESS -> REJECTED)."""
        req = self.get_object()
        rejection_reason = request.data.get('rejection_reason', '')
        try:
            updated = ServiceRequestService.reject_request(req, actor=request.user, rejection_reason=rejection_reason)
            return Response(ServiceRequestSerializer(updated).data, status=status.HTTP_200_OK)
        except (InvalidServiceStateTransitionError, ServiceValidationError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='complete')
    def complete_request(self, request, pk=None):
        """Staff user finalizes request (APPROVED -> COMPLETED)."""
        req = self.get_object()
        resolution_notes = request.data.get('resolution_notes', '')
        try:
            updated = ServiceRequestService.complete_request(req, actor=request.user, resolution_notes=resolution_notes)
            return Response(ServiceRequestSerializer(updated).data, status=status.HTTP_200_OK)
        except (InvalidServiceStateTransitionError, ServiceValidationError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_request(self, request, pk=None):
        """Student or staff user cancels request."""
        req = self.get_object()
        reason = request.data.get('reason', '')
        try:
            updated = ServiceRequestService.cancel_request(req, actor=request.user, reason=reason)
            return Response(ServiceRequestSerializer(updated).data, status=status.HTTP_200_OK)
        except (InvalidServiceStateTransitionError, ServiceValidationError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='attach-document')
    def attach_document(self, request, pk=None):
        """Attaches supporting StudentDocument."""
        req = self.get_object()
        document_id = request.data.get('document_id')
        if not document_id:
            return Response({'detail': 'document_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        document = get_object_or_404(StudentDocument, id=document_id)
        try:
            updated = ServiceRequestService.attach_document(req, document=document, actor=request.user)
            return Response(ServiceRequestSerializer(updated).data, status=status.HTTP_200_OK)
        except ServiceValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='my-requests')
    def my_requests(self, request):
        """Returns requests belonging to the authenticated student."""
        student_id = request.query_params.get('student_id')
        if student_id:
            qs = self.queryset.filter(student_id=student_id)
        elif hasattr(request.user, 'student_profile') and request.user.student_profile:
            qs = self.queryset.filter(student=request.user.student_profile)
        else:
            qs = self.queryset.none()

        return Response(ServiceRequestSerializer(qs, many=True).data, status=status.HTTP_200_OK)


class ServiceRequestAuditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only audit log of all service request workflow events.
    """
    queryset = ServiceRequestAudit.objects.all().select_related('service_request', 'actor')
    serializer_class = ServiceRequestAuditSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        request_id = self.request.query_params.get('request_id')
        if request_id:
            qs = qs.filter(service_request_id=request_id)
        return qs
