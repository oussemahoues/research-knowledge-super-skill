from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DocumentationQualityTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        path = ROOT / relative
        self.assertTrue(path.is_file(), f"missing documentation contract: {relative}")
        return path.read_text(encoding="utf-8")

    def test_core_references_are_operational_not_stage_cards(self) -> None:
        required_sections = {
            "references/architecture.md": ["## Canonical state", "## Failure and recovery model", "## Implemented retrieval surface"],
            "references/evaluation.md": ["## Layer 1: deterministic run-completion audit", "## Layer 3: release qualification", "## Metrics and denominators"],
            "references/evidence-ontology.md": ["## Bitemporal semantics", "## Entity resolution", "## Validation checklist"],
            "references/report-contract.md": ["## Publishability", "## Marker audit", "## Completion versus report validation"],
            "references/security.md": ["## Threat model", "## Acquisition controls", "## Known limitations", "## Incident procedure"],
            "references/source-policy.md": ["## Independence", "## Acquisition and versioning", "## Evidence suitability"],
            "references/implementation-status.md": ["## Shipped local capabilities", "## Not shipped as v3 capabilities", "## Required wording"],
        }
        for relative, sections in required_sections.items():
            content = self.read(relative)
            self.assertGreaterEqual(len(content), 2500, f"{relative} regressed to a stub")
            for section in sections:
                self.assertIn(section, content, f"{relative} missing {section}")

    def test_adrs_record_enforceable_decisions(self) -> None:
        for number in range(1, 6):
            relative = f"docs/adr/{number:04d}-" + {
                1: "event-sourced-runtime.md",
                2: "temporal-evidence-model.md",
                3: "adaptive-orchestration.md",
                4: "hybrid-retrieval.md",
                5: "security-boundaries.md",
            }[number]
            content = self.read(relative)
            self.assertGreaterEqual(len(content), 2500, f"{relative} regressed to a decision blurb")
            for section in ("## Context", "## Decision", "## Alternatives considered", "## Verification"):
                self.assertIn(section, content, f"{relative} missing {section}")

    def test_v3_references_do_not_restore_v2_canonical_state(self) -> None:
        architecture = self.read("references/architecture.md")
        self.assertIn("`state.db` is the canonical transaction state", architecture)
        self.assertNotIn("`sources.jsonl`, `evidence-graph.jsonl`, and `decisions.jsonl` are canonical", architecture)

        security = self.read("references/security.md")
        self.assertIn("src/evidence_research/acquisition/source_episodes.py", security)
        self.assertIn("v2 `lib/injection_guard.py`", security)

    def test_retrieval_claims_match_shipped_runtime(self) -> None:
        adr = self.read("docs/adr/0004-hybrid-retrieval.md")
        status = self.read("references/implementation-status.md")
        self.assertIn("does **not** implement vector", adr)
        self.assertIn("No vector semantic retriever", status)
        self.assertIn("lexical ranking", adr)
        self.assertIn("graph-neighborhood", adr)
        self.assertIn("bounded shortest paths", adr)

    def test_audit_contract_separates_completion_report_and_release(self) -> None:
        command = self.read("commands/research-audit.md")
        auditor = self.read("agents/independent-auditor.md")
        for content in (command, auditor):
            self.assertIn("completion", content.lower())
            self.assertIn("report", content.lower())
            self.assertIn("release", content.lower())
            self.assertIn("does not", content.lower())
        self.assertGreaterEqual(len(command), 3500, "research-audit command regressed to a stub")
        self.assertGreaterEqual(len(auditor), 4500, "independent-auditor contract regressed to a stub")

    def test_material_cli_gates_have_command_contracts(self) -> None:
        checks = {
            "commands/research-verify.md": "verify-claim",
            "commands/research-capabilities.md": "researchctl.py capabilities",
            "commands/research-migrate.md": "migrate-v2",
        }
        for relative, command in checks.items():
            content = self.read(relative)
            self.assertGreaterEqual(len(content), 1200, f"{relative} regressed to a stub")
            self.assertIn(command, content)


if __name__ == "__main__":
    unittest.main()
