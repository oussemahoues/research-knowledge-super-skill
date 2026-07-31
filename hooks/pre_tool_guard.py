#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))
from lib.injection_guard import scan


def emit(decision: str, message: str, code: int) -> None:
    payload = {"permissionDecision": decision, "additionalContext": message}
    if decision == "deny":
        payload["decision"] = "block"
    print(json.dumps(payload))
    raise SystemExit(code)


def main() -> None:
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    except Exception as exc:
        emit("deny", f"Evidence Research guard could not parse tool payload: {exc}", 2)
    tool_input = payload.get("tool_input") or payload.get("toolInput") or payload.get("input") or {}
    file_path = str(tool_input.get("file_path") or tool_input.get("path") or "")
    content = str(tool_input.get("content") or tool_input.get("new_string") or "")
    if "research-runs" not in file_path.replace("\\", "/"):
        emit("allow", "Outside Evidence Research run tree.", 0)
    path = Path(file_path)
    run_dir = next((p for p in [path, *path.parents] if p.name.startswith("run_")), None)
    if run_dir and (run_dir / "run.json").exists():
        try:
            state = json.loads((run_dir / "run.json").read_text(encoding="utf-8")).get("state")
        except Exception:
            state = None
        if state == "COMPLETE":
            emit("deny", "Completed research runs are immutable. Create a superseding run.", 2)
    if path.name == "report.md":
        if "[C:" not in content or "[S:" not in content:
            emit("deny", "report.md requires claim markers [C:...] and source markers [S:...#...].", 2)
    result = scan(content)
    if result["risk"] == "high" and path.name in {"run.json", "task-graph.json", "report.md"}:
        emit("deny", "High-risk instruction-like content detected in a control artifact; store source data separately and delimit it as untrusted.", 2)
    emit("allow", "Evidence Research pre-write guard passed.", 0)


if __name__ == "__main__":
    main()
