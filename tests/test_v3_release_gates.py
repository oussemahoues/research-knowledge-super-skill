from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.evidence_research.acquisition import scan_untrusted_content
from src.evidence_research.evals import evaluate_promotion
from src.evidence_research.runtime import DurableExecutor, EventStore

ROOT = Path(__file__).resolve().parents[1]


class ReleaseGateTests(unittest.TestCase):
    def test_promotion_requires_every_numeric_gate(self):
        passing = {
            "claim_evidence_coverage": 1.0,
            "citation_resolvability": 1.0,
            "unsupported_material_claims": 0,
            "contested_claim_disclosure": 1.0,
            "citation_entailment": 0.96,
            "auto_merge_precision": 0.99,
            "temporal_validity_accuracy": 0.96,
            "multi_hop_recall_at_10": 0.91,
            "resume_idempotency_correctness": 1.0,
            "fake_task_dependencies": 0,
            "self_verification_violations": 0,
            "unbounded_loops": 0,
            "successful_injection_attacks": 0,
        }
        self.assertTrue(evaluate_promotion(passing, control=passing).passed)
        failing = dict(passing)
        failing["citation_entailment"] = 0.90
        result = evaluate_promotion(failing, control=passing)
        self.assertFalse(result.passed)
        self.assertTrue(any("citation_entailment" in error for error in result.errors))

    def test_security_corpus_matches_expected_risk(self):
        cases = json.loads((ROOT / "evals" / "security-fixtures.json").read_text(encoding="utf-8"))
        failures = []
        for case in cases:
            risk, _findings = scan_untrusted_content(case["content"])
            if risk != case["expected_risk"]:
                failures.append(f"{case['id']}: {risk} != {case['expected_risk']}")
        self.assertEqual([], failures)

    def test_expired_worker_lease_is_recovered_without_unbounded_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EventStore(Path(tmp) / "state.db")
            store.create_run("run:lease", "Lease recovery")
            executor = DurableExecutor(store)
            executor.register_graph("run:lease", {"tasks": [{
                "id": "task-a", "objective": "Lease test", "task_type": "research",
                "owner": "worker", "consumes": [], "produces": ["a.json"],
                "dependencies": [], "done_when": "artifact exists", "max_attempts": 2,
                "failure_policy": "block"
            }]})
            with store.connect() as conn:
                conn.execute("UPDATE tasks SET state='RUNNING',attempt_count=1,lease_owner='dead-worker',lease_expires_at='2020-01-01T00:00:00Z' WHERE run_id='run:lease' AND task_id='task-a'")
                conn.execute("INSERT INTO task_attempts(run_id,task_id,attempt,state,worker_id,started_at) VALUES('run:lease','task-a',1,'RUNNING','dead-worker','2020-01-01T00:00:00Z')")
            recovered = executor.recover_stale_leases("run:lease", now="2026-08-01T00:00:00Z")
            self.assertEqual(["task-a"], recovered)
            self.assertEqual(["task-a"], executor.ready_tasks("run:lease"))


if __name__ == "__main__":
    unittest.main()
