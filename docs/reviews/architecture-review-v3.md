# Evidence Research v3 Architecture Review

Review date: 2026-08-01
Review scope: PR #5, branch `sota-graph-engine-v3-phase2`
Decision: **conditionally acceptable for continued development; not release-approved**

## Reviewed architecture

The v3 design uses two explicit planes:

- a durable artifact-flow task graph backed by SQLite events, attempts, checkpoints, leases, interrupts, and approvals;
- a bitemporal evidence graph backed by immutable source episodes, versioned ontology records, reversible entity-resolution decisions, persisted retrieval traces, and claim adjudications.

The CLI defaults to v3 and preserves a sealed v2 fallback through `EVIDENCE_RESEARCH_ENGINE=v2`. JSON and JSONL are interchange or locator formats, not canonical transaction state.

## Strengths confirmed

1. Task dependencies are validated against actual artifact flow; fake dependencies and cycles are rejected.
2. Verification ownership is separated from evidence production.
3. Retries are bounded and stale leases are recoverable without discarding successful sibling work.
4. Source bytes are content-addressed and tamper-checkable.
5. Valid time and recorded time are represented separately.
6. Entity fusion records decisions and supports reversal.
7. Retrieval strategy is query-adaptive and produces durable traces.
8. Reports are rendered only from publishable adjudication states and audited for marker resolvability.
9. The fixed 100-case benchmark is deterministic and compared with v2 critical metrics.

## Findings

### A-01 — Release manifest was optional — P1 — Closed

Prior verification could print a sealed-plugin success message without requiring `MANIFEST.json`. Commit `881d746a` adds explicit release verification that requires complete file coverage and rejects missing, additional, modified, or removed files.

### A-02 — Plugin metadata and README still identify v2 — P2 — Open

`.claude-plugin/plugin.json` and the top-level README still advertise version 2.0 and JSONL-centric architecture. They must be updated only in the release-preparation commit, together with verifier expectations and final migration notes.

### A-03 — Final release manifest is not generated — P2 — Open

The deterministic manifest builder exists, but the manifest must be generated after the final release-content commit. Generating it earlier would immediately become stale.

### A-04 — Development CI does not execute release-seal mode — P2 — Open

Normal CI intentionally permits an absent final manifest. The release workflow must add a final job that builds the manifest in a clean checkout and then executes `python -B verify.py --release`.

### A-05 — External graph adapters remain optional and unproven — P3 — Open

SQLite is the canonical implementation. Neo4j/FalkorDB-style adapters are not required for release, but no adapter conformance suite currently exists.

## Architecture verdict

No open P1 finding remains. The architecture is coherent and testable, but release remains blocked by A-02 through A-04 and explicit human approval.
