# ADR 0004: Query-Adaptive Bounded Graph Retrieval

- Status: accepted and implemented
- Decision owners: retrieval architecture
- Affects: query command, graph access, evidence gaps, context serialization

## Context

Dumping an entire evidence graph into a model context is expensive, non-reproducible, and obscures why a result appeared. A single retrieval method performs poorly across direct, path, temporal, global, causal, and evidence-gap questions. Retrieval must expose methods, IDs, omissions, and bounds without pretending rank is truth.

## Decision

Classify the query and invoke only the required shipped methods: lexical ranking, graph-neighborhood expansion, bounded shortest paths, temporal validity filtering, connected-component community grouping, and unsupported-Claim gap scanning. Fuse applicable ranked lists deterministically, bound nodes/edges/paths, serialize selected context, and persist a retrieval trace.

The shipped runtime does **not** implement vector embeddings or learned semantic retrieval. “Hybrid” means the implemented lexical and graph/time methods. A future semantic adapter requires a new ADR or amendment, benchmarks, provenance rules, and a fail-closed capability contract.

## Query classes and methods

| Query class | Primary methods | Required caveat |
|---|---|---|
| `direct` | lexical, graph neighborhood | Rank is not verification |
| `entity-local` | lexical, seeded neighborhood | Seed identity must be validated |
| `comparative` | lexical, neighborhood across subjects | Shared sources may not be independent |
| `multi-hop-path` | lexical seeds, bounded shortest path | Missing path is graph/bound evidence, not real-world absence |
| `temporal` | lexical/neighborhood plus validity filter | Missing `as_of` uses current validity and must be surfaced |
| `global-theme` | lexical plus connected components | Component membership is not a learned summary or causal relation |
| `causal-event` | lexical plus neighborhood restricted to causal/event edge types | Graph edge type alone does not prove causality |
| `evidence-gap` | unsupported-Claim scan plus lexical | A support edge can still be weak or non-publishable |

## Trace contract

A persisted trace contains trace ID, query and class, selected methods, ordered node IDs, edge IDs, paths, source episode IDs, missing links, token estimate, as-of value, and serialized context. Stable inputs and selected IDs produce a stable logical trace identity.

## Bounds and serialization

The caller controls result limit and path hop limit. Edge selection is capped relative to the result limit. Serialization contains only selected graph records and episodes; the full database is never used as an implicit fallback. Truncation or no-match is a successful bounded result with explicit gaps.

## Alternatives considered

### Full graph dump

Rejected for context size, leakage, and lack of retrieval explanation.

### Lexical retrieval only

Rejected because it cannot answer graph paths, temporal applicability, or structural gaps.

### Mandatory vector database

Rejected for portability and because no release-qualified adapter/benchmark exists. It remains a possible future extension.

### Retrieval as adjudication

Rejected because relevance and truth are different. Material Claims must pass independent verification.

## Failure modes

- Unknown seed: return a structured input error.
- Fewer than two usable path seeds: return a missing-link explanation.
- No match/path: successful empty/partial trace with bounds stated.
- Missing `as_of` on temporal query: use current validity and record the limitation.
- Oversized context: truncate deterministically and report omission.
- Quarantined episode in graph state: retrieval may expose the ID for audit, but downstream verification/audit must reject evidentiary use.

## Verification

Tests cover query classification, method selection, validity filtering, hop limits, causal edge filtering, deterministic reciprocal-rank fusion, trace persistence/idempotency, gap scanning, bounded serialization, token estimates, and empty results.

## Consequences

Queries become reproducible and inspectable, and context remains bounded. The local method is deliberately conservative: it can miss semantic paraphrases that lexical/graph structure does not connect. That limitation must be reported rather than hidden behind the word “hybrid.”

