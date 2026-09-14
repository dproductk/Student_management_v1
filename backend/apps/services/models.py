import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class ServiceRequestType(models.Model):
    """
    Catalog of institutional student service types (e.g. Bonafide Certificate,
    Official Transcript, Fee Concession Application, Data Correction).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    requires_document = models.BooleanField(default=False)
    allowed_document_types = models.JSONField(default=list, help_text="Allowed document type keys from apps.documents")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'service_request_types'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class ServiceRequest(models.Model):
    """
    Core reusable student administrative service request.
    Tracks lifecycle from SUBMITTED to COMPLETED or REJECTED.
    """
    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('IN_PROGRESS', 'In Progress'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_number = models.CharField(max_length=50, unique=True, editable=False)
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.PROTECT,
        related_name='service_requests'
    )
    service_type = models.ForeignKey(
        ServiceRequestType,
        on_delete=models.PROTECT,
        related_name='requests'
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='SUBMITTED')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='NORMAL')
    request_data = models.JSONField(default=dict, help_text="Flexible parameters and purpose payload")
    attached_document = models.ForeignKey(
        'documents.StudentDocument',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='service_requests'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_service_requests'
    )
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_service_requests'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'service_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.request_number}: {self.service_type.code} ({self.status}) - {self.student.enrollment_no}"


class ServiceRequestAudit(models.Model):
    """
    Immutable audit trail recording every workflow state change and accountable actor.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_request = models.ForeignKey(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name='audits'
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='service_request_audits'
    )
    action = models.CharField(max_length=50)
    previous_status = models.CharField(max_length=30, null=True, blank=True)
    new_status = models.CharField(max_length=30)
    reason = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'service_request_audits'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} on {self.service_request.request_number} by {self.actor} at {self.timestamp}"
