from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.evidence_research.acquisition import SourceEpisodeStore
from src.evidence_research.graph import TemporalGraph
from src.evidence_research.runtime import EventStore
from src.evidence_research.synthesis import audit_rendered_report, render_report
from src.evidence_research.verification import EvidenceChainVerifier


class V3ReportRendererTests(unittest.TestCase):
    def test_renderer_uses_only_adjudicated_claims_and_resolvable_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = EventStore(root / "state.db")
            store.create_run("run:report", "Report target")
            episode = SourceEpisodeStore(store, root / "episodes").record(
                "run:report",
                "source:a",
                "demo://a#p1",
                "The controlled test reduced inspection time by 20 percent.",
                authority="primary",
                independence_group="trial-a",
            )
            graph = TemporalGraph(store)
            claim = graph.put_node("run:report", "Claim", "claim-a", {"text": "The controlled test reduced inspection time by 20 percent.", "material": True})
            omitted = graph.put_node("run:report", "Claim", "claim-b", {"text": "An unsupported claim.", "material": True})
            evidence = graph.put_node("run:report", "EvidenceSpan", "evidence-a", {"text": "The controlled test reduced inspection time by 20 percent."})
            edge = graph.add_edge("run:report", "SUPPORTS", evidence.node_id, claim.node_id, valid_from="2026-01-01T00:00:00Z", source_episode_id=episode.episode_id)
            decision = EvidenceChainVerifier(store).verify_claim("run:report", claim.node_id)
            self.assertEqual("verified", decision.status)
            result = render_report(store, "run:report", root / "report.md", as_of="2026-08-01")
            self.assertIn(claim.node_id, result.included_claims)
            self.assertIn(omitted.node_id, result.omitted_claims)
            text = (root / "report.md").read_text(encoding="utf-8")
            self.assertIn(f"[C:{claim.node_id}]", text)
            self.assertIn(f"[E:{edge.edge_id}]", text)
            self.assertIn(f"[S:{episode.episode_id}]", text)
            self.assertNotIn("An unsupported claim.", text.split("## Executive findings", 1)[1].split("## Detailed findings", 1)[0])
            audit = audit_rendered_report(store, "run:report", root / "report.md")
            self.assertTrue(audit["passed"], audit["errors"])


if __name__ == "__main__":
    unittest.main()
