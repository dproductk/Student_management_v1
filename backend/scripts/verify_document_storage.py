"""
Document & Object Storage Verification Script.
Audits student document storage integrity, verifies file existence, and detects checksum tampering.
Governed by TASKS.md 15.4.3, production-hardening-prd.md R-016, and ADR-031.
"""

import hashlib
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Setup Django standalone environment
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.core.files.storage import default_storage
from apps.documents.models import StudentDocument


def verify_storage_integrity() -> Dict[str, Any]:
    """
    Audits all StudentDocument records in the database against default_storage.
    Verifies physical presence and SHA-256 integrity.
    """
    report = {
        'total_documents_checked': 0,
        'valid_documents': 0,
        'missing_storage_files': 0,
        'checksum_mismatches': 0,
        'errors': []
    }

    docs = StudentDocument.objects.all().iterator(chunk_size=100)
    for doc in docs:
        report['total_documents_checked'] += 1
        key = doc.storage_key

        if not default_storage.exists(key):
            report['missing_storage_files'] += 1
            report['errors'].append({
                'document_id': str(doc.id),
                'student_id': str(doc.student_id),
                'storage_key': key,
                'issue': 'FILE_MISSING_ON_STORAGE'
            })
            continue

        # Check SHA-256 checksum if recorded
        if doc.checksum:
            try:
                sha256 = hashlib.sha256()
                with default_storage.open(key, 'rb') as f:
                    for chunk in iter(lambda: f.read(65536), b''):
                        sha256.update(chunk)
                computed_hash = sha256.hexdigest()

                if computed_hash.lower() != doc.checksum.lower():
                    report['checksum_mismatches'] += 1
                    report['errors'].append({
                        'document_id': str(doc.id),
                        'student_id': str(doc.student_id),
                        'storage_key': key,
                        'expected_checksum': doc.checksum,
                        'actual_checksum': computed_hash,
                        'issue': 'CHECKSUM_INTEGRITY_MISMATCH'
                    })
                    continue
            except Exception as e:
                report['errors'].append({
                    'document_id': str(doc.id),
                    'storage_key': key,
                    'issue': f"READ_ERROR: {str(e)}"
                })
                continue

        report['valid_documents'] += 1

    return report


if __name__ == '__main__':
    print("[STORAGE AUDIT] Starting document storage integrity audit...")
    res = verify_storage_integrity()
    print(f"Checked: {res['total_documents_checked']}")
    print(f"Valid: {res['valid_documents']}")
    print(f"Missing Files: {res['missing_storage_files']}")
    print(f"Checksum Mismatches: {res['checksum_mismatches']}")
    if res['errors']:
        print(f"Found {len(res['errors'])} anomalies:")
        for err in res['errors']:
            print(f"  - {err}")
    else:
        print("[STORAGE AUDIT] 100% document storage integrity verified.")
