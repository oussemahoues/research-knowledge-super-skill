---
name: extracting-claim-evidence
description: This skill should be used when accepted source episodes must be converted into atomic claims, exact evidence spans, entities, events, calculations, or typed temporal edges. Also trigger for table, code, figure, transcript, or structured-data extraction. Do not browse for sources, merge identities, adjudicate truth, or store unsupported summaries as evidence.
---

# Extract Claim Evidence

Write typed graph records from verified source episodes so a separate verifier can reproduce every evidentiary connection.

## Inputs

```json
{
  "run_id": "run:...",
  "task_id": "task:...",
  "source_episode_ids": ["episode:..."],
  "question_ids": ["q1"],
  "ontology_version": 1,
  "allowed_entity_types": [],
  "allowed_relations": []
}
```

## Procedure

### 1. Verify episode integrity

Resolve each episode ID, verify its stored content hash, and confirm it is not quarantined. A hash mismatch blocks extraction and creates a tamper finding.

### 2. Select extraction mode

Use deterministic field mapping for structured data; row, column, units, and footnotes for tables; repository, commit, file, symbol, and lines for code; page and region for figures; timestamps and speaker for transcripts; stable offsets for prose.

### 3. Extract atomic claims

Split propositions by subject, metric, population, condition, time, geography, or modality. Preserve hedging and scope.

### 4. Create evidence spans

Store the smallest exact span that preserves meaning. Redact sensitive values from span text unless the contract explicitly requires them and access is authorized; retain a hash and locator to the original episode.

### 5. Add temporal semantics

Every material edge records `valid_from`, optional `valid_to`, and `recorded_at`. Distinguish source-effective time from retrieval time.

### 6. Link semantically

Use `SUPPORTS`, `CONTRADICTS`, or `QUALIFIES` only when the span matches the proposition and scope. Topical similarity is not support.

### 7. Create source-form entities

Preserve names, identifiers, attributes, provenance, and ambiguity. Do not choose canonical identity here.

### 8. Represent calculations and inferences

Store inputs, units, formulas, premise claims, and method. Never present a model assumption as observed evidence.

### 9. Write through the graph API

Use `TemporalGraph.put_node` and `add_edge`. Do not write directly to legacy JSONL files or bypass ontology validation.

### 10. Validate the batch

Check node and edge types, source-episode references, temporal intervals, provenance, unique IDs, and sensitive-data redaction before completing the task.

## Output contract

```json
{
  "schema_version": "3.0",
  "run_id": "run:...",
  "task_id": "task:...",
  "created": {"claims": [], "evidence_spans": [], "entities": [], "events": [], "edges": []},
  "candidate_duplicates": [],
  "warnings": [],
  "validation": {"passed": true, "errors": []}
}
```

## Failure recovery

- Missing locator: create a source-quality gap, not a factual span.
- Episode hash mismatch: block and record tamper evidence.
- Ambiguous reference: preserve the surface form and mark unresolved.
- Footnote changes meaning: include it or add a qualifying edge.
- OCR uncertainty: retain confidence and require independent verification for material claims.
- Invalid graph batch: reject the whole transaction; do not partially apply it.

## Completion checklist

- [ ] Episode integrity and quarantine status were checked.
- [ ] Claims are atomic and scope-preserving.
- [ ] Spans have reproducible locators and redaction status.
- [ ] Edges carry temporal and provenance fields.
- [ ] Entity candidates remain unmerged.
- [ ] Calculations expose inputs and premises.
- [ ] Graph validation passes transactionally.
