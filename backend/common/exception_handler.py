"""
Custom DRF exception handler for standardized error responses.
Ensures authentication failures, token errors, and domain exceptions do not leak internal details.
Governed by identity-and-access-prd.md Requirement 6 and AGENTS.md.
"""

from django.conf import settings
from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, PermissionDenied, Throttled
from common.exceptions import DomainException, EntityNotFoundError


def custom_exception_handler(exc, context):
    """
    Standardized exception handler returning consistent JSON:
    {"error": "<message>", "code": "<code>"}
    Governed by R-003, R-004 (Safe Error Exposure & API Security).
    """
    # Call REST framework's default exception handler first to get standard response
    response = exception_handler(exc, context)

    if isinstance(exc, (InvalidToken, TokenError)):
        return Response(
            {
                "error": "Token is invalid or expired.",
                "code": "INVALID_OR_EXPIRED_TOKEN"
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    if isinstance(exc, NotAuthenticated):
        return Response(
            {
                "error": "Authentication credentials were not provided.",
                "code": "NOT_AUTHENTICATED"
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    if isinstance(exc, AuthenticationFailed):
        return Response(
            {
                "error": "Authentication failed.",
                "code": "AUTHENTICATION_FAILED"
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    if isinstance(exc, PermissionDenied):
        return Response(
            {
                "error": "You do not have permission to perform this action.",
                "code": "PERMISSION_DENIED"
            },
            status=status.HTTP_403_FORBIDDEN
        )

    if isinstance(exc, Throttled):
        wait_seconds = getattr(exc, 'wait', None)
        detail = "Request was throttled."
        if wait_seconds:
            detail += f" Expected available in {wait_seconds} seconds."
        return Response(
            {
                "error": detail,
                "code": "REQUEST_THROTTLED",
                "available_in_seconds": wait_seconds
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    if isinstance(exc, EntityNotFoundError):
        return Response(
            {
                "error": exc.message,
                "code": exc.code
            },
            status=status.HTTP_404_NOT_FOUND
        )

    if isinstance(exc, DomainException):
        return Response(
            {
                "error": exc.message,
                "code": exc.code
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Safe error exposure in production: mask unhandled server exceptions (500)
    if response is None and not settings.DEBUG:
        return Response(
            {
                "error": "An unexpected internal server error occurred. Please contact system administrator.",
                "code": "INTERNAL_SERVER_ERROR"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response
