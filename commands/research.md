---
description: Start a durable Evidence Research v3 run from a validated contract and persisted capability decision.
argument-hint: <research brief, constraints, and desired deliverable>
model: inherit
---

# /research

## Purpose

Create the canonical v3 run, architecture decision, and artifact-flow task graph. This command initializes work; it does not claim that research has completed.

## Required intake

Extract from `$ARGUMENTS`: target, as-of date, acceptance questions, domains, exclusions, consequence, source constraints, budgets, deliverable, and definition of done. Ask only when a missing choice would materially change scope or safety.

Create `contract.json` with at least:

```json
{
  "target": "Decision-relevant research target",
  "as_of": "2026-08-01",
  "questions": [{"id": "q1", "text": "...", "domain": "general"}],
  "profile": {
    "independent_branches": 1,
    "dependency_depth": 1,
    "shared_context_ratio": 0.0,
    "source_overlap_ratio": 0.0,
    "sequential_dependency_ratio": 0.0,
    "verification_burden": 0.5,
    "consequence": "medium",
    "existing_graph": false,
    "needs_new_evidence": true
  }
}
```

## Procedure

1. Read `$CLAUDE_PLUGIN_ROOT/skills/running-evidence-research/SKILL.md`.
2. Validate absolute dates, acceptance questions, profile ranges, and budgets.
3. Determine available host capabilities. Use strict mode for consequential work when nondisclosure must block execution.
4. Run:

```bash
python -B $CLAUDE_PLUGIN_ROOT/scripts/researchctl.py init \
  --contract <contract.json> --root research-runs \
  --max-agents <n> [--capability <capability>] [--strict-capabilities]
```

5. Inspect the returned run path, run ID, architecture decision, contract hash, and capability decision.
6. Confirm `contract.json`, `task-graph.json`, `run.json`, and `state.db` exist. Validate the graph before dispatch.
7. Report ready tasks and next action. Do not bypass ontology, source episodes, independent adjudication, or audit.

## Idempotency and recovery

The run ID derives from normalized target and contract digest. Repeating the identical contract reuses the same run directory and does not re-register the graph. A changed contract creates a different run. Never edit a completed run to accommodate new scope; create a superseding run.

## Output

Return run path/ID, target/as-of, architecture with reasons/warnings, capability result, task counts/states, open interrupts, budgets, and next command.

## Blockers

Invalid profile, missing target, failed strict capability preflight, invalid graph, or unsafe output path blocks initialization.
