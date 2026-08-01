---
name: synthesizing-cited-research
description: This skill should be used when an adjudicated evidence graph must be rendered into a final research report, executive brief, comparison, decision matrix, or updated report view with claim-level citations, visible disagreement, limitations, and unresolved gaps. It synthesizes only terminal-status claims and runs a deterministic report preflight before writing `report.md`. Do not browse, add unsupported bridging facts, hide contested evidence, or cite rejected candidate claims as established findings.
---

# Synthesize Cited Research

Render the canonical graph into an audience-appropriate report without weakening provenance. Success means every factual paragraph resolves to graph claims and source locators, and the report preflight passes.

## Inputs

```json
{
  "run_id": "...",
  "run_path": "...",
  "research_contract": "run.json",
  "graph_path": "evidence-graph.jsonl",
  "sources_path": "sources.jsonl",
  "adjudication_path": "decisions.jsonl",
  "deliverable": {"type": "report", "format": "markdown", "audience": "..."}
}
```

## Load before starting

- `references/report-contract.md`
- `references/evidence-ontology.md`
- `references/source-policy.md`
- `lib/report_audit.py`

## Preconditions

- Every critical and major claim has status `verified`, `contested`, `rejected`, `superseded`, or `unknown`.
- Source and claim IDs resolve.
- The synthesis editor is the sole writer of `report.md`.
- The editor has no authority to acquire new evidence.

## Procedure

### 1. Build a question-first outline

Organize by the research questions and decision needs in `run.json`, not by source order. Map each section to accepted claims and required acceptance criteria.

### 2. Select claims by status

- `verified`: present as findings at the exact supported scope
- `contested`: present the strongest support and contradiction, then state why unresolved
- `unknown`: state what cannot be concluded and why
- `superseded`: use the current claim and mention the older state only when historically relevant
- `rejected`: exclude from findings; mention only when correcting a material misconception

Do not convert unknowns into recommendations merely to make the report decisive.

### 3. Separate fact, inference, and recommendation

- Factual paragraphs use adjudicated claims.
- Derived paragraphs begin with `Inference:` and cite every material premise claim.
- Recommendations begin with `Recommendation:` and state the decision criterion, trade-off, and uncertainty.
- Descriptive transitions must not introduce new factual content.

### 4. Add claim and source markers

Every factual paragraph includes:

```text
[C:<claim-id>] [S:<source-id>#<locator>]
```

A paragraph with multiple propositions uses multiple claim markers. Each source marker must resolve to a source record and evidence span linked to the cited claim.

### 5. Render required sections

Use, unless the contract defines a stricter template:

1. Title
2. Research scope and as-of date
3. Executive findings
4. Detailed findings by question
5. Comparison or decision matrix when applicable
6. Contested or conflicting evidence
7. Limitations
8. Unresolved research gaps
9. Source register

The executive section must not contain facts absent from detailed findings.

### 6. Represent comparisons consistently

For comparison tables:

- define columns from acceptance criteria
- use consistent units and dates
- cite each factual row or cell group
- distinguish missing data from zero/not applicable
- avoid rankings when criteria or weights are not defined

### 7. Preserve uncertainty visibly

State:

- source limitations
- unresolved contradictions
- missing primary evidence
- freshness constraints
- capability limitations
- assumptions that could change the conclusion

Do not bury these only in footnotes when they affect the decision.

### 8. Run report preflight

Write a temporary draft, then run:

```bash
python -B ${CLAUDE_PLUGIN_ROOT}/scripts/researchctl.py audit-report <run>
```

Correct unresolved claim markers, source markers, unsupported paragraphs, missing sections, hidden contested claims, and missing as-of date. Repeat only until structural preflight passes; do not reacquire evidence from this skill.

### 9. Write once and freeze

Write `<run>/report.md` after preflight passes. If the run later changes, generate a superseding report/run rather than silently editing a completed artifact.

## Output contract

Return:

```json
{
  "run_id": "...",
  "report_path": "<run>/report.md",
  "sections": ["..."],
  "claims_rendered": ["claim:..."],
  "contested_claims_exposed": ["claim:..."],
  "unknown_claims_exposed": ["claim:..."],
  "preflight": {"passed": true, "errors": [], "warnings": []}
}
```

## Failure recovery

- **Claim marker does not resolve:** remove the statement or return to adjudication; never invent an ID.
- **Source locator missing:** return the claim to extraction/adjudication.
- **Two claims conflict:** use the contested section; do not choose by narrative preference.
- **Required comparison field is missing:** show `Not established` with a gap reference.
- **Report is too long:** compress supporting prose, not citations, limitations, or conflict disclosure.
- **Preflight fails:** correct only the reported structural issues or block with the exact failing gates.
- **A new fact seems necessary:** emit a gap request to the orchestrator; do not browse directly.

## Completion checklist

- [ ] Outline follows questions and acceptance criteria.
- [ ] Only terminal-status claims are rendered.
- [ ] Fact, inference, and recommendation are labeled distinctly.
- [ ] Every factual paragraph has resolvable claim and source markers.
- [ ] Contested and unknown claims are visible.
- [ ] Required sections and as-of date are present.
- [ ] Tables use consistent units and missing-data semantics.
- [ ] Report preflight passes before final write.
