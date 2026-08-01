#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evidence_research.acquisition import SourceEpisodeStore
from src.evidence_research.audit import audit_run
from src.evidence_research.graph import TemporalGraph
from src.evidence_research.runtime import DurableExecutor, EventStore, TaskResult
from src.evidence_research.runtime.event_store import stable_key
from src.evidence_research.verification import EvidenceChainVerifier


def _atomic_json(path: Path, value: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def run_demo(path: str | Path) -> int:
    root = Path(path)
    run_dir = root / "run_v3_demo"
    run_dir.mkdir(parents=True, exist_ok=True)
    store = EventStore(run_dir / "state.db")
    run_id = "run:v3-demo"
    with store.connect() as conn:
        exists = conn.execute("SELECT 1 FROM runs WHERE run_id=?", (run_id,)).fetchone()
    if exists is None:
        store.create_run(run_id, "Verify the Evidence Research v3 execution path", "single")
        executor = DurableExecutor(store)
        executor.register_graph(run_id, {
            "tasks": [{
                "id": "demo-task", "objective": "Exercise durable execution", "task_type": "research",
                "owner": "demo-worker", "consumes": [], "produces": ["demo.json"],
                "dependencies": [], "done_when": "demo artifact exists", "max_attempts": 1,
                "failure_policy": "block"
            }]
        })
        artifact = run_dir / "demo.json"
        artifact.write_text('{"demo":true}\n', encoding="utf-8")
        executor.run_task(run_id, "demo-task", "demo-worker", lambda: TaskResult([
            {"artifact_id": "artifact:demo", "path": str(artifact), "content_hash": "sha256:" + stable_key(artifact.read_text(encoding="utf-8")), "media_type": "application/json"}
        ], {"demo": True}))
        episode = SourceEpisodeStore(store, run_dir / "source-episodes").record(
            run_id, "source:demo", "demo://controlled-trial#p1",
            "The controlled trial reported a 20 percent reduction in median inspection time.",
            authority="primary-controlled-trial", independence_group="demo-trial-1",
            effective_at="2026-01-10T00:00:00Z"
        )
        graph = TemporalGraph(store)
        claim = graph.put_node(run_id, "Claim", "demo-claim", {"text": "The trial reported a 20 percent reduction in median inspection time.", "material": True})
        evidence = graph.put_node(run_id, "EvidenceSpan", "demo-evidence", {"text": "The controlled trial reported a 20 percent reduction in median inspection time.", "locator": "paragraph 1"})
        graph.add_edge(run_id, "SUPPORTS", evidence.node_id, claim.node_id, valid_from="2026-01-10T00:00:00Z", source_episode_id=episode.episode_id, provenance={"locator": "paragraph 1"})
        verification = EvidenceChainVerifier(store).verify_claim(run_id, claim.node_id)
        if verification.status != "verified":
            raise RuntimeError(json.dumps(verification.to_dict()))
    result = audit_run(store, run_id)
    _atomic_json(run_dir / "audit.json", result.to_dict())
    payload = {"run_path": str(run_dir), "run_id": run_id, "audit_path": str(run_dir / "audit.json"), "audit": result.to_dict()}
    print(json.dumps(payload, indent=2))
    return 0 if result.passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(prog="researchctl demo")
    parser.add_argument("command")
    parser.add_argument("path")
    args = parser.parse_args()
    return run_demo(args.path)


if __name__ == "__main__":
    raise SystemExit(main())
