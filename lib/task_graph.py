from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class TaskGraphResult:
    errors: list[str]
    warnings: list[str]
    levels: list[list[str]]
    metrics: dict[str, Any]

    @property
    def passed(self) -> bool:
        return not self.errors


def load_graph(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("task graph must be an object")
    return data


def validate_task_graph(graph: dict[str, Any]) -> TaskGraphResult:
    errors: list[str] = []
    warnings: list[str] = []
    tasks_list = graph.get("tasks")
    if not isinstance(tasks_list, list) or not tasks_list:
        return TaskGraphResult(["tasks must be a non-empty array"], [], [], {})

    tasks: dict[str, dict[str, Any]] = {}
    for task in tasks_list:
        if not isinstance(task, dict) or not task.get("id"):
            errors.append("every task requires an id")
            continue
        tid = task["id"]
        if tid in tasks:
            errors.append(f"duplicate task id: {tid}")
        tasks[tid] = task
        for field in ("objective", "consumes", "produces", "dependencies", "owner", "budget", "done_when"):
            if field not in task:
                errors.append(f"{tid}: missing {field}")

    indegree = {tid: 0 for tid in tasks}
    outgoing = {tid: [] for tid in tasks}
    fake_edges = 0
    for tid, task in tasks.items():
        deps = task.get("dependencies", [])
        if not isinstance(deps, list):
            errors.append(f"{tid}: dependencies must be a list")
            continue
        consumes = set(task.get("consumes", []))
        for dep in deps:
            if dep not in tasks:
                errors.append(f"{tid}: missing dependency task {dep}")
                continue
            indegree[tid] += 1
            outgoing[dep].append(tid)
            produced = set(tasks[dep].get("produces", []))
            if not produced.intersection(consumes):
                fake_edges += 1
                errors.append(f"fake dependency: {dep} -> {tid}; no produced artifact is consumed")

    levels: list[list[str]] = []
    frontier = sorted([tid for tid, degree in indegree.items() if degree == 0])
    visited = 0
    while frontier:
        levels.append(frontier)
        next_frontier: list[str] = []
        for tid in frontier:
            visited += 1
            for child in outgoing[tid]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    next_frontier.append(child)
        frontier = sorted(next_frontier)
    if visited != len(tasks):
        errors.append("task graph contains a cycle")

    writers: dict[str, set[str]] = {}
    for tid, task in tasks.items():
        for artifact in task.get("produces", []):
            writers.setdefault(artifact, set()).add(task.get("owner", ""))
    for artifact, owners in writers.items():
        if len(owners) > 1:
            errors.append(f"artifact {artifact} has multiple writer owners: {sorted(owners)}")

    merge_owner = graph.get("merge_owner")
    if not merge_owner:
        errors.append("merge_owner required")

    max_width = max((len(level) for level in levels), default=0)
    if max_width > int(graph.get("max_parallel", 8)):
        errors.append(f"parallel width {max_width} exceeds max_parallel")

    return TaskGraphResult(
        errors=errors,
        warnings=warnings,
        levels=levels,
        metrics={"tasks": len(tasks), "edges": sum(len(t.get("dependencies", [])) for t in tasks.values()), "fake_edges": fake_edges, "max_parallel_width": max_width},
    )
