from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..runtime.event_store import EventStore, utc_now


@dataclass(frozen=True)
class V3AuditResult:
    run_id: str
    passed: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    metrics: dict[str, Any]
    audited_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "3.0",
            "run_id": self.run_id,
            "passed": self.passed,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "metrics": self.metrics,
            "audited_at": self.audited_at,
        }


def audit_run(store: EventStore, run_id: str) -> V3AuditResult:
    errors: list[str] = []
    warnings: list[str] = []
    with store.connect() as conn:
        run = conn.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if run is None:
            raise KeyError(run_id)
        tasks = conn.execute("SELECT * FROM tasks WHERE run_id=? ORDER BY task_id", (run_id,)).fetchall()
        dependencies = conn.execute("SELECT * FROM task_dependencies WHERE run_id=?", (run_id,)).fetchall()
        open_interrupts = conn.execute("SELECT * FROM interrupts WHERE run_id=? AND status='OPEN'", (run_id,)).fetchall()
        claims = conn.execute("SELECT * FROM graph_nodes WHERE run_id=? AND node_type='Claim'", (run_id,)).fetchall()
        decisions = conn.execute(
            """SELECT a.* FROM adjudication_decisions a
               JOIN (SELECT claim_id,MAX(rowid) AS max_rowid FROM adjudication_decisions WHERE run_id=? GROUP BY claim_id) latest
               ON a.rowid=latest.max_rowid""",
            (run_id,),
        ).fetchall()
        episodes = conn.execute("SELECT * FROM source_episodes WHERE run_id=?", (run_id,)).fetchall()
        graph_edges = conn.execute("SELECT * FROM graph_edges WHERE run_id=?", (run_id,)).fetchall()
        unresolved_merges = conn.execute(
            "SELECT COUNT(*) AS n FROM resolution_decisions WHERE run_id=? AND decision='review' AND applied_at IS NULL AND reversed_at IS NULL",
            (run_id,),
        ).fetchone()["n"]

    task_by_id = {task["task_id"]: task for task in tasks}
    for dependency in dependencies:
        child = task_by_id.get(dependency["task_id"])
        parent = task_by_id.get(dependency["depends_on"])
        if child is None or parent is None:
            errors.append(f"dangling task dependency: {dependency['depends_on']} -> {dependency['task_id']}")
            continue
        child_inputs = set(json.loads(child["consumes_json"]))
        parent_outputs = set(json.loads(parent["produces_json"]))
        if not child_inputs & parent_outputs:
            errors.append(f"fake task dependency: {parent['task_id']} -> {child['task_id']}")
        if child["task_type"] == "verification" and child["owner"] == parent["owner"]:
            errors.append(f"self-verification violation: {child['task_id']}")

    incomplete = [task["task_id"] for task in tasks if task["state"] != "SUCCEEDED"]
    if incomplete:
        errors.append("incomplete tasks: " + ", ".join(incomplete))
    if open_interrupts:
        errors.append(f"{len(open_interrupts)} human interrupt(s) remain open")

    decision_by_claim = {row["claim_id"]: row for row in decisions}
    material_claims: list[str] = []
    for claim in claims:
        data = json.loads(claim["data_json"])
        if data.get("material", True):
            material_claims.append(claim["node_id"])
    for claim_id in material_claims:
        decision = decision_by_claim.get(claim_id)
        if decision is None:
            errors.append(f"material claim lacks adjudication: {claim_id}")
        elif decision["status"] == "needs_review":
            errors.append(f"material claim still needs review: {claim_id}")

    used_episode_ids = {edge["source_episode_id"] for edge in graph_edges if edge["source_episode_id"]}
    episode_by_id = {episode["episode_id"]: episode for episode in episodes}
    tampered = 0
    quarantined_used = 0
    legacy_unverified = 0
    for episode_id in sorted(used_episode_ids):
        episode = episode_by_id.get(episode_id)
        if episode is None:
            errors.append(f"graph edge references missing source episode: {episode_id}")
            continue
        risk = episode["injection_risk"]
        if risk == "quarantine":
            quarantined_used += 1
            errors.append(f"quarantined source episode is used by the graph: {episode_id}")
        elif risk == "unverified-legacy":
            legacy_unverified += 1
            warnings.append(f"legacy source episode cannot be byte-reverified: {episode_id}")
        else:
            path = Path(episode["content_path"])
            if not path.exists():
                tampered += 1
                errors.append(f"source episode content missing: {episode_id}")
            else:
                actual = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
                if actual != episode["content_hash"]:
                    tampered += 1
                    errors.append(f"source episode hash mismatch: {episode_id}")

    if unresolved_merges:
        warnings.append(f"{unresolved_merges} entity-resolution proposal(s) remain in review")

    status_counts: dict[str, int] = {}
    for decision in decisions:
        status_counts[decision["status"]] = status_counts.get(decision["status"], 0) + 1
    metrics = {
        "tasks": len(tasks),
        "incomplete_tasks": len(incomplete),
        "open_interrupts": len(open_interrupts),
        "claims": len(claims),
        "material_claims": len(material_claims),
        "adjudicated_claims": len(decisions),
        "verified_claims": status_counts.get("verified", 0),
        "contested_claims": status_counts.get("contested", 0),
        "needs_review_claims": status_counts.get("needs_review", 0),
        "source_episodes": len(episodes),
        "used_source_episodes": len(used_episode_ids),
        "quarantined_sources_used": quarantined_used,
        "tampered_sources": tampered,
        "legacy_unverified_sources": legacy_unverified,
        "unresolved_merge_reviews": int(unresolved_merges),
    }
    return V3AuditResult(run_id, not errors, tuple(sorted(set(errors))), tuple(sorted(set(warnings))), metrics, utc_now())
