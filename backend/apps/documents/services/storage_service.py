"""
Object Storage service abstraction for document management.
Ensures document binaries remain outside PostgreSQL and zero storage credentials
reach the frontend client (PRD Requirements 5-9).
"""

import os
import uuid
import hashlib
import mimetypes
from typing import Tuple, IO
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from apps.documents.domain.invariants import validate_file_spec


class StorageService:
    """Server-side abstraction for secure document object storage."""

    @staticmethod
    def store_student_document(
        student_id: str,
        file_obj,
        original_filename: str
    ) -> Tuple[str, str, int, str]:
        """
        Store uploaded binary outside the database.
        Returns:
            (storage_key, checksum_sha256, file_size_bytes, mime_type)
        """
        content = file_obj.read()
        file_size = len(content)

        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(original_filename)
        if not mime_type:
            mime_type = getattr(file_obj, 'content_type', 'application/octet-stream')

        # Domain Invariant validation
        validate_file_spec(file_size, mime_type)

        # Compute SHA-256 Checksum
        sha256_hash = hashlib.sha256(content).hexdigest()

        # Generate non-colliding secure storage key
        clean_filename = os.path.basename(original_filename).replace(' ', '_')
        unique_prefix = uuid.uuid4().hex[:12]
        storage_key = f"documents/students/{student_id}/{unique_prefix}_{clean_filename}"

        # Save to storage backend
        default_storage.save(storage_key, ContentFile(content))

        return storage_key, sha256_hash, file_size, mime_type

    @staticmethod
    def get_document_stream(storage_key: str) -> IO[bytes]:
        """Retrieve binary file stream for controlled server-side serving."""
        if not default_storage.exists(storage_key):
            raise FileNotFoundError(f"Document storage key '{storage_key}' not found in object store.")
        return default_storage.open(storage_key, 'rb')

    @staticmethod
    def delete_document(storage_key: str) -> None:
        """Purge storage object if required during testing or cleanup."""
        if default_storage.exists(storage_key):
            default_storage.delete(storage_key)
