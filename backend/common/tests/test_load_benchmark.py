"""
Automated Load-Testing Benchmark Test.
Governed by TASKS.md 15.3.4, production-hardening-prd.md R-014, and ADR-030.
"""

from django.test import TestCase
from scripts.load_test_benchmark import run_load_benchmark


class LoadTestingBenchmarkTests(TestCase):
    """
    Executes automated load testing with realistic cohorts to ensure query latencies
    and bounded export generation remain strictly within institutional performance SLAs.
    """

    def test_load_testing_benchmark_meets_sla_targets(self):
        """Verify queries and export latency meet performance SLAs under load."""
        metrics = run_load_benchmark(cohort_size=100)

        # Ensure directory latency is sub-250ms
        self.assertLess(metrics['directory_query_time_ms'], 250.0)

        # Ensure cross-module KPI aggregation is sub-300ms
        self.assertLess(metrics['kpi_aggregation_time_ms'], 300.0)

        # Ensure 500-row CSV generation is sub-1500ms
        self.assertLess(metrics['csv_export_time_ms'], 1500.0)
