---
description: Render and trace-audit a report from the latest publishable v3 adjudications.
argument-hint: <run-path> [--output <path>] [--title <title>] [--as-of <date>]
model: inherit
---

# /research-render

## Preconditions

Canonical graph state must contain Claim nodes and latest adjudications. Only `verified` and `contested` claims are publishable. The output path must be authorized and should normally remain inside the run directory.

## Procedure

1. Inspect the run and choose title/as-of value.
2. Run:

```bash
python -B $CLAUDE_PLUGIN_ROOT/scripts/researchctl.py render \
  <run-path> [--output <path>] [--title "<title>"] [--as-of <timestamp>]
```

3. The renderer reads canonical state, writes atomically, and immediately runs the marker audit.
4. Confirm every factual finding has resolvable `[C:<claim-id>]`, `[E:<edge-id>]`, and `[S:<episode-id>]` markers.
5. Confirm contested claims expose both sides and non-publishable claims appear only as gaps/omissions.
6. Treat a nonzero exit or `audit.passed=false` as blocked output. Do not hand-edit the report to conceal a graph defect.

## Output

Return report path, included/contested/omitted claim IDs, marker-audit result/errors, as-of time, and publishability.

## Boundaries

The renderer may not browse, acquire evidence, change adjudications, cite quarantined episodes, or invent connective facts. Repair canonical evidence through the owning stage, then render again.
