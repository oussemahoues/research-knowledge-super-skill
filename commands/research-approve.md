---
description: Resolve a persisted Evidence Research v3 human interrupt.
argument-hint: <run-path> <interrupt-id> APPROVE|REJECT --reviewer <name> --rationale <text>
model: inherit
---

Review the interrupt payload and affected artifacts before running:

```bash
python -B ${CLAUDE_PLUGIN_ROOT}/scripts/researchctl.py approve $ARGUMENTS
```

The proposer cannot self-approve a high-consequence decision. Preserve the reviewer, decision, rationale, and timestamp in the event store.
