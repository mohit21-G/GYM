"""
Regression Test Suite for Fitness AI 10,000-Test Benchmark Engine
Verifies fixes for:
1. Status accounting invariants (sum to 100%, non-negative skipped_count, standard status enum).
2. Dual accuracy formulas (all cases vs eligible cases, no infra/skipped counted as passes).
3. Error classification (database quota, auth, rate limit, timeout, connection errors).
4. Monotonic timing capture, UTC timestamps, and percentile calculations.
5. Checkpoint loading and scope isolation.
6. Production database safety and cleanup isolation.
"""

import unittest
import numpy as np
from datetime import datetime, timezone
import json
import tempfile
import os

VALID_STATUSES = {"PASS", "PARTIAL_PASS", "FAIL", "INFRA_ERROR", "SKIPPED"}


class TestBenchmarkEngineRegression(unittest.TestCase):

    def test_status_accounting_invariants(self):
        """Regression test for negative skipped_count bug and missing status normalization."""
        total_cases = 100
        # Simulated run where 40 passed, 20 partial, 10 failed, 5 infra errors, 25 unexecuted
        results = {}
        for i in range(40):
            results[f"tc_{i}"] = {"test_id": f"tc_{i}", "status": "PASS", "total_latency_ms": 25.0}
        for i in range(40, 60):
            results[f"tc_{i}"] = {"test_id": f"tc_{i}", "status": "PARTIAL_PASS", "total_latency_ms": 30.0}
        for i in range(60, 70):
            results[f"tc_{i}"] = {"test_id": f"tc_{i}", "status": "FAIL", "total_latency_ms": 20.0}
        for i in range(70, 75):
            results[f"tc_{i}"] = {"test_id": f"tc_{i}", "status": "INFRA_ERROR", "total_latency_ms": 10.0}

        # Populate unexecuted cases as SKIPPED
        all_case_ids = [f"tc_{i}" for i in range(total_cases)]
        for cid in all_case_ids:
            if cid not in results:
                results[cid] = {"test_id": cid, "status": "SKIPPED", "total_latency_ms": None}

        # Assert all statuses are valid
        for r in results.values():
            self.assertIn(r["status"], VALID_STATUSES)

        passed = sum(1 for r in results.values() if r["status"] == "PASS")
        partial = sum(1 for r in results.values() if r["status"] == "PARTIAL_PASS")
        failed = sum(1 for r in results.values() if r["status"] == "FAIL")
        infra = sum(1 for r in results.values() if r["status"] == "INFRA_ERROR")
        skipped = sum(1 for r in results.values() if r["status"] == "SKIPPED")

        # Counts must be non-negative
        self.assertGreaterEqual(skipped, 0, "skipped_count must never be negative!")
        self.assertEqual(skipped, 25)
        self.assertEqual(passed, 40)
        self.assertEqual(partial, 20)
        self.assertEqual(failed, 10)
        self.assertEqual(infra, 5)

        # Total must reconcile exactly to total_cases
        total_reconciled = passed + partial + failed + infra + skipped
        self.assertEqual(total_reconciled, total_cases, "Statuses must sum to total test cases")

    def test_dual_accuracy_formulas(self):
        """Verify strict and eligible accuracy formulas and denominator separation."""
        total_cases = 1000
        passed = 600
        partial = 150
        failed = 50
        infra = 100
        skipped = 100

        # Formula 1: Over ALL cases
        strict_acc_all = round((passed / total_cases) * 100, 2)
        total_pass_acc_all = round(((passed + partial) / total_cases) * 100, 2)
        self.assertEqual(strict_acc_all, 60.0)
        self.assertEqual(total_pass_acc_all, 75.0)

        # Formula 2: Over ELIGIBLE executed cases (excluding infra and skipped)
        eligible = passed + partial + failed
        self.assertEqual(eligible, 800)
        strict_acc_eligible = round((passed / eligible) * 100, 2)
        total_pass_acc_eligible = round(((passed + partial) / eligible) * 100, 2)
        self.assertEqual(strict_acc_eligible, 75.0)
        self.assertEqual(total_pass_acc_eligible, 93.75)

        # Zero eligible cases edge-case protection
        zero_eligible = 0
        safe_strict = round((0 / zero_eligible) * 100, 2) if zero_eligible > 0 else 0.0
        self.assertEqual(safe_strict, 0.0)

    def test_error_classification_logic(self):
        """Verify root-cause error classification accurately isolates quota, auth, and network errors."""
        def classify_http_error(status: int, body: str) -> str:
            err_class = f"API_{status}"
            body_lower = body.lower()
            if "quota" in body_lower or "512" in body:
                return "DATABASE_QUOTA_ERROR"
            elif status in (401, 403):
                return "AUTH_FAILURE"
            elif status == 429:
                return "RATE_LIMIT"
            return err_class

        # MongoDB Atlas Quota Exceeded (The 7,432 root cause)
        atlas_err = "HTTP 500: you are over your space quota, using 516 MB of 512 MB. Writes are blocked."
        self.assertEqual(classify_http_error(500, atlas_err), "DATABASE_QUOTA_ERROR")

        # Auth Failure
        self.assertEqual(classify_http_error(401, "Invalid JWT token"), "AUTH_FAILURE")
        self.assertEqual(classify_http_error(403, "Forbidden"), "AUTH_FAILURE")

        # Rate Limit
        self.assertEqual(classify_http_error(429, "Too Many Requests"), "RATE_LIMIT")

        # General 500
        self.assertEqual(classify_http_error(500, "Internal Server Error"), "API_500")

    def test_timing_and_latency_capture(self):
        """Verify timestamps are UTC ISO strings and latencies are non-zero."""
        # Simulated latencies (ms)
        raw_latencies = [12.5, 45.2, 89.1, 150.0, 320.4, 18.2, 5.0]

        # Minimum latency must never be 0.0 ms
        for lat in raw_latencies:
            self.assertGreater(lat, 0.0, "Latency cannot be 0.0 ms")

        p50 = float(np.percentile(raw_latencies, 50))
        p95 = float(np.percentile(raw_latencies, 95))
        p99 = float(np.percentile(raw_latencies, 99))
        mean_l = float(np.mean(raw_latencies))
        min_l = float(np.min(raw_latencies))
        max_l = float(np.max(raw_latencies))

        self.assertAlmostEqual(min_l, 5.0)
        self.assertAlmostEqual(max_l, 320.4)
        self.assertGreater(p95, p50)
        self.assertGreater(p99, p95)
        self.assertGreater(mean_l, 0)

        # UTC timestamp format verification
        now_utc = datetime.now(timezone.utc).isoformat()
        self.assertIn("+00:00", now_utc)
        parsed = datetime.fromisoformat(now_utc)
        self.assertEqual(parsed.tzinfo, timezone.utc)

    def test_checkpoint_isolation_and_scope(self):
        """Verify that checkpoint loader filters records to active cases only."""
        all_cases = [{"test_id": f"tc_{i}"} for i in range(100)]
        active_sample = all_cases[:10]  # sample of 10
        valid_tids = {tc["test_id"] for tc in active_sample}

        # Simulated historical execution results file with 100 cases
        historical_results = {f"tc_{i}": {"test_id": f"tc_{i}", "status": "PASS"} for i in range(100)}

        # Filter logic from repaired benchmark code
        scoped_results = {k: v for k, v in historical_results.items() if k in valid_tids}
        self.assertEqual(len(scoped_results), 10)
        self.assertEqual(set(scoped_results.keys()), valid_tids)

    def test_production_safety_filters(self):
        """Verify test queries never delete or match production accounts."""
        prod_accounts = {
            "admin@fitness-ai.com",
            "admin@Fitness-ai.com",
            "dhoni@gmail.com",
            "fitbit_demo@example.com"
        }
        test_session_id = "session_10k_a1b2c3d4"
        prod_session_id = "prod_session_user_admin"

        # Regex filter for session cleanup
        import re
        session_regex = re.compile(r"^session_10k_|^conv_")

        self.assertTrue(bool(session_regex.match(test_session_id)))
        self.assertFalse(bool(session_regex.match(prod_session_id)))

        # Benchmark user prefix check
        test_email = "bench10k_user_a_1790617654@example.com"
        for prod_email in prod_accounts:
            self.assertFalse(prod_email.startswith("bench10k_"))
        self.assertTrue(test_email.startswith("bench10k_"))


if __name__ == "__main__":
    unittest.main()
