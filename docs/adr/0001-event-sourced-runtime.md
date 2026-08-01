# ADR 0001: SQLite Event Store and Durable Executor

- Status: accepted and implemented
- Decision owners: runtime architecture
- Affects: execution, recovery, audit, migration, release

## Context

A Markdown checklist or mutable JSON run file cannot safely represent concurrent branches, bounded retries, worker leases, partial recovery, human interrupts, or idempotent replay. Reconstructing progress from chat or output files creates duplicate work and false completion.

The plugin must remain locally deployable without requiring a service while preserving an auditable order of state changes.

## Decision

Use SQLite in WAL mode as the canonical local store. Every state-altering runtime operation appends an immutable run event with a stable idempotency key and updates query projections for runs, tasks, attempts, dependencies, artifacts, checkpoints, interrupts, approvals, source episodes, graph state, retrieval traces, and adjudications.

Use `DurableExecutor` as the only task-state transition authority. Workers operate under persisted attempts and leases; successful tasks register artifacts and checkpoints. Completion is decided through executor/audit gates, never by editing `run.json`.

## Invariants

- One `run_id` identifies one canonical database state.
- Identical idempotency keys cannot create duplicate logical events.
- A task runs only when persisted state is `READY` and its dependencies succeeded.
- A worker cannot take another worker's active lease.
- Recovery acts only on expired leases and respects `max_attempts`.
- Successful siblings survive failure in another branch.
- Artifact success requires a persisted successful attempt, not just file existence.
- Completed runs are immutable and superseded rather than edited.

## Transaction boundary

SQLite transactions protect local event/projection changes. Side effects outside the database are not automatically atomic with the event store. External operations therefore require stable idempotency identifiers and reconciliation before retry after an ambiguous outcome.

WAL improves local concurrency but does not make a run safe for uncoordinated multi-host writers or network-filesystem copying.

## Alternatives considered

### Markdown or JSON as canonical state

Rejected because it lacks transaction isolation, durable leases, indexed reconciliation, and reliable replay.

### JSONL event log without projections

Rejected as the primary store because atomic append plus multi-record invariants and efficient current-state queries are harder to guarantee portably. JSONL remains an export format.

### Mandatory hosted database or workflow service

Rejected for the default path because it breaks local portability and introduces operational dependencies. A remote adapter may be added only if it preserves the same semantics.

## Failure modes and handling

- Process crash during task work: lease expires; recover and retry within bounds.
- Ambiguous external write: inspect the target by idempotency key before retry.
- Database missing/corrupt: block; do not create a replacement in the same run directory.
- Active lease appears stuck: wait or investigate; do not force recovery as normal operation.
- Event/projection inconsistency: fail audit and repair through a tested migration, not manual SQL.
- Disk full or fsync failure: report terminal storage failure and preserve available evidence.

## Verification

Tests must cover duplicate event keys, graph registration replay, attempt limits, lease renewal/expiry, stale recovery, checkpoint retrieval, interrupt approval/rejection, successful-sibling preservation, and completion refusal with open gates. Migration and release tests must exercise supported Python versions.

## Consequences

The runtime gains local durability, resumability, and reproducible inspection. It also takes on schema migration, SQLite locking, filesystem integrity, backup, and deployment-security responsibilities. Optional runtimes must prove semantic equivalence rather than merely accept the same commands.

