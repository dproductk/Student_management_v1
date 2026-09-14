"""
Domain invariants and constraints for Documents bounded context.
Governed by Deliverable D.6 of DATABASE_ARCHITECTURE.md, ADR-011, and ADR-015.
"""

from common.exceptions import InvariantViolationError

DOCUMENT_TYPES = [
    ('PHOTO', 'Student Photograph'),
    ('SIGNATURE', 'Student Signature'),
    ('AADHAAR_CARD', 'Aadhaar Card (Sensitive)'),
    ('SSC_MARKSHEET', 'SSC Marksheet (10th)'),
    ('HSC_MARKSHEET', 'HSC Marksheet (12th)'),
    ('ALLOTMENT_LETTER', 'Government Allotment Letter'),
    ('BANK_PASSBOOK', 'Bank Passbook / Cancelled Cheque (Sensitive)'),
    ('INCOME_CERTIFICATE', 'Income Certificate'),
    ('CASTE_CERTIFICATE', 'Caste Certificate'),
    ('OTHER', 'Other Official Certificate'),
]

SENSITIVE_DOCUMENT_TYPES = {'AADHAAR_CARD', 'BANK_PASSBOOK'}

VERSION_STATUS_CHOICES = [
    ('CURRENT', 'Current Authoritative Version'),
    ('SUPERSEDED', 'Superseded Historical Version'),
]

VERIFICATION_STATUS_CHOICES = [
    ('PENDING', 'Pending Verification'),
    ('APPROVED', 'Approved'),
    ('REJECTED', 'Rejected'),
    ('NEEDS_CORRECTION', 'Needs Correction'),
]

ALLOWED_MIME_TYPES = {
    'application/pdf',
    'image/jpeg',
    'image/jpg',
    'image/png',
}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def validate_document_type(doc_type: str) -> None:
    valid_types = {k for k, _ in DOCUMENT_TYPES}
    if doc_type not in valid_types:
        raise InvariantViolationError(f"Invalid document type: '{doc_type}'. Allowed types: {sorted(valid_types)}")


def validate_version_status(status: str) -> None:
    valid_statuses = {k for k, _ in VERSION_STATUS_CHOICES}
    if status not in valid_statuses:
        raise InvariantViolationError(f"Invalid version status: '{status}'. Allowed: {sorted(valid_statuses)}")


def validate_verification_status(status: str) -> None:
    valid_statuses = {k for k, _ in VERIFICATION_STATUS_CHOICES}
    if status not in valid_statuses:
        raise InvariantViolationError(f"Invalid verification status: '{status}'. Allowed: {sorted(valid_statuses)}")


def validate_file_spec(file_size: int, mime_type: str) -> None:
    if file_size > MAX_FILE_SIZE_BYTES:
        raise InvariantViolationError(
            f"File size ({file_size} bytes) exceeds maximum allowable limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
        )
    if mime_type and mime_type.lower() not in ALLOWED_MIME_TYPES:
        raise InvariantViolationError(
            f"MIME type '{mime_type}' is not supported. Allowed formats: PDF, JPEG, PNG."
        )
