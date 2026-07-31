---
name: synthesizing-cited-research
description: Render verified, contested, and explicitly unknown graph claims into a structured audience-appropriate research report with claim-level citations, limitations, and unresolved gaps. Use only after claim adjudication or to regenerate a report from an unchanged evidence graph. Do not browse, invent bridging facts, suppress disagreement, or cite candidate/rejected claims as established findings.
---

# Synthesize Cited Research

1. Read the research contract, adjudicated graph, and report contract.
2. Build the answer outline from research questions and accepted findings, not source order.
3. State verified findings directly. Label contested findings and present the strongest evidence on each side. State unknowns plainly.
4. Mark every factual paragraph with `[C:<claim-id>]` and `[S:<source-id>#<locator>]`.
5. Prefix derived conclusions with `Inference:` and cite all premise claims.
6. Include as-of date, scope, limitations, unresolved gaps, and source register.
7. Run `researchctl.py audit-report <run-path>` before writing the final report. Correct all structural failures.
8. Write `report.md` once. Later corrections require a superseding run.
