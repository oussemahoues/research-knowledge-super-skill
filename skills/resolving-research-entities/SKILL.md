---
name: resolving-research-entities
description: This skill should be used when a v3 evidence graph contains duplicate entities, aliases, repeated claims, source versions, or broken retrieval paths caused by identity fragmentation. It creates conservative, scored, reversible fusion decisions and canonical projections. Do not merge solely on name similarity, delete original nodes, overwrite conflicting attributes, or adjudicate claim truth.
---

# Resolve Research Entities

Reduce fragmentation without introducing false-positive identity merges. Prefer unresolved duplicates to corrupt canonical identity.

## Inputs

```json
{
  "run_id": "run:...",
  "task_id": "task:...",
  "entity_types": ["Organization", "Product", "Person"],
  "thresholds": {"auto_merge": 0.90, "review": 0.65},
  "ontology_version": 1
}
```

## Procedure

### 1. Build candidate blocks

Compare only type-compatible nodes sharing a stable identifier, normalized name token, official domain, jurisdiction key, product model, dataset identifier, or neighborhood signature.

### 2. Compute features

Score names, aliases, identifiers, attributes, temporal compatibility, and graph neighborhoods separately. Record hard conflicts explicitly.

### 3. Apply conservative bands

Auto-merge only when stable identifiers agree and the high-confidence threshold is met. Queue ambiguous cases for human review. Reject hard conflicts regardless of lexical similarity.

### 4. Choose canonical identity

Prefer authoritative stable identifiers, then authoritative earlier nodes, then deterministic semantic IDs. Do not use arbitrary insertion order.

### 5. Preserve provenance

Keep source surface forms, aliases, conflicting assertions, temporal ranges, and original node IDs. Canonical views are projections, not destructive rewrites.

### 6. Record reversible decisions

Use `resolution_decisions` and `canonical_members`. Every applied merge includes score components, rationale, reviewer, and executable reversal data.

### 7. Require approval where needed

A `review` proposal cannot be applied until an independent reviewer changes it to `review-approved`. The fusion engine cannot approve its own ambiguous result.

### 8. Link versions correctly

Use temporal supersession for real versions or renamed legal entities. Do not flatten materially distinct product or organization versions.

### 9. Revalidate paths

Check canonical projections, active memberships, contradictions, and affected retrieval paths after each decision batch.

### 10. Preserve rollback

Test that reversing a decision deactivates canonical membership without deleting nodes, edges, or prior decision evidence.

## Output contract

```json
{
  "schema_version": "3.0",
  "run_id": "run:...",
  "task_id": "task:...",
  "applied_decisions": ["resolution:..."],
  "review_queue": [],
  "rejected": [],
  "hard_conflicts": [],
  "validation": {"passed": true, "errors": []}
}
```

## Failure recovery

- Stable identifiers conflict: reject and preserve a conflict note.
- Same name but incompatible date or jurisdiction: keep separate.
- Organization renamed: model temporal succession where legal identity changed.
- Large ambiguous cluster: tighten blocking keys and split by type, time, or jurisdiction.
- Validation failure: reverse the decision batch and retain evidence for review.

## Completion checklist

- [ ] Candidate pairs are type-compatible.
- [ ] Stable identifiers and conflicts are explicit.
- [ ] Name similarity alone never auto-merges.
- [ ] Canonical IDs are deterministic.
- [ ] Provenance and original nodes remain intact.
- [ ] Ambiguous decisions require independent approval.
- [ ] Every applied merge is reversible and tested.
