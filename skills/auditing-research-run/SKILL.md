---
name: auditing-research-run
description: This skill should be used before research is declared complete, when reviewing a run produced by another agent, when CI or a report audit fails, or when diagnosing why a run is blocked. It deterministically checks run-state history, task-DAG integrity, canonical graph records, claim-evidence coverage, citation resolution, contested-claim disclosure, required report sections, thresholds, and completed-run immutability. Do not acquire evidence, reinterpret claims, or rewrite the report while auditing.
---

# Audit the Research Run

Produce a reproducible pass/fail verdict from canonical artifacts. A failed audit is a valid result and must identify the earliest repair stage for each failure.

## Inputs

```json
{
  "run_path": "research-runs/run_...",
  "mode": "completion|diagnostic|review",
  "expected_run_id": "optional",
  "strict_warnings": false
}
```

## Load before starting

- `references/architecture.md`
- `references/evaluation.md`
- `references/report-contract.md`
- `lib/run_state.py`
- `lib/task_graph.py`
- `lib/research_graph.py`
- `lib/report_audit.py`

## Procedure

### 1. Verify run identity and file set

Confirm the run directory exists and contains the artifacts required for its current state. Verify `run_id` consistency across `run.json`, `task-graph.json`, graph records, decisions, report metadata, and prior audit when present.

### 2. Validate state history

Check:

- legal transitions only
- monotonically ordered timestamps
- valid `resume_state` for blocked runs
- no transition from `COMPLETE` back to an active state
- no artifact modification after completion unless the run is explicitly superseded

Map state-history failures to repair stage `SCOPED` or `PLANNED` depending on the defect.

### 3. Validate the task graph

Require:

- schema-valid tasks
- unique task IDs
- acyclic topology
- every dependency backed by producer/consumer artifact intersection
- one writer per output artifact
- bounded fan-out and budgets
- one merge owner
- testable `done_when`
- completed task outputs present and hash-valid when hashes are recorded

### 4. Validate source records

Check JSONL parsing, unique IDs, required provenance, date formats, authority tiers, independence groups, content hashes, injection-risk metadata, and accepted/rejected status. Warn on missing publication dates; fail when a required current source lacks usable temporal metadata.

### 5. Validate the evidence graph

Check:

- parseability and unique IDs
- allowed node/edge types
- endpoint existence and type compatibility
- evidence spans resolve to sources
- exact locators and hashes are present
- verified claims have valid support
- contested claims retain both credible sides or explicit rationale
- calculations and inferences expose premises
- merge/supersession decisions are reversible and resolvable

### 6. Audit report traceability

Use `lib/report_audit.py` to verify:

- claim markers resolve
- source markers resolve to the cited claim's evidence path
- unsupported factual paragraphs are zero or within the explicit threshold
- contested and unknown claims are not represented as settled
- inference paragraphs cite premise claims
- source register entries resolve

### 7. Check report contract

Require the configured sections, audience/deliverable format, as-of date, scope, limitations, unresolved gaps, and conflict disclosure. For comparison artifacts, verify required columns, units, and missing-data semantics.

### 8. Evaluate thresholds and acceptance criteria

Compute metrics such as:

- `claim_evidence_coverage`
- `citation_resolvability`
- `unsupported_claims`
- `critical_questions_answered`
- `primary_source_coverage`
- `independence_group_coverage`
- `contested_claims_exposed`
- `fake_task_edges`

Evaluate each acceptance criterion and attach the artifact evidence used for the verdict.

### 9. Map failures to repair stages

Use the earliest stage capable of repair:

| Failure | Resume stage |
|---|---|
| target/criteria ambiguity | `SCOPED` |
| DAG, ownership, or budget defect | `PLANNED` |
| missing/weak source | `ACQUIRING` |
| missing span/locator/hash | `EXTRACTING` |
| duplicate or mistaken identity | `RESOLVING` |
| invalid status or entailment | `VERIFYING` |
| report marker/section/rendering defect | `SYNTHESIZING` |
| audit implementation error | `AUDITING` |

Do not send all failures back to the beginning.

### 10. Write audit.json

```json
{
  "schema_version": "2.0",
  "run_id": "...",
  "passed": false,
  "errors": [
    {"gate": "citation_resolvability", "message": "...", "repair_stage": "SYNTHESIZING", "artifacts": ["report.md"]}
  ],
  "warnings": [],
  "metrics": {},
  "criteria": [],
  "resume_state": "SYNTHESIZING",
  "instruments": {"researchctl": "2.0.0", "report_audit": "2.0.0", "graph_validator": "2.0.0"}
}
```

Write `passed: true` only when no hard gate fails. Warnings never become silent errors; strict-warning mode may promote named warning classes explicitly.

## Runtime

Run the integrated audit:

```bash
python -B ${CLAUDE_PLUGIN_ROOT}/scripts/researchctl.py audit <run>
```

If the CLI output lacks the richer per-gate structure above, preserve its result and supplement it in the audit record without changing a passing result to failure arbitrarily.

## Output contract

Return:

```json
{
  "run_path": "...",
  "passed": true,
  "audit_path": "<run>/audit.json",
  "hard_failures": [],
  "warnings": [],
  "metrics": {},
  "criteria": [],
  "complete_eligible": true,
  "resume_state": null
}
```

## Failure recovery

- **Malformed JSONL:** stop parsing at the first malformed record, report line number, and preserve the file unchanged.
- **Missing optional artifact:** warn only if the current state does not require it.
- **Missing required artifact:** fail and map to its owning stage.
- **Audit tool exception:** return an audit-instrument failure with `resume_state: AUDITING`; do not infer pass/fail from partial metrics.
- **Threshold absent:** use the contract default only if documented; otherwise report configuration ambiguity.
- **Completed run changed:** fail immutability and require a superseding run.
- **Warnings are numerous:** keep them visible; do not convert to success prose that hides their effect.

## Completion checklist

- [ ] Run identity is consistent.
- [ ] State history is legal and immutable after completion.
- [ ] Task graph has zero cycles and fake edges.
- [ ] Canonical JSONL files parse and validate.
- [ ] Verified claims have valid evidence paths.
- [ ] Report markers and required sections resolve.
- [ ] Acceptance criteria and thresholds are evaluated explicitly.
- [ ] Every failure has an earliest repair stage.
- [ ] `audit.json` is written without mutating other artifacts.
