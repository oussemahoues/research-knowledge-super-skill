from __future__ import annotations

from collections import deque
from typing import Any


def active_edges(conn: Any, run_id: str, as_of: str | None = None, *, causal_only: bool = False) -> list[Any]:
    clauses = ["run_id=?"]
    params: list[Any] = [run_id]
    if as_of is not None:
        clauses.extend(["valid_from<=?", "(valid_to IS NULL OR valid_to>?)"])
        params.extend([as_of, as_of])
    if causal_only:
        clauses.append("edge_type IN ('CAUSES','TRIGGERS','PRECEDES','ENABLES')")
    return conn.execute("SELECT * FROM graph_edges WHERE " + " AND ".join(clauses), tuple(params)).fetchall()


def expand(edges: list[Any], seeds: list[str], *, hops: int) -> tuple[set[str], list[str]]:
    adjacency: dict[str, list[tuple[str, str]]] = {}
    for edge in edges:
        adjacency.setdefault(edge["from_id"], []).append((edge["to_id"], edge["edge_id"]))
        adjacency.setdefault(edge["to_id"], []).append((edge["from_id"], edge["edge_id"]))
    visited = set(seeds)
    frontier = set(seeds)
    used_edges: list[str] = []
    for _ in range(hops):
        next_frontier: set[str] = set()
        for node in frontier:
            for neighbor, edge_id in adjacency.get(node, []):
                used_edges.append(edge_id)
                if neighbor not in visited:
                    visited.add(neighbor)
                    next_frontier.add(neighbor)
        frontier = next_frontier
        if not frontier:
            break
    return visited, list(dict.fromkeys(used_edges))


def shortest_path(edges: list[Any], start: str, end: str, *, max_hops: int) -> tuple[str, ...] | None:
    adjacency: dict[str, list[tuple[str, str]]] = {}
    for edge in edges:
        adjacency.setdefault(edge["from_id"], []).append((edge["to_id"], edge["edge_id"]))
        adjacency.setdefault(edge["to_id"], []).append((edge["from_id"], edge["edge_id"]))
    queue: deque[tuple[str, tuple[str, ...], int]] = deque([(start, (start,), 0)])
    visited = {start}
    while queue:
        node, path, hops = queue.popleft()
        if node == end:
            return path
        if hops >= max_hops:
            continue
        for neighbor, edge_id in sorted(adjacency.get(node, [])):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            queue.append((neighbor, path + (edge_id, neighbor), hops + 1))
    return None


def communities(nodes: list[str], edges: list[Any]) -> list[list[str]]:
    adjacency: dict[str, set[str]] = {node: set() for node in nodes}
    for edge in edges:
        adjacency.setdefault(edge["from_id"], set()).add(edge["to_id"])
        adjacency.setdefault(edge["to_id"], set()).add(edge["from_id"])
    result: list[list[str]] = []
    unseen = set(nodes)
    while unseen:
        start = min(unseen)
        stack = [start]
        component: list[str] = []
        unseen.remove(start)
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbor in adjacency.get(node, set()):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    stack.append(neighbor)
        result.append(sorted(component))
    return sorted(result, key=lambda group: (-len(group), group[0] if group else ""))
