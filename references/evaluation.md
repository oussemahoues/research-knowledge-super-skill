# Evaluation and completion thresholds

## Structural metrics

- Task graph acyclic: required.
- Fake dependency count: zero.
- Orphan graph edge count: zero.
- Duplicate canonical entity rate after resolution: reported.

## Evidence metrics

- Claim evidence coverage = report claims with at least one support edge / report claims.
- Citation resolvability = source markers resolving to source records / source markers.
- Citation entailment = sampled citations whose evidence span directly supports the claim / sampled citations.
- Contradiction exposure = contested report claims with visible contradictory evidence / contested report claims.
- Independent corroboration = verified claims meeting the run's independence threshold / verified claims requiring corroboration.

## Report metrics

- Scope coverage against acceptance questions.
- Required-section completeness.
- Unsupported factual claim count.
- Source-tier distribution.
- As-of date present.
- Limitations and unresolved gaps present.

## Default gate

- claim evidence coverage: 1.00
- citation resolvability: 1.00
- citation entailment sample: ≥0.90
- unsupported factual claims: 0
- fake dependencies: 0

Thresholds may be made stricter per run. Lowering them must be recorded in `decisions.jsonl` with rationale and must not be hidden from the report.
