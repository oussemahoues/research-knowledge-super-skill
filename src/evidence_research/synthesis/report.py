from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..runtime.event_store import EventStore, utc_now

CLAIM_RE = re.compile(r"\[C:([^\]]+)\]")
EDGE_RE = re.compile(r"\[E:([^\]]+)\]")
SOURCE_RE = re.compile(r"\[S:([^\]]+)\]")


@dataclass(frozen=True)
class ReportRenderResult:
    run_id: str
    report_path: str
    included_claims: tuple[str, ...]
    contested_claims: tuple[str, ...]
    omitted_claims: tuple[str, ...]
    source_episode_ids: tuple[str, ...]
    rendered_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "report_path": self.report_path,
            "included_claims": list(self.included_claims),
            "contested_claims": list(self.contested_claims),
            "omitted_claims": list(self.omitted_claims),
            "source_episode_ids": list(self.source_episode_ids),
            "rendered_at": self.rendered_at,
        }


def _latest_decisions(conn: Any, run_id: str) -> dict[str, Any]:
    rows = conn.execute(
        """SELECT a.* FROM adjudication_decisions a
           JOIN (SELECT claim_id,MAX(rowid) AS max_rowid FROM adjudication_decisions WHERE run_id=? GROUP BY claim_id) latest
           ON a.rowid=latest.max_rowid ORDER BY a.claim_id""",
        (run_id,),
    ).fetchall()
    return {row["claim_id"]: row for row in rows}


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def render_report(
    store: EventStore,
    run_id: str,
    output_path: str | Path,
    *,
    title: str | None = None,
    as_of: str | None = None,
) -> ReportRenderResult:
    output = Path(output_path)
    with store.connect() as conn:
        run = conn.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if run is None:
            raise KeyError(run_id)
        claims = conn.execute("SELECT * FROM graph_nodes WHERE run_id=? AND node_type='Claim' ORDER BY node_id", (run_id,)).fetchall()
        decisions = _latest_decisions(conn, run_id)
        edges = {row["edge_id"]: row for row in conn.execute("SELECT * FROM graph_edges WHERE run_id=?", (run_id,)).fetchall()}
        episodes = {row["episode_id"]: row for row in conn.execute("SELECT * FROM source_episodes WHERE run_id=?", (run_id,)).fetchall()}

    included: list[str] = []
    contested: list[str] = []
    omitted: list[str] = []
    used_sources: set[str] = set()
    findings: list[str] = []
    conflicts: list[str] = []

    for claim in claims:
        claim_id = claim["node_id"]
        decision = decisions.get(claim_id)
        if decision is None or decision["status"] not in {"verified", "contested"}:
            omitted.append(claim_id)
            continue
        data = json.loads(claim["data_json"])
        text = str(data.get("text") or data.get("claim") or claim_id)
        support_ids = json.loads(decision["support_edge_ids_json"])
        contradiction_ids = json.loads(decision["contradiction_edge_ids_json"])
        source_ids = json.loads(decision["source_episode_ids_json"])
        used_sources.update(source_ids)
        markers = [f"[C:{claim_id}]", *[f"[E:{edge_id}]" for edge_id in support_ids], *[f"[S:{source_id}]" for source_id in source_ids]]
        findings.append(f"- {text} {' '.join(markers)}")
        included.append(claim_id)
        if decision["status"] == "contested":
            contested.append(claim_id)
            contradiction_sources = sorted({edges[eid]["source_episode_id"] for eid in contradiction_ids if eid in edges and edges[eid]["source_episode_id"]})
            conflict_markers = [f"[C:{claim_id}]", *[f"[E:{edge_id}]" for edge_id in contradiction_ids], *[f"[S:{source_id}]" for source_id in contradiction_sources]]
            conflicts.append(f"- {text} remains contested. {' '.join(conflict_markers)}")

    source_lines = []
    for source_id in sorted(used_sources):
        episode = episodes.get(source_id)
        if episode is not None:
            source_lines.append(f"- `{source_id}` — {episode['locator']} — hash `{episode['content_hash']}` — risk `{episode['injection_risk']}` [S:{source_id}]")

    report = f"""# {title or f'Evidence Report: {run["target"]}'}

## Research scope and as-of date

Target: {run['target']}  
As of: {as_of or run['updated_at'][:10]}

## Executive findings

{chr(10).join(findings) if findings else '- No adjudicated material findings are available.'}

## Detailed findings

{chr(10).join(findings) if findings else '- No adjudicated material findings are available.'}

## Contested or conflicting evidence

{chr(10).join(conflicts) if conflicts else '- No adjudicated contested claims are present.'}

## Limitations

- This report is a deterministic view of the latest adjudication decisions in the evidence graph.
- Claims marked `needs_review` or `rejected` are excluded from the findings.

## Unresolved research gaps

{chr(10).join(f'- `{claim_id}` has no publishable adjudication.' for claim_id in omitted) if omitted else '- No unresolved claim-status gaps remain.'}

## Source register

{chr(10).join(source_lines) if source_lines else '- No source episodes are cited.'}
"""
    _atomic_write(output, report)
    return ReportRenderResult(run_id, str(output), tuple(included), tuple(contested), tuple(omitted), tuple(sorted(used_sources)), utc_now())


def audit_rendered_report(store: EventStore, run_id: str, report_path: str | Path) -> dict[str, Any]:
    report = Path(report_path).read_text(encoding="utf-8")
    claim_ids = set(CLAIM_RE.findall(report))
    edge_ids = set(EDGE_RE.findall(report))
    source_ids = set(SOURCE_RE.findall(report))
    errors: list[str] = []
    with store.connect() as conn:
        decisions = _latest_decisions(conn, run_id)
        edges = {row["edge_id"]: row for row in conn.execute("SELECT * FROM graph_edges WHERE run_id=?", (run_id,)).fetchall()}
        episodes = {row["episode_id"] for row in conn.execute("SELECT episode_id FROM source_episodes WHERE run_id=?", (run_id,)).fetchall()}
    for claim_id in sorted(claim_ids):
        decision = decisions.get(claim_id)
        if decision is None:
            errors.append(f"report claim lacks an adjudication decision: {claim_id}")
            continue
        if decision["status"] not in {"verified", "contested"}:
            errors.append(f"report includes non-publishable claim {claim_id} with status {decision['status']}")
        allowed = set(json.loads(decision["support_edge_ids_json"])) | set(json.loads(decision["contradiction_edge_ids_json"]))
        if not edge_ids & allowed:
            errors.append(f"report claim has no cited adjudicated evidence edge: {claim_id}")
    for edge_id in sorted(edge_ids):
        if edge_id not in edges:
            errors.append(f"report evidence edge does not resolve: {edge_id}")
    for source_id in sorted(source_ids):
        if source_id not in episodes:
            errors.append(f"report source episode does not resolve: {source_id}")
    for heading in (
        "Research scope and as-of date",
        "Executive findings",
        "Detailed findings",
        "Contested or conflicting evidence",
        "Limitations",
        "Unresolved research gaps",
        "Source register",
    ):
        if f"## {heading}" not in report:
            errors.append(f"required report section missing: {heading}")
    return {
        "schema_version": "3.0",
        "run_id": run_id,
        "passed": not errors,
        "errors": errors,
        "metrics": {
            "claim_markers": len(claim_ids),
            "evidence_edge_markers": len(edge_ids),
            "source_episode_markers": len(source_ids),
        },
    }
