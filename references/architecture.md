# Architecture

## Control plane

The command and orchestrator manage the immutable target, run state, task graph, budgets, and completion gate. They never substitute orchestration metadata for evidence.

## Data plane

The data plane is an append-only registry of sources and graph records. Markdown reports are disposable views; `sources.jsonl`, `evidence-graph.jsonl`, and `decisions.jsonl` are canonical.

## Task graph

Each task declares `consumes` and `produces`. A dependency is legal only if at least one artifact produced by the predecessor is consumed by the successor. This makes fake dependencies mechanically detectable. DAG levels identify safe parallel work. Sequential chains remain with one context unless a distinct verifier is required.

## Evidence graph

Nodes and edges are separate JSONL records. Stable IDs derive from normalized semantic identity, not insertion order. Merge decisions are logged and reversible. Contradictions remain first-class edges.

## Write ownership

| Artifact | Owner |
|---|---|
| run.json | research-orchestrator |
| task-graph.json | research-orchestrator |
| sources.jsonl | evidence-curator |
| evidence-graph.jsonl | evidence-curator |
| decisions.jsonl | research-orchestrator |
| report.md | synthesis-editor |
| audit.json | claim-verifier |

No two agents write the same artifact.
