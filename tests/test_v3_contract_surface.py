from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class V3ContractSurfaceTests(unittest.TestCase):
    def test_plugin_readme_and_harnesses_are_v3(self):
        plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual("3.0.0", plugin["version"])
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Evidence Research v3", readme)
        self.assertIn("SQLite is canonical", readme)
        for path in (ROOT / "harness-config.yaml", ROOT / ".claude" / "harness-config.yaml"):
            text = path.read_text(encoding="utf-8")
            self.assertIn("version: 3.0.0", text)
            self.assertIn("engine: sqlite", text)
            self.assertIn("jsonl_role: interchange-only", text)
            self.assertIn("independent-auditor", text)

    def test_all_stage_skills_use_v3_canonical_contracts(self):
        failures: list[str] = []
        forbidden = (
            'schema_version": "2.0',
            "canonical JSONL",
            "Own `run.json`",
            "Own writes to `sources.jsonl`",
            "append to `decisions.jsonl`",
            "appends a passing batch to `evidence-graph.jsonl`",
        )
        for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
            text = path.read_text(encoding="utf-8")
            for phrase in forbidden:
                if phrase in text:
                    failures.append(f"{path.parent.name}: forbidden v2 contract phrase {phrase}")
            if not re.search(r'"schema_version"\s*:\s*"3\.0"', text):
                failures.append(f"{path.parent.name}: missing v3 JSON output contract")
        self.assertEqual([], failures, "\n".join(failures))

    def test_release_workflow_contains_complete_seal_sequence(self):
        workflow = (ROOT / ".github" / "workflows" / "release-verify.yml").read_text(encoding="utf-8")
        ordered = [
            "python -B verify.py",
            "python -B scripts/run_benchmark.py",
            "python -B scripts/build_manifest.py",
            "python -B verify.py --release",
        ]
        positions = [workflow.index(command) for command in ordered]
        self.assertEqual(sorted(positions), positions)
        self.assertIn('python-version: ["3.10", "3.11", "3.12", "3.13"]', workflow)


if __name__ == "__main__":
    unittest.main()
