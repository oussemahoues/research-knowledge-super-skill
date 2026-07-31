# Evidence ontology

## Node types

- `ResearchQuestion`: a scoped question with acceptance criteria.
- `Hypothesis`: a proposition intentionally tested, not presumed true.
- `Claim`: one atomic, externally checkable proposition.
- `EvidenceSpan`: exact text, table cell, figure region, or structured field.
- `Source`: an acquired document, page, dataset, repository object, or record.
- `Entity`: a resolved real-world object with aliases.
- `Event`: a time-bounded occurrence with typed participants.
- `Method`: a method, standard, procedure, or analytical technique.
- `Dataset`: a defined data collection.
- `Finding`: an adjudicated result derived from claims.
- `ResearchGap`: missing evidence that could change the conclusion.

## Edge types

- `ASSERTED_BY`: Claim → Source
- `SUPPORTS`: EvidenceSpan → Claim
- `CONTRADICTS`: EvidenceSpan → Claim
- `QUALIFIES`: EvidenceSpan or Claim → Claim
- `DERIVED_FROM`: Finding or Claim → Claim, Dataset, or Method
- `ABOUT`: Claim or EvidenceSpan → Entity or Event
- `SAME_AS`: Entity → Entity
- `SUPERSEDES`: Claim, Source, or Run → same type
- `ANSWERS`: Finding or Claim → ResearchQuestion
- `CITES`: Source → Source

## Claim granularity

A claim should be falsifiable by one focused evidence check. Split sentences joined by independent conjunctions. Keep interpretation separate from observation. Store an inference as a claim with `claim_kind: inference` and edges to every premise.

## Status

`candidate`, `verified`, `contested`, `rejected`, `superseded`, `unknown`.

`verified` means the evidence threshold defined in the run is satisfied; it does not mean metaphysical certainty. `contested` means material supporting and contradictory evidence remains unresolved.
