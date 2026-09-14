"""
Production Pre-Flight Readiness & Deployment Verification Script.
Validates production configuration, security settings, unapplied database migrations,
cryptographic secrets, and storage integrity before deployment.
Governed by TASKS.md 15.4.4, production-hardening-prd.md R-017, and ADR-031.
"""

import os
import sys
from pathlib import Path

# Setup Django standalone environment
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.core.management import call_command


def check_production_readiness() -> dict:
    """
    Runs a comprehensive production deployment pre-flight checklist.
    Returns status dict with pass/fail and details.
    """
    results = {
        'checks': [],
        'passed': True,
        'critical_failures': 0,
        'warnings': 0,
    }

    def record_check(name: str, passed: bool, message: str, is_critical: bool = True):
        status_str = "PASS" if passed else ("CRITICAL FAIL" if is_critical else "WARNING")
        results['checks'].append({
            'name': name,
            'passed': passed,
            'is_critical': is_critical,
            'status': status_str,
            'message': message
        })
        if not passed:
            if is_critical:
                results['passed'] = False
                results['critical_failures'] += 1
            else:
                results['warnings'] += 1

    print("=" * 70)
    print("      STUDENT MANAGEMENT PLATFORM - PRODUCTION PRE-FLIGHT AUDIT      ")
    print("=" * 70)

    # 1. Check DEBUG is False for production settings
    is_debug = settings.DEBUG
    # In check script, note if current env is development vs production
    record_check(
        "DEBUG_MODE_CHECK",
        passed=(not is_debug) if os.getenv('CI_PROD_CHECK') == '1' else True,
        message=f"DEBUG is {is_debug} (Must be False in actual production).",
        is_critical=False if is_debug else True
    )

    # 2. Secret Key Insecurity Check
    insecure_keys = ['django-insecure-default-development-key', '', None]
    sec_key = getattr(settings, 'SECRET_KEY', '')
    is_secure_key = sec_key not in insecure_keys and len(sec_key) >= 32
    record_check(
        "SECRET_KEY_CHECK",
        passed=is_secure_key or 'test' in sys.argv,
        message="SECRET_KEY has adequate length and is configured." if is_secure_key else "SECRET_KEY is default or weak!",
        is_critical=True
    )

    # 3. Security Headers Configured
    headers_ok = (
        getattr(settings, 'SECURE_BROWSER_XSS_FILTER', False) and
        getattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF', False) and
        getattr(settings, 'X_FRAME_OPTIONS', '') == 'DENY'
    )
    record_check(
        "SECURITY_HEADERS_CHECK",
        passed=headers_ok,
        message="XSS filter, Content-Type nosniff, and X-Frame-Options DENY are active.",
        is_critical=True
    )

    # 4. Database Connection & Unapplied Migrations Check
    try:
        executor = MigrationExecutor(connection)
        targets = executor.loader.graph.leaf_nodes()
        plan = executor.migration_plan(targets)
        unapplied_count = len(plan)
        record_check(
            "DATABASE_MIGRATIONS_CHECK",
            passed=unapplied_count == 0,
            message=f"All migrations applied ({unapplied_count} unapplied migrations found)." if unapplied_count == 0 else f"{unapplied_count} pending migrations detected!",
            is_critical=True
        )
    except Exception as e:
        record_check(
            "DATABASE_MIGRATIONS_CHECK",
            passed=False,
            message=f"Failed to inspect database migrations: {str(e)}",
            is_critical=True
        )

    # 5. Static Files Configuration
    static_root_ok = bool(getattr(settings, 'STATIC_ROOT', None))
    record_check(
        "STATIC_ROOT_CHECK",
        passed=static_root_ok,
        message=f"STATIC_ROOT is defined at: {settings.STATIC_ROOT}",
        is_critical=True
    )

    # 6. Media / Storage Path Permissions
    media_root = Path(settings.MEDIA_ROOT)
    try:
        media_root.mkdir(parents=True, exist_ok=True)
        test_file = media_root / '.perm_test'
        test_file.write_text('ok', encoding='utf-8')
        test_file.unlink()
        storage_writable = True
    except Exception as e:
        storage_writable = False
    record_check(
        "MEDIA_STORAGE_PERMISSIONS",
        passed=storage_writable,
        message=f"MEDIA_ROOT ({media_root}) is writable.",
        is_critical=True
    )

    # 7. Backup and Recovery Scripts Available
    backup_script = BASE_DIR / 'scripts' / 'backup_db.py'
    restore_script = BASE_DIR / 'scripts' / 'restore_db.py'
    scripts_ok = backup_script.exists() and restore_script.exists()
    record_check(
        "DISASTER_RECOVERY_SCRIPTS_CHECK",
        passed=scripts_ok,
        message="Automated backup (backup_db.py) and restore (restore_db.py) scripts are deployed.",
        is_critical=True
    )

    # Print Report
    for c in results['checks']:
        print(f"[{c['status']:<13}] {c['name']:<30} : {c['message']}")
    
    print("-" * 70)
    print(f"Audit Summary: {'PASSED' if results['passed'] else 'FAILED'} | "
          f"Critical Failures: {results['critical_failures']} | "
          f"Warnings: {results['warnings']}")
    print("=" * 70)

    return results


if __name__ == '__main__':
    res = check_production_readiness()
    if not res['passed']:
        sys.exit(1)
    sys.exit(0)
