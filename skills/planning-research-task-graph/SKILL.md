---
name: planning-research-task-graph
description: Design and validate the execution DAG for a scoped research contract, deciding which work remains sequential and which independent branches may run in parallel. Use after research scoping, when replanning a blocked run, or when diagnosing wasteful agent orchestration. Do not perform research, create unsupported dependencies, or spawn agents merely because multiple agents are available.
---

# Plan the Research Task Graph

1. Create tasks with `id`, `objective`, `consumes`, `produces`, `dependencies`, `owner`, `budget`, and `done_when`.
2. Draw an edge only when the downstream task consumes a named artifact produced by the upstream task.
3. Keep tightly sequential work in one task/context. Split by independent question, source family, jurisdiction, or adversarial perspective when outputs can be verified and merged independently.
4. Add a separate verifier for material claims; do not let an extraction worker approve its own output.
5. Assign one merge owner and one writer per artifact.
6. Add targeted gap-resolution tasks conditionally, with a maximum iteration count.
7. Validate using `python -B ${CLAUDE_PLUGIN_ROOT}/scripts/researchctl.py validate-task-graph <path>`.
8. Emit `task-graph.json` only when acyclic, fake-edge-free, and within the global agent/tool budgets.

Use the smallest graph that meets the contract.
