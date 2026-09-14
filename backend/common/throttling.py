"""
Scoped rate limiting throttle classes for authentication and sensitive data reveals.
Governed by production-hardening-prd.md R-003 and Security Notes.
"""

from rest_framework.throttling import SimpleRateThrottle


class AuthRateThrottle(SimpleRateThrottle):
    """Throttle for authentication endpoints to prevent brute-force attacks."""
    scope = 'auth'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return self.cache_format % {
                'scope': self.scope,
                'ident': request.user.pk
            }
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request)
        }


class SensitiveRevealRateThrottle(SimpleRateThrottle):
    """Throttle for sensitive PII reveal requests (ADR-015)."""
    scope = 'sensitive_reveal'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return self.cache_format % {
                'scope': self.scope,
                'ident': request.user.pk
            }
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request)
        }
