---
name: adjudicating-research-claims
description: This skill should be used when material research claims require independent verification, contradiction analysis, citation checking, confidence assessment, or a terminal status such as verified, contested, rejected, superseded, or unknown. It tests exact evidence spans for entailment, provenance, authority, freshness, independence, and methodological quality. Do not rely on titles, semantic similarity, extractor confidence, or absence of contradiction as proof.
---

# Adjudicate Research Claims

Evaluate candidate claims in a context separate from extraction. Success means every material claim receives a reasoned terminal status or an explicit bounded evidence gap.

## Inputs

```json
{
  "run_id": "...",
  "task_id": "...",
  "claim_ids": ["claim:..."],
  "graph_path": "<run>/evidence-graph.jsonl",
  "sources_path": "<run>/sources.jsonl",
  "contract": "<run>/run.json",
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

1. Confirm the verifier did not create the candidate claim or extraction batch. If separation is impossible, disclose the limitation and apply heightened review.
2. Read the atomic claim, its scope, modality, time, population/entity, and all linked exact evidence spans.
3. Test entailment for each span:
   - does it assert or validly imply the same proposition;
   - does it match scope, population, timeframe, and modality;
   - is omitted context material;
   - is the locator exact and content hash consistent?
4. Test source provenance, claim-relative authority, freshness, and methodological suitability.
5. Group evidence by independence family. Do not count repeated reporting of the same underlying source as corroboration.
6. Inspect supporting, contradicting, and qualifying evidence. Preserve credible disagreement.
7. Detect citation laundering: a secondary source citing a primary source does not create a second independent evidence family.
8. Evaluate calculations and inferences by checking every premise, transformation, unit, and assumption.
9. Assign one status:
   - `verified`: configured evidence threshold is met and no unresolved material contradiction remains;
   - `contested`: credible support and contradiction remain;
   - `rejected`: the claim is materially refuted or unsupported at its stated strength;
   - `superseded`: a newer time-bounded claim replaces it;
   - `unknown`: available evidence is insufficient.
10. Record a reasoned confidence statement. Do not emit a bare numeric score.
11. For material `unknown` or `contested` claims, define the minimum evidence that could change the status.
12. Request a targeted gap-acquisition task only through the orchestrator and only while below `max_gap_iterations`.
13. Append adjudication decisions and status updates through the designated canonical writer; do not rewrite source evidence.

## Output contract

```json
{
  "claim_id": "claim:...",
  "status": "verified|contested|rejected|superseded|unknown",
  "supporting_evidence": ["evidence:..."],
  "contradicting_evidence": [],
  "qualifying_evidence": [],
  "independence_groups": ["..."],
  "entailment_findings": [],
  "confidence": {"level": "high|medium|low", "reason": "..."},
  "rationale": "...",
  "gap": {"needed": false, "minimum_evidence": "..."}
}
```

## Status rules

- Do not verify a broader claim from narrower evidence.
- Do not convert “associated with” into “caused.”
- Do not convert absence of evidence into evidence of absence unless the method supports it.
- Do not verify current claims with stale sources outside the configured freshness limit.
- Do not reject a claim merely because one source disagrees; assess authority and method.
- Do not suppress contradictions to produce a cleaner report.

## Failure recovery

- **Evidence locator cannot be resolved:** downgrade the evidence and create a citation-integrity gap.
- **Source content changed:** compare content hashes, preserve the old record, and acquire/version the new source.
- **Methodology cannot be assessed:** retain `unknown` or lower confidence; do not assume quality.
- **Gap budget exhausted:** finalize as `unknown` or `contested` with explicit limitation.
- **Claim is compound:** return it for splitting before adjudication.
- **Conflicting authoritative versions:** apply effective dates and use `superseded` when appropriate.
- **User premise conflicts with evidence:** state the conflict and adjudicate from evidence, not user preference.

## Completion checklist

- [ ] Exact spans were inspected.
- [ ] Entailment matches claim scope and modality.
- [ ] Authority, freshness, and methodology were assessed.
- [ ] Independence groups were deduplicated.
- [ ] Contradictory and qualifying evidence were considered.
- [ ] Terminal status has a rationale.
- [ ] Confidence has a reason.
- [ ] Material gaps specify evidence that could change the result.
