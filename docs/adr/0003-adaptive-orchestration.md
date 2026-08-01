# ADR 0003: Adaptive, Bounded Orchestration

- Status: accepted and implemented
- Decision owners: execution architecture
- Affects: contract intake, topology selection, task compilation, delegation, recovery

## Context

Multi-agent execution helps when work can be decomposed into independent artifact-producing branches, but it adds coordination cost and can degrade tightly sequential tasks. A fixed swarm obscures ownership, encourages fake dependencies, expands the prompt-injection surface, and makes retries expensive.

## Decision

Select the smallest valid topology from `single`, `diamond`, `hierarchical`, `retrieval-only`, and `audit-only` using a validated `WorkProfile` and `max_agents`. Compile a real artifact-flow DAG and reject a topology that cannot express concrete input/output dependencies and one-writer ownership.

There is no swarm mode. Delegation depth, branches, attempts, sources, tool calls, leases, hop limits, and parallel workers are bounded.

## Selection contract

| Mode | Selection intent | Required ownership |
|---|---|---|
| `single` | Shared context or sequential coupling dominates | One execution context; separate verifier when material |
| `diamond` | Independent branches converge once | One writer per branch artifact and one merge owner |
| `hierarchical` | Broad multi-domain work has real layered dependencies | Registered parent/child artifacts; bounded depth; independent verification |
| `retrieval-only` | Existing graph is sufficient; no acquisition required | Retrieval trace writer; verifier for publishable conclusions |
| `audit-only` | Existing run/release evidence needs independent evaluation | Auditor separate from all audited writers |

The current selector reserves hierarchical mode for broad work meeting branch/domain/depth thresholds and host capacity. Operators must inspect returned reasons/warnings rather than infer a topology from the label alone.

## DAG invariants

- Every dependency is justified by an artifact intersection.
- Every required artifact has exactly one canonical writer.
- Fan-in consumes all required branch artifacts.
- Verification ownership differs from the material producer.
- Children are registered before execution and cannot create undeclared descendants.
- Parallel tasks do not require hidden shared mutable context.

## Delegation envelope

Each handoff identifies run/task/attempt, objective, input artifact IDs, constraints, budget, expected output schema, and checkpoint. Missing identifiers or output contracts produce `needs_input`; workers never invent them.

## Alternatives considered

### Always single-agent

Rejected because independent branches and separate verification can benefit from bounded parallelism.

### Always multi-agent or swarm

Rejected because coordination overhead, context fragmentation, and security risk dominate for coupled work.

### Dependency labels without artifact contracts

Rejected because they permit fake DAGs that serialize or parallelize work without a testable data dependency.

## Failure and recovery

- Invalid profile or graph: fail before dispatch.
- Worker timeout: inspect lease and attempt; recover only after expiry.
- One branch fails: preserve successful siblings and block only consumers that lack required artifacts.
- Fan-in conflict: return a conflict/gap artifact; the merge owner cannot erase it.
- Open approval interrupt: block affected tasks until a scoped decision is persisted.
- Budget exhausted: stop or narrow explicitly; do not silently add workers or calls.

## Verification

Tests cover selector boundaries, profile validation, DAG cycles, fake edges, multiple writers, incomplete fan-in, self-verification, bounded attempts, stale leases, checkpoint replay, and successful-sibling preservation. Benchmarks compare v3 with protected v2 metrics so coordination complexity must earn its cost.

## Consequences

The architecture avoids unnecessary delegation and makes parallelism auditable. It requires explicit artifact schemas and can choose a conservative topology when profile data is incomplete. That is preferable to unbounded or cosmetic parallelism.

