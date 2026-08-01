---
description: Resolve one persisted v3 human interrupt with an attributable approve or reject decision.
argument-hint: <run-path> <interrupt-id> APPROVE|REJECT --reviewer <name> --rationale <text>
model: inherit
---

# /research-approve

## Preconditions

The interrupt must exist and be `OPEN`. The reviewer must understand the affected task/artifacts, consequence, alternatives, and rollback path. A proposer may not self-approve a high-consequence or breaking-ontology decision.

## Procedure

1. Inspect the run and locate the exact interrupt.
2. Review its reason, payload, proposed decision, affected artifacts, evidence, and requested approval scope.
3. Reject vague reviewer identities, empty rationales, or decisions outside `APPROVE|REJECT`.
4. Run:

```bash
python -B $CLAUDE_PLUGIN_ROOT/scripts/researchctl.py approve \
  <run-path> <interrupt-id> APPROVE|REJECT \
  --reviewer "<name>" --rationale "<decision-specific rationale>"
```

5. Confirm the returned approval ID and decision. Re-inspect before resuming.

## Semantics

Approval resolves only the named interrupt. It does not certify the full run, validate evidence, waive audit failures, or authorize unrelated side effects. Rejection preserves the run and requires replanning or closure.

## Failure handling

Unknown or already-resolved interrupt is a terminal input error. Do not create a second approval. If command outcome is ambiguous, inspect the interrupt before retrying.

## Output

Return run ID, interrupt ID, approval ID, decision, reviewer, rationale summary, affected tasks, and next action.
