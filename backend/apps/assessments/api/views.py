"""
DRF ViewSets and Views for Assessments & Unit Test Marks module.
"""

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied

from apps.assessments.models import (
    AssessmentType,
    Assessment,
    AssessmentMark,
    AssessmentStatus,
)
from apps.assessments.services.assessment_service import AssessmentService
from apps.assessments.api.serializers import (
    AssessmentTypeSerializer,
    AssessmentSerializer,
    AssessmentMarkSerializer,
    UploadUnitTestMarksSerializer,
    StudentMarkViewSerializer,
)
from common.exceptions import InvariantViolationError


class AssessmentTypeViewSet(viewsets.ModelViewSet):
    queryset = AssessmentType.objects.all()
    serializer_class = AssessmentTypeSerializer
    permission_classes = [IsAuthenticated]


class AssessmentViewSet(viewsets.ModelViewSet):
    queryset = Assessment.objects.all().select_related(
        'assessment_type',
        'academic_year',
        'semester',
        'department',
        'program',
        'scheme_subject__subject',
        'batch',
        'created_by'
    )
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        dept_id = self.request.query_params.get('department')
        if dept_id:
            qs = qs.filter(department_id=dept_id)

        ay_id = self.request.query_params.get('academic_year')
        if ay_id:
            qs = qs.filter(academic_year_id=ay_id)

        sem_id = self.request.query_params.get('semester')
        if sem_id:
            qs = qs.filter(semester_id=sem_id)

        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)

        return qs

    @action(detail=True, methods=['post'], url_path='upload-marks')
    def upload_marks(self, request, pk=None):
        """
        Faculty unit-test marks upload endpoint (Task 10.2.1, 10.2.2).
        Extracts, validates, and persists student mark records.
        """
        assessment = self.get_object()
        serializer = UploadUnitTestMarksSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        marks_data = serializer.validated_data['marks']
        try:
            result = AssessmentService.upload_unit_test_marks(
                assessment_id=str(assessment.id),
                mark_rows=marks_data,
                actor=request.user
            )
            return Response(result, status=status.HTTP_200_OK)
        except InvariantViolationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        """Publishes assessment so marks become visible to students."""
        assessment = self.get_object()
        try:
            published = AssessmentService.publish_assessment(str(assessment.id), actor=request.user)
            return Response(AssessmentSerializer(published).data, status=status.HTTP_200_OK)
        except InvariantViolationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='lock')
    def lock(self, request, pk=None):
        """Permanently locks assessment marks against any further modifications."""
        assessment = self.get_object()
        try:
            locked = AssessmentService.lock_assessment(str(assessment.id), actor=request.user)
            return Response(AssessmentSerializer(locked).data, status=status.HTTP_200_OK)
        except InvariantViolationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='marks')
    def marks(self, request, pk=None):
        """Retrieves all marks recorded for this assessment."""
        assessment = self.get_object()
        marks_qs = AssessmentMark.objects.filter(assessment=assessment).select_related(
            'student', 'entered_by'
        )
        return Response(AssessmentMarkSerializer(marks_qs, many=True).data, status=status.HTTP_200_OK)


class AssessmentMarkViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AssessmentMark.objects.all().select_related(
        'assessment', 'student', 'entered_by'
    )
    serializer_class = AssessmentMarkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        assessment_id = self.request.query_params.get('assessment')
        if assessment_id:
            qs = qs.filter(assessment_id=assessment_id)
        student_id = self.request.query_params.get('student')
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs


class StudentMarksView(APIView):
    """
    Student view endpoint (Task 10.2.3).
    Students can only view their own published or locked assessment marks.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        marks = AssessmentService.get_student_marks(request.user)
        return Response(StudentMarkViewSerializer(marks, many=True).data, status=status.HTTP_200_OK)
