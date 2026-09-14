"""
API ViewSets for Verification workflow and decision processing.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.verification.models import VerificationRequest, VerificationDecision
from apps.verification.api.serializers import (
    VerificationRequestSerializer,
    VerificationDecisionSerializer,
    VerificationSubmitSerializer,
    VerificationDecisionActionSerializer,
    VerificationResubmitSerializer,
)
from apps.verification.services.verification_service import VerificationService
from apps.students.models import Student
from common.exceptions import InvariantViolationError, StateTransitionError


class VerificationRequestViewSet(viewsets.ModelViewSet):
    """
    CRUD and review actions for Verification Requests.
    """
    queryset = VerificationRequest.objects.all().select_related('student', 'submitted_by').prefetch_related('decisions', 'decisions__reviewer')
    serializer_class = VerificationRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        student_id = self.request.query_params.get('student_id')
        if student_id:
            qs = qs.filter(student_id=student_id)

        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param.upper())

        entity_type = self.request.query_params.get('entity_type')
        if entity_type:
            qs = qs.filter(entity_type=entity_type.upper())

        return qs

    @action(detail=False, methods=['post'], url_path='submit')
    def submit(self, request):
        """
        Submit a new piece of information, document, or correction for verification.
        """
        serializer = VerificationSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student_id = serializer.validated_data['student_id']
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({"detail": f"Student {student_id} not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            verif_req = VerificationService.submit_for_verification(
                student=student,
                entity_type=serializer.validated_data['entity_type'],
                entity_id=serializer.validated_data.get('entity_id'),
                field_name=serializer.validated_data.get('field_name'),
                submitted_value=serializer.validated_data.get('submitted_value'),
                submitted_by=request.user
            )
            return Response(VerificationRequestSerializer(verif_req).data, status=status.HTTP_201_CREATED)
        except InvariantViolationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='decide')
    def decide(self, request, pk=None):
        """
        Record a decision (APPROVED, REJECTED, NEEDS_CORRECTION).
        Accountable actor identified from request.user.
        """
        verif_req = self.get_object()
        serializer = VerificationDecisionActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            req_obj, dec_obj = VerificationService.record_decision(
                verification_request=verif_req,
                decision=serializer.validated_data['decision'],
                reviewer=request.user,
                rejection_reason=serializer.validated_data.get('rejection_reason'),
                notes=serializer.validated_data.get('notes')
            )
            req_obj = VerificationRequest.objects.prefetch_related('decisions', 'decisions__reviewer').get(id=req_obj.id)
            return Response(VerificationRequestSerializer(req_obj).data, status=status.HTTP_200_OK)
        except InvariantViolationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except StateTransitionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)

    @action(detail=True, methods=['post'], url_path='resubmit')
    def resubmit(self, request, pk=None):
        """
        Re-submit a rejected or needs-correction item with updated data.
        """
        verif_req = self.get_object()
        serializer = VerificationResubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_req = VerificationService.resubmit_correction(
                verification_request=verif_req,
                new_submitted_value=serializer.validated_data.get('new_submitted_value'),
                new_entity_id=serializer.validated_data.get('new_entity_id'),
                submitted_by=request.user
            )
            return Response(VerificationRequestSerializer(updated_req).data, status=status.HTTP_200_OK)
        except InvariantViolationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='audit-trail')
    def audit_trail(self, request):
        """
        Comprehensive audit trail of all verification decisions and review activities.
        Accessible to Verification Officers and Administrative Head.
        """
        decisions = VerificationDecision.objects.select_related(
            'verification_request__student', 'reviewer'
        ).order_by('-reviewed_at')[:150]

        data = []
        for d in decisions:
            student = getattr(d.verification_request, 'student', None) if d.verification_request else None
            data.append({
                'id': str(d.id),
                'action': d.decision,
                'candidate_name': student.candidate_name if student else 'Unknown',
                'application_id': student.application_id if student else '',
                'entity_type': d.verification_request.entity_type if d.verification_request else '',
                'field_name': d.verification_request.field_name if d.verification_request else '',
                'version': d.version,
                'actor': (d.reviewer.get_full_name() or d.reviewer.username) if d.reviewer else 'System',
                'actor_role': 'Verification Officer',
                'rejection_reason': d.rejection_reason or '',
                'notes': d.notes or '',
                'timestamp': d.reviewed_at.isoformat() if d.reviewed_at else None,
            })
        return Response(data)
