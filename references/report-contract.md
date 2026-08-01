# Deterministic Report Contract

## Purpose

`report.md` is a reproducible presentation view over canonical v3 state. It may clarify and organize adjudicated findings, but it may not create evidence, upgrade a verdict, hide contradiction, or repair graph defects.

## Publishability

Only Claims whose latest adjudication is `verified` or `contested` may appear as factual findings. `needs_review`, `rejected`, and unadjudicated Claims belong in omissions, limitations, or research gaps and must not be phrased as settled facts.

The report's as-of time controls which graph relations are applicable. When no historical time is supplied, the report must state that current graph validity was used.

## Required markers

Each factual finding must resolve all three layers:

```text
The standard requires X under condition Y. [C:claim:abc] [E:edge:def] [S:episode:ghi]
```

- `[C:<claim-id>]` identifies the atomic Claim.
- `[E:<edge-id>]` identifies a supporting or contradicting evidentiary edge.
- `[S:<episode-id>]` identifies the immutable source episode used by that edge.

Markers are machine traceability records, not decoration. A source marker without an evidence edge does not demonstrate support. A logical source ID is not a substitute for an episode ID.

## Inference rule

An inference must begin with `Inference:` or an equally explicit label, identify every premise Claim, and include the premise evidence markers. The report may explain the inference method but may not introduce an unrepresented factual premise.

Recommendations must separate value judgments or policy preferences from evidence-backed predictions.

## Required sections

1. Title.
2. Scope, acceptance questions, exclusions, and as-of basis.
3. Executive findings with calibrated status language.
4. Detailed findings mapped to acceptance questions.
5. Contested evidence showing support and contradiction.
6. Limitations, including verifier and corpus limitations.
7. Unresolved gaps and evidence that could change conclusions.
8. Omitted or non-publishable material Claims when decision-relevant.
9. Source register keyed by immutable episode.
10. Reproducibility note with run ID and audit status.

## Rendering rules

- Preserve Claim wording, modality, numbers, units, population, geography, and time bounds.
- Do not merge separate Claims into a sentence that changes their scope.
- Render contested Claims with both support and contradiction markers.
- Distinguish lack of evidence from evidence of absence.
- State when evidence is legacy-unverified, dependent, stale, or authority-limited.
- Do not cite quarantined or integrity-failing episodes.
- Keep narrative transitions non-factual or attach them to represented Claims.
- Use deterministic ordering so identical canonical state produces stable output.

## Marker audit

`researchctl render` calls `audit_rendered_report` after atomic write. A publishable result requires:

- well-formed Claim, Edge, and Episode markers;
- every marker resolves within the same run;
- edges connect the cited evidence to the cited Claim;
- cited episodes are eligible and not quarantined;
- the latest Claim adjudication is publishable;
- contested material is not rendered as unqualified verification.

A failed marker audit blocks delivery. Repair canonical state through its owning stage and render again. Hand-editing the report to suppress a failing marker is prohibited.

## Completion versus report validation

The shipped `audit_run` and report-marker audit are separate calls. Operators must run both when the deliverable includes a report. A passing completion audit alone does not prove that a report exists or that its markers resolve.

## Delivery checklist

- Scope and as-of basis are explicit.
- Every acceptance question is answered or marked open.
- Every factual finding has C/E/S markers.
- Contested findings expose both sides.
- Inferences name every premise.
- Non-publishable material Claims are not silently omitted when their absence affects the decision.
- Limitations describe corpus, time, independence, migration, and verifier constraints.
- Marker audit passes and its result is reported separately from run completion.

