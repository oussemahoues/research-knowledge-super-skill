# Evidence Research v3

Evidence Research v3 is a durable research-agent plugin built around one invariant:

> **The task graph executes the work; the temporal evidence graph preserves, challenges, and verifies it.**

It replaces monolithic research prompts and JSONL-as-state workflows with a resumable SQLite event store, artifact-backed task graphs, immutable source episodes, bitemporal evidence, reversible entity fusion, independent claim adjudication, and deterministic release gates.

## Core capabilities

- Adaptive `single`, `diamond`, `hierarchical`, `retrieval-only`, and `audit-only` execution
- Durable attempts, leases, checkpoints, interrupts, approvals, bounded retries, and idempotent replay
- Task-DAG validation for real artifact dependencies, writer ownership, fan-in, and verifier separation
- Immutable content-addressed source episodes with version supersession and integrity checks
- Prompt-injection quarantine across normalized, fragmented, multilingual, and encoded views
- Sensitive-data classification and redaction for persisted excerpts and reports
- Versioned ontology registry and bitemporal graph reconstruction
- Conservative reversible entity fusion
- Query-adaptive lexical, neighborhood, path, temporal, causal, community, and evidence-gap retrieval
- Independent evidence-chain adjudication
- Deterministic report rendering with claim, edge, and source-episode markers
- Fixed 100-case benchmark, v2 regression comparison, fault tests, and complete release sealing

## Canonical state

SQLite is canonical for runs, events, tasks, attempts, dependencies, artifacts, checkpoints, interrupts, approvals, source episodes, ontology versions, graph nodes and edges, fusion decisions, retrieval traces, and adjudications.

`contract.json`, `task-graph.json`, `run.json`, reports, audits, and JSONL exports are readable artifacts or interchange formats. They are not authoritative transaction state.

## Commands

```bash
python -B scripts/researchctl.py engine
python -B scripts/researchctl.py init --contract contract.json --root research-runs
python -B scripts/researchctl.py inspect <run>
python -B scripts/researchctl.py ready <run>
python -B scripts/researchctl.py recover-leases <run>
python -B scripts/researchctl.py query <run> "<question>" --as-of <timestamp>
python -B scripts/researchctl.py verify-claim <run> <claim-id>
python -B scripts/researchctl.py render <run>
python -B scripts/researchctl.py audit <run>
python -B scripts/researchctl.py migrate-v2 <legacy-run> <destination>
```

Set `EVIDENCE_RESEARCH_ENGINE=v2` only for emergency fallback or migration validation.

## Run layout

```text
research-runs/<run-id>/
├── state.db
├── source-episodes/
├── contract.json
├── task-graph.json
├── run.json
├── report.md
└── audit.json
```

## Development verification

```bash
python -B verify.py
python -B scripts/run_benchmark.py --output benchmark-report.json
python -B scripts/researchctl.py demo /tmp/evidence-research-demo
```

## Release verification

Release verification is stricter than development CI. It requires complete file coverage in `MANIFEST.json` and rejects modified, missing, or extra shipped files.

```bash
python -B scripts/build_manifest.py
python -B verify.py --release
```

The `Release verification` workflow performs development verification, the fixed benchmark, manifest generation, complete seal verification, and evidence-artifact upload on manual dispatch or a `v3.*` tag.

## Migration

See `docs/migration-v2-to-v3.md`. Migration is non-destructive, preserves legacy graph IDs, records unverifiable legacy provenance explicitly, and leaves the v2 source run unchanged.

## Release rule

Do not promote or merge a release candidate until Python 3.10–3.13 CI, the fixed benchmark, security and fault suites, v2 fallback, complete release seal, architecture/security reviews, and explicit human approval all pass.

## Design provenance

The plugin incorporates ontology-first and task-graph concepts from `codejunkie99/graph-engineering` under its MIT license without importing that project as a runtime dependency. See `NOTICE` and `references/research-basis.md`.
