---
description: Run the deterministic Evidence Research v3 completion audit.
argument-hint: <run-path>
model: inherit
---

Read `${CLAUDE_PLUGIN_ROOT}/skills/auditing-research-run/SKILL.md`, then run:

```bash
python -B ${CLAUDE_PLUGIN_ROOT}/scripts/researchctl.py audit $ARGUMENTS
```

Do not acquire evidence or rewrite the report during audit. A failed audit is a valid blocked result.
