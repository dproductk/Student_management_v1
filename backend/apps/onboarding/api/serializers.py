"""
Serializers for student onboarding and batch import APIs.
"""

from rest_framework import serializers
from apps.onboarding.models import ImportBatch, ImportStagingRow
from apps.students.api.serializers import StudentListSerializer


class ImportBatchSerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.label', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = ImportBatch
        fields = [
            'id',
            'source_file_name',
            'source_file_hash',
            'source_type',
            'academic_year',
            'academic_year_name',
            'department',
            'department_name',
            'status',
            'total_rows',
            'processed_rows',
            'error_rows',
            'uploaded_by',
            'uploaded_by_username',
            'uploaded_at',
            'completed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'source_file_hash', 'status', 'total_rows', 'processed_rows',
            'error_rows', 'uploaded_by', 'uploaded_at', 'completed_at',
            'created_at', 'updated_at'
        ]


class ImportStagingRowSerializer(serializers.ModelSerializer):
    matched_student_detail = StudentListSerializer(source='matched_student', read_only=True)

    class Meta:
        model = ImportStagingRow
        fields = [
            'id',
            'import_batch',
            'row_number',
            'raw_data',
            'normalized_data',
            'validation_errors',
            'processing_status',
            'matched_student',
            'matched_student_detail',
            'match_type',
            'conflict_details',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BatchUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    academic_year_id = serializers.UUIDField(required=False, allow_null=True)
    department_id = serializers.UUIDField(required=False, allow_null=True)


class ConflictResolutionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['LINK_TO_STUDENT', 'FORCE_AS_NEW', 'SKIP'])
    chosen_student_id = serializers.UUIDField(required=False, allow_null=True)


class ExecuteImportSerializer(serializers.Serializer):
    default_program_id = serializers.UUIDField(required=False, allow_null=True)
    default_semester_id = serializers.UUIDField(required=False, allow_null=True)
    default_scheme_id = serializers.UUIDField(required=False, allow_null=True)
    default_batch_id = serializers.UUIDField(required=False, allow_null=True)
