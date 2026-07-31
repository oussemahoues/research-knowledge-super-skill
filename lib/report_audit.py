from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .research_graph import read_jsonl, validate_records

CLAIM_RE = re.compile(r"\[C:([A-Za-z0-9:_-]+)\]")
SOURCE_RE = re.compile(r"\[S:([A-Za-z0-9:_-]+)(?:#([^\]]+))?\]")
REQUIRED_HEADINGS = [
    "research scope", "executive findings", "detailed findings",
    "contested", "limitations", "unresolved research gaps", "source register",
]


def audit_report(run_dir: str | Path) -> dict[str, Any]:
    root = Path(run_dir)
    report_path = root / "report.md"
    graph_path = root / "evidence-graph.jsonl"
    sources_path = root / "sources.jsonl"
    errors: list[str] = []
    warnings: list[str] = []

    if not report_path.exists():
        return {"passed": False, "errors": ["report.md missing"], "warnings": [], "metrics": {}}
    report = report_path.read_text(encoding="utf-8")
    records = read_jsonl(graph_path)
    graph_validation = validate_records(records)
    errors.extend(graph_validation.errors)
    warnings.extend(graph_validation.warnings)
    nodes = {r["id"]: r for r in records if r.get("record_type") == "node"}
    edges = [r for r in records if r.get("record_type") == "edge"]
    sources = {r.get("id"): r for r in read_jsonl(sources_path)}

    claim_markers = CLAIM_RE.findall(report)
    source_markers = SOURCE_RE.findall(report)
    unique_claims = set(claim_markers)
    unique_sources = {sid for sid, _ in source_markers}

    for cid in unique_claims:
        node = nodes.get(cid)
        if not node or node.get("node_type") != "Claim":
            errors.append(f"report claim marker does not resolve: {cid}")
            continue
        if node.get("status") not in {"verified", "contested"}:
            errors.append(f"report includes non-adjudicated claim {cid} with status {node.get('status')}")

    for sid in unique_sources:
        if sid not in sources:
            errors.append(f"report source marker does not resolve: {sid}")

    support_by_claim = {cid: [] for cid in unique_claims}
    contradiction_by_claim = {cid: [] for cid in unique_claims}
    for edge in edges:
        if edge.get("to_id") in unique_claims and edge.get("edge_type") == "SUPPORTS":
            support_by_claim[edge["to_id"]].append(edge["from_id"])
        if edge.get("to_id") in unique_claims and edge.get("edge_type") == "CONTRADICTS":
            contradiction_by_claim[edge["to_id"]].append(edge["from_id"])

    unsupported = [cid for cid, evidence in support_by_claim.items() if not evidence]
    for cid in unsupported:
        errors.append(f"report claim has no support edge: {cid}")
    for cid in unique_claims:
        node = nodes.get(cid, {})
        if node.get("status") == "contested" and not contradiction_by_claim.get(cid):
            errors.append(f"contested report claim has no contradiction edge: {cid}")

    lower = report.lower()
    for heading in REQUIRED_HEADINGS:
        if heading not in lower:
            errors.append(f"required report section missing: {heading}")
    if not re.search(r"\bas[- ]of\b.{0,30}\b20\d{2}-\d{2}-\d{2}\b", report, re.I | re.S):
        errors.append("report requires an ISO as-of date")

    factual_paragraphs = []
    for block in re.split(r"\n\s*\n", report):
        stripped = block.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("-") or stripped.startswith("|"):
            continue
        if len(stripped.split()) >= 8:
            factual_paragraphs.append(stripped)
    unmarked_paragraphs = [p[:120] for p in factual_paragraphs if not CLAIM_RE.search(p)]
    if unmarked_paragraphs:
        warnings.append(f"{len(unmarked_paragraphs)} prose paragraphs have no claim marker")

    claim_coverage = 1.0 if not unique_claims else (len(unique_claims) - len(unsupported)) / len(unique_claims)
    source_resolvability = 1.0 if not unique_sources else sum(1 for sid in unique_sources if sid in sources) / len(unique_sources)
    metrics = {
        "claim_markers": len(claim_markers),
        "unique_report_claims": len(unique_claims),
        "source_markers": len(source_markers),
        "unique_report_sources": len(unique_sources),
        "unsupported_claims": len(unsupported),
        "claim_evidence_coverage": round(claim_coverage, 4),
        "citation_resolvability": round(source_resolvability, 4),
        "unmarked_prose_paragraphs": len(unmarked_paragraphs),
        **{f"graph_{k}": v for k, v in graph_validation.metrics.items()},
    }
    return {"passed": not errors, "errors": errors, "warnings": warnings, "metrics": metrics}
