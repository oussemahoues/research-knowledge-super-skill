import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from scripts.researchctl import cmd_demo

class ReportAuditTests(unittest.TestCase):
    def test_demo_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = cmd_demo(Namespace(path=tmp))
            self.assertEqual(code, 0)
            self.assertEqual(len(list(Path(tmp).glob("run_*/audit.json"))), 1)

if __name__ == "__main__": unittest.main()
