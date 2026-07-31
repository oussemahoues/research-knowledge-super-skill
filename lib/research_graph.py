from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

NODE_TYPES = {
    "ResearchQuestion", "Hypothesis", "Claim", "EvidenceSpan", "Source",
    "Entity", "Event", "Method", "Dataset", "Finding", "ResearchGap",
}
EDGE_TYPES = {
    "ASSERTED_BY", "SUPPORTS", "CONTRADICTS", "QUALIFIES", "DERIVED_FROM",
    "ABOUT", "SAME_AS", "SUPERSEDES", "ANSWERS", "CITES",
}
CLAIM_STATUSES = {"candidate", "verified", "contested", "rejected", "superseded", "unknown"}

EDGE_ENDPOINTS = {
    "ASSERTED_BY": ({"Claim"}, {"Source"}),
    "SUPPORTS": ({"EvidenceSpan"}, {"Claim"}),
    "CONTRADICTS": ({"EvidenceSpan"}, {"Claim"}),
    "QUALIFIES": ({"EvidenceSpan", "Claim"}, {"Claim"}),
    "DERIVED_FROM": ({"Finding", "Claim"}, {"Claim", "Dataset", "Method"}),
    "ABOUT": ({"Claim", "EvidenceSpan"}, {"Entity", "Event"}),
    "SAME_AS": ({"Entity"}, {"Entity"}),
    "SUPERSEDES": ({"Claim", "Source"}, {"Claim", "Source"}),
    "ANSWERS": ({"Finding", "Claim"}, {"ResearchQuestion"}),
    "CITES": ({"Source"}, {"Source"}),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).strip().lower().split())


def stable_id(prefix: str, *parts: str, length: int = 16) -> str:
    payload = "\x1f".join(normalize(str(p)) for p in parts)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]
    return f"{prefix}:{digest}"


def content_hash(content: bytes | str) -> str:
    data = content.encode("utf-8") if isinstance(content, str) else content
    return "sha256:" + hashlib.sha256(data).hexdigest()


def make_node(node_type: str, semantic_key: str, data: dict[str, Any], *, status: str = "candidate") -> dict[str, Any]:
    if node_type not in NODE_TYPES:
        raise ValueError(f"unknown node type: {node_type}")
    if status not in CLAIM_STATUSES:
        raise ValueError(f"unknown status: {status}")
    return {
        "record_type": "node",
        "id": stable_id(node_type.lower(), semantic_key),
        "node_type": node_type,
        "status": status,
        "created_at": utc_now(),
        "data": data,
    }


def make_edge(edge_type: str, from_id: str, to_id: str, provenance: dict[str, Any]) -> dict[str, Any]:
    if edge_type not in EDGE_TYPES:
        raise ValueError(f"unknown edge type: {edge_type}")
    return {
        "record_type": "edge",
        "id": stable_id("edge", edge_type, from_id, to_id, json.dumps(provenance, sort_keys=True)),
        "edge_type": edge_type,
        "from_id": from_id,
        "to_id": to_id,
        "created_at": utc_now(),
        "provenance": provenance,
    }


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    p = Path(path)
    if not p.exists():
        return result
    for line_no, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{p}:{line_no}: invalid JSON: {exc}") from exc
        if not isinstance(obj, dict):
            raise ValueError(f"{p}:{line_no}: record must be an object")
        result.append(obj)
    return result


def atomic_write_jsonl(path: str | Path, records: Iterable[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=p.name + ".", dir=p.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            for record in records:
                fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def append_records(path: str | Path, new_records: Iterable[dict[str, Any]]) -> None:
    current = read_jsonl(path)
    combined = current + list(new_records)
    validate_records(combined)
    atomic_write_jsonl(path, combined)


@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]
    metrics: dict[str, Any]

    @property
    def passed(self) -> bool:
        return not self.errors


def validate_records(records: list[dict[str, Any]]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    ids: dict[str, dict[str, Any]] = {}
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    for i, record in enumerate(records, 1):
        rid = record.get("id")
        if not isinstance(rid, str) or not rid:
            errors.append(f"record {i}: missing id")
            continue
        if rid in ids:
            errors.append(f"duplicate id: {rid}")
        ids[rid] = record
        rtype = record.get("record_type")
        if rtype == "node":
            ntype = record.get("node_type")
            if ntype not in NODE_TYPES:
                errors.append(f"{rid}: invalid node_type {ntype!r}")
            if record.get("status") not in CLAIM_STATUSES:
                errors.append(f"{rid}: invalid status {record.get('status')!r}")
            if not isinstance(record.get("data"), dict):
                errors.append(f"{rid}: data must be an object")
            nodes[rid] = record
        elif rtype == "edge":
            etype = record.get("edge_type")
            if etype not in EDGE_TYPES:
                errors.append(f"{rid}: invalid edge_type {etype!r}")
            if not isinstance(record.get("provenance"), dict) or not record.get("provenance"):
                errors.append(f"{rid}: edge provenance required")
            edges.append(record)
        else:
            errors.append(f"{rid}: record_type must be node or edge")

    for edge in edges:
        rid = edge.get("id", "<edge>")
        from_id, to_id = edge.get("from_id"), edge.get("to_id")
        if from_id not in nodes:
            errors.append(f"{rid}: missing from node {from_id}")
            continue
        if to_id not in nodes:
            errors.append(f"{rid}: missing to node {to_id}")
            continue
        etype = edge.get("edge_type")
        if etype in EDGE_ENDPOINTS:
            allowed_from, allowed_to = EDGE_ENDPOINTS[etype]
            from_type = nodes[from_id].get("node_type")
            to_type = nodes[to_id].get("node_type")
            if from_type not in allowed_from or to_type not in allowed_to:
                errors.append(f"{rid}: {etype} endpoint types invalid: {from_type} -> {to_type}")

    claims = {rid: n for rid, n in nodes.items() if n.get("node_type") == "Claim"}
    support_count = {rid: 0 for rid in claims}
    contradiction_count = {rid: 0 for rid in claims}
    for edge in edges:
        if edge.get("edge_type") == "SUPPORTS" and edge.get("to_id") in support_count:
            support_count[edge["to_id"]] += 1
        if edge.get("edge_type") == "CONTRADICTS" and edge.get("to_id") in contradiction_count:
            contradiction_count[edge["to_id"]] += 1

    for rid, claim in claims.items():
        status = claim.get("status")
        if status == "verified" and support_count[rid] == 0:
            errors.append(f"{rid}: verified claim has no supporting evidence")
        if status == "contested" and (support_count[rid] == 0 or contradiction_count[rid] == 0):
            errors.append(f"{rid}: contested claim requires support and contradiction")
        if status == "candidate" and support_count[rid] == 0:
            warnings.append(f"{rid}: candidate claim has no evidence yet")

    return ValidationResult(
        errors=errors,
        warnings=warnings,
        metrics={
            "records": len(records),
            "nodes": len(nodes),
            "edges": len(edges),
            "claims": len(claims),
            "verified_claims": sum(1 for c in claims.values() if c.get("status") == "verified"),
            "contested_claims": sum(1 for c in claims.values() if c.get("status") == "contested"),
        },
    )
