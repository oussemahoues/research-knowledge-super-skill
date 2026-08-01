---
name: scoping-research-question
description: This skill should be used when the user asks to define, narrow, frame, or operationalize a research question, or when a deep-research request is broad, ambiguous, volatile, or missing measurable completion criteria. It produces an executable research contract with atomic questions, exclusions, source requirements, assumptions, thresholds, and a definition of done. Do not acquire sources, answer the question, or design the agent topology.
---

# Scope the Research Question

Convert a natural-language request into a contract that another agent can execute without guessing the target. Success means each acceptance criterion can be evaluated against named artifacts or metrics.

## Inputs

```json
{
  "request": "Original user request",
  "audience": "optional",
  "deliverable": "optional",
  "as_of": "YYYY-MM-DD or omitted",
  "geography": ["optional"],
  "jurisdiction": ["optional"],
  "known_sources": ["optional"],
  "constraints": {},
  "explicit_exclusions": ["optional"]
}
```

## Load before starting

- `references/source-policy.md`
- `references/evaluation.md`
- `schemas/research-run.schema.json`

## Procedure

### 1. Extract the immutable target

Write one outcome sentence using this structure:

> Determine / compare / verify / explain **X**, for **audience/use**, within **scope**, as of **date**, delivered as **artifact**.

Separate the target from proposed methods. “Search the web” is not a target; “determine which supplier meets specification X” is.

### 2. Decompose into atomic research questions

Create one question per independently answerable proposition. Assign:

- `id`: stable within the run, such as `q1`
- `text`: one focused question
- `kind`: `descriptive`, `comparative`, `causal`, `predictive`, `normative`, or `verification`
- `materiality`: `critical`, `major`, or `supporting`
- `answer_form`: fact, table row, ranked option, causal explanation, or uncertainty statement

Split compound questions joined by “and” when either part could have a different evidence base or conclusion.

### 3. Define scope boundaries

Record:

- included products, entities, populations, standards, periods, and geographies
- excluded adjacent topics
- units, currencies, language, and terminology conventions
- audience and decision context
- required deliverable and file format

Do not silently broaden the scope to whatever sources are easiest to find.

### 4. Set temporal semantics

- Use an explicit ISO date for `as_of`.
- Classify volatility:
  - `low`: stable historical or mathematical facts
  - `medium`: technical guidance, market structure, organizational practices
  - `high`: prices, laws, schedules, product specifications, office holders, live metrics
- For high-volatility questions, require current retrieval and record a maximum acceptable source age.
- Distinguish event date, publication date, effective date, and access date when they may differ.

### 5. Classify consequence and evidence burden

Set consequence to `low`, `moderate`, `high`, or `critical`.

| Consequence | Minimum evidence posture |
|---|---|
| Low | One directly relevant credible source may suffice |
| Moderate | Prefer one authoritative source plus independent corroboration |
| High | Current primary authority plus independent challenge source |
| Critical | Primary authority, explicit uncertainty, domain-review warning, no unsupported recommendation |

Authority is claim-relative. A vendor is primary for its own specification but not independent evidence of comparative superiority.

### 6. Declare source constraints

For each critical question, define:

- acceptable authority tiers
- required source types
- excluded source types
- freshness limit
- minimum independence groups
- whether user-provided sources are mandatory, optional, or context only

Use `references/source-policy.md`; do not replace source requirements with a raw source-count target.

### 7. State assumptions

List every assumption that materially affects search or interpretation. Mark each as:

- `safe_default`: proceed unless contradicted
- `needs_validation`: create a research question or task
- `user_decision`: cannot be inferred without changing the target

Use reasonable defaults for presentation, file naming, and non-material formatting. Do not infer jurisdiction, compliance threshold, medical condition, financial risk tolerance, or engineering design basis.

### 8. Define measurable acceptance criteria

Each criterion must include:

```json
{
  "id": "a1",
  "criterion": "Every critical comparison row is supported by a current primary source",
  "measure": "critical_rows_primary_source_coverage == 1.0",
  "required_artifacts": ["sources.jsonl", "evidence-graph.jsonl", "report.md"],
  "threshold": 1.0
}
```

Good criteria test coverage, source authority, citation resolvability, required sections, treatment of uncertainty, or a concrete decision matrix. Avoid “comprehensive,” “well researched,” and “high quality.”

### 9. Set operational thresholds and budgets

Define defaults appropriate to the request:

```json
{
  "thresholds": {
    "claim_evidence_coverage": 1.0,
    "citation_resolvability": 1.0,
    "unsupported_claims": 0
  },
  "budgets": {
    "max_sources": 40,
    "max_tool_calls": 80,
    "max_child_agents": 5,
    "max_gap_iterations": 2
  }
}
```

Increase evidence burden for consequence, not merely for topic breadth.

### 10. Validate the contract

Before emitting:

- verify every critical question maps to at least one acceptance criterion
- verify every acceptance criterion has a measurable expression
- verify exclusions do not conflict with the target
- verify the as-of date and volatility rules are compatible
- verify required source types are realistically acquirable; otherwise record a limitation

## Output contract

Emit a JSON object suitable for inclusion in `run.json`:

```json
{
  "schema_version": "2.0",
  "target": "...",
  "audience": "...",
  "deliverable": {"type": "report", "format": "markdown", "path": "report.md"},
  "as_of": "YYYY-MM-DD",
  "scope": {"included": [], "excluded": [], "geography": [], "jurisdiction": []},
  "questions": [
    {"id": "q1", "text": "...", "kind": "verification", "materiality": "critical", "answer_form": "fact"}
  ],
  "source_requirements": [],
  "assumptions": [{"text": "...", "class": "safe_default"}],
  "acceptance_criteria": [],
  "thresholds": {},
  "budgets": {},
  "limitations": []
}
```

## Edge cases

- **The request contains several deliverables:** choose one canonical research run and list secondary renderings; do not create separate evidence bases unless scopes differ materially.
- **The user gives a conclusion to prove:** restate it as a hypothesis and include a disconfirming question.
- **The target is impossible to verify:** change the answer form to an uncertainty or evidence-gap statement; do not promise certainty.
- **No date is supplied for a current topic:** use the current ISO date and mark volatility high.
- **User sources conflict with authoritative sources:** preserve both as inputs; do not grant user-provided material automatic authority.
- **Scope is too broad for the budget:** prioritize critical questions and mark supporting questions deferred rather than weakening all questions silently.
- **A required jurisdiction or design basis is missing:** classify it as `user_decision`; do not invent it.

## Completion checklist

- [ ] One immutable outcome sentence exists.
- [ ] Questions are atomic and typed.
- [ ] Scope and exclusions are explicit.
- [ ] Temporal and consequence classes are assigned.
- [ ] Source constraints are claim-relative.
- [ ] Assumptions are classified.
- [ ] Acceptance criteria are measurable.
- [ ] Thresholds and budgets are present.
- [ ] Output conforms to the run schema fields.
