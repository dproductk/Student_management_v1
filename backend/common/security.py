"""
Security utilities for encrypting and masking sensitive identity & financial data.
Governed by ADR-015 (Sensitive Data Reveal Boundary & Auditing).
"""

import base64
import hashlib
from django.conf import settings
from cryptography.fernet import Fernet


def _get_fernet_key() -> bytes:
    """Derive a URL-safe base64-encoded 32-byte key from Django SECRET_KEY."""
    raw_key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(raw_key)


def encrypt_sensitive_value(raw_value: str) -> bytes:
    """Encrypt a string (e.g. Aadhaar or Bank Account) using AES."""
    if not raw_value:
        return b''
    f = Fernet(_get_fernet_key())
    return f.encrypt(raw_value.encode('utf-8'))


def decrypt_sensitive_value(encrypted_bytes: bytes) -> str:
    """Decrypt encrypted byte data back to cleartext string."""
    if not encrypted_bytes:
        return ''
    f = Fernet(_get_fernet_key())
    return f.decrypt(bytes(encrypted_bytes)).decode('utf-8')


def mask_aadhaar(aadhaar_number: str) -> str:
    """Format: XXXX XXXX 1234 (last 4 digits visible)."""
    if not aadhaar_number:
        return ''
    clean = "".join(filter(str.isdigit, str(aadhaar_number)))
    if len(clean) < 4:
        return 'XXXX'
    last_four = clean[-4:]
    return f"XXXX XXXX {last_four}"


def mask_bank_account(account_number: str) -> str:
    """Format: XXXXXXXX1234 (last 4 digits visible)."""
    if not account_number:
        return ''
    clean = str(account_number).strip()
    if len(clean) <= 4:
        return clean
    masked_prefix = 'X' * (len(clean) - 4)
    return f"{masked_prefix}{clean[-4:]}"
