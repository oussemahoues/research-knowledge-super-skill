import unittest
from lib.task_graph import validate_task_graph

class TaskGraphTests(unittest.TestCase):
    def task(self,tid,consumes,produces,dependencies,owner="a"):
        return {"id":tid,"objective":tid,"consumes":consumes,"produces":produces,"dependencies":dependencies,"owner":owner,"budget":{},"done_when":"done"}
    def test_valid_graph(self):
        graph={"merge_owner":"a","tasks":[self.task("a",["brief"],["plan"],[]),self.task("b",["plan"],["result"],["a"])]}
        result=validate_task_graph(graph); self.assertTrue(result.passed,result.errors); self.assertEqual(result.levels,[["a"],["b"]])
    def test_fake_edge(self):
        graph={"merge_owner":"a","tasks":[self.task("a",[],["plan"],[]),self.task("b",["other"],["result"],["a"])]}
        result=validate_task_graph(graph); self.assertFalse(result.passed); self.assertEqual(result.metrics["fake_edges"],1)
    def test_cycle(self):
        graph={"merge_owner":"a","tasks":[self.task("a",["b-out"],["a-out"],["b"]),self.task("b",["a-out"],["b-out"],["a"])]}
        result=validate_task_graph(graph); self.assertFalse(result.passed); self.assertIn("cycle"," ".join(result.errors))

if __name__ == "__main__": unittest.main()
