from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from ..runtime.event_store import EventStore, stable_key, utc_now


@dataclass(frozen=True)
class TemporalNode:
    run_id: str
    node_id: str
    node_type: str
    ontology_version: int
    data: dict[str, Any]
    created_at: str


@dataclass(frozen=True)
class TemporalEdge:
    run_id: str
    edge_id: str
    edge_type: str
    from_id: str
    to_id: str
    ontology_version: int
    valid_from: str
    valid_to: str | None
    recorded_at: str
    source_episode_id: str | None
    provenance: dict[str, Any]
    status: str
    supersedes_edge_id: str | None


class TemporalGraph:
    def __init__(self, store: EventStore):
        self.store = store

    def put_node(
        self,
        run_id: str,
        node_type: str,
        semantic_key: str,
        data: dict[str, Any],
        *,
        ontology_version: int = 1,
    ) -> TemporalNode:
        node_id = f"{node_type.lower()}:" + stable_key(node_type, semantic_key)[:24]
        created_at = utc_now()
        payload = {
            "node_id": node_id,
            "node_type": node_type,
            "ontology_version": ontology_version,
            "data": data,
        }
        self.store.append_event(run_id, "GRAPH_NODE_WRITTEN", payload, f"graph-node:{run_id}:{node_id}")
        encoded = json.dumps(data, sort_keys=True)
        with self.store.connect() as conn:
            existing = conn.execute(
                "SELECT * FROM graph_nodes WHERE run_id=? AND node_id=?",
                (run_id, node_id),
            ).fetchone()
            if existing is not None and existing["data_json"] != encoded:
                raise ValueError(f"stable node identity collision for {node_id}")
            conn.execute(
                "INSERT OR IGNORE INTO graph_nodes(run_id,node_id,node_type,ontology_version,data_json,created_at) VALUES(?,?,?,?,?,?)",
                (run_id, node_id, node_type, ontology_version, encoded, created_at),
            )
            row = conn.execute(
                "SELECT * FROM graph_nodes WHERE run_id=? AND node_id=?",
                (run_id, node_id),
            ).fetchone()
        return self._node(row)

    def add_edge(
        self,
        run_id: str,
        edge_type: str,
        from_id: str,
        to_id: str,
        *,
        valid_from: str,
        valid_to: str | None = None,
        ontology_version: int = 1,
        source_episode_id: str | None = None,
        provenance: dict[str, Any] | None = None,
        status: str = "active",
        supersedes_edge_id: str | None = None,
        recorded_at: str | None = None,
    ) -> TemporalEdge:
        provenance = dict(provenance or {})
        recorded_at = recorded_at or utc_now()
        if valid_to is not None and valid_to <= valid_from:
            raise ValueError("valid_to must be later than valid_from")
        self._require_nodes(run_id, from_id, to_id)
        edge_id = "edge:" + stable_key(
            run_id,
            edge_type,
            from_id,
            to_id,
            valid_from,
            valid_to or "",
            source_episode_id or "",
            json.dumps(provenance, sort_keys=True),
        )[:24]
        payload = {
            "edge_id": edge_id,
            "edge_type": edge_type,
            "from_id": from_id,
            "to_id": to_id,
            "valid_from": valid_from,
            "valid_to": valid_to,
            "source_episode_id": source_episode_id,
        }
        self.store.append_event(run_id, "GRAPH_EDGE_WRITTEN", payload, f"graph-edge:{run_id}:{edge_id}")
        with self.store.connect() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO graph_edges(
                    run_id,edge_id,edge_type,from_id,to_id,ontology_version,valid_from,valid_to,
                    recorded_at,source_episode_id,provenance_json,status,supersedes_edge_id
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    run_id,
                    edge_id,
                    edge_type,
                    from_id,
                    to_id,
                    ontology_version,
                    valid_from,
                    valid_to,
                    recorded_at,
                    source_episode_id,
                    json.dumps(provenance, sort_keys=True),
                    status,
                    supersedes_edge_id,
                ),
            )
            row = conn.execute(
                "SELECT * FROM graph_edges WHERE run_id=? AND edge_id=?",
                (run_id, edge_id),
            ).fetchone()
        return self._edge(row)

    def supersede_edge(
        self,
        run_id: str,
        edge_id: str,
        *,
        new_to_id: str,
        valid_from: str,
        source_episode_id: str | None,
        provenance: dict[str, Any],
    ) -> TemporalEdge:
        with self.store.connect() as conn:
            old = conn.execute(
                "SELECT * FROM graph_edges WHERE run_id=? AND edge_id=?",
                (run_id, edge_id),
            ).fetchone()
        if old is None:
            raise KeyError(edge_id)
        if old["status"] == "superseded":
            with self.store.connect() as conn:
                row = conn.execute(
                    "SELECT * FROM graph_edges WHERE run_id=? AND supersedes_edge_id=? ORDER BY recorded_at DESC LIMIT 1",
                    (run_id, edge_id),
                ).fetchone()
            if row is None:
                raise ValueError(f"edge {edge_id} is superseded without a successor")
            return self._edge(row)
        if valid_from <= old["valid_from"]:
            raise ValueError("successor validity must start after the original edge")

        event_payload = {
            "edge_id": edge_id,
            "new_to_id": new_to_id,
            "valid_from": valid_from,
            "source_episode_id": source_episode_id,
        }
        event_key = f"graph-edge-supersede:{run_id}:{edge_id}:{valid_from}:{new_to_id}"
        self.store.append_event(run_id, "GRAPH_EDGE_SUPERSEDED", event_payload, event_key)
        with self.store.connect() as conn:
            conn.execute(
                "UPDATE graph_edges SET valid_to=?,status='superseded' WHERE run_id=? AND edge_id=?",
                (valid_from, run_id, edge_id),
            )
        return self.add_edge(
            run_id,
            old["edge_type"],
            old["from_id"],
            new_to_id,
            valid_from=valid_from,
            valid_to=None,
            ontology_version=int(old["ontology_version"]),
            source_episode_id=source_episode_id,
            provenance=provenance,
            status="active",
            supersedes_edge_id=edge_id,
        )

    def edges_as_of(
        self,
        run_id: str,
        as_of: str,
        *,
        recorded_by: str | None = None,
        edge_type: str | None = None,
        from_id: str | None = None,
    ) -> list[TemporalEdge]:
        clauses = ["run_id=?", "valid_from<=?", "(valid_to IS NULL OR valid_to>?)"]
        params: list[Any] = [run_id, as_of, as_of]
        if recorded_by is not None:
            clauses.append("recorded_at<=?")
            params.append(recorded_by)
        if edge_type is not None:
            clauses.append("edge_type=?")
            params.append(edge_type)
        if from_id is not None:
            clauses.append("from_id=?")
            params.append(from_id)
        query = "SELECT * FROM graph_edges WHERE " + " AND ".join(clauses) + " ORDER BY edge_type,from_id,to_id,recorded_at"
        with self.store.connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [self._edge(row) for row in rows]

    def conflicts(self, run_id: str, *, edge_type: str | None = None) -> list[tuple[TemporalEdge, TemporalEdge]]:
        clauses = [
            "a.run_id=b.run_id",
            "a.edge_id<b.edge_id",
            "a.from_id=b.from_id",
            "a.edge_type=b.edge_type",
            "a.to_id!=b.to_id",
            "a.valid_from < COALESCE(b.valid_to,'9999-12-31T23:59:59Z')",
            "b.valid_from < COALESCE(a.valid_to,'9999-12-31T23:59:59Z')",
            "a.run_id=?",
        ]
        params: list[Any] = [run_id]
        if edge_type is not None:
            clauses.append("a.edge_type=?")
            params.append(edge_type)
        with self.store.connect() as conn:
            rows = conn.execute(
                "SELECT a.edge_id AS a_id,b.edge_id AS b_id FROM graph_edges a JOIN graph_edges b ON " + " AND ".join(clauses),
                tuple(params),
            ).fetchall()
            pairs: list[tuple[TemporalEdge, TemporalEdge]] = []
            for row in rows:
                left = conn.execute("SELECT * FROM graph_edges WHERE run_id=? AND edge_id=?", (run_id, row["a_id"])).fetchone()
                right = conn.execute("SELECT * FROM graph_edges WHERE run_id=? AND edge_id=?", (run_id, row["b_id"])).fetchone()
                pairs.append((self._edge(left), self._edge(right)))
        return pairs

    def _require_nodes(self, run_id: str, from_id: str, to_id: str) -> None:
        with self.store.connect() as conn:
            rows = conn.execute(
                "SELECT node_id FROM graph_nodes WHERE run_id=? AND node_id IN (?,?)",
                (run_id, from_id, to_id),
            ).fetchall()
        present = {row["node_id"] for row in rows}
        missing = {from_id, to_id} - present
        if missing:
            raise ValueError(f"missing graph nodes: {sorted(missing)}")

    @staticmethod
    def _node(row: Any) -> TemporalNode:
        return TemporalNode(row["run_id"], row["node_id"], row["node_type"], int(row["ontology_version"]), json.loads(row["data_json"]), row["created_at"])

    @staticmethod
    def _edge(row: Any) -> TemporalEdge:
        return TemporalEdge(
            row["run_id"],
            row["edge_id"],
            row["edge_type"],
            row["from_id"],
            row["to_id"],
            int(row["ontology_version"]),
            row["valid_from"],
            row["valid_to"],
            row["recorded_at"],
            row["source_episode_id"],
            json.loads(row["provenance_json"]),
            row["status"],
            row["supersedes_edge_id"],
        )
