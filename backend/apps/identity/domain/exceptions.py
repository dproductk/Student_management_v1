"""
Domain exceptions for Identity & Access.
Governed by identity-and-access-prd.md.
"""

from common.exceptions import DomainException


class AuthenticationFailedError(DomainException):
    """Raised when user credential validation fails."""
    def __init__(self, message: str = "Invalid username or password."):
        super().__init__(message, code="INVALID_CREDENTIALS")


class AccountSuspendedError(DomainException):
    """Raised when an authentication attempt is made on a suspended account."""
    def __init__(self, message: str = "Account is suspended. Please contact administrator."):
        super().__init__(message, code="ACCOUNT_SUSPENDED")


class AccountInactiveError(DomainException):
    """Raised when an authentication attempt is made on an inactive/deactivated account."""
    def __init__(self, message: str = "Account is inactive."):
        super().__init__(message, code="ACCOUNT_INACTIVE")


class InvalidTokenError(DomainException):
    """Raised when a token is invalid, expired, or revoked."""
    def __init__(self, message: str = "Token is invalid, expired, or revoked."):
        super().__init__(message, code="INVALID_OR_EXPIRED_TOKEN")


class PasswordPolicyError(DomainException):
    """Raised when a password violates security policy."""
    def __init__(self, message: str):
        super().__init__(message, code="PASSWORD_POLICY_VIOLATION")
