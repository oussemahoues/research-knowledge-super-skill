---
description: Query an existing Evidence Research v3 temporal graph with query-adaptive retrieval.
argument-hint: <run-path> <query> [--entity <node-id>] [--as-of <timestamp>]
model: inherit
---

Use the retrieval planner and run:

```bash
python -B ${CLAUDE_PLUGIN_ROOT}/scripts/researchctl.py query $ARGUMENTS
```

Return the persisted retrieval trace, evidence paths, source episodes, missing links, and token-bounded serialized context. Do not dump the entire graph.
