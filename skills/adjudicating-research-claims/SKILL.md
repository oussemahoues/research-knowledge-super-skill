---
name: adjudicating-research-claims
description: This skill should be used when candidate claims must be independently verified, challenged, rejected, superseded, or left unknown, including citation checking, disputed conclusions, high-consequence findings, and gap analysis. It evaluates exact evidence spans for entailment, scope, authority, freshness, independence, contradiction, and methodological quality, then records a reasoned terminal status. Do not trust extractor confidence, source titles, citation count, or absence of contradiction as proof.
---

# Adjudicate Research Claims

Evaluate material claims in a context separate from extraction. Success means every material claim has a justified terminal status and every remaining uncertainty is represented as a research gap rather than hidden in prose.

## Inputs

```json
{
  "run_id": "...",
  "task_id": "...",
  "claim_ids": ["claim:..."],
  "graph_path": "<run>/evidence-graph.jsonl",
  "sources_path": "<run>/sources.jsonl",
  "research_contract": "<run>/run.json",
  "gap_iteration": 0,
  "max_gap_iterations": 2
}
```

## Load before starting

- `references/evidence-ontology.md`
- `references/source-policy.md`
- `references/evaluation.md`
- `lib/research_graph.py`

## Procedure

### 1. Reconstruct each claim packet

Load:

- exact atomic claim text and kind
- scope, population, time, geography, condition, metric, and modality
- all supporting, contradicting, and qualifying spans
- source records and independence groups
- premise claims for calculations/inferences
- acceptance criterion and materiality

Reject packets that contain summaries without exact spans.

### 2. Test semantic entailment

For each evidence edge, ask:

- Does the span assert or validly imply the same proposition?
- Are subject, population, metric, units, timeframe, geography, and conditions aligned?
- Is possibility being overstated as certainty?
- Is correlation being presented as causation?
- Is a subgroup result generalized?
- Is a quotation being represented as established fact?

Downgrade or remove edges that fail entailment.

### 3. Test provenance and source fitness

Evaluate claim-relative authority, freshness, directness, methodological transparency, and version validity. Confirm source IDs and locators resolve. A source may be authoritative for one claim and weak for another.

### 4. Test independence

Count underlying evidence origins, not documents. Collapse:

- syndicated copies
- press-release rewrites
- multiple articles citing one study
- studies using the same dataset without independent replication
- vendor pages repeating one internal test

Record the effective independence count.

### 5. Inspect contradiction and qualification

Compare contradictory spans at matched scope. Some apparent contradictions are explained by different populations, versions, dates, or definitions; represent these as qualifications rather than forcing a binary result.

Do not suppress credible contradiction because supporting sources are more numerous.

### 6. Verify calculations and inferences

- Recompute deterministic calculations from stored inputs and units.
- Confirm every inference premise is itself adjudicated.
- Label normative recommendations separately from empirical findings.
- Do not promote an inference above the confidence of its weakest material premise.

### 7. Assign a terminal status

Use:

- `verified`: contract threshold met, direct evidence valid, and no unresolved material contradiction
- `contested`: credible support and contradiction remain after scope matching
- `rejected`: claim is materially refuted, misquoted, scope-inflated, or unsupported
- `superseded`: a newer time/version-bounded claim replaces the old one
- `unknown`: evidence is insufficient, inaccessible, or methodologically inadequate

“No contradiction found” is not verification.

### 8. Decide whether a gap task is warranted

Create a `ResearchGap` only when:

- the claim is critical or major
- missing evidence could change the conclusion
- an identifiable source type or test could resolve it
- gap iterations and budget remain

The verifier returns a gap request to the orchestrator; it does not browse opportunistically outside the task graph.

### 9. Record the adjudication

```json
{
  "decision_id": "adjudication:<claim-id>:<version>",
  "claim_id": "claim:...",
  "status": "verified|contested|rejected|superseded|unknown",
  "supporting_evidence": ["evidence:..."],
  "contradicting_evidence": [],
  "qualifying_evidence": [],
  "independence_groups": ["..."],
  "confidence": {"level": "high|medium|low", "reason": "..."},
  "rationale": "...",
  "gap_request": null
}
```

Confidence always includes a reason and is subordinate to status.

## Output contract

```json
{
  "run_id": "...",
  "task_id": "...",
  "decisions": [],
  "status_counts": {},
  "gap_requests": [],
  "invalid_edges": [],
  "limitations": [],
  "validation": {"passed": true, "errors": []}
}
```

## Failure recovery

- **Span is missing or inaccessible:** status `unknown`; request a precise gap only if material.
- **Source has changed since extraction:** require a new versioned source record and re-extraction.
- **Evidence supports only a narrower claim:** reject or supersede the broad claim and propose the narrower claim.
- **Contradiction is due to date/version:** create time-bounded claims and `SUPERSEDES` edges.
- **Calculation inputs disagree:** adjudicate inputs first; do not average silently.
- **Gap budget exhausted:** retain `unknown` or `contested` and expose the limitation.
- **Verifier is the original extractor:** require a separate context or agent for material claims.

## Completion checklist

- [ ] Every material claim packet contains exact spans.
- [ ] Entailment and scope were tested explicitly.
- [ ] Authority, freshness, and independence were evaluated claim-relatively.
- [ ] Contradictory and qualifying evidence are preserved.
- [ ] Calculations/inferences expose adjudicated premises.
- [ ] Every material claim has a terminal status.
- [ ] Gap requests are precise and bounded.
- [ ] Confidence includes a reason.
