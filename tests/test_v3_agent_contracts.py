from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AgentContractTests(unittest.TestCase):
    def test_v3_roles_exist_and_use_canonical_state_contracts(self):
        required = {
            "research-orchestrator.md", "source-scout.md", "evidence-curator.md",
            "claim-verifier.md", "synthesis-editor.md", "ontology-architect.md",
            "retrieval-planner.md", "independent-auditor.md",
        }
        present = {path.name for path in (ROOT / "agents").glob("*.md")}
        self.assertTrue(required <= present, sorted(required - present))
        orchestrator = (ROOT / "agents" / "research-orchestrator.md").read_text(encoding="utf-8")
        curator = (ROOT / "agents" / "evidence-curator.md").read_text(encoding="utf-8")
        verifier = (ROOT / "agents" / "claim-verifier.md").read_text(encoding="utf-8")
        synthesis = (ROOT / "agents" / "synthesis-editor.md").read_text(encoding="utf-8")
        self.assertIn("state.db", orchestrator)
        self.assertIn("JSONL is export only", curator)
        self.assertIn("Never self-verify", verifier)
        self.assertIn("resolvable claim, evidence-edge, and source-episode markers", synthesis)
        self.assertNotIn("Own writes to `sources.jsonl`", curator)


if __name__ == "__main__":
    unittest.main()
