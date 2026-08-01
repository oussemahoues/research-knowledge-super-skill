from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..runtime.event_store import EventStore, stable_key, utc_now


@dataclass(frozen=True)
class MigrationReport:
    run_id: str
    database_path: str
    source_records: int
    nodes: int
    edges: int
    warnings: tuple[str, ...]
    source_immutable: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "database_path": self.database_path,
            "source_records": self.source_records,
            "nodes": self.nodes,
            "edges": self.edges,
            "warnings": list(self.warnings),
            "source_immutable": self.source_immutable,
        }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: record must be an object")
        records.append(value)
    return records


def _directory_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(str(path.relative_to(root)).encode("utf-8"))
        digest.update(b"\x00")
        digest.update(path.read_bytes())
        digest.update(b"\x00")
    return digest.hexdigest()


def migrate_v2_run(v2_run: str | Path, database_path: str | Path, content_dir: str | Path) -> MigrationReport:
    root = Path(v2_run)
    if not root.is_dir():
        raise ValueError("v2 run path must be a directory")
    run_file = root / "run.json"
    if not run_file.exists():
        raise ValueError("run.json missing")
    before_digest = _directory_digest(root)
    run = json.loads(run_file.read_text(encoding="utf-8"))
    run_id = str(run.get("run_id") or "run:migrated:" + stable_key(str(root))[:12])
    target = str(run.get("target") or "Migrated v2 research run")
    as_of = str(run.get("as_of") or run.get("created_at") or utc_now())
    if len(as_of) == 10:
        as_of += "T00:00:00Z"

    db = Path(database_path)
    if db.exists():
        raise FileExistsError(f"migration destination already exists: {db}")
    content_root = Path(content_dir)
    content_root.mkdir(parents=True, exist_ok=True)
    store = EventStore(db)
    store.create_run(run_id, target, architecture="migrated-v2")
    store.append_event(run_id, "V2_MIGRATION_STARTED", {"source_path": str(root)}, f"v2-migration-start:{run_id}")

    warnings: list[str] = []
    sources = _read_jsonl(root / "sources.jsonl")
    source_episode_by_source_id: dict[str, str] = {}
    with store.connect() as conn:
        for index, source in enumerate(sources, 1):
            source_id = str(source.get("id") or f"legacy-source:{index}")
            original_hash = str(source.get("content_hash") or "")
            metadata_bytes = json.dumps(source, ensure_ascii=False, sort_keys=True).encode("utf-8")
            metadata_hash = "sha256:" + hashlib.sha256(metadata_bytes).hexdigest()
            episode_id = "episode:" + stable_key(run_id, source_id, original_hash or metadata_hash)[:24]
            content_path = content_root / f"{episode_id.replace(':', '_')}.legacy-source.json"
            content_path.write_bytes(metadata_bytes)
            conn.execute(
                """INSERT INTO source_episodes(
                    run_id,episode_id,source_id,version,locator,media_type,content_hash,content_path,
                    authority,independence_group,injection_risk,effective_at,retrieved_at,
                    supersedes_episode_id,metadata_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    run_id,
                    episode_id,
                    source_id,
                    1,
                    str(source.get("locator") or source.get("url") or "legacy:unknown"),
                    "application/vnd.evidence-research.legacy-source+json",
                    original_hash or metadata_hash,
                    str(content_path),
                    str(source.get("authority_tier") or "unknown"),
                    str(source.get("independence_group") or source_id),
                    "unverified-legacy",
                    source.get("published_at"),
                    str(source.get("accessed_at") or utc_now()),
                    None,
                    json.dumps({"migrated_from_v2": True, "legacy_record": source}, sort_keys=True),
                ),
            )
            source_episode_by_source_id[source_id] = episode_id
            if original_hash:
                warnings.append(f"{source_id}: original content bytes unavailable; legacy hash preserved but not reverified")

    records = _read_jsonl(root / "evidence-graph.jsonl")
    nodes = [record for record in records if record.get("record_type") == "node"]
    edges = [record for record in records if record.get("record_type") == "edge"]
    with store.connect() as conn:
        for node in nodes:
            data = dict(node.get("data") or {})
            data["_legacy_status"] = node.get("status")
            data["_legacy_created_at"] = node.get("created_at")
            conn.execute(
                "INSERT INTO graph_nodes(run_id,node_id,node_type,ontology_version,data_json,created_at) VALUES(?,?,?,?,?,?)",
                (
                    run_id,
                    str(node["id"]),
                    str(node.get("node_type") or "LegacyNode"),
                    0,
                    json.dumps(data, sort_keys=True),
                    str(node.get("created_at") or utc_now()),
                ),
            )
        for edge in edges:
            provenance = dict(edge.get("provenance") or {})
            legacy_source_id = provenance.get("source_id")
            episode_id = source_episode_by_source_id.get(str(legacy_source_id)) if legacy_source_id else None
            conn.execute(
                """INSERT INTO graph_edges(
                    run_id,edge_id,edge_type,from_id,to_id,ontology_version,valid_from,valid_to,
                    recorded_at,source_episode_id,provenance_json,status,supersedes_edge_id
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    run_id,
                    str(edge["id"]),
                    str(edge.get("edge_type") or "LEGACY_EDGE"),
                    str(edge["from_id"]),
                    str(edge["to_id"]),
                    0,
                    as_of,
                    None,
                    str(edge.get("created_at") or utc_now()),
                    episode_id,
                    json.dumps({**provenance, "migrated_from_v2": True}, sort_keys=True),
                    "active",
                    None,
                ),
            )

    store.append_event(
        run_id,
        "V2_MIGRATION_COMPLETED",
        {"sources": len(sources), "nodes": len(nodes), "edges": len(edges), "warnings": warnings},
        f"v2-migration-complete:{run_id}",
    )
    after_digest = _directory_digest(root)
    if before_digest != after_digest:
        raise RuntimeError("v2 source run changed during migration")
    return MigrationReport(run_id, str(db), len(sources), len(nodes), len(edges), tuple(warnings), True)
