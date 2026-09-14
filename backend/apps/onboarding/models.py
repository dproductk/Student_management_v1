"""
Onboarding & Import domain models.
Implements Deliverable D.4 of DATABASE_ARCHITECTURE.md:
ImportBatch and ImportStagingRow.
"""

from django.db import models
from django.utils import timezone
from common.models import TimeStampedUUIDModel


class ImportBatch(TimeStampedUUIDModel):
    """Lifecycle tracking for student data ingestion batches."""
    STATUS_CHOICES = [
        ('UPLOADED', 'Uploaded'),
        ('VALIDATING', 'Validating'),
        ('VALIDATED', 'Validated'),
        ('IMPORTING', 'Importing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('PARTIALLY_COMPLETED', 'Partially Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    source_file_name = models.CharField(max_length=500)
    source_file_hash = models.CharField(max_length=128)
    source_type = models.CharField(max_length=30, default='GOVERNMENT_EXCEL')
    academic_year = models.ForeignKey(
        'academic.AcademicYear',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='import_batches',
        db_column='academic_year_id'
    )
    department = models.ForeignKey(
        'academic.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='import_batches',
        db_column='department_id'
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='UPLOADED')
    total_rows = models.IntegerField(null=True, blank=True)
    processed_rows = models.IntegerField(default=0)
    error_rows = models.IntegerField(default=0)
    uploaded_by = models.ForeignKey(
        'identity.User',
        on_delete=models.RESTRICT,
        related_name='uploaded_import_batches',
        db_column='uploaded_by'
    )
    uploaded_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'import_batches'
        ordering = ['-uploaded_at']
        verbose_name = 'Import Batch'
        verbose_name_plural = 'Import Batches'
        indexes = [
            models.Index(fields=['status'], name='idx_import_batches_status'),
            models.Index(fields=['source_file_hash'], name='idx_import_batches_hash'),
        ]

    def __str__(self):
        return f"Batch {self.id} [{self.status}]: {self.source_file_name}"


class ImportStagingRow(TimeStampedUUIDModel):
    """Raw and normalized row data preserved verbatim from imported source."""
    PROCESSING_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('VALIDATED', 'Validated'),
        ('INVALID', 'Invalid'),
        ('IMPORTED', 'Imported'),
        ('DUPLICATE', 'Duplicate'),
        ('CONFLICT', 'Conflict'),
        ('SKIPPED', 'Skipped'),
        ('FAILED', 'Failed'),
    ]

    MATCH_TYPE_CHOICES = [
        ('APPLICATION_ID', 'Matched by Application ID'),
        ('ENROLLMENT_NO', 'Matched by Enrollment No'),
        ('BOARD_ENROLLMENT_NO', 'Matched by Board Enrollment No'),
        ('NEW', 'New Student'),
        ('CONFLICT', 'Conflicting Identifiers'),
    ]

    import_batch = models.ForeignKey(
        ImportBatch,
        on_delete=models.CASCADE,
        related_name='staging_rows',
        db_column='import_batch_id'
    )
    row_number = models.IntegerField()
    raw_data = models.JSONField(help_text="Original Excel row dictionary preserved verbatim")
    normalized_data = models.JSONField(null=True, blank=True, help_text="Cleaned, normalized field values")
    validation_errors = models.JSONField(null=True, blank=True, help_text="List of validation errors")
    processing_status = models.CharField(max_length=30, choices=PROCESSING_STATUS_CHOICES, default='PENDING')
    matched_student = models.ForeignKey(
        'students.Student',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matched_staging_rows',
        db_column='matched_student_id'
    )
    match_type = models.CharField(max_length=30, choices=MATCH_TYPE_CHOICES, null=True, blank=True)
    conflict_details = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'import_staging_rows'
        ordering = ['import_batch', 'row_number']
        unique_together = (('import_batch', 'row_number'),)
        verbose_name = 'Import Staging Row'
        verbose_name_plural = 'Import Staging Rows'
        indexes = [
            models.Index(fields=['import_batch', 'processing_status'], name='idx_staging_batch_status'),
        ]

    def __str__(self):
        return f"Batch {self.import_batch_id} Row #{self.row_number} ({self.processing_status})"
