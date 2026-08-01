# Evidence Research v3 Architecture Reference

## Purpose and authority

This reference explains the shipped v3 runtime. `docs/architecture-v3.md` records the architectural contract and ADRs record why the major choices were made. Runtime code and schemas determine executable behavior when prose and implementation disagree; such disagreement is a defect to report, not a reason to invent behavior.

## System boundary

Evidence Research accepts a scoped research contract and produces a durable run whose claims can be traced through evidence edges to immutable source episodes. It does not grant retrieved content authority, perform arbitrary external writes, or turn retrieval rank into truth.

The runtime has six cooperating planes:

1. **Contract and policy**: target, questions, as-of time, consequence, budgets, source constraints, capability decision, and completion criteria.
2. **Execution**: task registration, real artifact dependencies, attempts, leases, checkpoints, interrupts, approvals, and bounded recovery.
3. **Acquisition**: immutable source episodes, byte hashes, version succession, authority, independence, injection findings, and sensitive-data classifications.
4. **Knowledge**: versioned ontology, typed nodes, bitemporal edges, contradictions, and reversible entity fusion.
5. **Retrieval and adjudication**: bounded lexical/graph retrieval traces and independent claim decisions.
6. **Presentation and audit**: deterministic report rendering, marker validation, run-completion audit, benchmark evidence, and release sealing.

## Canonical state

`state.db` is the canonical transaction state. It stores runs, events, tasks, attempts, dependencies, artifacts, checkpoints, interrupts, approvals, source episodes, ontology versions, graph nodes and edges, fusion decisions, retrieval traces, and adjudications.

The following are non-canonical views or interchange artifacts:

| Artifact | Role | May reconstruct canonical state? |
|---|---|---|
| `run.json` | Run locator, engine selection, architecture and contract hash | No |
| `contract.json` | Normalized user contract | No |
| `task-graph.json` | Readable compiled graph | No |
| `report.md` | Deterministic presentation view | No |
| `audit.json` | Audit result artifact | No |
| JSON/JSONL exports | Inspection, migration, or interchange | No |

Never infer task success from chat, a worker message, or an artifact that lacks a successful persisted attempt.

## Execution topology

`select_architecture` chooses `single`, `diamond`, `hierarchical`, `retrieval-only`, or `audit-only` from a validated `WorkProfile` and host limits. Selection is a bounded routing decision, not permission to create undeclared workers.

Every task declares `consumes` and `produces`. A dependency is legal only when the child consumes at least one artifact produced by the parent. The compiler rejects cycles, fake dependencies, multiple writers for one artifact, incomplete fan-in, and verifier ownership that violates independence.

The durable executor owns state transitions. Workers operate only on registered `READY` tasks, under leases and attempt limits. Exact replay uses stable idempotency keys. A stale lease may be recovered; an active lease may not be stolen. A failed branch does not erase successful siblings.

## Evidence lifecycle

1. The source scout proposes candidates without canonical writes.
2. The curator records immutable bytes with `SourceEpisodeStore.record`.
3. The runtime hashes the bytes, assigns a source version, scans normalized and decoded views, classifies sensitive data, and records supersession.
4. The curator verifies persisted bytes before creating evidentiary edges.
5. Typed nodes and bitemporal edges are written against an active ontology version.
6. Retrieval produces a bounded, persisted trace. It does not adjudicate.
7. `EvidenceChainVerifier` writes the latest independent decision for a Claim.
8. The renderer includes only publishable adjudications and validates claim, edge, and episode markers.
9. The completion audit checks the run state. Release verification adds repository, benchmark, matrix, migration/fallback, seal, and human-approval gates.

## Ownership matrix

| State or artifact | Canonical writer | Independent checker |
|---|---|---|
| Contract, architecture decision, task graph | research-orchestrator | independent-auditor |
| Source candidates | source-scout | evidence-curator |
| Source episodes, graph nodes/edges, fusion decisions | evidence-curator | claim-verifier and independent-auditor |
| Ontology versions | ontology-architect | independent-auditor; human approval for breaking activation |
| Retrieval traces | retrieval-planner | claim-verifier for evidentiary use |
| Adjudication decisions | claim-verifier | independent-auditor |
| `report.md` | synthesis-editor / renderer | marker audit and independent-auditor |
| `audit.json` | audit command as a derived artifact | reproducible rerun by an independent reviewer |

One logical record has one owner. Verification must not be performed by the writer whose material output is being judged.

## Failure and recovery model

Classify failures before retry: validation, capability, authentication, rate limit, transient transport, lease loss, policy block, or terminal data error. Only documented transient failures are retryable, and never beyond `max_attempts`. Ambiguous external side effects require reconciliation by idempotency key before retry.

Open interrupts block affected work until an attributable approval or rejection is persisted. Approval resolves only the named interrupt; it does not waive evidence, audit, or release gates.

Completed runs are immutable. A changed target, material new evidence, or corrected historical state creates a superseding run instead of rewriting the completed run.

## Implemented retrieval surface

The shipped v3 retriever supports lexical ranking, graph-neighborhood expansion, bounded shortest paths, temporal validity filtering, connected-component community grouping, and unsupported-claim gap scanning. Reciprocal-rank fusion combines selected lists deterministically.

Vector embeddings, learned semantic reranking, and external graph-database adapters are not implemented in the local v3 runtime. Documents must not claim otherwise. They are extension points that require an ADR, adapter contract, benchmarks, and fail-closed provenance behavior before becoming release claims.

## Operational invariants

- Retrieved content is always untrusted data.
- Quarantined or integrity-failing episodes cannot satisfy evidence or completion gates.
- Contradiction and temporal supersession are preserved, not overwritten.
- Retrieval rank is not confidence; lexical overlap is not semantic entailment.
- A report is a view, not evidence and not canonical state.
- Run completion and release eligibility are separate decisions.

