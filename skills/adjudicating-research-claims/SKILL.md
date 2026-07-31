---
name: adjudicating-research-claims
description: Independently verify, contest, reject, supersede, or leave unknown the material claims in an evidence graph by testing direct support, contradiction, source independence, freshness, and methodological quality. Use after extraction and resolution, for citation checking, or when a conclusion is disputed. Do not rely on source titles, semantic similarity alone, or the extractor's confidence as proof.
---

# Adjudicate Research Claims

1. Work in a context separate from the extractor. Read the atomic claim and its exact evidence spans.
2. Test entailment: does the cited span directly assert or validly imply the claim at the same scope, population, time, and modality?
3. Test provenance, authority, freshness, and independence. Detect citation laundering and shared underlying datasets.
4. Search for disconfirming evidence only when the task graph authorizes a gap-resolution acquisition task.
5. Assign status:
   - `verified`: threshold met with no unresolved material contradiction;
   - `contested`: credible support and contradiction both remain;
   - `rejected`: evidence refutes or fails the claim materially;
   - `superseded`: a newer time-bounded claim replaces it;
   - `unknown`: evidence is insufficient.
6. Record rationale and evidence IDs. Confidence must include a reason, not a bare number.
7. Produce explicit research gaps for any material `unknown` or `contested` claim.

Never turn “no contradiction found” into verification.
