---
description: Start a durable Evidence Research v3 run with adaptive graph orchestration.
argument-hint: <research brief, constraints, and desired deliverable>
model: inherit
---

Read `${CLAUDE_PLUGIN_ROOT}/skills/running-evidence-research/SKILL.md`. Convert `$ARGUMENTS` into a scoped contract, then initialize the canonical v3 run with:

```bash
python -B ${CLAUDE_PLUGIN_ROOT}/scripts/researchctl.py init --contract <contract.json> --root research-runs
```

Use the persisted architecture decision and registered task graph. Do not bypass ontology validation, source episodes, independent adjudication, or the final v3 audit.
