# Evidence Research 2.0 — Implementation Report

## Target

Replace the monolithic research super-skill with a modular, auditable, resumable research plugin built around explicit execution topology and a persistent claim-evidence graph.

## Delivered

- 9 focused skills
- 5 bounded agents
- 3 explicit commands
- claim-evidence ontology and JSON schemas
- resumable state machine
- task DAG validation
- reversible entity-resolution decisions
- source authority, freshness, independence, and injection assessment
- report and completion audits
- pre-write and post-write hooks
- offline evaluation fixtures and tests
- plugin and harness manifests

## Verification

The release was verified locally with Python 3.13 using `python -B verify.py`.

- skill frontmatter and layout: PASS
- Python parse gate: PASS
- unit tests: 20/20 PASS
- synthetic end-to-end research run: PASS
- task fake-edge detection: PASS
- task cycle detection: PASS
- graph endpoint validation: PASS
- verified-claim evidence requirement: PASS
- prompt-injection detection: PASS
- completed-run immutability guard: PASS
- report claim and source resolution: PASS

## Architecture decision

The plugin uses an append-only JSONL event/record layer plus deterministic validators instead of requiring a graph database. This keeps the core portable and testable. A graph database may be added as a projection adapter later without changing canonical IDs or schemas.

## Research integration

The ontology-first knowledge pipeline and the distinction between knowledge graphs and task graphs were adapted from `codejunkie99/graph-engineering` under MIT. The implementation, contracts, runtime, and tests are independent.

## Known portability boundary

Claude Code receives native commands, agents, skills, and hooks. Codex and Antigravity require target rendering through the user's harness framework. Unsupported hook payloads must be reported rather than silently claimed as active.
