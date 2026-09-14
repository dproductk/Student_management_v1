"""
API views for batch import and student onboarding.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from apps.onboarding.models import ImportBatch, ImportStagingRow
from apps.onboarding.api.serializers import (
    ImportBatchSerializer,
    ImportStagingRowSerializer,
    BatchUploadSerializer,
    ConflictResolutionSerializer,
    ExecuteImportSerializer,
)
from apps.onboarding.services.import_service import ImportService
from common.exceptions import InvariantViolationError, StateTransitionError


class ImportBatchViewSet(viewsets.ModelViewSet):
    """
    CRUD and actions for student data import batches.
    DELETE is allowed for every authenticated account and is recorded
    in the internal immutable audit log (audit_log table).
    Deleting a batch removes its staging rows (CASCADE) but preserves
    any Students already migrated to production (matched_student SET_NULL).
    """
    queryset = ImportBatch.objects.all().select_related('academic_year', 'department', 'uploaded_by')
    serializer_class = ImportBatchSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def destroy(self, request, *args, **kwargs):
        batch = self.get_object()

        # Guard against deleting a batch mid-pipeline (race safety)
        if batch.status in ('VALIDATING', 'IMPORTING'):
            return Response(
                {"detail": f"Cannot delete batch while it is {batch.status}. Please wait for it to finish."},
                status=status.HTTP_409_CONFLICT,
            )

        # Snapshot for internal audit trail (before deletion)
        snapshot = ImportBatchSerializer(batch).data
        # Ensure JSON-serializable (UUIDs/datetimes -> strings)
        old_value = {
            "source_file_name": snapshot.get("source_file_name"),
            "source_file_hash": snapshot.get("source_file_hash"),
            "status": snapshot.get("status"),
            "total_rows": snapshot.get("total_rows"),
            "processed_rows": snapshot.get("processed_rows"),
            "error_rows": snapshot.get("error_rows"),
            "academic_year": str(snapshot.get("academic_year")) if snapshot.get("academic_year") else None,
            "department": str(snapshot.get("department")) if snapshot.get("department") else None,
            "uploaded_by": str(snapshot.get("uploaded_by")) if snapshot.get("uploaded_by") else None,
            "uploaded_by_username": snapshot.get("uploaded_by_username"),
            "uploaded_at": str(snapshot.get("uploaded_at")) if snapshot.get("uploaded_at") else None,
        }
        batch_id = batch.id
        file_name = batch.source_file_name
        staging_count = batch.staging_rows.count()

        ip_address = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get("REMOTE_ADDR")

        # Perform deletion (staging rows CASCADE, production Students preserved)
        response = super().destroy(request, *args, **kwargs)

        # Internal audit log — not exposed to regular users, queryable via audit trail
        try:
            from apps.audit.services.audit_service import AuditService
            AuditService.record_audit(
                action="IMPORT_BATCH_DELETED",
                target_type="IMPORT_BATCH",
                module="onboarding",
                actor=request.user,
                target_id=batch_id,
                old_value={**old_value, "staging_rows_deleted": staging_count},
                new_value=None,
                reason=f"{request.user.username} deleted import batch '{file_name}' ({staging_count} staging rows removed, production students preserved)",
                ip_address=ip_address,
            )
        except Exception:
            # Deletion already succeeded; audit failure must not roll it back.
            # Use logging instead of failing the request.
            import logging
            logging.getLogger(__name__).exception("Failed to record IMPORT_BATCH_DELETED audit entry")

        return response

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param.upper())
        dept_param = self.request.query_params.get('department_id')
        if dept_param:
            qs = qs.filter(department_id=dept_param)
        return qs

    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request):
        """
        Upload an Excel file to stage for ingestion.
        """
        serializer = BatchUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_obj = serializer.validated_data['file']
        ay_id = serializer.validated_data.get('academic_year_id')
        dept_id = serializer.validated_data.get('department_id')

        try:
            batch = ImportService.upload_and_stage_excel(
                file_obj=file_obj,
                source_file_name=file_obj.name,
                academic_year_id=ay_id,
                department_id=dept_id,
                uploaded_by=request.user
            )
            return Response(ImportBatchSerializer(batch).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"detail": f"Failed to ingest Excel file: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='validate')
    def validate_batch(self, request, pk=None):
        """
        Run validation, normalization, and deterministic student matching on staged rows.
        """
        batch = self.get_object()
        try:
            batch = ImportService.validate_and_normalize_batch(batch)
            return Response(ImportBatchSerializer(batch).data)
        except StateTransitionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)
        except Exception as e:
            return Response({"detail": f"Validation failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='execute')
    def execute_import(self, request, pk=None):
        """
        Execute production import for validated rows in this batch.
        """
        batch = self.get_object()
        serializer = ExecuteImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            batch = ImportService.execute_production_import(
                batch=batch,
                user=request.user,
                default_program_id=serializer.validated_data.get('default_program_id'),
                default_semester_id=serializer.validated_data.get('default_semester_id'),
                default_scheme_id=serializer.validated_data.get('default_scheme_id'),
                default_batch_id=serializer.validated_data.get('default_batch_id'),
            )
            return Response(ImportBatchSerializer(batch).data)
        except StateTransitionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)
        except Exception as e:
            return Response({"detail": f"Import execution failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='staging-rows')
    def staging_rows(self, request, pk=None):
        """
        List staging rows for this batch with optional status filtering.
        """
        batch = self.get_object()
        rows = batch.staging_rows.all().select_related('matched_student').order_by('row_number')

        status_param = request.query_params.get('status')
        if status_param:
            rows = rows.filter(processing_status=status_param.upper())

        serializer = ImportStagingRowSerializer(rows, many=True)
        return Response(serializer.data)


class ImportStagingRowViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read staging rows and manually resolve conflicts.
    """
    queryset = ImportStagingRow.objects.all().select_related('import_batch', 'matched_student')
    serializer_class = ImportStagingRowSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='resolve')
    def resolve(self, request, pk=None):
        """
        Manually resolve an identity conflict on a staged row.
        """
        row = self.get_object()
        serializer = ConflictResolutionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            resolved_row = ImportService.resolve_staging_conflict(
                staging_row=row,
                resolution_action=serializer.validated_data['action'],
                chosen_student_id=serializer.validated_data.get('chosen_student_id'),
                resolved_by=request.user
            )
            return Response(ImportStagingRowSerializer(resolved_row).data)
        except InvariantViolationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
