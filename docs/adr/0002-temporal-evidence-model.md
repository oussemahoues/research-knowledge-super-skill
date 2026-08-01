# ADR 0002: Immutable Source Episodes and Bitemporal Evidence

- Status: accepted and implemented
- Decision owners: evidence architecture
- Affects: acquisition, graph, retrieval, adjudication, migration, reporting

## Context

Web pages, documents, repositories, laws, and datasets change. A single mutable Source record cannot answer which bytes supported a Claim, when the asserted fact was valid, or what the research run knew at an earlier time. Overwriting old facts destroys contradiction and correction history.

## Decision

Represent every acquired byte sequence as an immutable, content-addressed Source Episode. A logical source may have multiple ordered episodes. Represent factual relations as typed graph edges with both validity time and recording time. Supersede edges and episodes explicitly instead of overwriting them.

## Source episode contract

An episode records logical source ID, episode ID, version, locator, media type, SHA-256 content hash/path, authority, independence group, injection risk, effective/retrieved time, metadata, and optional predecessor episode.

The episode is created before evidentiary edges. Stored bytes are re-hashed before release-quality use. Quarantined bytes remain auditable but ineligible for evidence.

## Edge time contract

- `valid_from`: inclusive start of real-world applicability.
- `valid_to`: exclusive end of applicability, or null while open.
- `recorded_at`: time the runtime persisted the relation.
- `source_episode_id`: immutable bytes supporting the relation when evidentiary.
- `ontology_version`: schema under which the edge was validated.
- `supersedes_edge_id`: predecessor relation when updating applicability.

An as-of query filters validity. A recorded-by query reconstructs the information state known by a historical recording time. These queries answer different questions.

## Invariants

- `valid_to`, when present, is later than `valid_from`.
- Edge endpoints exist and conform to the referenced ontology version.
- Supersession closes the predecessor interval and creates a successor.
- Old bytes, edges, contradictions, and provenance remain queryable.
- Entity fusion never erases source/edge provenance.
- Report citations identify episodes, not mutable logical sources alone.

## Alternatives considered

### Mutable latest-value records

Rejected because they cannot reproduce historical answers or audits.

### Ingestion-time timestamps only

Rejected because acquisition time and real-world validity are different dimensions.

### URL as source identity

Rejected because content at one locator changes and identical content can appear at multiple locators.

## Migration

V2 records without preserved bytes are imported non-destructively with explicit `unverified-legacy` provenance. The migration must not manufacture byte hashes or claim integrity verification that cannot be performed.

## Failure modes

- Missing/tampered episode bytes: block dependent evidence and audit.
- Unknown validity: preserve null/explicit uncertainty; do not infer dates from retrieval time.
- Overlapping contradictory edges: retain and surface as conflict.
- Broken supersession chain: fail validation; do not silently select the newest row.
- Changed locator with identical bytes: decide logical source identity from provenance, not hash alone.

## Verification

Tests cover idempotent identical episodes, version increments for changed content, predecessor links, hash verification, validity boundaries, historical reconstruction, recorded-by filtering, contradiction detection, and non-destructive migration.

## Consequences

The model supports reproducible historical research and explicit correction history. It increases storage and requires careful time semantics, retention policy, and privacy controls for immutable raw bytes.

