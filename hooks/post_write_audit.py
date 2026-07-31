#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))
from lib.report_audit import audit_report
from lib.research_graph import read_jsonl, validate_records
from lib.task_graph import load_graph, validate_task_graph


def main() -> None:
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    except Exception:
        return
    tool_input = payload.get("tool_input") or payload.get("toolInput") or payload.get("input") or {}
    file_path = str(tool_input.get("file_path") or tool_input.get("path") or "")
    if "research-runs" not in file_path.replace("\\", "/"):
        return
    path = Path(file_path)
    context: list[str] = []
    try:
        if path.name == "task-graph.json" and path.exists():
            result = validate_task_graph(load_graph(path))
            context.append(f"task graph: {'PASS' if result.passed else 'FAIL'}; errors={result.errors}")
        elif path.name == "evidence-graph.jsonl" and path.exists():
            result = validate_records(read_jsonl(path))
            context.append(f"evidence graph: {'PASS' if result.passed else 'FAIL'}; errors={result.errors}")
        elif path.name == "report.md" and path.exists():
            result = audit_report(path.parent)
            context.append(f"report audit: {'PASS' if result['passed'] else 'FAIL'}; errors={result['errors']}")
    except Exception as exc:
        context.append(f"post-write validation error: {exc}")
    if context:
        print(json.dumps({"additionalContext": " | ".join(context)}))


if __name__ == "__main__":
    main()
