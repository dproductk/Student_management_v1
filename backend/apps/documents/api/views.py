"""
API views for Student Documents management.
Enforces controlled access, versioning, allotment-letter replacement,
and ADR-015 sensitive document reveal boundaries.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.http import FileResponse, Http404

from apps.documents.models import StudentDocument
from apps.documents.api.serializers import (
    StudentDocumentSerializer,
    DocumentUploadSerializer,
    AllotmentLetterReplaceSerializer,
    DocumentRevealSerializer,
)
from apps.documents.services.document_service import DocumentService
from apps.documents.services.storage_service import StorageService
from apps.students.models import Student
from common.exceptions import InvariantViolationError


class StudentDocumentViewSet(viewsets.ModelViewSet):
    """
    CRUD and controlled operations for student documents.
    """
    queryset = StudentDocument.objects.all().select_related('student', 'uploaded_by', 'reviewed_by')
    serializer_class = StudentDocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = super().get_queryset()
        student_id = self.request.query_params.get('student_id')
        if student_id:
            qs = qs.filter(student_id=student_id)

        doc_type = self.request.query_params.get('document_type')
        if doc_type:
            qs = qs.filter(document_type=doc_type.upper())

        include_superseded = self.request.query_params.get('include_superseded', 'false').lower() == 'true'
        if not include_superseded:
            qs = qs.filter(version_status='CURRENT')

        return qs

    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request):
        """
        Upload a document for a student. Automatically increments version if replacing.
        """
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student_id = serializer.validated_data['student_id']
        doc_type = serializer.validated_data['document_type']
        file_obj = serializer.validated_data['file']

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({"detail": f"Student {student_id} not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            doc = DocumentService.upload_student_document(
                student=student,
                document_type=doc_type,
                file_obj=file_obj,
                filename=file_obj.name,
                uploaded_by=request.user
            )
            return Response(StudentDocumentSerializer(doc).data, status=status.HTTP_201_CREATED)
        except InvariantViolationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        """
        Download document binary.
        Blocked for sensitive documents (Aadhaar, Bank) unless accessed via reveal endpoint (ADR-015).
        """
        doc = self.get_object()

        if doc.is_sensitive:
            return Response(
                {"detail": "Access restricted. Sensitive documents require explicit reveal via /reveal/ endpoint (ADR-015)."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            stream = StorageService.get_document_stream(doc.storage_key)
            return FileResponse(
                stream,
                content_type=doc.mime_type or 'application/octet-stream',
                as_attachment=True,
                filename=doc.original_filename or f"doc_{doc.id}"
            )
        except FileNotFoundError:
            raise Http404("Document binary file not found in storage.")

    @action(detail=True, methods=['post'], url_path='reveal')
    def reveal(self, request, pk=None):
        """
        Explicit reveal of sensitive document (Aadhaar, Bank).
        Performs permission verification, mandatory reason check, records SensitiveDataAccessLog,
        and returns file stream.
        """
        doc = self.get_object()
        serializer = DocumentRevealSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reason = serializer.validated_data.get('reason', '')
        ip_address = request.META.get('REMOTE_ADDR')

        try:
            DocumentService.reveal_sensitive_document(
                document=doc,
                user=request.user,
                reason=reason,
                ip_address=ip_address
            )

            stream = StorageService.get_document_stream(doc.storage_key)
            return FileResponse(
                stream,
                content_type=doc.mime_type or 'application/octet-stream',
                as_attachment=True,
                filename=doc.original_filename or f"doc_{doc.id}"
            )
        except InvariantViolationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except FileNotFoundError:
            raise Http404("Document binary file not found in storage.")

    @action(detail=False, methods=['post'], url_path='students/(?P<student_id>[^/.]+)/allotment-letter/replace')
    def replace_allotment_letter(self, request, student_id=None):
        """
        Task 5.2.2: Controlled allotment-letter replacement/reset with mandatory audit reason.
        """
        serializer = AllotmentLetterReplaceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

        file_obj = serializer.validated_data['file']
        reason = serializer.validated_data['reason']

        try:
            new_doc = DocumentService.replace_allotment_letter(
                student=student,
                file_obj=file_obj,
                filename=file_obj.name,
                uploaded_by=request.user,
                reason=reason
            )
            return Response(StudentDocumentSerializer(new_doc).data, status=status.HTTP_201_CREATED)
        except InvariantViolationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='history')
    def history(self, request, pk=None):
        """
        Retrieve complete version history for this document.
        """
        doc = self.get_object()
        all_versions = StudentDocument.objects.filter(
            student_id=doc.student_id,
            document_type=doc.document_type
        ).order_by('-version')
        return Response(StudentDocumentSerializer(all_versions, many=True).data)
