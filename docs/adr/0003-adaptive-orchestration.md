# ADR 0003: Adaptive orchestration

## Decision

Select among `single`, `diamond`, `hierarchical`, `audit-only`, and `retrieval-only` execution. Do not provide a swarm mode.

## Selection principles

- Keep tightly sequential work in one context.
- Parallelize only independent artifact branches.
- Require a separate verifier and one merge owner for material fan-out.
- Bound delegation depth, task attempts, gap rounds, sources, and tool calls.
- Route consequential boundaries through persisted human interrupts.
