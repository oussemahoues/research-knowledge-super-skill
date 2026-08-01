---
name: auditing-research-run
description: Use this skill before an Evidence Research v3 run is declared complete, when reviewing another agent's run, when CI or report verification fails, or when diagnosing a blocked run. It deterministically checks event-store integrity, task-DAG semantics, attempts and leases, open interrupts, source-episode hashes and quarantine state, temporal graph references, fusion decisions, claim adjudication, retrieval traces, report markers, migration integrity, and release thresholds. Do not acquire evidence, reinterpret claims, or rewrite the report while auditing.
---

# Audit an Evidence Research v3 Run

Produce a reproducible pass/fail verdict from canonical SQLite state and immutable source bytes. A failed audit is a valid result.

## Procedure

1. Resolve the run path and read `run.json` only as a locator for `state.db` and the run ID.
2. Run the integrated audit:

```bash
python -B ${CLAUDE_PLUGIN_ROOT}/scripts/researchctl.py audit <run>
```

3. Verify task control:
   - every dependency carries a real producer/consumer artifact flow;
   - no cycles, duplicate writers, unbounded retries, stale running leases, or self-verification;
   - all required tasks succeeded;
   - successful sibling branches remain preserved;
   - all required interrupts are resolved by authorized reviewers.
4. Verify source episodes:
   - IDs and content hashes are unique and resolvable;
   - source bytes exist and match the stored hash;
   - authority, independence group, locator, effective time, retrieval time, and injection risk are present;
   - quarantined source episodes are not used as evidence;
   - legacy-unverified episodes remain explicitly warned, never silently treated as byte-verified.
5. Verify the temporal graph:
   - node and edge endpoints exist;
   - ontology versions resolve;
   - validity intervals are legal;
   - supersession chains are coherent;
   - contradictions and overlapping incompatible facts remain visible;
   - fusion decisions are reversible and ambiguous reviews are not silently applied.
6. Verify adjudication:
   - every material claim has a latest decision;
   - `verified` claims have valid support chains;
   - `contested` claims retain contradiction edges;
   - numbers, temporal validity, independence requirements, and quarantine status were checked;
   - `needs_review` and `rejected` claims are excluded from publishable findings.
7. Verify retrieval and report traceability when present:
   - retrieval traces persist query class, methods, selected nodes, paths, source episodes, gaps, and token estimate;
   - report claim, evidence-edge, and source-episode markers resolve to the latest adjudication chain;
   - required sections, as-of date, limitations, conflicts, gaps, and source register exist.
8. Verify migration and rollback evidence when applicable:
   - the v2 source run digest remained unchanged;
   - legacy IDs were preserved;
   - v3 destination was new and isolated;
   - `EVIDENCE_RESEARCH_ENGINE=v2` fallback remains executable.

## Failure routing

Map each failure to the earliest repair plane:

- scope or acceptance defect -> control/scoping;
- DAG, ownership, lease, or budget defect -> task planning/runtime;
- missing or weak source -> acquisition;
- missing span, locator, hash, or ontology type -> extraction;
- mistaken identity or irreversible merge -> fusion;
- invalid support, contradiction, number, or temporal decision -> adjudication;
- report marker or section defect -> synthesis;
- audit implementation failure -> audit tooling.

Do not restart the whole run when a bounded repair is sufficient.

## Completion gate

Return `passed: true` only when no hard error remains. Keep warnings visible. Never convert warnings into reassuring prose that obscures their operational significance. A run is complete-eligible only after the deterministic audit passes and any required final human release gate is approved.
