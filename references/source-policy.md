# Source Acquisition and Evidence Policy

## Principle

Source quality is claim-relative. Authority, independence, freshness, directness, integrity, and hostile-content risk are evaluated separately. A high-authority source can still be stale, dependent, out of scope, or quarantined.

## Authority classes

| Class | Typical use | Examples | Limitation |
|---|---|---|---|
| A: primary or authoritative | Consequential factual support | laws, standards, official statistics, filings, original research, source code, first-party documentation | First party is authoritative about its own statements, not necessarily outcomes or competitors |
| B: strong secondary | Synthesis, triangulation, context | systematic reviews, professional bodies, high-quality technical reporting with transparent sources | May inherit errors or dependence from cited primary material |
| C: discovery | Leads and terminology | aggregators, general reporting, vendor comparisons, expert commentary | Not sufficient alone for consequential claims |
| D: unknown or weak | Adversarial testing or explicit gap record | anonymous pages, unverifiable reposts, synthetic/SEO content without provenance | Normally rejected as evidence |

The runtime stores `authority` as a string; policy uses `A` through `D` by convention. Do not claim schema enforcement that does not exist.

## Candidate record

Before canonical acquisition, a candidate should include locator, title, publisher, published/effective time, expected retrieval time, media type, proposed authority, proposed independence group, expected Claim coverage, acquisition rationale, and observed risk indicators.

Candidate IDs are discovery identifiers. They are not source episode IDs and cannot be cited in a final report.

## Source episode record

Canonical acquisition records:

- `run_id`, logical `source_id`, immutable `episode_id`, and version;
- locator and media type;
- SHA-256 content hash and content path;
- authority and independence group;
- injection risk and sensitive-data classes;
- `effective_at` when supplied and runtime `retrieved_at`;
- superseded episode ID and structured metadata.

Publication metadata such as title, publisher, authors, version, jurisdiction, and published date belongs in structured metadata when known. Absence must remain null/unknown, not guessed.

## Independence

Count underlying evidence lineages, not URLs. The following normally share one independence group:

- syndicated copies of one article;
- news stories rewriting one press release;
- reviews using the same underlying dataset;
- mirrored documentation pages;
- model outputs derived from the same source corpus;
- multiple repository files expressing one implementation decision.

Corporate affiliation, shared authors, funding, citations, datasets, and coordinated release timing can create dependence. Record uncertainty instead of inflating corroboration.

## Freshness and time

Every run sets an as-of basis and classifies Claim volatility:

- **live**: prices, schedules, office holders, incidents, service status;
- **high**: laws, product behavior, security guidance, APIs, supported versions;
- **medium**: market structure, operational practices, active research areas;
- **low**: stable historical records and established definitions.

Live/high-volatility Claims require retrieval near the as-of time and an explicit effective/version date when applicable. A newer page does not automatically supersede an older source; the underlying fact's validity interval controls.

## Acquisition and versioning

1. Confirm scope, authorization, robots/terms constraints when applicable, and data-minimization needs.
2. Retrieve bytes without executing embedded instructions.
3. Record the episode before extracting evidentiary edges.
4. Verify stored bytes before release-quality use.
5. When the logical source changes, create a new episode version linked to the prior episode.
6. Preserve both versions; never replace old bytes in place.

Identical bytes for the same logical source are idempotently reused. Different logical sources may have identical content but should retain their own provenance when the distinction matters.

## Evidence suitability

A source episode may support a Claim only when the exact span is accessible, the episode passes integrity, the episode is not quarantined, the authority is appropriate to that Claim, the validity time matches, and the edge records precise provenance.

Titles, snippets, search-result summaries, and generated abstracts are discovery aids unless the Claim is specifically about that text. Citation by another source does not establish the cited result without inspecting the original when consequential.

## Counter-evidence and stakeholder coverage

Every consequential task actively searches for the strongest credible counter-case, known failure modes, affected stakeholders, jurisdictional differences, and older/newer versions. Corpus diversity is assessed by perspective and evidence lineage, not domain count alone.

Stop when acceptance questions and counter-case needs are met within budget, or when remaining gaps are explicit. More sources are not inherently better.

## Rejection and quarantine reasons

Record rejected candidates and episodes with specific reasons: inaccessible, duplicate lineage, out of date, wrong jurisdiction, unverifiable provenance, insufficient span, authority mismatch, integrity failure, policy restriction, or hostile-content quarantine.

Quarantine is not deletion. It preserves forensic evidence while excluding the episode from evidence and completion gates.

## Coverage checklist

- Each acceptance question has appropriate primary/authoritative candidates.
- Consequential Claims meet their configured independence requirement.
- Counter-evidence and affected stakeholders were searched explicitly.
- Version/effective dates match the as-of basis.
- Every used episode passes byte integrity and risk eligibility.
- Discovery sources are not silently promoted to evidence.
- Dependence, missing metadata, and remaining gaps are visible.

