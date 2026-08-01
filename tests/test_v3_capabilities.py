from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.evidence_research.runtime import evaluate_capabilities, parse_capabilities

ROOT = Path(__file__).resolve().parents[1]


class CapabilityTests(unittest.TestCase):
    def test_declared_missing_capabilities_fail_closed(self):
        result = evaluate_capabilities(["read-local"], strict=False)
        self.assertFalse(result.passed)
        self.assertFalse(result.research_capability_satisfied)

    def test_unknown_capabilities_warn_unless_strict(self):
        permissive = evaluate_capabilities(None, strict=False)
        strict = evaluate_capabilities(None, strict=True)
        self.assertTrue(permissive.passed)
        self.assertFalse(strict.passed)
        self.assertFalse(strict.discovery_available)

    def test_declared_supported_capabilities_pass(self):
        result = evaluate_capabilities(["read-local", "web-search"])
        self.assertTrue(result.passed)
        self.assertEqual(("read-local", "web-search"), result.available)

    def test_environment_parser_is_deterministic(self):
        self.assertEqual(("read-local", "web-search"), parse_capabilities("web-search, read-local,web-search"))

    def test_cli_init_persists_capability_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            command = [
                sys.executable, "-B", str(ROOT / "scripts" / "researchctl_v3.py"), "init",
                "--root", tmp, "--target", "Capability test",
                "--capability", "read-local", "--capability", "web-search",
            ]
            result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            manifest = json.loads((Path(payload["run_path"]) / "run.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["capability_check"]["passed"])
            self.assertIn("web-search", manifest["capability_check"]["available"])


if __name__ == "__main__":
    unittest.main()
