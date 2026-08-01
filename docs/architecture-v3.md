# Evidence Research v3 Architecture

## Status

Implemented architecture contract for engine `v3`. The original target-lock phase is complete; this document now describes the shipped local runtime and its release boundaries. A behavior change that affects durability, evidence semantics, trust boundaries, topology selection, or release gates requires an ADR, tests, and benchmark/security impact analysis.

## Objective

Produce resumable, provider-independent research in which a task graph executes bounded work and a temporal evidence graph preserves, challenges, retrieves, and verifies the resulting evidence. Material report Claims must trace to adjudicated edges and immutable source episodes.

## Non-goals

- General autonomous web action or external account mutation.
- Treating a graph, retrieval score, or language-model judgment as truth by itself.
- Mandatory cloud services, vector databases, or a specific model provider.
- Reconstructing canonical state from Markdown, JSONL, or chat.
- Hiding contradiction, legacy provenance limits, or failed gates to improve narrative quality.

## Component map

| Concern | Implementation | Canonical outputs |
|---|---|---|
| Capabilities | `runtime/capabilities.py` | persisted capability decision in run metadata/events |
| Event and execution state | `runtime/event_store.py`, `runtime/executor.py` | events, runs, tasks, attempts, dependencies, artifacts, checkpoints, interrupts, approvals |
| Topology and DAG | `taskgraph/selector.py`, `taskgraph/compiler.py` | architecture decision and registered artifact-flow graph |
| Ontology | `ontology/registry.py` | immutable ontology versions and activation state |
| Acquisition security | `acquisition/security.py`, `acquisition/source_episodes.py` | source episodes, findings, byte hashes, version chain |
| Temporal graph | `graph/temporal_graph.py` | typed nodes and bitemporal edges |
| Entity fusion | `graph/fusion.py` | proposals, decisions, canonical mappings, reversals |
| Retrieval | `retrieval/query.py`, `lexical.py`, `graph_search.py`, `hybrid.py` | persisted bounded retrieval traces |
| Adjudication | `verification/evidence_chain.py` | claim decisions and issues |
| Synthesis | `synthesis/report.py` | deterministic report and marker-audit result |
| Completion | `audit/run_audit.py` | deterministic run audit |
| Migration/release | `migration/v2_import.py`, `release/seal.py`, benchmark modules | migration record, promotion evidence, release seal |

## Canonical state and transaction model

SQLite `state.db` is canonical. Event append and projection update occur within the local runtime's state-altering operations. Idempotency keys make exact replay stable. Projections provide efficient current-state reads; events preserve an auditable change history.

`run.json` locates the database and records engine/architecture metadata. `contract.json`, `task-graph.json`, reports, audits, and JSONL are readable artifacts, not transaction state.

SQLite WAL enables local concurrency but is not a distributed consensus protocol. One run directory must not be concurrently mutated by uncoordinated hosts or copied over a live database.

## Run lifecycle

1. Validate contract and host capabilities.
2. Select the smallest suitable architecture.
3. Compile and validate the task graph.
4. Create the run and register the graph idempotently.
5. Execute persisted `READY` tasks under attempts and leases.
6. Record source episodes before evidentiary edges.
7. Activate a valid ontology and curate typed temporal graph state.
8. Retrieve bounded context and adjudicate material Claims independently.
9. Render and marker-audit the report when requested.
10. Run completion audit; call `DurableExecutor.complete` only after required gates pass.
11. For a software release, additionally pass benchmark, migration/fallback, matrix, security/fault, manifest/seal, review, and human-approval gates.

## Architecture selection

| Mode | Use when | Prohibited shortcut |
|---|---|---|
| `single` | Work is tightly coupled or sequential and benefits from shared context | Splitting merely to appear parallel |
| `diamond` | Independent branches produce artifacts for one controlled fan-in | Multiple merge writers or undeclared sibling dependencies |
| `hierarchical` | At least six branches span at least three domains with real layered depth and host capacity | Unbounded recursive delegation |
| `retrieval-only` | An existing graph can answer without new evidence acquisition | Treating retrieved context as adjudicated truth |
| `audit-only` | Existing persisted work needs independent checks | Repairing artifacts inside the same audit task |

Task dependencies must represent artifact consumption. The compiler rejects cycles, fake edges, missing producers, multi-writer artifacts, incomplete fan-in, and self-verification.

## Durability and recovery

Tasks progress through persisted states and attempts. A worker acquires a lease; successful completion registers declared artifacts and checkpoints. Retriable failure is bounded by `max_attempts`. Expired leases can be recovered, while active leases cannot be reassigned.

Successful parallel siblings remain successful if another branch fails. Ambiguous external effects require idempotency reconciliation. Open interrupts block affected work until a scoped decision is persisted.

Completed runs are immutable. New scope or corrected evidence creates a linked superseding run.

## Evidence and time model

Source bytes are immutable and content-addressed. A logical source can have multiple episodes; changed bytes create a successor episode. Risk scanning and sensitive-data classification occur at acquisition, while byte integrity is rechecked before release-quality use.

Graph edges carry validity time (`valid_from`, `valid_to`) and recording time (`recorded_at`). Historical queries can reconstruct facts valid at one time or known by another. Supersession closes an earlier validity interval and creates a successor without deleting provenance.

Contradictions are parallel evidence edges, not overwrites. Entity fusion is proposed, decided, applied, and reversible.

## Retrieval and verification

The query classifier selects from lexical, graph-neighborhood, bounded path, temporal filter, community grouping, and evidence-gap scanning. Results are deduplicated, bounded, serialized, and persisted with method/ID traces.

The local runtime does not ship vector semantic search or a release-qualified external graph adapter. Those are future extensions, not current capabilities.

Claim adjudication checks active evidence edges, source episodes, independence groups, numeric consistency, lexical signal, contradiction, and quarantine. Deterministic signals triage; they do not prove semantic entailment. Consequential or low-signal cases require separately recorded review.

## Presentation and audit boundaries

The renderer includes only `verified` and `contested` Claims and emits Claim/Edge/Episode markers. `audit_rendered_report` checks trace resolution.

`audit_run` checks execution completion, dependency integrity, verifier separation, open interrupts, material Claim adjudication, used source integrity/quarantine, and unresolved fusion reviews. It does not currently invoke the report-marker audit or release suite. Operators must run the appropriate separate gates.

## Security boundaries

All acquired content and worker/tool messages are untrusted data. Quarantined episodes cannot qualify as evidence. Sensitive excerpts are redacted in derived records, while authorized raw bytes remain immutable. Role tools and write ownership enforce least privilege at the plugin layer; deployment owners must still validate host filesystem, network, credential, and process isolation.

## Observability and reproducibility

Persist run/contract IDs, architecture rationale, events, attempts, leases, checkpoints, source hashes, ontology versions, fusion decisions, retrieval traces, adjudications, report audit, completion audit, benchmark artifacts, and release-manifest hashes. A status report must distinguish observed persisted state from inference.

## Known limitations

- SQLite is local durability, not multi-host coordination.
- Injection detection is pattern-based and cannot prove safety.
- Raw source retention may require deployment-specific privacy controls.
- The built-in verifier is not full semantic entailment.
- Community retrieval uses local graph connectivity, not learned community summaries.
- No vector retriever or external graph backend is release-qualified.
- Migrated v2 sources can remain `unverified-legacy`.
- Completion and report-marker audits are separate in the shipped CLI.

## Release gate

Promotion requires Python 3.10-3.13 verification, the fixed benchmark and v2 comparison, security/fault/replay tests, migration and fallback evidence, deterministic complete sealing, architecture/security review, and explicit human approval. Missing evidence is a failed gate, not an assumed pass.

