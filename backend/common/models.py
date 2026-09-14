import uuid
from django.db import models


class TimeStampedUUIDModel(models.Model):
    """
    Abstract base model providing UUID primary key and timestamp fields.
    Matches DATABASE_ARCHITECTURE.md physical schema standard.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier (UUIDv4)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        help_text="Timestamp when the record was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the record was last updated"
    )

    class Meta:
        abstract = True
