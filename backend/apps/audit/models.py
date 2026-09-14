"""
Audit models for immutable, system-wide accountability and business audit trails.
Governed by DATABASE_ARCHITECTURE.md Deliverable D.11, Deliverable N,
and identity-and-access-prd.md Requirements 21, 25, 26, 27.
"""

import uuid
from django.db import models
from django.utils import timezone
from common.exceptions import InvariantViolationError


class AuditLog(models.Model):
    """
    Physical table: 'audit_log'.
    Append-only audit trail capturing accountable actors, actions, targets, and diffs.
    Immutability enforced: UPDATE and DELETE operations are rejected.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    actor = models.ForeignKey(
        'identity.User',
        on_delete=models.RESTRICT,
        related_name='audit_logs',
        null=True,
        blank=True,
        help_text="Accountable actor who initiated the action (null for unauthenticated events)"
    )
    action = models.CharField(
        max_length=100,
        help_text="Action performed (e.g. LOGIN_SUCCESS, ROLE_CHANGED, USER_SUSPENDED)"
    )
    target_type = models.CharField(
        max_length=50,
        help_text="Type of resource affected (e.g. USER, ROLE, USER_ROLE, STUDENT)"
    )
    target_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="UUID of the specific affected entity"
    )
    module = models.CharField(
        max_length=50,
        help_text="Owning bounded context (e.g. identity, academic, finance)"
    )
    old_value = models.JSONField(
        null=True,
        blank=True,
        help_text="Snapshot of state before mutation (sanitized)"
    )
    new_value = models.JSONField(
        null=True,
        blank=True,
        help_text="Snapshot of state after mutation (sanitized)"
    )
    reason = models.TextField(
        null=True,
        blank=True,
        help_text="Optional human or system explanation for the change"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Client IP address where request originated"
    )
    occurred_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        help_text="Timestamp when the audited event occurred"
    )

    class Meta:
        db_table = 'audit_log'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-occurred_at']
        indexes = [
            models.Index(fields=['actor'], name='idx_audit_actor'),
            models.Index(fields=['target_type', 'target_id'], name='idx_audit_target'),
            models.Index(fields=['occurred_at'], name='idx_audit_occurred'),
            models.Index(fields=['module'], name='idx_audit_module'),
        ]

    def save(self, *args, **kwargs):
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise InvariantViolationError("AuditLog entries are append-only and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise InvariantViolationError("AuditLog entries are append-only and cannot be deleted.")

    def __str__(self):
        actor_name = self.actor.username if self.actor else "SYSTEM/ANONYMOUS"
        return f"[{self.occurred_at}] {actor_name} -> {self.action} on {self.target_type}:{self.target_id}"


class SensitiveDataAccessLog(models.Model):
    """
    Physical table: 'sensitive_data_access_log'.
    Immutable access log recorded whenever sensitive fields (Aadhaar, Bank Accounts)
    are decrypted/revealed. Governed by ADR-015 and DATABASE_ARCHITECTURE.md.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    accessor = models.ForeignKey(
        'identity.User',
        on_delete=models.RESTRICT,
        related_name='sensitive_access_logs',
        help_text="Accountable operator who requested the unmasked data"
    )
    student_id = models.UUIDField(
        help_text="UUID of the student whose sensitive data was revealed"
    )
    field_name = models.CharField(
        max_length=50,
        help_text="Field accessed (e.g. aadhaar, bank_account_number)"
    )
    reason = models.TextField(
        help_text="Mandatory business reason for revealing unmasked sensitive data"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the requester"
    )
    accessed_at = models.DateTimeField(
        default=timezone.now,
        editable=False
    )

    class Meta:
        db_table = 'sensitive_data_access_log'
        verbose_name = 'Sensitive Data Access Log'
        verbose_name_plural = 'Sensitive Data Access Logs'
        ordering = ['-accessed_at']
        indexes = [
            models.Index(fields=['accessor'], name='idx_sens_accessor'),
            models.Index(fields=['student_id'], name='idx_sens_student'),
            models.Index(fields=['accessed_at'], name='idx_sens_accessed'),
        ]

    def save(self, *args, **kwargs):
        if self.pk and SensitiveDataAccessLog.objects.filter(pk=self.pk).exists():
            raise InvariantViolationError("SensitiveDataAccessLog entries are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise InvariantViolationError("SensitiveDataAccessLog entries are immutable and cannot be deleted.")

    def __str__(self):
        return f"[{self.accessed_at}] {self.accessor.username} revealed {self.field_name} for student {self.student_id}"
