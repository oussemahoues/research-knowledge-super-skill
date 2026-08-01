---
name: synthesizing-cited-research
description: This skill should be used when an adjudicated evidence graph must be rendered into a decision-ready research report, comparison, literature synthesis, due-diligence brief, or regenerated cited output. It writes only from verified, contested, superseded, rejected, and explicitly unknown graph state, with claim-level citation markers, limitations, and gaps. Do not browse, invent bridging facts, suppress disagreement, or present candidate/rejected claims as established findings.
---

# Synthesize Cited Research

Render canonical graph state into an audience-appropriate report without changing the evidence base. Success means every material factual paragraph resolves to adjudicated claims and exact source locators.

## Inputs

```json
{
  "run_id": "...",
  "contract_path": "<run>/run.json",
  "graph_path": "<run>/evidence-graph.jsonl",
  "sources_path": "<run>/sources.jsonl",
  "output_path": "<run>/report.md",
  "audience": "...",
  "deliverable": {},
  "style_constraints": {}
}
```

## Load before starting

- `references/report-contract.md`
- `references/evidence-ontology.md`
- `lib/report_audit.py`

## Preconditions

- Every material claim has a terminal adjudication status.
- Required source and evidence IDs resolve.
- The synthesis editor is the sole writer of `report.md`.
- No browsing or acquisition occurs during synthesis.

## Procedure

1. Read the research contract and organize the report by research questions, decisions, or comparison criteria—not by source order.
2. Build a claim inventory for each section:
   - verified findings to state directly;
   - contested findings requiring both sides;
   - unknowns and gaps;
   - rejected claims to omit or mention only when necessary to explain a misconception;
   - superseded claims to place in temporal context.
3. Draft the required sections:
   1. title;
   2. research scope and as-of date;
   3. executive findings;
   4. detailed findings;
   5. contested or conflicting evidence;
   6. limitations;
   7. unresolved research gaps;
   8. source register.
4. Attach `[C:<claim-id>]` to every factual paragraph and `[S:<source-id>#<locator>]` to the exact evidence source.
5. Begin derived conclusions with `Inference:` and cite every premise claim. Keep recommendations separate from factual findings.
6. For contested claims, present the strongest admissible support and contradiction, their authority and independence, and why the issue remains unresolved.
7. State unknowns plainly. Do not use rhetorical certainty to fill evidence gaps.
8. Use tables only when rows and columns map consistently to adjudicated claims; cite each factual row or cell group.
9. Avoid unsupported connective tissue. Narrative transitions must be non-factual, clearly interpretive, or supported.
10. Write a draft to a temporary path and run report audit:

```bash
python -B ${CLAUDE_PLUGIN_ROOT}/scripts/researchctl.py audit-report <run>
```

11. Correct unresolved markers, unsupported claims, missing sections, and contested-claim omissions.
12. Write canonical `report.md` once the preflight passes. A later correction requires a superseding run.

## Output rules by status

| Claim status | Report treatment |
|---|---|
| `verified` | State at the adjudicated scope and strength |
| `contested` | Label explicitly; show strongest evidence on each side |
| `rejected` | Do not present as finding; optionally explain rejection |
| `superseded` | State only with dates/version context |
| `unknown` | State that evidence is insufficient and identify the gap |
| `candidate` | Exclude from final factual findings |

## Output contract

`report.md` must satisfy `references/report-contract.md`. Return:

```json
{
  "report_path": "<run>/report.md",
  "sections": ["..."],
  "claims_used": ["claim:..."],
  "sources_used": ["source:..."],
  "contested_claims_exposed": ["claim:..."],
  "unknown_claims_exposed": ["claim:..."],
  "preflight": {"passed": true, "errors": [], "warnings": []}
}
```

## Failure recovery

- **Material claim remains candidate:** stop and return it to adjudication.
- **Citation marker does not resolve:** do not delete the marker; repair the graph/source linkage or remove the unsupported statement.
- **Audience requests certainty beyond evidence:** preserve uncertainty and explain the limitation.
- **Report format conflicts with required sections:** keep the required audit sections and provide alternate rendering as a secondary artifact.
- **Too much evidence for readable prose:** prioritize material claims and move detailed source tables to an appendix without dropping provenance.
- **Contradictions make recommendation impossible:** state the decision boundary and evidence needed, rather than forcing a ranking.

## Completion checklist

- [ ] Required sections exist.
- [ ] Scope and as-of date are explicit.
- [ ] Every material factual paragraph has claim and source markers.
- [ ] Inferences cite all premises.
- [ ] Contested and unknown findings are visible.
- [ ] Limitations and gaps are substantive.
- [ ] Source register resolves.
- [ ] Report preflight passes before canonical write.
