---
name: synthesizing-cited-research
description: This skill should be used when the latest v3 adjudication state must be rendered into a report, executive brief, comparison, decision matrix, or updated report view. It exposes verified and contested claims with resolvable claim, evidence-edge, and source-episode markers while listing omitted gaps. Do not browse, invent bridging facts, hide disagreement, or render `needs_review` or rejected claims as findings.
---

# Synthesize Cited Research

Render a deterministic report view from the SQLite evidence graph. The report is derived output, never canonical research state.

## Inputs

```json
{
  "run_id": "run:...",
  "run_path": "research-runs/run_...",
  "title": "Research report",
  "as_of": "YYYY-MM-DD",
  "output": "report.md"
}
```

## Procedure

### 1. Load latest decisions

Select the latest adjudication for every material claim. Include only `verified` and `contested` claims in findings.

### 2. Build a question-first outline

Organize sections by research questions and acceptance criteria, not source order or retrieval sequence.

### 3. Preserve status semantics

Present verified claims at supported scope. Present contested claims with both support and contradiction. List `needs_review` and rejected material as omissions or gaps, not findings.

### 4. Separate content types

Label inference and recommendation explicitly. Every material premise of an inference must itself be publishable and marked.

### 5. Add resolvable markers

Every factual statement includes claim IDs, evidence-edge IDs, and source-episode IDs. Do not cite a source title or URL without the exact evidentiary edge.

### 6. Render temporal context

State the as-of date and preserve historical or superseded states only when relevant. Do not blend incompatible effective periods.

### 7. Redact sensitive content

Never expose secrets, credentials, private keys, personal contact data, or sensitive source excerpts. Keep resolvable hashes and locators instead.

### 8. Show limitations

Expose source limitations, capability gaps, quarantined evidence, unresolved contradictions, stale data, assumptions, and missing primary evidence.

### 9. Run deterministic rendering

Use `researchctl.py render`. Do not construct final prose from memory or arbitrary worker summaries.

### 10. Audit markers

Run the rendered-report audit and verify every claim, edge, and episode marker resolves. Block publication on any unresolved marker.

## Output contract

```json
{
  "schema_version": "3.0",
  "run_id": "run:...",
  "report_path": "report.md",
  "claims_rendered": [],
  "contested_claims_exposed": [],
  "omitted_claims": [],
  "marker_audit": {"passed": true, "errors": []}
}
```

## Failure recovery

- Unresolved claim marker: omit the statement or return it to adjudication.
- Missing evidence edge or episode: block rendering of that claim.
- Conflict between claims: expose it as contested; never choose by narrative preference.
- Required comparison data missing: write `Not established` and link the gap.
- Report too long: compress prose, not markers, limitations, or conflict disclosure.
- New fact appears necessary: request a graph gap through the orchestrator; do not browse.

## Completion checklist

- [ ] Outline follows questions and acceptance criteria.
- [ ] Only verified and contested claims are findings.
- [ ] Inference and recommendation are labeled.
- [ ] Claim, edge, and episode markers resolve.
- [ ] Sensitive values are absent.
- [ ] Temporal scope, disagreement, limitations, and gaps are visible.
- [ ] Deterministic marker audit passes.
