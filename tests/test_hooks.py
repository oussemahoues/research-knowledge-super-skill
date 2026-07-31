import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class HookTests(unittest.TestCase):
    def run_hook(self, payload):
        return subprocess.run([sys.executable, str(ROOT / "hooks/pre_tool_guard.py")], input=json.dumps(payload), text=True, capture_output=True)
    def test_report_without_markers_blocked(self):
        payload = {"tool_input": {"file_path": "/tmp/research-runs/run_demo/report.md", "content": "plain report"}}
        result = self.run_hook(payload)
        self.assertEqual(result.returncode, 2)
        self.assertIn("deny", result.stdout)
    def test_non_run_path_allowed(self):
        payload = {"tool_input": {"file_path": "/tmp/notes.md", "content": "plain"}}
        result = self.run_hook(payload)
        self.assertEqual(result.returncode, 0)

if __name__ == "__main__": unittest.main()
