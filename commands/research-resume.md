---
description: Resume a durable Evidence Research v3 run from its persisted task and checkpoint state.
argument-hint: <run-path>
model: inherit
---

Read `${CLAUDE_PLUGIN_ROOT}/skills/running-evidence-research/SKILL.md` in resume mode. Inspect the run first:

```bash
python -B ${CLAUDE_PLUGIN_ROOT}/scripts/researchctl.py inspect $ARGUMENTS
python -B ${CLAUDE_PLUGIN_ROOT}/scripts/researchctl.py recover-leases $ARGUMENTS
python -B ${CLAUDE_PLUGIN_ROOT}/scripts/researchctl.py ready $ARGUMENTS
```

Preserve successful sibling branches and continue only tasks reported as ready. Never reconstruct state from chat memory.
