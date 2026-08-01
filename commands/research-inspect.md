---
description: Inspect Evidence Research v3 run state, task attempts, checkpoints, interrupts, and latest retrieval trace.
argument-hint: <run-path>
model: inherit
---

Run:

```bash
python -B ${CLAUDE_PLUGIN_ROOT}/scripts/researchctl.py inspect $ARGUMENTS
```

Report persisted state only. Do not infer task completion from prose or agent self-reports.
