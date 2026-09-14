"""
Automated Tests for Database Backup & Restore Procedures.
Governed by TASKS.md 15.4.2, production-hardening-prd.md R-015, and ADR-031.
"""

import os
import shutil
import tempfile
import sqlite3
from pathlib import Path
from django.test import TestCase
from scripts.backup_db import create_database_backup, compute_sha256
from scripts.restore_db import verify_backup_integrity, restore_database


class BackupRestoreProcedureTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_backup_generates_file_and_valid_sha256_checksum(self):
        """Validates backup creation generates backup file and accurate SHA-256."""
        res = create_database_backup(destination_dir=self.temp_dir)
        backup_path = Path(res['backup_path'])
        checksum_path = Path(res['checksum_path'])

        self.assertTrue(backup_path.exists())
        self.assertTrue(checksum_path.exists())

        # Verify checksum calculation
        calculated_sha = compute_sha256(backup_path)
        self.assertEqual(res['checksum'], calculated_sha)

        with open(checksum_path, 'r', encoding='utf-8') as f:
            stored_checksum = f.read().strip().split()[0]
        self.assertEqual(stored_checksum, calculated_sha)

    def test_integrity_check_detects_and_aborts_on_tampered_backup(self):
        """Validates that modifying even a single byte of backup triggers integrity failure."""
        res = create_database_backup(destination_dir=self.temp_dir)
        backup_path = Path(res['backup_path'])

        # Tamper with the backup file by appending corrupt bytes
        with open(backup_path, 'ab') as f:
            f.write(b'MALICIOUS_CORRUPT_BYTES')

        with self.assertRaises(ValueError) as ctx:
            verify_backup_integrity(str(backup_path))
        self.assertIn("Integrity check failed", str(ctx.exception))

        # Restore must also abort
        with self.assertRaises(ValueError):
            restore_database(str(backup_path))

    def test_clean_restore_procedure(self):
        """Validates restoring a verified backup into a target path."""
        res = create_database_backup(destination_dir=self.temp_dir)
        backup_path = res['backup_path']

        target_restore_path = Path(self.temp_dir) / 'restored_db.sqlite3'
        restore_result = restore_database(backup_path, target_db_path=str(target_restore_path))

        self.assertEqual(restore_result['status'], 'RESTORED_SUCCESSFULLY')
        self.assertTrue(target_restore_path.exists())

        # Verify restored database is readable
        conn = sqlite3.connect(str(target_restore_path))
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        self.assertEqual(cursor.fetchone()[0], 1)
        conn.close()
