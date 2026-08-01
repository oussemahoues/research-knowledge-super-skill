---
description: Import a v2 run into a separate v3 destination without modifying the source run.
argument-hint: <v2-run-path> <v3-destination>
model: inherit
---

# /research-migrate

## Purpose

Create a non-destructive v3 representation of a v2 run while preserving legacy IDs and making unverifiable provenance explicit. Migration is not a release approval and does not convert legacy bytes into verified source episodes.

## Preconditions

Require a readable v2 run, a new authorized destination, sufficient storage, and a recorded inventory/hash of the source. The destination must not overwrite the v2 directory or an existing completed v3 run.

## Procedure

1. Read `docs/migration-v2-to-v3.md` and inspect the v2 artifacts.
2. Record source path, engine/version, artifact counts, hashes, and known gaps.
3. Run:

```bash
python -B $CLAUDE_PLUGIN_ROOT/scripts/researchctl.py migrate-v2 \
  <v2-run-path> <v3-destination>
```

4. Inspect the destination and migration record.
5. Verify task/graph ID preservation, source episode mapping, legacy provenance labels, and that the source run is byte-for-byte unchanged.
6. Run v3 inspect, query smoke checks, adjudication sampling, render/marker audit when applicable, and completion audit.
7. Validate `EVIDENCE_RESEARCH_ENGINE=v2` fallback independently before any release promotion.

## Provenance rule

When v2 did not preserve source bytes or a verifiable hash, mark the imported episode `unverified-legacy`. Do not synthesize a hash, infer retrieval time, or claim byte verification.

## Rollback

Rollback selects the untouched v2 run/engine. It does not delete the v3 destination. A failed migration remains available for diagnosis and must use a new clean destination for retry unless the migration implementation documents safe idempotent reuse.

## Output

Return source/destination IDs and paths, imported/skipped counts, preserved IDs, legacy-unverified counts, validation errors/warnings, fallback result, and release blockers.

