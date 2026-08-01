from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable

from ..runtime.event_store import EventStore, stable_key, utc_now
from .graph_search import active_edges, communities, expand, shortest_path
from .lexical import lexical_rank
from .query import classify_query


@dataclass(frozen=True)
class RetrievalContext:
    trace_id: str
    query_class: str
    methods: tuple[str, ...]
    node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]
    paths: tuple[tuple[str, ...], ...]
    source_episode_ids: tuple[str, ...]
    missing_links: tuple[str, ...]
    token_estimate: int
    serialized: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id, "query_class": self.query_class,
            "methods": list(self.methods), "node_ids": list(self.node_ids),
            "edge_ids": list(self.edge_ids), "paths": [list(path) for path in self.paths],
            "source_episode_ids": list(self.source_episode_ids),
            "missing_links": list(self.missing_links), "token_estimate": self.token_estimate,
            "serialized": self.serialized,
        }


class HybridRetriever:
    def __init__(self, store: EventStore):
        self.store = store

    def retrieve(self, run_id: str, query: str, *, entity_ids: Iterable[str] = (), as_of: str | None = None, limit: int = 12, max_hops: int = 3) -> RetrievalContext:
        entity_ids = tuple(dict.fromkeys(entity_ids))
        query_class = classify_query(query, entity_count=len(entity_ids))
        methods: list[str] = []
        missing: list[str] = []
        paths: list[tuple[str, ...]] = []
        with self.store.connect() as conn:
            node_rows = conn.execute("SELECT node_id,node_type,data_json FROM graph_nodes WHERE run_id=?", (run_id,)).fetchall()
            all_edges = active_edges(conn, run_id, as_of)
            lexical = lexical_rank(node_rows, query, limit=max(limit, 20))
        ranked_nodes = [node_id for node_id, _score in lexical]
        edge_ids: list[str] = []
        if lexical:
            methods.append("lexical")
        seeds = list(entity_ids) or ranked_nodes[:3]
        if query_class in {"entity-local", "direct", "comparative", "temporal", "causal-event"} and seeds:
            methods.append("graph-neighborhood")
            selected_edges = [edge for edge in all_edges if not (query_class == "causal-event") or edge["edge_type"] in {"CAUSES", "TRIGGERS", "PRECEDES", "ENABLES"}]
            neighborhood_nodes, neighborhood_edges = expand(selected_edges, seeds, hops=2 if query_class in {"comparative", "causal-event"} else 1)
            ranked_nodes = self._rrf([ranked_nodes, list(neighborhood_nodes)])
            edge_ids.extend(neighborhood_edges)
        if query_class == "multi-hop-path":
            methods.append("path")
            if len(seeds) < 2:
                missing.append("Two linked entities are required for path retrieval.")
            else:
                for left, right in zip(seeds, seeds[1:]):
                    path = shortest_path(all_edges, left, right, max_hops=max_hops)
                    if path is None:
                        missing.append(f"No path found between {left} and {right} within {max_hops} hops.")
                    else:
                        paths.append(path)
                        ranked_nodes = self._rrf([ranked_nodes, list(path[::2])])
                        edge_ids.extend(path[1::2])
        if query_class == "temporal":
            methods.append("temporal-filter")
            if as_of is None:
                missing.append("No as_of timestamp was supplied; current graph validity was used.")
        if query_class == "global-theme":
            methods.append("community")
            for community in communities([row["node_id"] for row in node_rows], all_edges)[:limit]:
                ranked_nodes.extend(community[:3])
        if query_class == "evidence-gap":
            methods.append("gap-scan")
            ranked_nodes = self._unsupported_claims(run_id) + ranked_nodes
        ranked_nodes = list(dict.fromkeys(ranked_nodes))[:limit]
        edge_ids = list(dict.fromkeys(edge_ids))[:max(limit * 3, 20)]
        source_episode_ids = self._source_episodes(run_id, edge_ids)
        serialized = self._serialize(run_id, ranked_nodes, edge_ids, paths, source_episode_ids)
        token_estimate = max(1, len(serialized.split()) * 4 // 3)
        trace_id = "trace:" + stable_key(run_id, query, query_class, json.dumps(ranked_nodes), json.dumps(edge_ids), as_of or "")[:24]
        payload = {"trace_id": trace_id, "query": query, "query_class": query_class, "methods": methods, "node_ids": ranked_nodes, "edge_ids": edge_ids, "paths": [list(path) for path in paths], "source_episode_ids": source_episode_ids, "missing_links": missing, "token_estimate": token_estimate, "as_of": as_of}
        self.store.append_event(run_id, "RETRIEVAL_COMPLETED", payload, f"retrieval:{run_id}:{trace_id}")
        with self.store.connect() as conn:
            conn.execute("""INSERT OR IGNORE INTO retrieval_traces(run_id,trace_id,query,query_class,methods_json,node_ids_json,edge_ids_json,paths_json,source_episode_ids_json,missing_links_json,token_estimate,as_of,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""", (run_id, trace_id, query, query_class, json.dumps(methods), json.dumps(ranked_nodes), json.dumps(edge_ids), json.dumps([list(path) for path in paths]), json.dumps(source_episode_ids), json.dumps(missing), token_estimate, as_of, utc_now()))
        return RetrievalContext(trace_id, query_class, tuple(methods), tuple(ranked_nodes), tuple(edge_ids), tuple(paths), tuple(source_episode_ids), tuple(missing), token_estimate, serialized)

    def _unsupported_claims(self, run_id: str) -> list[str]:
        with self.store.connect() as conn:
            rows = conn.execute("""SELECT n.node_id FROM graph_nodes n WHERE n.run_id=? AND n.node_type='Claim' AND NOT EXISTS (SELECT 1 FROM graph_edges e WHERE e.run_id=n.run_id AND e.to_id=n.node_id AND e.edge_type='SUPPORTS') ORDER BY n.node_id""", (run_id,)).fetchall()
        return [row["node_id"] for row in rows]

    def _source_episodes(self, run_id: str, edge_ids: list[str]) -> list[str]:
        if not edge_ids:
            return []
        placeholders = ",".join("?" for _ in edge_ids)
        with self.store.connect() as conn:
            rows = conn.execute(f"SELECT DISTINCT source_episode_id FROM graph_edges WHERE run_id=? AND edge_id IN ({placeholders}) AND source_episode_id IS NOT NULL ORDER BY source_episode_id", (run_id, *edge_ids)).fetchall()
        return [row["source_episode_id"] for row in rows]

    def _serialize(self, run_id: str, node_ids: list[str], edge_ids: list[str], paths: list[tuple[str, ...]], source_ids: list[str]) -> str:
        lines: list[str] = []
        with self.store.connect() as conn:
            if node_ids:
                placeholders = ",".join("?" for _ in node_ids)
                rows = conn.execute(f"SELECT * FROM graph_nodes WHERE run_id=? AND node_id IN ({placeholders})", (run_id, *node_ids)).fetchall()
                nodes = {row["node_id"]: row for row in rows}
                for node_id in node_ids:
                    row = nodes.get(node_id)
                    if row:
                        lines.append(f"NODE {node_id} [{row['node_type']}] {row['data_json']}")
            if edge_ids:
                placeholders = ",".join("?" for _ in edge_ids)
                rows = conn.execute(f"SELECT * FROM graph_edges WHERE run_id=? AND edge_id IN ({placeholders})", (run_id, *edge_ids)).fetchall()
                edges = {row["edge_id"]: row for row in rows}
                for edge_id in edge_ids:
                    row = edges.get(edge_id)
                    if row:
                        lines.append(f"EDGE {edge_id} ({row['from_id']})-[{row['edge_type']} valid={row['valid_from']}..{row['valid_to'] or 'open'} source={row['source_episode_id'] or 'none'}]->({row['to_id']})")
            if source_ids:
                placeholders = ",".join("?" for _ in source_ids)
                rows = conn.execute(f"SELECT * FROM source_episodes WHERE run_id=? AND episode_id IN ({placeholders})", (run_id, *source_ids)).fetchall()
                for row in rows:
                    lines.append(f"SOURCE {row['episode_id']} locator={row['locator']} hash={row['content_hash']} risk={row['injection_risk']}")
        for index, path in enumerate(paths, 1):
            lines.append(f"PATH {index} " + " -> ".join(path))
        return "\n".join(lines)

    @staticmethod
    def _rrf(rankings: list[list[str]], *, k: int = 60) -> list[str]:
        scores: Counter[str] = Counter()
        for ranking in rankings:
            for rank, item in enumerate(ranking, 1):
                scores[item] += 1.0 / (k + rank)
        return [item for item, _score in sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))]
