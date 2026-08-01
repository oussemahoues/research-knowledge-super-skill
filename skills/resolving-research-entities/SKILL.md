---
name: resolving-research-entities
description: This skill should be used when an evidence graph contains duplicate entities, aliases, source versions, repeated claims, or broken multi-hop paths caused by identity fragmentation. It performs reversible candidate blocking, matching, merge decisions, and supersession while preserving provenance and conflicts. Do not merge solely on name similarity, delete original records, or adjudicate whether claims are true.
---

# Resolve Research Entities

Reduce identity fragmentation without corrupting the graph. Success means high-confidence duplicates are linked or canonically resolved through reversible decisions, while ambiguous cases remain separate.

## Inputs

```json
{
  "run_id": "...",
  "graph_path": "<run>/evidence-graph.jsonl",
  "decision_path": "<run>/decisions.jsonl",
  "entity_types": ["optional"],
  "thresholds": {"auto_merge": 0.95, "review": 0.70},
  "blocking_keys": ["type", "normalized_name", "stable_identifier"]
}
```

## Load before starting

- `references/evidence-ontology.md`
- `lib/entity_resolution.py`
- `lib/research_graph.py`

## Procedure

1. Validate the current graph before resolution. Do not repair identity on top of invalid endpoints or malformed records.
2. Build candidate blocks using compatible node type and normalized stable keys. Avoid all-pairs comparison at scale.
3. Compute match evidence from:
   - exact stable identifiers;
   - normalized names and aliases;
   - dates, locations, organizations, and other stable attributes;
   - source-specific identifiers;
   - graph neighborhood compatibility;
   - explicit contradiction signals.
4. Reject type-incompatible candidates immediately.
5. Score candidates and retain the component scores, not only the total.
6. Apply decisions:
   - below review threshold: `rejected-match`;
   - between review and auto-merge thresholds: `ambiguous`, keep separate;
   - above auto-merge threshold: merge only if no hard contradiction exists.
7. Prefer false negatives to false-positive merges. A wrong merge can contaminate every downstream claim.
8. Select a canonical ID using stable identifiers and existing graph references; do not use insertion order alone.
9. Preserve aliases, source-specific attributes, conflicting values, and provenance. Do not overwrite disagreement.
10. Append a decision record with candidates, score components, rationale, canonical ID, `merged_from`, and reversal instructions.
11. Add `SAME_AS` for equivalent identities and `SUPERSEDES` for versioned records. Never delete original nodes from the append-only log.
12. Revalidate the graph and calculate unresolved-cluster and estimated duplicate metrics.

## Decision record contract

```json
{
  "decision_id": "decision:...",
  "kind": "entity-resolution",
  "candidates": ["entity:a", "entity:b"],
  "decision": "merge|ambiguous|reject",
  "canonical_id": "entity:a|null",
  "score": 0.97,
  "components": {"identifier": 1.0, "name": 0.9, "context": 0.8},
  "rationale": "...",
  "merged_from": ["entity:b"],
  "reversal": {"remove_edges": ["edge:..."], "restore_ids": ["entity:b"]},
  "timestamp": "..."
}
```

## Output contract

```json
{
  "resolved": [],
  "ambiguous_clusters": [],
  "rejected_pairs": [],
  "decision_ids": [],
  "metrics": {"candidate_pairs": 0, "auto_merges": 0, "ambiguous": 0},
  "graph_validation": {"passed": true, "errors": []}
}
```

## Failure recovery

- **Conflicting stable identifiers:** never auto-merge; retain an ambiguous cluster.
- **Same name, different type or context:** reject the pair.
- **Source versions:** use `SUPERSEDES` rather than `SAME_AS` when content or effective date differs.
- **Claim duplicates with different scope:** keep separate claims and use `QUALIFIES` or temporal relations as appropriate.
- **Canonical node already heavily referenced:** preserve it unless a stronger immutable identifier requires a new canonical mapping.
- **Thresholds unavailable:** use conservative defaults and report them.
- **Graph validation fails after decisions:** append no resolution batch; return exact failures.

## Completion checklist

- [ ] Candidate blocking is bounded.
- [ ] Type compatibility is enforced.
- [ ] Component scores and rationale are retained.
- [ ] Ambiguous cases remain separate.
- [ ] Merges are reversible.
- [ ] Conflicting attributes retain provenance.
- [ ] Original records are not deleted.
- [ ] Graph validation passes after resolution.
