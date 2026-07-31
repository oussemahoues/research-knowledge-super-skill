import unittest
from lib.source_quality import assess, independent_groups

class SourceQualityTests(unittest.TestCase):
    def test_primary_source_admissible(self):
        s={"authority_tier":"A","content_hash":"sha256:x","locator":"https://x","publisher":"Official","independence_group":"official","published_at":"2026-07-01","injection_risk":"none"}
        self.assertTrue(assess(s,as_of="2026-07-31",max_age_days=90).admissible_as_evidence)
    def test_high_injection_not_admissible(self):
        s={"authority_tier":"A","content_hash":"sha256:x","locator":"https://x","publisher":"Official","independence_group":"official","published_at":"2026-07-01","injection_risk":"high"}
        self.assertFalse(assess(s,as_of="2026-07-31",max_age_days=90).admissible_as_evidence)
    def test_independence(self): self.assertEqual(independent_groups([{"independence_group":"a"},{"independence_group":"a"},{"independence_group":"b"}]),2)

if __name__ == '__main__': unittest.main()
