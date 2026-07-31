import unittest
from lib.research_graph import make_edge, make_node, validate_records

class GraphTests(unittest.TestCase):
    def test_verified_claim_requires_support(self):
        claim = make_node("Claim", "x", {"text": "x"}, status="verified")
        result = validate_records([claim])
        self.assertFalse(result.passed)
        self.assertIn("verified claim has no supporting evidence", " ".join(result.errors))
    def test_valid_support(self):
        claim = make_node("Claim", "x", {"text": "x"}, status="verified")
        evidence = make_node("EvidenceSpan", "e", {"text": "x", "source_id": "source:s"})
        edge = make_edge("SUPPORTS", evidence["id"], claim["id"], {"source_id": "source:s", "locator": "p1"})
        self.assertTrue(validate_records([claim, evidence, edge]).passed)
    def test_invalid_endpoint_types(self):
        a = make_node("Entity", "a", {"name": "a"}); b = make_node("Claim", "b", {"text": "b"})
        edge = make_edge("SAME_AS", a["id"], b["id"], {"source_id": "source:s"})
        self.assertFalse(validate_records([a, b, edge]).passed)

if __name__ == "__main__": unittest.main()
