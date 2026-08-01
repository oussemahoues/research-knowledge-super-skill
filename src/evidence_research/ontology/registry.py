from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from ..runtime.event_store import EventStore, utc_now
from .compiler import validate_ontology


@dataclass(frozen=True)
class OntologyVersion:
    run_id: str
    version: int
    ontology_hash: str
    ontology: dict[str, Any]
    status: str
    created_at: str


@dataclass(frozen=True)
class EvolutionCheck:
    compatible: bool
    breaking_changes: tuple[str, ...]
    additive_changes: tuple[str, ...]


def check_evolution(previous: dict[str, Any], proposed: dict[str, Any]) -> EvolutionCheck:
    breaking: list[str] = []
    additive: list[str] = []
    old_entities = previous.get("entities", {})
    new_entities = proposed.get("entities", {})
    old_relations = previous.get("relations", {})
    new_relations = proposed.get("relations", {})

    for name in old_entities:
        if name not in new_entities:
            breaking.append(f"entity type removed: {name}")
    for name in new_entities:
        if name not in old_entities:
            additive.append(f"entity type added: {name}")
    for name, old_spec in old_relations.items():
        if name not in new_relations:
            breaking.append(f"relation removed: {name}")
            continue
        new_spec = new_relations[name]
        if old_spec.get("domain") != new_spec.get("domain") or old_spec.get("range") != new_spec.get("range"):
            breaking.append(f"relation signature changed: {name}")
    for name in new_relations:
        if name not in old_relations:
            additive.append(f"relation added: {name}")
    return EvolutionCheck(not breaking, tuple(breaking), tuple(additive))


class OntologyRegistry:
    def __init__(self, store: EventStore):
        self.store = store

    def store_version(
        self,
        run_id: str,
        ontology: dict[str, Any],
        *,
        activate: bool = False,
        allow_breaking: bool = False,
    ) -> OntologyVersion:
        validation = validate_ontology(ontology)
        if not validation.passed:
            raise ValueError("; ".join(validation.errors))
        encoded = json.dumps(ontology, sort_keys=True, separators=(",", ":"))
        digest = "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        with self.store.connect() as conn:
            existing = conn.execute(
                "SELECT * FROM ontology_versions WHERE run_id=? AND ontology_hash=?",
                (run_id, digest),
            ).fetchone()
            if existing is not None:
                return self._from_row(existing)
            current = conn.execute(
                "SELECT * FROM ontology_versions WHERE run_id=? AND status='active' ORDER BY ontology_version DESC LIMIT 1",
                (run_id,),
            ).fetchone()
            next_version = int(conn.execute(
                "SELECT COALESCE(MAX(ontology_version),0)+1 AS next_version FROM ontology_versions WHERE run_id=?",
                (run_id,),
            ).fetchone()["next_version"])
        if current is not None:
            evolution = check_evolution(json.loads(current["ontology_json"]), ontology)
            if not evolution.compatible and not allow_breaking:
                raise ValueError("breaking ontology migration requires explicit approval: " + "; ".join(evolution.breaking_changes))
        status = "active" if activate else "draft"
        payload = {"ontology_version": next_version, "ontology_hash": digest, "status": status}
        self.store.append_event(run_id, "ONTOLOGY_VERSION_STORED", payload, f"ontology:{run_id}:{digest}")
        with self.store.connect() as conn:
            if activate:
                conn.execute("UPDATE ontology_versions SET status='superseded' WHERE run_id=? AND status='active'", (run_id,))
            conn.execute(
                "INSERT INTO ontology_versions(run_id,ontology_version,ontology_hash,ontology_json,status,created_at) VALUES(?,?,?,?,?,?)",
                (run_id, next_version, digest, encoded, status, utc_now()),
            )
            row = conn.execute(
                "SELECT * FROM ontology_versions WHERE run_id=? AND ontology_version=?",
                (run_id, next_version),
            ).fetchone()
        return self._from_row(row)

    def activate(self, run_id: str, version: int) -> OntologyVersion:
        with self.store.connect() as conn:
            row = conn.execute(
                "SELECT * FROM ontology_versions WHERE run_id=? AND ontology_version=?",
                (run_id, version),
            ).fetchone()
        if row is None:
            raise KeyError(version)
        self.store.append_event(run_id, "ONTOLOGY_VERSION_ACTIVATED", {"ontology_version": version}, f"ontology-activate:{run_id}:{version}")
        with self.store.connect() as conn:
            conn.execute("UPDATE ontology_versions SET status='superseded' WHERE run_id=? AND status='active'", (run_id,))
            conn.execute("UPDATE ontology_versions SET status='active' WHERE run_id=? AND ontology_version=?", (run_id, version))
            row = conn.execute(
                "SELECT * FROM ontology_versions WHERE run_id=? AND ontology_version=?",
                (run_id, version),
            ).fetchone()
        return self._from_row(row)

    def active(self, run_id: str) -> OntologyVersion | None:
        with self.store.connect() as conn:
            row = conn.execute(
                "SELECT * FROM ontology_versions WHERE run_id=? AND status='active' ORDER BY ontology_version DESC LIMIT 1",
                (run_id,),
            ).fetchone()
        return None if row is None else self._from_row(row)

    def versions(self, run_id: str) -> list[OntologyVersion]:
        with self.store.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM ontology_versions WHERE run_id=? ORDER BY ontology_version",
                (run_id,),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _from_row(row: Any) -> OntologyVersion:
        return OntologyVersion(
            row["run_id"],
            int(row["ontology_version"]),
            row["ontology_hash"],
            json.loads(row["ontology_json"]),
            row["status"],
            row["created_at"],
        )
