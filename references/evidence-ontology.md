# Evidence Ontology and Temporal Graph Contract

## Purpose

The ontology defines legal graph vocabulary for a scoped run. It is not a universal knowledge model and must remain no larger than the acceptance questions require. Runtime storage separates source bytes, source episodes, typed graph nodes, bitemporal edges, fusion decisions, retrieval traces, and adjudications.

## Core records

| Record | Identity and role |
|---|---|
| Source episode | Immutable version of acquired bytes with locator, hash, authority, independence, risk, and time metadata |
| Graph node | Stable typed object with `node_id`, `node_type`, ontology version, and structured data |
| Graph edge | Typed relation with endpoints, valid time, recorded time, source episode, provenance, status, and optional supersession |
| Fusion decision | Reversible proposal/apply/reverse record mapping aliases to a canonical entity |
| Adjudication | Latest independent decision about one Claim's active evidence chain |

## Recommended node types

- `ResearchQuestion`: scoped question with acceptance criteria.
- `Hypothesis`: proposition deliberately tested rather than presumed.
- `Claim`: one atomic, externally checkable proposition.
- `EvidenceSpan`: exact text, table cell, figure region, code range, or structured field.
- `Source`: logical source across one or more immutable episodes.
- `Entity`: resolved real-world object with aliases.
- `Event`: time-bounded occurrence with typed participants.
- `Method`: standard, procedure, model, or analytical technique.
- `Dataset`: defined data collection and version.
- `Finding`: adjudicated, decision-relevant result.
- `ResearchGap`: missing or weak evidence that could change a conclusion.

These are defaults, not permission to bypass the active ontology. A run may add task-specific types only through ontology versioning.

## Evidence relations

| Edge | Direction | Required meaning |
|---|---|---|
| `SUPPORTS` | EvidenceSpan -> Claim | Span directly increases support for the complete atomic Claim |
| `CONTRADICTS` | EvidenceSpan -> Claim | Span materially conflicts with the Claim |
| `QUALIFIES` | EvidenceSpan or Claim -> Claim | Narrows scope, modality, population, time, or conditions |
| `ASSERTED_BY` | Claim -> Source | Logical source asserts the Claim; not sufficient without a span |
| `DERIVED_FROM` | Finding or Claim -> premise Claim, Dataset, or Method | Explicit derivation or inference dependency |
| `ABOUT` | Claim or EvidenceSpan -> Entity or Event | Subject association, not evidentiary support |
| `SAME_AS` | Entity -> Entity | Recorded identity assertion; prefer reversible fusion for canonicalization |
| `SUPERSEDES` | Claim, Source, Episode, Edge, Ontology, or Run -> same kind | Later version replaces current applicability without deleting history |
| `ANSWERS` | Finding or Claim -> ResearchQuestion | Connects output to an acceptance question |
| `CITES` | Source -> Source | Bibliographic reference, not independent corroboration by itself |

Task-specific causal edges such as `CAUSES`, `TRIGGERS`, `PRECEDES`, and `ENABLES` require declared domains/ranges and evidence appropriate to causal wording.

## Claim granularity

A Claim must be falsifiable through one focused evidence check. Split independent conjunctions, preserve modality, population, denominator, unit, geography, and time window, and distinguish observation from inference. Store inference premises through `DERIVED_FROM`; never let narrative prose create an unrepresented premise.

Compound statement warning signs include multiple independent verbs, mixed time ranges, separate populations, a factual premise plus recommendation, or causal and correlational clauses in one node.

## Bitemporal semantics

Every evidentiary edge has:

- `valid_from` and optional `valid_to`: when the relation is true or applicable in the researched world;
- `recorded_at`: when the runtime learned and persisted it.

An as-of query filters validity time. `recorded_by` may reconstruct what the run knew at an earlier recording time. These dimensions must not be conflated.

Supersession closes the old edge's validity interval, marks it superseded, and creates a successor linked by `supersedes_edge_id`. It never overwrites the old provenance.

## Source episodes and provenance

An evidentiary edge should reference the immutable source episode containing its EvidenceSpan. Provenance should include a precise locator and extraction method. Logical Source identity alone is insufficient because content can change over time.

Quarantined or byte-integrity-failing episodes cannot support a publishable adjudication. Legacy migrated episodes marked `unverified-legacy` remain visible and require explicit limitations.

## Entity resolution

Fusion begins with a scored proposal. Apply only an attributable decision. Preserve feature scores, threshold, rationale, aliases, canonical ID, application time, and reversal state. High ambiguity or consequential fusion remains `review`; it is not resolved by choosing the highest score silently.

Reversal restores prior canonical mappings without deleting the proposal or its history.

## Adjudication state

The shipped verifier emits `verified`, `contested`, `needs_review`, or `rejected`. Temporal supersession is modeled in graph state rather than as a verifier status. `unknown` may appear in imported or domain-specific records but is not a built-in publishable adjudication.

`verified` means configured deterministic conditions passed. It is not metaphysical certainty or proof that a language model performed semantic entailment. `contested` preserves material support and contradiction. `needs_review` and `rejected` are not publishable factual findings.

## Ontology evolution

Additive versions may be activated under the run policy. Removing a type/relation or changing a relation domain/range is breaking and requires an impact analysis, migration plan, persisted interrupt, and independent human approval before activation. Existing records retain their original ontology version.

## Validation checklist

- Every node and edge type exists in the active ontology version.
- Every relation endpoint satisfies its declared domain/range.
- Every competency question has at least one representable path.
- Every evidentiary edge resolves to nodes and an eligible source episode.
- Time intervals are ordered and supersession chains are coherent.
- Compound Claims are split and inference premises are explicit.
- Fusion decisions are attributable and reversible.
- Contradictions and rejected proposals remain queryable.

