# Source policy

## Authority tiers

- **A — Primary/authoritative:** laws, standards, official statistics, first-party technical documentation, original research, source code, filings, direct records.
- **B — Strong secondary:** reputable systematic reviews, professional bodies, established technical journalism with transparent sourcing.
- **C — Discovery:** aggregators, vendor comparisons, general journalism, expert commentary. Useful for leads; not sufficient alone for consequential claims.
- **D — Untrusted/unknown:** anonymous pages, SEO content, unverifiable reposts, synthetic content without provenance.

Authority is claim-relative. A vendor is primary for its own published specifications but not an independent authority on competitor performance.

## Required source fields

`id`, `title`, `locator`, `publisher`, `published_at`, `accessed_at`, `authority_tier`, `source_type`, `content_hash`, `independence_group`, and `injection_risk`.

## Diversity

Count independence groups, not URLs. Syndicated copies, press-release rewrites, and papers sharing the same underlying dataset do not count as independent corroboration.

## Freshness

Each run sets an as-of date and a volatility class. Current office holders, prices, laws, product specifications, schedules, and live metrics require current retrieval. Stable historical facts may use older primary sources.
