---
name: planning-research-task-graph
description: This skill should be used when a scoped investigation must be decomposed, replanned, resumed, or validated as an executable task graph. Also trigger for blocked runs, wasteful multi-agent designs, fake dependencies, artifact ownership conflicts, or topology selection. Do not acquire evidence, answer research questions, or add agents merely to increase parallelism.
---

# Plan the Research Task Graph

Compile the smallest artifact-backed DAG that satisfies the research contract and can resume safely in the v3 event store.

## Inputs

```json
{
  "run_id": "run:...",
  "research_contract": {},
  "available_capabilities": ["read-local", "web-search"],
  "budgets": {"max_tool_calls": 80, "max_sources": 40, "max_child_agents": 5},
  "completed_artifacts": {},
  "existing_tasks": []
}
```

## Procedure

### 1. Profile the work

Measure question count, independent branches, dependency depth, domain count, temporal requirements, and audit-only or retrieval-only intent.

### 2. Select topology

Choose `single`, `diamond`, `hierarchical`, `retrieval-only`, or `audit-only`. Reject swarm topology and unnecessary parallelism.

### 3. Map questions to artifacts

Start with required artifacts and decisions, not agent names. Every task declares `consumes`, `produces`, owner, bounded attempts, failure policy, and testable `done_when`.

### 4. Draw real dependencies

Create an edge only when a downstream task consumes an upstream artifact. Chronology, shared ownership, or desired serialization are not valid graph edges.

### 5. Assign ownership

Use one canonical writer per artifact. Source scouts return candidates; curators write graph state; verifiers write adjudications; synthesis renders reports; auditors write release findings.

### 6. Preserve verifier separation

A worker must not verify or approve its own material output. The compiler must reject self-verification ownership.

### 7. Bound retries and loops

Use bounded attempts and conditional gap tasks. Never encode an unbounded cycle. Preserve successful independent branches after sibling failure.

### 8. Add leases and recovery

Declare lease duration, renewal policy, stale-lease recovery, and idempotency keys. Recovered tasks resume without duplicating successful artifacts.

### 9. Support invalidation

Reuse completed tasks only when input hashes and outputs remain valid. Invalidate descendants of changed inputs while preserving unrelated branches.

### 10. Register and validate

Register the graph through `DurableExecutor.register_graph`. Reject cycles, fake edges, duplicate writers, unbounded attempts, invalid fan-in, and missing owners before execution.

## Output contract

```json
{
  "schema_version": "3.0",
  "run_id": "run:...",
  "architecture": "diamond",
  "max_parallel": 4,
  "tasks": [
    {
      "id": "acquire-q1",
      "task_type": "acquisition",
      "owner": "source-scout",
      "consumes": ["contract:q1"],
      "produces": ["candidate-sources:q1"],
      "dependencies": [],
      "max_attempts": 2,
      "failure_policy": "continue-with-gap",
      "done_when": "accepted source episode or explicit gap exists"
    }
  ],
  "artifact_owners": {},
  "resume": {"reusable_tasks": [], "invalidated_tasks": []}
}
```

## Failure recovery

- Duplicate output writers: redesign outputs or appoint one owner.
- Undeclared input: add the consumed artifact and real dependency before execution.
- Excessive topology: reduce agents or batch deterministic branches.
- Changed upstream input: invalidate affected descendants only.
- Verifier requires more evidence: emit a bounded acquisition gap task through the orchestrator.

## Completion checklist

- [ ] Topology matches actual dependency structure.
- [ ] Every task has a testable completion condition.
- [ ] Every edge represents artifact flow.
- [ ] Writers are unique.
- [ ] Verification ownership is independent.
- [ ] Retries, leases, and gap loops are bounded.
- [ ] Resume and invalidation rules are explicit.
- [ ] Runtime graph validation passes.
