---
name: adjudicating-research-claims
description: This skill should be used when candidate claims require independent verification, falsification, contradiction analysis, numerical checking, supersession, rejection, or evidence-gap classification. Also trigger for consequential conclusions and citation-entailment review. Do not trust extractor confidence, source titles, citation counts, or absence of contradiction as proof, and do not verify work produced by the same owner.
---

# Adjudicate Research Claims

Produce durable terminal decisions from exact evidence chains in a context independent from extraction.

## Inputs

```json
{
  "run_id": "run:...",
  "task_id": "task:...",
  "claim_ids": ["claim:..."],
  "as_of": "YYYY-MM-DDTHH:MM:SSZ",
  "minimum_independence_groups": 1,
  "gap_iteration": 0,
  "max_gap_iterations": 2
}
```

## Procedure

### 1. Reconstruct claim packets

Load claim scope, materiality, premise claims, supporting, contradicting, and qualifying edges, source episodes, independence groups, temporal intervals, and acceptance criteria.

### 2. Enforce separation

Reject material adjudication when verifier ownership matches extraction ownership. Route it to an independent verifier or auditor.

### 3. Test entailment

Compare subject, population, metric, units, time, geography, conditions, and modality. Reject citation laundering and topical-only support.

### 4. Verify provenance and integrity

Resolve every edge and source episode, verify source bytes, reject quarantined evidence, and account for sensitive-data redaction without losing locator integrity.

### 5. Test independence

Collapse syndicated copies, shared studies, common datasets, press-release rewrites, and repeated vendor assertions into their underlying independence groups.

### 6. Analyze contradiction and qualification

Match scope and time before declaring contradiction. Preserve credible unresolved disagreement instead of selecting by source count.

### 7. Recompute numbers

Check units, arithmetic, dates, and deterministic calculations. A numerical mismatch blocks verification.

### 8. Assign v3 status

Use `verified`, `contested`, `needs_review`, or `rejected`. Represent historical replacement through graph supersession rather than overwriting a decision.

### 9. Request bounded gaps

Request new acquisition only for material claims when identifiable evidence could change the conclusion and gap budget remains.

### 10. Persist the decision

Write an `adjudication_decisions` record with exact support and contradiction edge IDs, source episodes, independence groups, lexical entailment, numerical consistency, issues, and model-review requirement.

## Output contract

```json
{
  "schema_version": "3.0",
  "run_id": "run:...",
  "task_id": "task:...",
  "decisions": [{"claim_id": "claim:...", "status": "verified", "support_edge_ids": [], "issues": []}],
  "gap_requests": [],
  "limitations": []
}
```

## Failure recovery

- Missing or inaccessible span: use `needs_review` and request a precise gap when material.
- Source bytes changed: require a new episode and re-extraction.
- Evidence supports a narrower claim: reject the broad claim and propose the narrower one.
- Date or version explains conflict: use time-bounded claims and supersession.
- Gap budget exhausted: retain `contested` or `needs_review` visibly.
- Same worker extracted and verifies: block and reassign.

## Completion checklist

- [ ] Claim packets contain exact evidence edges.
- [ ] Verifier independence is satisfied.
- [ ] Entailment, scope, provenance, and source integrity were tested.
- [ ] Independence groups were collapsed correctly.
- [ ] Contradiction, qualification, and numbers were checked.
- [ ] Every material claim has a durable v3 status.
- [ ] Gap requests are precise and bounded.
