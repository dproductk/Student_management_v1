"""
Serializers for Student Documents APIs.
Implements sensitive document masking by default per ADR-015.
"""

from rest_framework import serializers
from apps.documents.models import StudentDocument
from apps.documents.domain.invariants import DOCUMENT_TYPES, SENSITIVE_DOCUMENT_TYPES


class StudentDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    reviewed_by_username = serializers.CharField(source='reviewed_by.username', read_only=True)
    is_sensitive = serializers.BooleanField(read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = StudentDocument
        fields = [
            'id',
            'student',
            'document_type',
            'original_filename',
            'file_size_bytes',
            'mime_type',
            'checksum',
            'version',
            'version_status',
            'superseded_by',
            'verification_status',
            'rejection_reason',
            'reviewed_by',
            'reviewed_by_username',
            'reviewed_at',
            'uploaded_by',
            'uploaded_by_username',
            'uploaded_at',
            'is_sensitive',
            'download_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'version', 'version_status', 'superseded_by',
            'checksum', 'file_size_bytes', 'mime_type', 'uploaded_by',
            'uploaded_at', 'created_at', 'updated_at'
        ]

    def get_download_url(self, obj) -> str:
        """
        Task 5.3.1: Sensitive documents do NOT expose direct download URLs by default.
        Access must go through the explicit reveal endpoint.
        """
        if obj.is_sensitive:
            return None
        return f"/api/v1/documents/{obj.id}/download/"


class DocumentUploadSerializer(serializers.Serializer):
    student_id = serializers.UUIDField(required=True)
    document_type = serializers.ChoiceField(choices=[k for k, _ in DOCUMENT_TYPES], required=True)
    file = serializers.FileField(required=True)


class AllotmentLetterReplaceSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    reason = serializers.CharField(required=True, min_length=5)


class DocumentRevealSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)
