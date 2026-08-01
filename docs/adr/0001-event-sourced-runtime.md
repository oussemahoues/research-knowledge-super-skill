# ADR 0001: Event-sourced durable runtime

## Decision

Use SQLite WAL as the default event store. Append immutable run events before updating projections. Persist tasks, attempts, artifacts, checkpoints, interrupts, and approvals.

## Rationale

A Markdown task graph and global run state cannot provide idempotent retries, crash recovery, partial parallel recovery, replay, or human interrupts. SQLite provides transactional local durability without a mandatory service dependency.

## Consequences

- JSONL remains an export format, not the transaction boundary.
- Every state-altering operation requires an idempotency key.
- Current state can be rebuilt and audited from events.
- Optional remote runtimes must implement the same event-store interface.
