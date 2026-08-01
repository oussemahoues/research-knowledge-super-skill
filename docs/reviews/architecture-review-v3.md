# Evidence Research v3 Architecture Review

Review date: 2026-08-01
Review scope: PR #5, branch `sota-graph-engine-v3-phase2`
Decision: **implementation acceptable for release-candidate sealing; release approval withheld**

## Reviewed architecture

The v3 design uses two explicit planes:

- a durable artifact-flow task graph backed by SQLite events, attempts, checkpoints, leases, interrupts, approvals, and capability decisions;
- a bitemporal evidence graph backed by immutable source episodes, versioned ontology records, reversible entity-resolution decisions, persisted retrieval traces, and claim adjudications.

The CLI defaults to v3 and preserves a sealed v2 fallback through `EVIDENCE_RESEARCH_ENGINE=v2`. JSON and JSONL are interchange, export, or readable locator formats, not canonical transaction state.

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
10. Host capability decisions are explicit, persisted, and fail closed when declared requirements are absent.
11. Plugin metadata, README, root skill, both harness manifests, and all stage skills describe the same v3 canonical architecture.

## Findings

### A-01 — Release manifest was optional — P1 — Closed

Explicit release verification requires complete file coverage and rejects missing, additional, modified, or removed files.

### A-02 — Plugin metadata and README identified v2 — P2 — Closed

The plugin metadata is version 3.0.0. README, root skill, harness files, migration guide, agents, and stage skills now describe SQLite canonical state and JSON/JSONL as derived or interchange formats.

### A-03 — Final release manifest is not committed — P2 — Controlled release step

The deterministic manifest builder exists. The release workflow generates `MANIFEST.json` only after checkout and before `verify.py --release`; the repository intentionally does not maintain a stale development manifest.

### A-04 — Development CI did not execute release-seal mode — P2 — Closed

`.github/workflows/release-verify.yml` performs development verification, fixed benchmark execution, manifest generation, complete release verification, and evidence-artifact upload across Python 3.10–3.13.

### A-05 — External graph adapters remain optional and unproven — P3 — Accepted limitation

SQLite is the release canonical implementation. External adapters are outside the v3 release target and must not claim conformance without a separate adapter suite.

## Architecture verdict

No open P1 or P2 architecture finding remains. The implementation may proceed to clean release-workflow execution. Release remains withheld until that workflow produces sealed evidence and the user gives explicit final approval.
