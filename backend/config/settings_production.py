"""
Production Django Settings.
Strict security hardening, HTTPS enforcement, DB connection pooling, and production logging.
Governed by TASKS.md 15.4.1 and production-hardening-prd.md.
"""
import os
from .settings import *

DEBUG = False

# Validate secret key is explicitly provided and not insecure default
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY or SECRET_KEY == 'django-insecure-default-development-key':
    # Allow fallback during test runner or CI if specified
    if os.environ.get('CI') or 'test' in sys.argv:
        SECRET_KEY = 'production-test-only-key-not-for-real-deployment'
    else:
        raise ValueError("SECRET_KEY environment variable must be set to a secure, unique value in production.")

# Allowed Hosts
hosts = os.environ.get('ALLOWED_HOSTS', '')
if hosts:
    ALLOWED_HOSTS = [h.strip() for h in hosts.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# CORS Configuration
cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '')
if cors_origins:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in cors_origins.split(',') if o.strip()]
CORS_ALLOW_ALL_ORIGINS = False

# Production DB pooling
if 'default' in DATABASES and DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
    DATABASES['default']['CONN_MAX_AGE'] = int(os.environ.get('DB_CONN_MAX_AGE', 600))

# Strict HTTPS & Security Headers
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', 31536000))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Production Logging uses structured JSON format
LOGGING['handlers']['console']['formatter'] = 'structured'
LOGGING['root']['level'] = os.environ.get('LOG_LEVEL', 'INFO')
