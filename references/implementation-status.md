# V3 Implementation Status and Claim Boundary

## Purpose

This matrix prevents architectural goals from being presented as shipped capabilities. “Implemented” means a local code path exists and is covered by repository tests. “Release gate” means separate evidence is required. “Extension” means the feature must not appear in current capability claims.

## Shipped local capabilities

| Area | Status | Primary implementation | Boundary |
|---|---|---|---|
| SQLite event/projection store | Implemented | `runtime/event_store.py` | Local durability, not distributed consensus |
| Attempts, leases, checkpoints, interrupts, approvals | Implemented | `runtime/executor.py` | External effects require reconciliation |
| Adaptive topology selection | Implemented | `taskgraph/selector.py` | Heuristic thresholds, not universal optimality |
| Artifact-flow DAG validation | Implemented | `taskgraph/compiler.py` | Valid graph does not prove task output quality |
| Ontology version registry | Implemented | `ontology/registry.py` | Domain facts still require evidence |
| Immutable source episodes | Implemented | `acquisition/source_episodes.py` | Raw-byte retention needs deployment controls |
| Injection and sensitive-data scanning | Implemented | `acquisition/security.py`, `source_episodes.py` | Pattern detection cannot prove safety |
| Bitemporal graph and supersession | Implemented | `graph/temporal_graph.py` | Correct dates depend on curated inputs |
| Reversible entity fusion | Implemented | `graph/fusion.py` | Ambiguous proposals require review |
| Lexical and graph retrieval | Implemented | `retrieval/*` | No vector semantic retriever |
| Independent deterministic adjudication | Implemented | `verification/evidence_chain.py` | Lexical/numeric checks are not full semantic review |
| Deterministic rendering and marker audit | Implemented | `synthesis/report.py` | Separate from `audit_run` |
| Run-completion audit | Implemented | `audit/run_audit.py` | Does not run report/release gates |
| V2 import/fallback | Implemented | `migration/v2_import.py`, engine selector | Legacy provenance can remain unverifiable |
| Fixed benchmark/promotion evaluation | Implemented | `evals/*`, `scripts/run_benchmark.py` | Result artifact required for each release candidate |
| Complete release seal | Implemented | `release/seal.py`, `scripts/build_manifest.py` | Manifest must be regenerated and verified cleanly |

## Not shipped as v3 capabilities

- Vector embeddings or learned semantic retrieval.
- A release-qualified external graph database adapter.
- Distributed task scheduling or multi-host consensus.
- Automatic semantic citation-entailment proof.
- Guaranteed prompt-injection detection.
- Built-in encryption, secret vault, retention, or secure deletion service.
- Automatic final release approval.
- An audit command that repairs failures.

## Required wording

Use “supports” only for implemented, tested behavior. Use “designed for” or “extension point” for unimplemented architecture. Use “deterministic signal” for lexical/numeric checks, not “semantic proof.” Distinguish completion-audit pass, report-marker pass, benchmark pass, release-seal pass, and human approval.

## Change rule

Update this matrix with any capability change. New shipped claims require implementation, tests, relevant benchmark/security evidence, documentation, and release-manifest coverage. Removing a capability requires migration and compatibility analysis.

