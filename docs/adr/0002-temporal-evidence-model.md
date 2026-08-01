# ADR 0002: Temporal evidence model

## Decision

Represent retrieved content as immutable source episodes and represent facts with both validity time and recording time. Preserve superseded and contradictory facts rather than overwriting them.

## Required fields

- `valid_from`, `valid_to`
- `recorded_at`
- `source_episode_id`
- `content_hash`
- exact locator
- ontology version
- supersession link when applicable

## Consequences

Current answers may prefer the newest valid fact, while historical queries can reconstruct prior states. Fusion and adjudication must never erase provenance.
