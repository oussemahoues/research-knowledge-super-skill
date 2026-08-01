---
name: planning-research-task-graph
description: This skill should be used when the user or orchestrator asks to plan a deep-research workflow, decompose a scoped investigation, repair a blocked run, validate a task DAG, or reduce wasteful multi-agent orchestration. It creates the smallest executable graph whose edges represent real artifact dependencies, assigns bounded owners and budgets, and defines machine-checkable completion conditions. Do not perform research, acquire sources, or create agents merely to increase parallelism.
---

# Plan the Research Task Graph

Turn a validated research contract into an execution DAG. Success means the graph is acyclic, fake-edge-free, within budget, and explicit enough that tasks can be resumed or invalidated by artifact hash.

## Inputs

```json
{
  "run_id": "...",
  "research_contract": {},
  "available_capabilities": ["web-search", "connected-files", "scholarly-search"],
  "budgets": {
    "max_tool_calls": 80,
    "max_sources": 40,
    "max_child_agents": 5,
    "max_parallel": 4,
    "max_gap_iterations": 2
  },
  "existing_graph": "optional path for replanning",
  "completed_artifacts": "optional hash map for resume"
}
```

## Load before starting

- `references/architecture.md`
- `references/evaluation.md`
- `schemas/task-graph.schema.json`
- `lib/task_graph.py`

## Task contract

Every task must contain:

```json
{
  "id": "acquire-q1-primary",
  "objective": "Acquire authoritative current evidence for q1",
  "consumes": ["run.json#questions/q1"],
  "produces": ["candidate-sources/q1-primary.json"],
  "dependencies": ["scope"],
  "owner": "source-scout",
  "budget": {"tool_calls": 12, "sources": 8, "child_agents": 0},
  "done_when": "At least one admissible tier-A source or an explicit primary-source gap is returned",
  "failure_policy": "block|continue-with-gap|retry-once",
  "input_hashes": {},
  "output_paths": ["candidate-sources/q1-primary.json"]
}
```

`done_when` must be testable from the produced artifact. Do not use “research completed” or “enough sources found.”

## Procedure

### 1. Map contract questions to required artifacts

For each research question, identify the minimal artifacts required to satisfy its acceptance criteria. Typical artifact classes:

- scoped question/criteria
- candidate source set
- accepted source records
- extracted evidence batch
- resolution decisions
- adjudication decisions
- report section or decision matrix
- audit verdict

Do not start from an agent list. Start from artifacts.

### 2. Create the sequential backbone

The default backbone is:

1. scope contract
2. plan graph
3. acquire sources
4. extract evidence
5. resolve identities
6. adjudicate claims
7. synthesize report
8. audit run

Collapse stages when no distinct artifact or independent verification boundary exists. Keep a separate verifier for material claims even when the rest remains sequential.

### 3. Identify legitimate parallel branches

Parallelize only when branches:

- consume the same stable upstream artifact or independent inputs
- produce different artifacts
- do not write the same canonical file
- can fail independently
- have a defined merge owner

Good split axes include independent research questions, jurisdictions, source families, entities, or adversarial perspectives. Poor split axes include “agent A searches” and “agent B also searches” without separate evidence needs.

### 4. Draw only data dependencies

Create edge `A -> B` only when `B.consumes` intersects `A.produces`.

Invalid reasons for an edge:

- preferred chronological order without data flow
- desire to limit concurrency
- the same agent owns both tasks
- vague relationship such as “B follows A”

Use explicit resource locks or budgets for concurrency control, not fake graph edges.

### 5. Assign ownership

Enforce one writer per artifact:

| Artifact | Owner |
|---|---|
| `run.json` | research-orchestrator |
| `task-graph.json` | research-orchestrator |
| candidate source files | source-scout |
| `sources.jsonl` | evidence-curator |
| `evidence-graph.jsonl` | evidence-curator |
| `decisions.jsonl` | research-orchestrator |
| `report.md` | synthesis-editor |
| `audit.json` | claim-verifier |

Workers may return records to the owner; they may not append directly to another owner's file.

### 6. Allocate bounded budgets

Allocate from the global budget; do not duplicate the full budget on every task. Reserve capacity for verification and one authorized gap loop before spending it on broad discovery.

For each task, set:

- maximum tool calls
- maximum accepted sources
- maximum child agents, usually zero for workers
- timeout or retry policy when supported
- maximum output size when large documents are possible

The sum of task ceilings may exceed the global ceiling only when mutually exclusive conditional branches are clearly marked.

### 7. Add verification and gap loops

- Create a verifier task that consumes extracted claim/evidence records and produces adjudication decisions.
- Add conditional gap tasks only for `critical` or `major` claims where new evidence could change the conclusion.
- Express the loop as a bounded conditional transition, not a cycle in the DAG.
- Set `max_gap_iterations` and a terminal status of `unknown` or `contested` when exhausted.

### 8. Define merge behavior

For every fan-in:

- name one merge owner
- define the expected child output schema
- define deduplication keys
- define conflict behavior
- define which branch failures block the merge

Do not ask the synthesizer to infer how arbitrary worker prose should be combined.

### 9. Support resume and invalidation

For an existing run:

1. Read each completed task's input and output hashes.
2. Mark a task reusable only when all declared inputs are unchanged and outputs validate.
3. Invalidate descendants of a changed task.
4. Preserve completed independent branches.
5. Never repeat a costly task merely because the parent session restarted.

### 10. Validate and emit

Write `task-graph.json`, then run:

```bash
python -B ${CLAUDE_PLUGIN_ROOT}/scripts/researchctl.py validate-task-graph \
  <run>/task-graph.json
```

Correct every cycle, missing dependency, fake edge, duplicate output writer, and budget violation before execution.

## Output contract

```json
{
  "schema_version": "2.0",
  "run_id": "...",
  "merge_owner": "research-orchestrator",
  "max_parallel": 4,
  "budgets": {},
  "tasks": [],
  "conditional_tasks": [
    {
      "when": "material_gap_exists && gap_iterations < max_gap_iterations",
      "task_template": "acquire-gap-{claim_id}"
    }
  ],
  "artifact_owners": {},
  "resume": {"reusable_tasks": [], "invalidated_tasks": []}
}
```

## Edge cases

- **One question and one source:** keep a small sequential graph; do not manufacture parallel branches.
- **Ten independent entities:** create one bounded branch per entity only if the global child-agent limit allows it; otherwise batch entities deterministically.
- **Two tasks produce the same file:** redesign outputs or choose one owner; never rely on append timing.
- **A worker needs data not declared in `consumes`:** add the artifact and a real dependency before execution.
- **The verifier needs new evidence:** emit a gap task through the orchestrator; the verifier does not browse opportunistically.
- **A graph would exceed budgets:** prioritize critical questions and defer supporting tasks explicitly.
- **A replanned graph changes completed artifacts:** create superseding outputs and invalidate affected descendants.

## Completion checklist

- [ ] Every task has one objective and a testable `done_when`.
- [ ] Every edge has a real producer/consumer artifact intersection.
- [ ] Graph is acyclic.
- [ ] Parallel branches have separate write targets.
- [ ] One merge owner is named.
- [ ] Verification is independent from extraction.
- [ ] Gap loops are conditional and bounded.
- [ ] Budgets fit the global contract.
- [ ] Resume hashes and invalidation rules are represented.
- [ ] Runtime validation passes.
