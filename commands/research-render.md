---
description: Render and trace-audit an Evidence Research v3 report from latest adjudication decisions.
argument-hint: <run-path> [--output <path>] [--title <title>] [--as-of <date>]
model: inherit
---

Run:

```bash
python -B ${CLAUDE_PLUGIN_ROOT}/scripts/researchctl.py render $ARGUMENTS
```

The renderer may read canonical graph state but may not browse, acquire evidence, or invent connective facts. Publish only `verified` and `contested` claims, preserve contested status, and require every claim, evidence-edge, and source-episode marker to resolve.
