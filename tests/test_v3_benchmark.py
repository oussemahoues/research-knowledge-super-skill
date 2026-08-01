from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.evidence_research.evals import load_corpus, run_benchmark

ROOT = Path(__file__).resolve().parents[1]


class BenchmarkTests(unittest.TestCase):
    def test_fixed_corpus_has_exact_100_case_contract(self):
        corpus = load_corpus(ROOT / "evals" / "benchmark-v3.json")
        self.assertEqual(100, len(corpus["cases"]))

    def test_fixed_corpus_passes_promotion_gates(self):
        control = json.loads((ROOT / "evals" / "baseline-v2" / "promotion-metrics.json").read_text(encoding="utf-8"))
        report = run_benchmark(ROOT / "evals" / "benchmark-v3.json", control_metrics=control)
        failures = [case.case_id for case in report.cases if not case.passed]
        self.assertEqual([], failures)
        self.assertTrue(report.promotion.passed, report.promotion.errors)
        self.assertTrue(report.passed)
        self.assertEqual(100, report.passed_cases)


if __name__ == "__main__":
    unittest.main()
