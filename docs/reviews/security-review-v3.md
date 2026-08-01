# Evidence Research v3 Security Review

Review date: 2026-08-01
Review scope: acquisition, graph persistence, agent contracts, report rendering, fallback, migration, and release sealing
Decision: **security controls are materially improved; release approval withheld**

## Trust boundaries

- User goals and platform policy are trusted control input.
- Retrieved pages, files, source text, tool output, and delegated-agent messages are untrusted data.
- Source episodes are immutable evidence containers, not executable instructions.
- Only declared runtime APIs may mutate canonical state.
- The independent auditor is read-only and may not repair failing evidence.

## Controls confirmed

1. High-risk instruction override, credential, tool-execution, hidden-context, exfiltration, and false-authority patterns are quarantined.
2. Encoded-payload indicators are retained as medium risk and are never executed automatically.
3. Quarantined source episodes cannot satisfy completion audit.
4. Source content hashes are verified before release-quality use.
5. Agent contracts prohibit embedded source instructions and self-verification.
6. Human interrupts gate high-consequence decisions.
7. The v2 fallback is selected only through an explicit environment switch.
8. Release sealing detects modified and newly introduced files.

## Findings

### S-01 — Optional release seal — P1 — Closed

Resolved by complete-manifest release mode in commit `881d746a`.

### S-02 — Injection detection is primarily pattern-based — P2 — Open

The fixed hostile corpus passes, but regex detection can be evaded through multilingual phrasing, homoglyphs, fragmented instructions, or novel encodings. Expand the corpus and add normalization and structural heuristics before release.

### S-03 — No explicit secret-redaction layer for persisted excerpts — P2 — Open

The scanner detects credential requests, but source findings and excerpts can still persist accidental secret material. Add redaction or a sensitive-data classification gate before episode persistence.

### S-04 — Tool capability enforcement depends partly on host declarations — P2 — Open

Agent files declare allowed and disallowed tools, but the repository does not independently prove host enforcement. Release documentation must state this dependency and provide a fail-closed capability check where supported.

### S-05 — Legacy migration preserves unverifiable source hashes — P3 — Accepted limitation

When original v2 bytes are unavailable, migration records `unverified-legacy` and audit warnings. Such episodes cannot be represented as byte-reverified evidence without reacquisition.

## Security verdict

No open P1 finding remains. Release remains blocked by S-02 through S-04, final release-seal execution, and explicit human approval.
