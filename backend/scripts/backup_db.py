"""
Database Backup Utility Script.
Produces timestamped, consistent database backups with SHA-256 checksum validation.
Supports both PostgreSQL (production) and SQLite (testing/local).
Governed by TASKS.md 15.4.2, production-hardening-prd.md R-015, and ADR-031.
"""

import hashlib
import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Setup Django standalone environment
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings


def compute_sha256(file_path: Path) -> str:
    """Computes the SHA-256 hex digest of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def create_database_backup(destination_dir: str = None) -> dict:
    """
    Creates a full, timestamped backup of the primary database with an SHA-256 checksum.
    Returns metadata dictionary containing backup path, checksum, and timestamp.
    """
    if destination_dir:
        backup_dir = Path(destination_dir)
    else:
        backup_dir = BASE_DIR / 'backups' / 'db'
    
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')

    db_conf = settings.DATABASES['default']
    engine = db_conf['ENGINE']

    if 'postgresql' in engine:
        backup_filename = f"backup_postgres_{db_conf['NAME']}_{timestamp}.dump"
        backup_path = backup_dir / backup_filename
        
        env = os.environ.copy()
        env['PGPASSWORD'] = str(db_conf.get('PASSWORD', ''))
        
        cmd = [
            'pg_dump',
            '-h', str(db_conf.get('HOST', 'localhost')),
            '-p', str(db_conf.get('PORT', '5432')),
            '-U', str(db_conf.get('USER', 'postgres')),
            '-F', 'c',  # custom format
            '-b',        # include blobs
            '-v',        # verbose
            '-f', str(backup_path),
            str(db_conf['NAME'])
        ]
        
        try:
            subprocess.run(cmd, env=env, check=True, capture_output=True)
        except Exception as e:
            raise RuntimeError(f"pg_dump execution failed: {str(e)}")

    elif 'sqlite3' in engine:
        source_db = Path(db_conf['NAME'])
        backup_filename = f"backup_sqlite_{timestamp}.db"
        backup_path = backup_dir / backup_filename

        # Use sqlite3 online backup API for safe, transactional snapshot
        src_conn = sqlite3.connect(str(source_db))
        dst_conn = sqlite3.connect(str(backup_path))
        with dst_conn:
            src_conn.backup(dst_conn)
        dst_conn.close()
        src_conn.close()

    else:
        raise ValueError(f"Unsupported database engine for backup: {engine}")

    # Compute SHA-256 checksum
    checksum = compute_sha256(backup_path)
    checksum_path = backup_dir / f"{backup_filename}.sha256"
    with open(checksum_path, 'w', encoding='utf-8') as f:
        f.write(f"{checksum}  {backup_filename}\n")

    return {
        'backup_path': str(backup_path),
        'checksum_path': str(checksum_path),
        'checksum': checksum,
        'timestamp': timestamp,
        'engine': engine,
        'size_bytes': os.path.getsize(backup_path)
    }


if __name__ == '__main__':
    result = create_database_backup()
    print(f"[BACKUP SUCCESS] Backup created at: {result['backup_path']}")
    print(f"[CHECKSUM] SHA-256: {result['checksum']}")
