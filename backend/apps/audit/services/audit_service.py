"""
Audit application service.
Orchestrates immutable audit entry recording and automatic sensitive data scrubbing.
Governed by identity-and-access-prd.md Requirements 25, 26, 27 and ADR-015.
"""

from typing import Optional, Dict, Any, Union
from uuid import UUID
from django.utils import timezone
from apps.audit.models import AuditLog
from apps.identity.models import User


SENSITIVE_KEYS = {
    'password',
    'password_hash',
    'current_password',
    'new_password',
    'confirm_password',
    'token',
    'refresh',
    'access',
    'secret',
    'secret_key',
    'pin',
    'aadhaar',
    'bank_account_number',
}


def sanitize_dict(data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Recursively redacts sensitive keys to ensure credentials and secret tokens
    are NEVER persisted into the audit log (PRD Requirement 25).
    """
    if not data or not isinstance(data, dict):
        return data

    sanitized = {}
    for key, val in data.items():
        if key.lower() in SENSITIVE_KEYS:
            sanitized[key] = '[REDACTED]'
        elif isinstance(val, dict):
            sanitized[key] = sanitize_dict(val)
        elif isinstance(val, list):
            sanitized[key] = [
                sanitize_dict(item) if isinstance(item, dict) else item
                for item in val
            ]
        elif isinstance(val, UUID):
            sanitized[key] = str(val)
        else:
            sanitized[key] = val

    return sanitized


class AuditService:
    """
    Centralized service for recording append-only audit entries.
    Called by domain services across all bounded contexts.
    """

    @classmethod
    def record_audit(
        cls,
        action: str,
        target_type: str,
        module: str,
        actor: Optional[User] = None,
        target_id: Optional[Union[str, UUID]] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """
        Creates and persists an immutable audit log entry.
        All old_value and new_value payloads are sanitized against sensitive credentials.
        """
        clean_old = sanitize_dict(old_value)
        clean_new = sanitize_dict(new_value)

        # Convert target_id to UUID if needed
        clean_target_id = None
        if target_id:
            try:
                clean_target_id = UUID(str(target_id))
            except (ValueError, TypeError):
                clean_target_id = None

        log_entry = AuditLog.objects.create(
            actor=actor if (actor and actor.is_authenticated) else None,
            action=action.strip().upper(),
            target_type=target_type.strip().upper(),
            module=module.strip().lower(),
            target_id=clean_target_id,
            old_value=clean_old,
            new_value=clean_new,
            reason=reason,
            ip_address=ip_address,
            occurred_at=timezone.now()
        )
        return log_entry
