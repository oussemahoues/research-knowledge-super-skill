---
name: auditing-research-run
description: This skill should be used before declaring research complete, when reviewing a run produced by another agent, when checking citations and evidence coverage, or when diagnosing why a run is blocked. It performs deterministic validation of state history, task topology, canonical artifacts, graph integrity, claim-evidence coverage, citation resolvability, report sections, contradiction exposure, and immutability. Do not acquire evidence, repair conclusions silently, or rewrite the report.
---

# Audit the Research Run

Produce an independent completion verdict. A failed audit is a valid and useful result; report exact gates and the earliest stage capable of repair.

## Inputs

```json
{
  "run_path": "research-runs/run_...",
  "mode": "completion|diagnostic|review",
  "threshold_overrides": "optional and must be explicitly authorized"
}
```

## Load before starting

- `references/evaluation.md`
- `references/report-contract.md`
- `lib/run_state.py`
- `lib/task_graph.py`
- `lib/research_graph.py`
- `lib/report_audit.py`

## Procedure

1. Verify the run directory exists and contains `run.json`, `task-graph.json`, `sources.jsonl`, `evidence-graph.jsonl`, and `report.md` for a completion audit.
2. Validate `run.json` schema, run ID, ISO dates, thresholds, budgets, assumptions, acceptance criteria, and legal state-transition history.
3. Validate task topology:
   - acyclic;
   - zero fake dependencies;
   - one writer per output;
   - bounded fan-out and budgets;
   - one merge owner;
   - completed tasks satisfy `done_when` and output hashes.
4. Validate source records:
   - parseable JSONL;
   - unique IDs;
   - required provenance;
   - content hashes;
   - authority/freshness/independence fields;
   - recorded injection risk.
5. Validate evidence graph:
   - unique node and edge IDs;
   - legal endpoint types;
   - resolvable references;
   - verified claims have support;
   - contested claims have visible support and contradiction;
   - inference claims link to premises;
   - append-only/supersession rules are respected.
6. Audit `report.md`:
   - required sections;
   - as-of date;
   - claim marker resolution;
   - source marker resolution;
   - evidence linkage;
   - unsupported factual paragraphs;
   - contested and unknown claim exposure;
   - limitations and gaps.
7. Evaluate every acceptance criterion against named artifacts and metrics. Do not infer a pass from overall plausibility.
8. Compare metrics with configured thresholds, including `claim_evidence_coverage`, `citation_resolvability`, and `unsupported_claims`.
9. Check immutability: a run already marked `COMPLETE` must not contain later in-place mutations without a superseding run record.
10. Write `audit.json` only. Do not mutate other artifacts.
11. Return completion eligibility and map each failure to the earliest repair stage.

## Runtime

```bash
python -B ${CLAUDE_PLUGIN_ROOT}/scripts/researchctl.py audit <run-path>
```

The runtime result is authoritative for deterministic checks. Add human-readable diagnosis without weakening failures.

## Output contract

```json
{
  "schema_version": "2.0",
  "run_id": "...",
  "passed": false,
  "errors": ["..."],
  "warnings": ["..."],
  "metrics": {},
  "criteria": [{"id": "a1", "passed": false, "evidence": [], "failure": "..."}],
  "repair_plan": [
    {"gate": "citation_resolvability", "resume_state": "SYNTHESIZING", "action": "repair markers"}
  ],
  "instruments": {"researchctl": "2.0.0"}
}
```

## Repair-stage mapping

| Failure | Earliest repair state |
|---|---|
| Invalid target/criteria | `SCOPED` |
| Cycle, fake edge, duplicate writer | `PLANNED` |
| Missing/weak source provenance | `ACQUIRING` |
| Missing span, invalid graph endpoint | `EXTRACTING` |
| Duplicate identity contamination | `RESOLVING` |
| Unsupported or unresolved material claim | `VERIFYING` |
| Broken report marker or missing section | `SYNTHESIZING` |
| Audit serialization issue only | `AUDITING` |

## Failure recovery

- **Artifact missing:** fail the corresponding gate; do not create a placeholder.
- **Malformed JSONL line:** report file and line number when available; stop dependent checks but continue independent checks.
- **Threshold override requested:** apply only when explicitly authorized and record original and override values.
- **Runtime tool unavailable:** run equivalent deterministic library checks when possible and record the instrument limitation.
- **Completed run mutated:** fail immutability and require a superseding run.
- **Warnings only:** permit completion only when no configured criterion treats the warning as blocking.

## Completion checklist

- [ ] State history is legal.
- [ ] Task graph has zero cycles and fake edges.
- [ ] Canonical artifacts parse and IDs resolve.
- [ ] Verified claims have evidence.
- [ ] Contested claims expose contradiction.
- [ ] Report markers and required sections pass.
- [ ] Acceptance criteria are evaluated individually.
- [ ] Thresholds pass.
- [ ] Immutability passes.
- [ ] `audit.json.passed` alone controls completion eligibility.
