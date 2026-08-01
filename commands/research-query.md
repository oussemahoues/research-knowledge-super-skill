---
description: Query an existing temporal evidence graph and persist a bounded, query-adaptive retrieval trace.
argument-hint: <run-path> <query> [--entity <node-id>] [--as-of <timestamp>] [--limit <n>] [--max-hops <n>]
model: inherit
---

# /research-query

## Purpose

Retrieve candidate evidence context from an existing run. This command does not browse, acquire evidence, adjudicate claims, or produce a final research conclusion.

## Procedure

1. Confirm the run and query are valid. Resolve each `--entity` seed to a graph node.
2. For temporal questions, require or explicitly discuss `--as-of`.
3. Choose conservative `--limit` and `--max-hops` values; defaults are 12 and 3.
4. Run:

```bash
python -B $CLAUDE_PLUGIN_ROOT/scripts/researchctl.py query \
  <run-path> "<query>" [--entity <node-id>] [--as-of <timestamp>] \
  [--limit <n>] [--max-hops <n>]
```

5. Return the persisted trace ID, query class, selected methods, ordered node/edge IDs, paths, source episode IDs, missing links, token estimate, and serialized context.

## Interpretation

Retrieval rank is not truth or claim confidence. “No path” means no path was found within the current graph and hop limit. A temporal query without `as_of` uses current validity and must surface that limitation. The serialized context is deliberately bounded; never dump the database as fallback.

## Follow-up

Route material claims through `verify-claim` before treating retrieved context as publishable evidence.

## Output

Return the raw trace plus a short explanation of method selection, gaps, time basis, and next validation step.
