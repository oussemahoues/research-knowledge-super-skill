---
name: extracting-claim-evidence
description: Extract atomic claims, exact evidence spans, entities, relations, events, methods, datasets, and provenance from already acquired sources into the canonical evidence graph. Use after source acquisition or when ingesting user-provided documents and structured data. Do not browse for sources, merge entities, adjudicate truth, or summarize without storing the supporting span.
---

# Extract Claim Evidence

1. Load the evidence ontology and task-specific entity/relation constraints.
2. Route structured sources to deterministic field mapping, semi-structured sources to parsers, and unstructured sources to bounded extraction.
3. Extract atomic claims. Split independent propositions and label observation, quotation, calculation, or inference.
4. Create an `EvidenceSpan` for the exact text, table cell, figure region, code location, or data field. Include source ID, locator, hash, and extraction timestamp.
5. Connect evidence to claims with `SUPPORTS`, `CONTRADICTS`, or `QUALIFIES`; never infer support from topical co-occurrence.
6. Extract entities and events without merging aliases. Preserve source surface forms.
7. Validate node and edge types with `lib/research_graph.py`; reject invalid endpoints.
8. Append records atomically to `evidence-graph.jsonl`. Return created IDs, candidates, and extraction warnings.
