# Evidence Research v3 Architecture

## Status

Target-locked implementation contract. This document governs the `sota-graph-engine-v3` branch. Runtime behavior must not diverge from it without an ADR and benchmark evidence.

## Objective

Build a provider-independent research plugin whose task graph executes research and whose temporal evidence graph stores, retrieves, and verifies it. The system must be durable, resumable, ontology-first, contradiction-preserving, query-adaptive, secure against hostile source content, and benchmarked against v2.

## Planes

1. **Control plane** — architecture selection, budgets, policy, approvals, task scheduling, replay, and audit.
2. **Task graph plane** — tasks, real artifact dependencies, attempts, checkpoints, leases, interrupts, and fan-in ownership.
3. **Evidence graph plane** — ontology versions, source episodes, entities, events, claims, evidence spans, temporal validity, fusion, and adjudication.
4. **Retrieval plane** — lexical, semantic, graph-path, temporal, community, and iterative evidence-chain retrieval.
5. **Evaluation plane** — deterministic validation, calibrated model evaluation, fault injection, security tests, and v2/v3 comparison.

## Invariants

- Draw a task edge only when a downstream task consumes an upstream artifact.
- Use one canonical writer per artifact.
- Never let a worker verify its own material output.
- Persist an immutable event before projecting mutable state.
- Make every retry idempotent and bounded.
- Checkpoint every successful task.
- Preserve successful parallel siblings when another branch fails.
- Generate and validate a task-specific ontology before extraction.
- Store exact source spans and source versions for factual claims.
- Preserve contradictions, uncertainty, and temporal supersession.
- Require human approval at high-blast-radius boundaries.
- Declare completion only after all acceptance and audit gates pass.

## Canonical state

SQLite in WAL mode is the default local canonical store. JSON and JSONL are import/export and inspection formats. Optional graph backends operate behind adapters and must not change semantic contracts.

## Work packages

- WP0: architecture, schemas, and v2 baseline
- WP1: durable task runtime
- WP2: ontology compiler
- WP3: adaptive task compiler
- WP4: secure acquisition and extraction
- WP5: fusion and temporal evidence graph
- WP6: hybrid GraphRAG retrieval
- WP7: independent verification and synthesis
- WP8: plugin command and agent surface
- WP9: security, benchmarks, and fault injection
- WP10: migration, rollback, and release

## Release gate

Do not merge to `main` until Python 3.10-3.13 CI, migration, rollback, benchmark, fault-injection, and injection-red-team suites all pass and the human release gate is approved.
