"""
Documents bounded context models.
Implements Deliverable D.6 of DATABASE_ARCHITECTURE.md:
Student Documents and Faculty Documents with versioning, supersession,
and ADR-015 sensitive document classification.
"""

from django.db import models
from django.utils import timezone
from common.models import TimeStampedUUIDModel
from apps.documents.domain.invariants import (
    DOCUMENT_TYPES,
    SENSITIVE_DOCUMENT_TYPES,
    VERSION_STATUS_CHOICES,
    VERIFICATION_STATUS_CHOICES,
    validate_document_type,
    validate_version_status,
    validate_verification_status,
)


class StudentDocument(TimeStampedUUIDModel):
    """
    Physical table: 'student_documents'.
    Tracks uploaded student document metadata, versions, verification, and storage keys.
    Actual document binaries are stored in object storage / external file store.
    """
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='documents',
        db_column='student_id'
    )
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    storage_key = models.CharField(max_length=500, help_text="Object storage path/key")
    original_filename = models.CharField(max_length=500, null=True, blank=True)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, null=True, blank=True)
    checksum = models.CharField(max_length=128, null=True, blank=True, help_text="SHA-256 digest")
    version = models.IntegerField(default=1)
    version_status = models.CharField(max_length=20, choices=VERSION_STATUS_CHOICES, default='CURRENT')
    superseded_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='superseded_versions',
        db_column='superseded_by_id'
    )
    verification_status = models.CharField(max_length=30, choices=VERIFICATION_STATUS_CHOICES, default='PENDING')
    rejection_reason = models.TextField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        'identity.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_student_documents',
        db_column='reviewed_by'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    uploaded_by = models.ForeignKey(
        'identity.User',
        on_delete=models.RESTRICT,
        related_name='uploaded_student_documents',
        db_column='uploaded_by'
    )
    uploaded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'student_documents'
        ordering = ['student', 'document_type', '-version']
        verbose_name = 'Student Document'
        verbose_name_plural = 'Student Documents'
        indexes = [
            models.Index(fields=['student', 'document_type', 'version_status'], name='idx_std_doc_type_vstatus'),
            models.Index(fields=['version_status'], name='idx_std_doc_vstatus'),
            models.Index(fields=['verification_status'], name='idx_std_doc_ver_status'),
        ]

    def clean(self):
        validate_document_type(self.document_type)
        validate_version_status(self.version_status)
        validate_verification_status(self.verification_status)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_sensitive(self) -> bool:
        """Determines if document contains sensitive identity/financial information (ADR-015)."""
        return self.document_type in SENSITIVE_DOCUMENT_TYPES

    def __str__(self):
        return f"{self.student.candidate_name} - {self.document_type} v{self.version} ({self.version_status})"
