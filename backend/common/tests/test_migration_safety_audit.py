"""
Migration Safety and Historical-Data Preservation Audit Test Suite.
Governed by TASKS.md 15.2.2, production-hardening-prd.md R-007, and ADR-007.
"""

from io import StringIO
from django.test import TestCase
from django.core.management import call_command
from django.db.migrations.recorder import MigrationRecorder
from django.db import connection
from django.apps import apps


class MigrationSafetyAuditTests(TestCase):
    """
    Audits Django migrations to guarantee zero schema drift, non-destructive operations,
    and historical-data preservation across production releases.
    """

    def test_zero_unapplied_model_changes_schema_drift(self):
        """Verify makemigrations --check --dry-run reports zero unmigrated model alterations."""
        out = StringIO()
        try:
            call_command('makemigrations', check=True, dry_run=True, stdout=out)
        except SystemExit as e:
            self.assertEqual(
                e.code, 0,
                f"Unapplied migrations detected! Please run makemigrations. Output: {out.getvalue()}"
            )

    def test_migration_operations_are_non_destructive(self):
        """Verify existing migrations do not destructively delete models or columns."""
        from django.db.migrations.loader import MigrationLoader
        loader = MigrationLoader(connection, ignore_no_migrations=True)

        destructive_operations = []
        for (app_label, migration_name), migration in loader.disk_migrations.items():
            if not app_label.startswith('apps.'):
                continue

            for op in migration.operations:
                op_type = op.__class__.__name__
                if op_type in ['DeleteModel', 'RemoveField']:
                    destructive_operations.append(f"{app_label}.{migration_name}: {op_type}")

        self.assertEqual(
            len(destructive_operations), 0,
            f"Destructive migration operations found on operational apps: {destructive_operations}"
        )

    def test_all_custom_apps_have_recorded_migrations(self):
        """Verify all domain apps have active initial migrations recorded."""
        from django.db.migrations.loader import MigrationLoader
        loader = MigrationLoader(connection, ignore_no_migrations=True)

        monitored_apps = [
            'apps.identity', 'apps.academic', 'apps.students', 'apps.onboarding',
            'apps.documents', 'apps.verification', 'apps.faculty',
            'apps.finance', 'apps.assessments', 'apps.results', 'apps.services',
            'apps.audit'
        ]

        for app_label in monitored_apps:
            app_migrations = [m for (a, m) in loader.disk_migrations.keys() if a == app_label or a == app_label.split('.')[-1]]
            self.assertGreater(
                len(app_migrations), 0,
                f"App '{app_label}' must have at least one migration file defined."
            )
