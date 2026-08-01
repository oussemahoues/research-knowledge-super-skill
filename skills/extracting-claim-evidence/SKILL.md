---
name: extracting-claim-evidence
description: This skill should be used when acquired documents, datasets, pages, code, transcripts, tables, or user-provided files must be converted into atomic claims and exact supporting, contradicting, or qualifying evidence spans. It writes validated batches for the canonical evidence graph while preserving provenance, source wording, and uncertainty. Do not browse for sources, merge entities, decide whether claims are true, or summarize facts without storing the exact evidence location.
---

# Extract Claim Evidence

Transform accepted source content into typed graph records. Success means another verifier can inspect each claim and its exact span without reopening the entire source or trusting the extractor's interpretation.

## Inputs

```json
{
  "run_id": "...",
  "task_id": "...",
  "source_records": ["source:<id>"],
  "source_content_paths": ["..."],
  "question_ids": ["q1"],
  "ontology_constraints": {"allowed_entity_types": [], "allowed_relations": []},
  "output_batch": "working/extraction-<task-id>.jsonl"
}
```

## Load before starting

- `references/evidence-ontology.md`
- `references/security.md`
- `schemas/evidence-graph.schema.json`
- `lib/research_graph.py`

## Procedure

### 1. Verify source identity and content integrity

Match each content item to a source record. Confirm the locator/version and recompute or verify its content hash. If content differs from the recorded hash, create a new source version or block extraction; never attach spans to the wrong source version.

### 2. Select the extraction path

- **Structured data:** map fields deterministically and preserve row/column keys.
- **Tables:** capture table title, page/sheet, row, column, unit, and footnotes.
- **Figures/images:** capture page/region and distinguish labels from inferred visual interpretation.
- **Code:** capture repository, commit/ref, file path, symbol, and line range.
- **Transcripts/audio:** capture timestamp range and speaker when available.
- **Unstructured prose:** capture page, section, paragraph, or stable text offsets.

Do not use OCR when reliable text extraction exists. When OCR is unavoidable, mark `extraction_method: ocr` and preserve confidence/quality warnings.

### 3. Extract atomic claims

A claim must be independently checkable. Split propositions when they differ by subject, metric, population, condition, time, or modality.

Classify `claim_kind`:

- `observation`: directly reported measurement or event
- `quotation`: attributed statement
- `calculation`: deterministic result from stored inputs and method
- `inference`: interpretation derived from premise claims
- `definition`: formal meaning from an authority
- `requirement`: normative obligation from a standard, law, or procedure

Retain hedging and scope. Do not turn “may improve” into “improves,” or a subgroup result into a universal claim.

### 4. Create exact EvidenceSpan nodes

Each span includes:

```json
{
  "type": "EvidenceSpan",
  "source_id": "source:<id>",
  "locator": "page 12, table 3, row B",
  "text": "Exact quoted text or normalized cell value",
  "content_hash": "sha256:...",
  "extraction_method": "text|table-map|code-map|ocr|manual-visual",
  "extracted_at": "YYYY-MM-DDTHH:MM:SSZ",
  "quality_warnings": []
}
```

Use the smallest span that preserves meaning. Include nearby qualifiers, units, headings, and footnotes when omission would distort interpretation.

### 5. Link spans to claims semantically

Use:

- `SUPPORTS` when the span directly supports the claim at the same scope
- `CONTRADICTS` when it materially conflicts
- `QUALIFIES` when it narrows, conditions, or limits the claim
- `ASSERTED_BY` from claim to source for attribution
- `ABOUT` for entity/event associations

Topical similarity is not support. A source discussing the same subject without asserting the proposition gets no support edge.

### 6. Extract entities and events without merging

Create source-form candidates with:

- surface name
- type
- stable identifiers present in the source
- source-specific attributes
- provenance

Do not collapse aliases or choose a canonical identity here. Preserve ambiguity for `resolving-research-entities`.

### 7. Represent calculations and inferences transparently

For a calculation, store input values, units, formula/method, and links to every source span. For an inference, create premise edges to all claims used. Never encode an unstated model assumption as if it were observed evidence.

### 8. Validate the batch

Write to a temporary batch, then validate:

```bash
python -B ${CLAUDE_PLUGIN_ROOT}/scripts/researchctl.py validate-graph \
  <working>/combined-existing-plus-batch.jsonl
```

Check unique IDs, valid endpoint types, required provenance, source existence, and verified-status restrictions. Only the evidence curator appends a passing batch to `evidence-graph.jsonl`.

## Output contract

```json
{
  "run_id": "...",
  "task_id": "...",
  "batch_path": "working/extraction-<task-id>.jsonl",
  "created": {
    "claims": ["claim:..."],
    "evidence_spans": ["evidence:..."],
    "entities": ["entity:..."],
    "events": ["event:..."],
    "edges": ["edge:..."]
  },
  "candidate_duplicates": [],
  "warnings": [],
  "validation": {"passed": true, "errors": []}
}
```

## Failure recovery

- **Missing locator:** do not create a factual span; return a source-quality gap.
- **Hash mismatch:** create or request a new source version before extracting.
- **Ambiguous pronoun or entity:** preserve the surface reference and mark unresolved.
- **Table footnote changes meaning:** include the footnote in the span or create a qualifying edge.
- **OCR uncertainty:** preserve the image locator, OCR text, and confidence warning; do not promote critical claims without independent verification.
- **Conflicting values in one source:** create separate claims/spans and let adjudication resolve context.
- **Invalid graph batch:** quarantine the batch, report exact validator errors, and do not partially append it.

## Completion checklist

- [ ] Every claim is atomic and scope-preserving.
- [ ] Every factual claim has an exact span or is explicitly an inference.
- [ ] Span locators are reproducible.
- [ ] Source IDs and hashes match.
- [ ] Support edges reflect entailment, not topic similarity.
- [ ] Entity candidates remain unmerged.
- [ ] Calculations and inferences expose premises.
- [ ] Batch validation passes before append.
