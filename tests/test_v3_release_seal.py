from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.evidence_research.release import verify_manifest, write_manifest


class ReleaseSealTests(unittest.TestCase):
    def test_release_mode_requires_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "plugin.txt").write_text("sealed", encoding="utf-8")
            result = verify_manifest(tmp, required=True)
            self.assertFalse(result.passed)
            self.assertIn("release manifest missing", result.errors)

    def test_manifest_detects_modification_and_unsealed_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            member = root / "plugin.txt"
            member.write_text("sealed", encoding="utf-8")
            write_manifest(root)
            self.assertTrue(verify_manifest(root).passed)
            member.write_text("changed", encoding="utf-8")
            self.assertTrue(any("hash mismatch" in error for error in verify_manifest(root).errors))
            write_manifest(root)
            (root / "extra.txt").write_text("extra", encoding="utf-8")
            self.assertTrue(any("unsealed release file" in error for error in verify_manifest(root).errors))


if __name__ == "__main__":
    unittest.main()
