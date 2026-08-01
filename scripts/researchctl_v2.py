#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from lib.report_audit import audit_report
from lib.research_graph import append_records, content_hash, make_edge, make_node, read_jsonl, stable_id, validate_records
from lib.run_state import atomic_json, create_run, load_run, transition, validate_history
from lib.task_graph import load_graph, validate_task_graph


def cmd_init(args: argparse.Namespace) -> int:
    contract = json.loads(Path(args.contract).read_text(encoding="utf-8")) if args.contract else {
        "target": args.target,
        "as_of": args.as_of or date.today().isoformat(),
        "questions": [{"id": "q1", "text": args.target, "kind": "verification"}],
        "acceptance_criteria": [{"id": "a1", "criterion": "Every material finding has claim-level evidence", "measure": "claim_evidence_coverage == 1.0"}],
    }
    run_dir = create_run(args.root, contract)
    print(run_dir)
    return 0


def cmd_transition(args: argparse.Namespace) -> int:
    result = transition(args.run, args.state, args.reason, resume_state=args.resume_state)
    print(json.dumps(result, indent=2))
    return 0


def cmd_validate_graph(args: argparse.Namespace) -> int:
    result = validate_records(read_jsonl(args.path))
    print(json.dumps({"passed": result.passed, "errors": result.errors, "warnings": result.warnings, "metrics": result.metrics}, indent=2))
    return 0 if result.passed else 1


def cmd_validate_task_graph(args: argparse.Namespace) -> int:
    result = validate_task_graph(load_graph(args.path))
    print(json.dumps({"passed": result.passed, "errors": result.errors, "warnings": result.warnings, "levels": result.levels, "metrics": result.metrics}, indent=2))
    return 0 if result.passed else 1


def cmd_audit(args: argparse.Namespace) -> int:
    root = Path(args.run)
    errors: list[str] = []
    warnings: list[str] = []
    metrics: dict = {}
    run = load_run(root)
    errors.extend(validate_history(run))
    task_path = root / "task-graph.json"
    if task_path.exists():
        task = validate_task_graph(load_graph(task_path))
        errors.extend(task.errors)
        warnings.extend(task.warnings)
        metrics.update({f"task_{k}": v for k, v in task.metrics.items()})
    else:
        errors.append("task-graph.json missing")
    report = audit_report(root)
    errors.extend(report["errors"])
    warnings.extend(report["warnings"])
    metrics.update(report["metrics"])
    thresholds = run.get("thresholds", {})
    for key in ("claim_evidence_coverage", "citation_resolvability"):
        if key in thresholds and metrics.get(key, 0) < thresholds[key]:
            errors.append(f"threshold failed: {key}={metrics.get(key, 0)} < {thresholds[key]}")
    if metrics.get("unsupported_claims", 0) > thresholds.get("unsupported_claims", 0):
        errors.append("unsupported claim threshold failed")
    audit = {
        "schema_version": "2.0",
        "run_id": run.get("run_id"),
        "passed": not errors,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "metrics": metrics,
        "instruments": {"researchctl": "2.0.0", "report_audit": "2.0.0", "graph_validator": "2.0.0"},
    }
    atomic_json(root / "audit.json", audit)
    print(json.dumps(audit, indent=2))
    return 0 if audit["passed"] else 1


def cmd_demo(args: argparse.Namespace) -> int:
    root = Path(args.path)
    root.mkdir(parents=True, exist_ok=True)
    contract = {
        "target": "Determine whether the demo technology reduces inspection time",
        "as_of": "2026-07-31",
        "questions": [{"id": "q1", "text": "Does the technology reduce inspection time?", "kind": "verification"}],
        "acceptance_criteria": [{"id": "a1", "criterion": "One verified claim with direct evidence", "measure": "claim_evidence_coverage == 1.0"}],
    }
    run_dir = create_run(root, contract)
    source_text = "The controlled trial reported a 20 percent reduction in median inspection time."
    source = {
        "id": stable_id("source", "demo controlled trial"), "title": "Demo controlled trial", "locator": "demo://trial",
        "publisher": "Example Laboratory", "published_at": "2026-01-10", "accessed_at": "2026-07-31",
        "authority_tier": "A", "source_type": "original-research", "content_hash": content_hash(source_text),
        "independence_group": "example-lab-trial-1", "injection_risk": "none"
    }
    (run_dir / "sources.jsonl").write_text(json.dumps(source, sort_keys=True) + "\n", encoding="utf-8")
    q = make_node("ResearchQuestion", "Does the technology reduce inspection time?", {"text": "Does the technology reduce inspection time?"})
    s = make_node("Source", source["id"], source)
    c = make_node("Claim", "technology reduces median inspection time by 20 percent", {"text": "The technology reduced median inspection time by 20 percent.", "claim_kind": "observation"}, status="verified")
    e = make_node("EvidenceSpan", source["content_hash"] + " paragraph 1", {"source_id": source["id"], "locator": "paragraph 1", "text": source_text, "content_hash": source["content_hash"]})
    records = [q, s, c, e, make_edge("SUPPORTS", e["id"], c["id"], {"source_id": source["id"], "locator": "paragraph 1"}), make_edge("ASSERTED_BY", c["id"], s["id"], {"source_id": source["id"]}), make_edge("ANSWERS", c["id"], q["id"], {"method": "direct evidence"})]
    append_records(run_dir / "evidence-graph.jsonl", records)
    task_graph = {
        "schema_version": "2.0", "run_id": load_run(run_dir)["run_id"], "merge_owner": "research-orchestrator", "max_parallel": 4,
        "tasks": [
            {"id": "scope", "objective": "Scope", "consumes": ["brief"], "produces": ["run.json"], "dependencies": [], "owner": "research-orchestrator", "budget": {"tool_calls": 0}, "done_when": "contract exists"},
            {"id": "extract", "objective": "Extract", "consumes": ["run.json", "source-content"], "produces": ["evidence-graph.jsonl"], "dependencies": ["scope"], "owner": "evidence-curator", "budget": {"tool_calls": 0}, "done_when": "graph validates"},
            {"id": "report", "objective": "Report", "consumes": ["evidence-graph.jsonl"], "produces": ["report.md"], "dependencies": ["extract"], "owner": "synthesis-editor", "budget": {"tool_calls": 0}, "done_when": "report audit passes"}
        ]
    }
    atomic_json(run_dir / "task-graph.json", task_graph)
    report = f"""# Demo Research Report

## Research scope and as-of date

As of 2026-07-31, this demo tests whether the technology reduced inspection time.

## Executive findings

The controlled trial reported a 20 percent reduction in median inspection time. [C:{c['id']}] [S:{source['id']}#paragraph 1]

## Detailed findings

The observed reduction was measured as median inspection time in one controlled trial. [C:{c['id']}] [S:{source['id']}#paragraph 1]

## Contested or conflicting evidence

No contradictory evidence was included in this synthetic demo.

## Limitations

This is a synthetic fixture and not a real-world conclusion.

## Unresolved research gaps

Independent replication is not represented.

## Source register

- Demo controlled trial. [S:{source['id']}#paragraph 1]
"""
    (run_dir / "report.md").write_text(report, encoding="utf-8")
    for state in ["PLANNED", "ACQUIRING", "EXTRACTING", "RESOLVING", "VERIFYING", "SYNTHESIZING", "AUDITING"]:
        transition(run_dir, state, "demo progression")
    print(run_dir)
    return cmd_audit(argparse.Namespace(run=str(run_dir)))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="researchctl")
    sub = p.add_subparsers(dest="command", required=True)
    x = sub.add_parser("init")
    x.add_argument("--root", default="research-runs")
    x.add_argument("--contract")
    x.add_argument("--target", default="Research target")
    x.add_argument("--as-of")
    x.set_defaults(func=cmd_init)
    x = sub.add_parser("transition")
    x.add_argument("run")
    x.add_argument("state")
    x.add_argument("reason")
    x.add_argument("--resume-state")
    x.set_defaults(func=cmd_transition)
    x = sub.add_parser("validate-graph")
    x.add_argument("path")
    x.set_defaults(func=cmd_validate_graph)
    x = sub.add_parser("validate-task-graph")
    x.add_argument("path")
    x.set_defaults(func=cmd_validate_task_graph)
    x = sub.add_parser("audit")
    x.add_argument("run")
    x.set_defaults(func=cmd_audit)
    x = sub.add_parser("audit-report")
    x.add_argument("run")
    x.set_defaults(func=lambda a: (print(json.dumps(audit_report(a.run), indent=2)) or (0 if audit_report(a.run)["passed"] else 1)))
    x = sub.add_parser("demo")
    x.add_argument("path")
    x.set_defaults(func=cmd_demo)
    return p


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
