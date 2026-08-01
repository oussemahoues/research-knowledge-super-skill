from __future__ import annotations

import unittest

from src.evidence_research.runtime import evaluate_capabilities, parse_capabilities


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


if __name__ == "__main__":
    unittest.main()
