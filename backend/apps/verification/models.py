"""
Verification bounded context models.
Implements Deliverable D.5 of DATABASE_ARCHITECTURE.md:
VerificationRequest, VerificationRequirement, and VerificationDecision.
"""

from django.db import models
from django.utils import timezone
from common.models import TimeStampedUUIDModel
from apps.verification.domain.invariants import (
    VERIFICATION_STATUS_CHOICES,
    ENTITY_TYPE_CHOICES,
    validate_verification_status,
    validate_entity_type,
    validate_state_transition,
)


class VerificationRequest(TimeStampedUUIDModel):
    """
    Physical table: 'verification_requests'.
    Tracks a piece of student information, document, or correction submitted for verification.
    """
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='verification_requests',
        db_column='student_id'
    )
    entity_type = models.CharField(max_length=50, choices=ENTITY_TYPE_CHOICES)
    entity_id = models.UUIDField(null=True, blank=True, help_text="Reference to specific document or entity if applicable")
    field_name = models.CharField(max_length=100, null=True, blank=True, help_text="Field name if field-level verification")
    submitted_value = models.TextField(null=True, blank=True, help_text="The value submitted for verification")
    status = models.CharField(max_length=30, choices=VERIFICATION_STATUS_CHOICES, default='PENDING')
    current_version = models.IntegerField(default=1)
    submitted_by = models.ForeignKey(
        'identity.User',
        on_delete=models.RESTRICT,
        related_name='submitted_verifications',
        db_column='submitted_by'
    )
    submitted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'verification_requests'
        ordering = ['-submitted_at']
        verbose_name = 'Verification Request'
        verbose_name_plural = 'Verification Requests'
        indexes = [
            models.Index(fields=['student', 'status'], name='idx_verif_student_status'),
            models.Index(fields=['entity_type', 'entity_id'], name='idx_verif_entity'),
            models.Index(fields=['status'], name='idx_verif_status'),
        ]

    def clean(self):
        validate_entity_type(self.entity_type)
        validate_verification_status(self.status)

    def save(self, *args, **kwargs):
        self.clean()
        if self.pk:
            prev = VerificationRequest.objects.filter(pk=self.pk).first()
            if prev and prev.status != self.status:
                validate_state_transition(prev.status, self.status)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.status}] {self.entity_type} for {self.student.candidate_name} (v{self.current_version})"


class VerificationRequirement(TimeStampedUUIDModel):
    """
    Physical table: 'verification_requirements'.
    Policy table for ADR-022 — defines which entity types or fields require manual verification.
    """
    entity_type = models.CharField(max_length=50, unique=True, choices=ENTITY_TYPE_CHOICES)
    requires_verification = models.BooleanField(default=True)
    auto_approve = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'verification_requirements'
        verbose_name = 'Verification Requirement'
        verbose_name_plural = 'Verification Requirements'

    def __str__(self):
        return f"{self.entity_type} (Requires Verification: {self.requires_verification})"


class VerificationDecision(TimeStampedUUIDModel):
    """
    Physical table: 'verification_decisions'.
    Immutable audit history of every verification action. Previous decisions are never rewritten.
    """
    verification_request = models.ForeignKey(
        VerificationRequest,
        on_delete=models.CASCADE,
        related_name='decisions',
        db_column='verification_request_id'
    )
    version = models.IntegerField()
    decision = models.CharField(max_length=30, choices=VERIFICATION_STATUS_CHOICES)
    reviewer = models.ForeignKey(
        'identity.User',
        on_delete=models.RESTRICT,
        related_name='reviewed_verification_decisions',
        db_column='reviewer_id'
    )
    reviewed_at = models.DateTimeField(default=timezone.now)
    rejection_reason = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'verification_decisions'
        ordering = ['verification_request', '-version']
        unique_together = (('verification_request', 'version'),)
        verbose_name = 'Verification Decision'
        verbose_name_plural = 'Verification Decisions'
        indexes = [
            models.Index(fields=['verification_request'], name='idx_vdecisions_request'),
            models.Index(fields=['reviewer'], name='idx_vdecisions_reviewer'),
        ]

    def __str__(self):
        return f"Decision v{self.version} [{self.decision}] by {self.reviewer.username}"
