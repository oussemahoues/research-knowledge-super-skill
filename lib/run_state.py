from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

STATES = ["SCOPED", "PLANNED", "ACQUIRING", "EXTRACTING", "RESOLVING", "VERIFYING", "SYNTHESIZING", "AUDITING", "COMPLETE"]
TRANSITIONS = {a: {b, "BLOCKED"} for a, b in zip(STATES, STATES[1:])}
TRANSITIONS["COMPLETE"] = set()
TRANSITIONS["BLOCKED"] = set(STATES[:-1])


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:48] or "research"


def make_run_id(target: str, as_of: str) -> str:
    digest = hashlib.sha256((target.strip() + "\x1f" + as_of).encode("utf-8")).hexdigest()[:12]
    return f"run:{slugify(target)}:{digest}"


def atomic_json(path: str | Path, data: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=p.name + ".", dir=p.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def create_run(root: str | Path, contract: dict[str, Any]) -> Path:
    as_of = contract.get("as_of") or date.today().isoformat()
    target = contract["target"]
    run_id = make_run_id(target, as_of)
    run_dir = Path(root) / run_id.replace(":", "_")
    run_dir.mkdir(parents=True, exist_ok=False)
    run = {
        "schema_version": "2.0",
        "run_id": run_id,
        "state": "SCOPED",
        "resume_state": None,
        "target": target,
        "questions": contract.get("questions", []),
        "acceptance_criteria": contract.get("acceptance_criteria", []),
        "scope": contract.get("scope", {}),
        "assumptions": contract.get("assumptions", []),
        "as_of": as_of,
        "thresholds": contract.get("thresholds", {"claim_evidence_coverage": 1.0, "citation_resolvability": 1.0, "citation_entailment_sample": 0.9, "unsupported_claims": 0}),
        "budgets": contract.get("budgets", {"max_agents": 8, "max_tool_calls": 120, "max_sources": 80, "max_gap_rounds": 2}),
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "history": [{"state": "SCOPED", "at": utc_now(), "reason": "run initialized"}],
    }
    atomic_json(run_dir / "run.json", run)
    for name in ("sources.jsonl", "evidence-graph.jsonl", "decisions.jsonl"):
        (run_dir / name).write_text("", encoding="utf-8")
    return run_dir


def load_run(run_dir: str | Path) -> dict[str, Any]:
    return json.loads((Path(run_dir) / "run.json").read_text(encoding="utf-8"))


def transition(run_dir: str | Path, new_state: str, reason: str, *, resume_state: str | None = None) -> dict[str, Any]:
    p = Path(run_dir) / "run.json"
    run = json.loads(p.read_text(encoding="utf-8"))
    current = run["state"]
    if new_state not in TRANSITIONS.get(current, set()):
        raise ValueError(f"illegal transition {current} -> {new_state}")
    if new_state == "BLOCKED":
        resume_state = resume_state or current
    elif current == "BLOCKED":
        expected = run.get("resume_state")
        if expected and new_state != expected:
            raise ValueError(f"blocked run must resume to {expected}, not {new_state}")
        resume_state = None
    run["state"] = new_state
    run["resume_state"] = resume_state
    run["updated_at"] = utc_now()
    run.setdefault("history", []).append({"state": new_state, "at": utc_now(), "reason": reason})
    atomic_json(p, run)
    return run


def validate_history(run: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    history = run.get("history", [])
    if not history:
        return ["run history is empty"]
    previous = history[0].get("state")
    if previous != "SCOPED":
        errors.append("first state must be SCOPED")
    resume_state = None
    for item in history[1:]:
        state = item.get("state")
        if previous == "BLOCKED":
            if resume_state and state != resume_state:
                errors.append(f"history resumes from BLOCKED to {state}, expected {resume_state}")
        elif state not in TRANSITIONS.get(previous, set()):
            errors.append(f"illegal historical transition {previous} -> {state}")
        if state == "BLOCKED":
            resume_state = previous
        else:
            resume_state = None
        previous = state
    if run.get("state") != previous:
        errors.append("run.state does not match final history state")
    return errors
