---
description: Inspect canonical v3 run metadata, execution state, open interrupts, and latest checkpoint without mutation.
argument-hint: <run-path>
model: inherit
---

# /research-inspect

## Procedure

Run:

```bash
python -B $CLAUDE_PLUGIN_ROOT/scripts/researchctl.py inspect <run-path>
```

The command loads `run.json` only as a locator for `state.db` and `run_id`, then reads persisted run and executor state.

## Report

Present:

- run ID, target, architecture, and run status;
- every task's state, attempt count, owner/worker, lease expiry, and declared outputs when returned;
- open interrupts and their reasons;
- latest checkpoint ID/state;
- latest retrieval trace or report/audit artifact when present in returned state;
- inconsistencies such as a missing database, unknown run, stale locator, or artifact without a successful task.

## Interpretation

Use only returned persisted fields. `READY` means dependencies are satisfied; it does not mean a worker has started. A missing checkpoint does not imply failure. A prose report or agent message is never proof of task completion.

## Safety

Read-only. Do not recover leases, approve interrupts, update state, or infer hidden progress.

## Output

Return the command JSON plus a concise status summary and the next safe command.
