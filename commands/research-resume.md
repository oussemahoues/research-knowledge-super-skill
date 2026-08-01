---
description: Resume a durable v3 run from canonical attempts, leases, checkpoints, artifacts, and interrupts.
argument-hint: <run-path>
model: inherit
---

# /research-resume

## Purpose

Continue only work that canonical state proves is ready. Never reconstruct progress from chat, a report, or JSONL export.

## Procedure

1. Read `$CLAUDE_PLUGIN_ROOT/skills/running-evidence-research/SKILL.md` in resume mode.
2. Inspect before mutation:

```bash
python -B $CLAUDE_PLUGIN_ROOT/scripts/researchctl.py inspect <run-path>
```

3. Report run status, task states/attempts, active leases, latest checkpoint, open interrupts, and registered artifacts.
4. If an interrupt is open, stop and route to `/research-approve`.
5. Recover only expired leases:

```bash
python -B $CLAUDE_PLUGIN_ROOT/scripts/researchctl.py recover-leases <run-path>
```

Use `--now` only for deterministic testing. Never force recovery of an unexpired lease.
6. List executable tasks:

```bash
python -B $CLAUDE_PLUGIN_ROOT/scripts/researchctl.py ready <run-path>
```

7. Dispatch only returned task IDs, using their next persisted attempt number and declared inputs/outputs. Preserve successful siblings and do not repeat completed tasks.
8. After each task, checkpoint success/failure through the runtime and refresh ready state.
9. Render and audit only when prerequisites are terminal and publishable.

## Failure rules

- Expired lease: recover and retry only within `max_attempts`.
- Exhausted attempts: leave failed and block dependents.
- Missing artifact: do not infer success from the prior worker message.
- Ambiguous side effect: reconcile by idempotency key before retry.
- Corrupt/missing `run.json` or database: return a data-integrity block; do not create a replacement run in place.

## Output

Return inspected state, recovered task IDs, ready task IDs, preserved successful branches, blocking interrupts/failures, checkpoint, remaining budget, and next action.
