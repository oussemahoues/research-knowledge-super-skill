import unittest
from lib.entity_resolution import decision, score_pair

class EntityResolutionTests(unittest.TestCase):
    def test_identifier_drives_match(self):
        a={"entity_type":"Organization","name":"Southeast University","aliases":["SEU"],"identifiers":{"domain":"seu.edu.cn"},"neighbors":["person:1"]}
        b={"entity_type":"Organization","name":"SEU","aliases":["Southeast Univ."],"identifiers":{"domain":"seu.edu.cn"},"neighbors":["person:1"]}
        score=score_pair(a,b)
        self.assertGreaterEqual(score.total,0.65)
        self.assertIn(decision(score),{"review","auto_merge"})
    def test_type_mismatch_rejects(self):
        score=score_pair({"entity_type":"Person","name":"Apple"},{"entity_type":"Organization","name":"Apple"})
        self.assertEqual(decision(score),"reject")

if __name__ == '__main__': unittest.main()
