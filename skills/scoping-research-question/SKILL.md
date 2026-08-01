---
name: scoping-research-question
description: This skill should be used when a deep-research request must be defined, narrowed, operationalized, or converted into measurable questions and acceptance criteria. Also trigger when the request is volatile, consequential, ambiguous, or missing an as-of date, exclusions, evidence burden, or definition of done. Do not acquire sources, answer the research questions, or choose an execution topology.
---

# Scope the Research Question

Create the immutable research contract that the v3 runtime stores before planning. Keep methods separate from the target.

## Inputs

```json
{
  "request": "Original research request",
  "audience": "decision maker",
  "deliverable": "report",
  "as_of": "YYYY-MM-DD",
  "constraints": {},
  "known_sources": [],
  "explicit_exclusions": []
}
```

## Procedure

### 1. State the target

Write one outcome sentence naming the subject, intended use, scope, cutoff date, and deliverable. Do not treat a tool such as web search as the objective.

### 2. Create atomic questions

Assign each question a stable ID, kind, materiality, and answer form. Split questions whose parts could have different evidence or conclusions.

### 3. Define boundaries

Record included and excluded entities, geographies, jurisdictions, periods, units, currencies, languages, standards, and decision context. Do not broaden scope to match convenient sources.

### 4. Set temporal semantics

Use an ISO as-of date. Distinguish event, publication, effective, retrieval, and supersession dates. Assign volatility and a maximum acceptable source age where relevant.

### 5. Set evidence burden

For each critical question, declare acceptable authority, required source types, minimum independence groups, freshness, disconfirming-evidence requirements, and prohibited source classes.

### 6. Classify assumptions

Use `safe_default`, `needs_validation`, or `user_decision`. Never infer jurisdiction, design basis, medical condition, legal threshold, or risk tolerance.

### 7. Define measurable acceptance criteria

Every criterion must name a metric, threshold, and canonical v3 state needed to evaluate it. Use graph coverage, source-episode integrity, adjudication status, citation resolvability, or required report sections.

### 8. Set budgets

Declare bounded sources, tool calls, child agents, retries, and gap iterations. Increase evidence burden for consequence, not merely breadth.

### 9. Validate

Confirm that every critical question maps to a criterion, criteria are measurable, exclusions do not conflict with the target, and required evidence is realistically acquirable.

### 10. Persist

Return the contract to the orchestrator. The orchestrator stores its hash in the SQLite event store and writes `contract.json` only as a readable run artifact.

## Output contract

```json
{
  "schema_version": "3.0",
  "target": "...",
  "as_of": "YYYY-MM-DD",
  "scope": {"included": [], "excluded": [], "geography": [], "jurisdiction": []},
  "questions": [{"id": "q1", "text": "...", "kind": "verification", "materiality": "critical"}],
  "source_requirements": [],
  "assumptions": [],
  "acceptance_criteria": [],
  "thresholds": {},
  "budgets": {},
  "limitations": []
}
```

## Failure recovery

- Missing current-date context: use the current ISO date and mark volatility high.
- Conclusion supplied as a premise: convert it to a hypothesis and add a disconfirming question.
- Verification is impossible: require an evidence-gap or uncertainty answer instead of promising certainty.
- Scope exceeds budget: prioritize critical questions and mark supporting questions deferred.
- Required jurisdiction or design basis is absent: classify it as `user_decision` and block affected conclusions.

## Completion checklist

- [ ] Target is one immutable outcome sentence.
- [ ] Questions are atomic, typed, and materiality-ranked.
- [ ] Scope, exclusions, and temporal semantics are explicit.
- [ ] Evidence burden is claim-relative.
- [ ] Assumptions are classified.
- [ ] Acceptance criteria are measurable.
- [ ] Budgets and limitations are present.
- [ ] Contract uses schema version 3.0.
