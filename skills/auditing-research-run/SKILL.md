---
name: auditing-research-run
description: Perform a deterministic completion audit of a research run, checking state integrity, task-graph topology, graph referential integrity, claim-evidence coverage, citation resolvability, contested-claim exposure, required report sections, and immutable-run rules. Use before declaring research complete, when reviewing a run produced by another agent, or when diagnosing a blocked run. Do not acquire new evidence or rewrite the report.
---

# Audit the Research Run

1. Validate `run.json` and legal state transitions.
2. Validate `task-graph.json`: acyclic, zero fake dependencies, bounded fan-out, one merge owner.
3. Validate `sources.jsonl` and `evidence-graph.jsonl`: parseable, unique IDs, valid endpoints, required provenance.
4. Audit `report.md` against graph claims and source markers using `lib/report_audit.py`.
5. Check required sections, as-of date, limitations, and unresolved gaps.
6. Compare metrics with thresholds in `run.json`.
7. Write `audit.json` with `passed`, metrics, failures, warnings, and instrument versions.
8. Return `COMPLETE` eligibility. Never mutate another artifact.

A failed audit is a useful result. Report exact failing gates rather than softening them.
