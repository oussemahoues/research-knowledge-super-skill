import tempfile
import unittest
from lib.run_state import create_run, load_run, transition, validate_history

class RunStateTests(unittest.TestCase):
    def contract(self):
        return {"target":"A sufficiently specific research target","as_of":"2026-07-31","questions":[{"id":"q1","text":"q","kind":"verification"}],"acceptance_criteria":[{"id":"a1","criterion":"c","measure":"m"}]}
    def test_legal_transitions(self):
        with tempfile.TemporaryDirectory() as tmp:
            run=create_run(tmp,self.contract()); transition(run,"PLANNED","planned")
            self.assertEqual(load_run(run)["state"],"PLANNED"); self.assertEqual(validate_history(load_run(run)),[])
    def test_illegal_transition(self):
        with tempfile.TemporaryDirectory() as tmp:
            run=create_run(tmp,self.contract())
            with self.assertRaises(ValueError): transition(run,"VERIFYING","skip")
    def test_block_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            run=create_run(tmp,self.contract()); transition(run,"BLOCKED","missing source"); transition(run,"SCOPED","resume")
            self.assertEqual(load_run(run)["state"],"SCOPED")

if __name__ == "__main__": unittest.main()
