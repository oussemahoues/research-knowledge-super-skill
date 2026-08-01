---
name: resolving-research-entities
description: This skill should be used when an evidence graph contains duplicate names, aliases, source versions, organizations, products, people, datasets, repeated claims, or broken paths caused by identity fragmentation. It performs reversible candidate blocking, scored matching, canonicalization decisions, and graph validation while preserving provenance and conflicts. Do not merge solely on name similarity, delete original records, or adjudicate whether claims are true.
---

# Resolve Research Entities

Reduce identity fragmentation without corrupting the graph through false-positive merges. Success means every merge is explainable, reversible, type-compatible, and recorded in `decisions.jsonl`.

## Inputs

```json
{
  "run_id": "...",
  "task_id": "...",
  "graph_path": "<run>/evidence-graph.jsonl",
  "entity_types": ["Organization", "Product", "Person"],
  "thresholds": {"auto_merge": 0.95, "review": 0.70},
  "stable_identifier_fields": ["doi", "orcid", "registration_number", "repository_url"]
}
```

## Load before starting

- `references/evidence-ontology.md`
- `references/architecture.md`
- `lib/entity_resolution.py`
- `lib/research_graph.py`

## Procedure

### 1. Build candidate blocks

Compare only type-compatible candidates sharing at least one blocking key:

- normalized name/token signature
- stable identifier prefix
- email/domain or official website
- jurisdiction and registration number
- product family/model pattern
- DOI, ORCID, ISBN, repository identity, or dataset identifier
- graph-neighborhood signature

Never compare all pairs at scale. Never compare incompatible entity types.

### 2. Compute evidence-based match features

Score independently:

- stable identifier equality
- exact and normalized names
- aliases/acronyms
- location/jurisdiction
- temporal overlap
- organization or product hierarchy
- shared official domains
- compatible graph neighborhoods
- conflicting attributes

A stable identifier match may dominate. Name similarity alone must never cross the auto-merge threshold.

### 3. Apply decision bands

- score >= `auto_merge` with no hard conflict: merge automatically
- `review` <= score < `auto_merge`: queue as ambiguous
- score < `review`: reject match
- any hard conflict in stable identity or type: reject regardless of lexical score

Prefer false negatives to false-positive merges for consequential entities.

### 4. Choose a canonical ID deterministically

Prefer, in order:

1. authoritative stable identifier
2. earliest valid graph ID tied to the authoritative source
3. deterministic stable ID from normalized semantic identity

Do not choose based on insertion order when a stronger identity exists.

### 5. Preserve all provenance and conflicts

The canonical entity retains:

- every alias and source surface form
- source-specific attributes
- conflicting values as separate provenance-bearing assertions
- valid temporal ranges
- original node IDs through `SAME_AS` edges or merge metadata

Never overwrite a conflicting attribute without retaining the source record.

### 6. Record a reversible decision

Append to `decisions.jsonl`:

```json
{
  "decision_id": "resolution:<id>",
  "decision_type": "entity-merge|claim-dedup|source-version-link|reject-match",
  "candidates": ["entity:a", "entity:b"],
  "canonical_id": "entity:a",
  "score": 0.97,
  "features": {"stable_id": 1.0, "name": 0.92, "conflicts": 0},
  "rationale": "...",
  "merged_from": ["entity:b"],
  "reversal": {"remove_edges": ["edge:..."], "restore_ids": ["entity:b"]},
  "decided_at": "..."
}
```

### 7. Update by append, never deletion

Add `SAME_AS` for aliases/duplicates and `SUPERSEDES` for true versions. Preserve original records in the append-only log. Consumers resolve canonical views through decisions and edges.

### 8. Revalidate and measure

Run graph validation after each decision batch. Report:

- candidates reviewed
- automatic merges
- ambiguous clusters
- rejected matches
- hard conflicts
- estimated residual duplicate rate
- paths restored or broken

## Output contract

```json
{
  "run_id": "...",
  "task_id": "...",
  "decision_batch": "working/resolution-<task-id>.jsonl",
  "auto_merged": [],
  "ambiguous": [],
  "rejected": [],
  "hard_conflicts": [],
  "metrics": {},
  "validation": {"passed": true, "errors": []}
}
```

## Failure recovery

- **Stable identifiers conflict:** reject merge and create a conflict note.
- **Same name, different jurisdictions or dates:** keep separate unless authoritative identity evidence resolves them.
- **Organization renamed:** use `SUPERSEDES` or temporal aliasing rather than flattening distinct legal entities blindly.
- **Product version changed materially:** retain separate version nodes and link them.
- **Repeated claims differ in scope:** do not deduplicate; use `QUALIFIES` or keep separate claims.
- **Ambiguous cluster too large:** tighten blocking keys and split by type/time/jurisdiction.
- **Validation fails:** quarantine the entire decision batch; do not apply partial canonicalization.

## Completion checklist

- [ ] Candidate blocks are type-compatible.
- [ ] Stable identifiers and conflicts are explicit features.
- [ ] Name similarity alone never causes auto-merge.
- [ ] Every merge has a deterministic canonical ID.
- [ ] Aliases and conflicting attributes retain provenance.
- [ ] Every decision is reversible.
- [ ] Original records remain in the append-only graph.
- [ ] Graph validation passes after the batch.
