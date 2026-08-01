---
name: auditing-research-run
description: This skill should be used before an Evidence Research v3 run is declared complete, when reviewing another agent's run, when CI or report verification fails, or when diagnosing a blocked run. It deterministically checks event-store integrity, task-DAG semantics, attempts and leases, open interrupts, source-episode hashes and quarantine state, temporal graph references, fusion decisions, claim adjudication, retrieval traces, report markers, migration integrity, and release thresholds. Do not acquire evidence, reinterpret claims, or rewrite the report while auditing.
---

# Audit an Evidence Research v3 Run

Produce a reproducible pass/fail verdict from canonical SQLite state and immutable source bytes. A failed audit is a valid result and must remain visible.

## Inputs

Provide:

```json
{
  "run_path": "research-runs/run_...",
  "mode": "completion|diagnostic|review",
  "expected_run_id": "optional",
  "strict_warnings": false,
  "release_review": false
}
```

Use `run.json` only to locate the run ID and database. Do not treat its contents as canonical transaction state.

## Preconditions

1. Confirm the run directory and `state.db` exist.
2. Confirm the requested run ID matches the database record.
3. Confirm no audit is attempting to mutate acquisition, extraction, fusion, or synthesis state.
4. Load the architecture, security, evaluation, and report contracts.

## Procedure

### 1. Run the integrated deterministic audit

```bash
python -B ${CLAUDE_PLUGIN_ROOT}/scripts/researchctl.py audit <run>
```

Preserve the resulting errors, warnings, metrics, and audit path exactly.

### 2. Verify task-control integrity

Check:

- every dependency carries a producer/consumer artifact intersection;
- task IDs and writer ownership are unique;
- the graph is acyclic and fan-in consumes every mandatory branch output;
- verifier owners differ from the workers whose outputs they verify;
- attempts and retries are bounded;
- running tasks hold valid leases;
- stale leases are recoverable;
- all completion-required tasks succeeded;
- successful sibling branches survived unrelated failures.

### 3. Verify human gates

- Fail completion when a mandatory interrupt remains open.
- Confirm every approval records reviewer, decision, rationale, and timestamp.
- Confirm a high-consequence proposer did not self-approve.
- Confirm rejected gates cancel or block the affected task rather than silently proceeding.

### 4. Verify source episodes

Check:

- source IDs, episode IDs, versions, and hashes are unique;
- content bytes exist and match the stored SHA-256 hash;
- locator, authority, independence group, effective time, retrieval time, and injection risk are present;
- superseding versions link to their predecessors;
- quarantined source episodes are not used by material evidence edges;
- legacy-unverified episodes remain warnings and are never described as byte-verified.

### 5. Verify ontology and temporal graph integrity

- Every node and edge references a valid ontology version.
- Edge endpoints exist and satisfy the active domain/range rules.
- Validity intervals are ordered and reconstructable as of historical dates.
- Supersession chains are coherent and non-destructive.
- Contradictory overlapping facts remain visible.
- Calculations and inferences expose premises.

### 6. Verify fusion decisions

- Candidate pairs were blocked and scored deterministically.
- Stable-identifier conflicts cannot auto-merge.
- Ambiguous material proposals require review.
- Canonical projections retain original members and provenance.
- Applied merges contain executable reversal records.
- Reversed merges are inactive and auditable.

### 7. Verify material-claim adjudication

For every material claim, require a latest decision. Check:

- `verified` claims contain valid support edges;
- `contested` claims contain contradiction edges;
- numbers in the claim occur in supporting spans when applicable;
- temporal validity matches the requested as-of date;
- source-independence requirements are evaluated;
- quarantined support cannot produce a publishable decision;
- `needs_review` and `rejected` claims are excluded from findings.

### 8. Verify retrieval traces

When retrieval was used, require persisted:

- query text and query class;
- selected retrieval methods;
- node IDs, edge IDs, and constrained paths;
- source-episode IDs;
- missing links and unresolved gaps;
- token estimate and as-of timestamp.

Warn when a query requested a temporal answer without an explicit as-of date.

### 9. Verify report traceability

When a report exists, check:

- every claim marker resolves to the latest publishable adjudication;
- every evidence-edge marker belongs to that claim's support or contradiction chain;
- every source marker resolves to an immutable source episode;
- required scope, findings, conflicts, limitations, gaps, and source-register sections exist;
- `needs_review` and `rejected` claims are absent from decision-ready findings;
- contested claims are not presented as settled.

### 10. Verify migration and rollback evidence

For migrated runs, confirm:

- the v2 source directory digest remained unchanged;
- legacy node and edge IDs were preserved;
- the v3 destination was new and isolated;
- migration limitations are recorded;
- the v2 fallback remains executable with `EVIDENCE_RESEARCH_ENGINE=v2`.

### 11. Map failures to bounded repair stages

Use the earliest plane capable of repair:

| Failure | Repair plane |
|---|---|
| target or acceptance ambiguity | scoping/control |
| DAG, ownership, lease, or budget defect | task planning/runtime |
| missing or weak source | acquisition |
| missing span, locator, hash, or ontology type | extraction |
| mistaken identity or irreversible merge | fusion |
| invalid support, contradiction, number, or time decision | adjudication |
| report marker or section defect | synthesis |
| audit implementation error | audit tooling |

Do not restart the full run when a bounded repair is sufficient.

## Failure recovery

- **Malformed database or migration:** stop and preserve the original files; do not attempt destructive repair.
- **Missing content bytes:** fail source integrity and reacquire as a new episode.
- **Expired lease:** recover through the runtime, then rerun the audit.
- **Audit tool exception:** return an audit-instrument failure; never infer a pass from partial checks.
- **Missing threshold:** use only a documented contract default; otherwise report configuration ambiguity.
- **Completed run changed:** fail immutability and require a superseding run.
- **Numerous warnings:** retain every warning; do not hide them behind success prose.

## Output contract

Return:

```json
{
  "schema_version": "3.0",
  "run_id": "run:...",
  "passed": false,
  "errors": [
    {
      "gate": "source_integrity",
      "message": "Source episode hash mismatch",
      "repair_plane": "acquisition",
      "artifacts": ["episode:..."]
    }
  ],
  "warnings": [],
  "metrics": {},
  "complete_eligible": false,
  "release_eligible": false,
  "audit_path": "<run>/audit.json"
}
```

Return `release_eligible: true` only after all benchmark, fault-injection, security, migration, rollback, review, and human release gates pass.

## Completion checklist

- [ ] Run identity and database location are consistent.
- [ ] Task graph has zero cycles, fake edges, and writer conflicts.
- [ ] Attempts, leases, retries, checkpoints, and interrupts are coherent.
- [ ] Source bytes and hashes resolve or are explicitly legacy-unverified.
- [ ] Quarantined evidence is excluded.
- [ ] Ontology versions and temporal intervals validate.
- [ ] Fusion decisions are reversible.
- [ ] Every material claim has a publishable or explicitly blocked decision.
- [ ] Retrieval traces and report markers resolve.
- [ ] Migration and fallback evidence is present when applicable.
- [ ] Every hard failure identifies a bounded repair plane.
- [ ] No completion or release claim is made while a hard gate fails.
