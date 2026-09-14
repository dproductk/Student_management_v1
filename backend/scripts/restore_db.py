"""
Database Restore Utility Script.
Validates SHA-256 integrity checksums before restoring database to prevent corruption or tampering.
Governed by TASKS.md 15.4.2, production-hardening-prd.md R-015, and ADR-031.
"""

import hashlib
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

# Setup Django standalone environment
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings
from scripts.backup_db import compute_sha256


def verify_backup_integrity(backup_path: str, checksum_path: str = None) -> bool:
    """
    Verifies that the backup file's SHA-256 matches the expected checksum in .sha256 file.
    Raises ValueError on mismatch.
    """
    b_path = Path(backup_path)
    if not b_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    if checksum_path is None:
        checksum_path = b_path.parent / f"{b_path.name}.sha256"
    else:
        checksum_path = Path(checksum_path)

    if not checksum_path.exists():
        raise FileNotFoundError(f"Checksum verification file not found: {checksum_path}")

    with open(checksum_path, 'r', encoding='utf-8') as f:
        expected_checksum = f.read().strip().split()[0]

    actual_checksum = compute_sha256(b_path)

    if actual_checksum.lower() != expected_checksum.lower():
        raise ValueError(
            f"Integrity check failed! Expected SHA-256 {expected_checksum}, got {actual_checksum}. "
            f"The backup file may be corrupt or tampered with."
        )

    return True


def restore_database(backup_path: str, target_db_path: str = None) -> dict:
    """
    Restores the database from a verified backup file.
    """
    verify_backup_integrity(backup_path)

    b_path = Path(backup_path)
    db_conf = settings.DATABASES['default']
    engine = db_conf['ENGINE']

    if 'sqlite3' in engine:
        target = Path(target_db_path) if target_db_path else Path(db_conf['NAME'])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(b_path, target)
        return {
            'status': 'RESTORED_SUCCESSFULLY',
            'engine': engine,
            'source_backup': str(b_path),
            'target_db': str(target)
        }

    elif 'postgresql' in engine:
        env = os.environ.copy()
        env['PGPASSWORD'] = str(db_conf.get('PASSWORD', ''))
        cmd = [
            'pg_restore',
            '-h', str(db_conf.get('HOST', 'localhost')),
            '-p', str(db_conf.get('PORT', '5432')),
            '-U', str(db_conf.get('USER', 'postgres')),
            '-d', str(db_conf['NAME']),
            '--clean',
            '--no-owner',
            str(b_path)
        ]
        try:
            subprocess.run(cmd, env=env, check=True, capture_output=True)
            return {
                'status': 'RESTORED_SUCCESSFULLY',
                'engine': engine,
                'source_backup': str(b_path),
                'target_db': db_conf['NAME']
            }
        except Exception as e:
            raise RuntimeError(f"pg_restore execution failed: {str(e)}")

    else:
        raise ValueError(f"Unsupported database engine: {engine}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python restore_db.py <path_to_backup_file>")
        sys.exit(1)
    
    res = restore_database(sys.argv[1])
    print(f"[RESTORE SUCCESS] {res['status']} -> {res['target_db']}")
