# Evidence Research v2 to v3 Migration

## Purpose

Migrate a completed or active v2 run into the v3 SQLite event store without modifying the source directory. The migration preserves legacy graph identifiers and records any provenance or integrity limitation that cannot be reconstructed.

## Canonical-state change

| v2 artifact | v3 canonical representation |
|---|---|
| `run.json` | run metadata plus SQLite `runs` and `run_events` |
| `task-graph.json` | registered tasks and dependencies in SQLite |
| `sources.jsonl` | immutable `source_episodes` and content-addressed bytes |
| `evidence-graph.jsonl` | versioned `graph_nodes` and bitemporal `graph_edges` |
| `decisions.jsonl` | resolution and adjudication decision tables |
| `report.md` | rendered view generated from latest adjudications |
| `audit.json` | reproducible audit output, not canonical state |

JSON and JSONL remain export and interchange formats only.

## Migration command

```bash
python -B scripts/researchctl.py migrate-v2 <v2-run> <v3-destination>
```

The destination must not contain an existing v3 database. The command creates `state.db`, `source-episodes/`, and a v3 `run.json` locator.

## Required checks

1. Record the source-directory digest before migration.
2. Preserve legacy node and edge IDs.
3. Import source metadata without asserting byte integrity when original content is unavailable.
4. Mark unverifiable legacy source episodes explicitly.
5. Run the deterministic v3 audit on the destination.
6. Recompute the source-directory digest and confirm it is unchanged.
7. Exercise the v2 fallback with `EVIDENCE_RESEARCH_ENGINE=v2` before promotion.

## Rollback

Migration is additive. Rollback means selecting the v2 engine and original v2 run; it never means rewriting the migrated database or source run.

```bash
EVIDENCE_RESEARCH_ENGINE=v2 python -B scripts/researchctl.py audit <v2-run>
```

Do not delete the v3 destination until migration evidence, audit results, and human approvals have been retained.

## Release restriction

A migrated run is not release evidence by itself. Promotion still requires the fixed benchmark, security and fault suites, complete release manifest, Python 3.10–3.13 verification, and explicit human approval.
