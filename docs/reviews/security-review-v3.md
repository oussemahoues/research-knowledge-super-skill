# Evidence Research v3 Security Review

Review date: 2026-08-01
Review scope: acquisition, graph persistence, agents, rendering, fallback, migration, capability enforcement, and release sealing
Decision: **security implementation acceptable for sealed release-candidate verification; release approval withheld**

## Trust boundaries

- User goals and platform policy are trusted control input.
- Retrieved pages, files, source text, tool output, and delegated-agent messages are untrusted data.
- Source episodes are immutable evidence containers, not executable instructions.
- Only declared runtime APIs may mutate canonical state.
- The independent auditor is read-only and may not repair failing evidence.
- Host capability declarations are trusted only as declarations; strict mode fails when disclosure is unavailable.

## Controls confirmed

1. Instruction override, credential access, tool execution, hidden-context access, exfiltration, false authority, and encoded payloads are scanned.
2. Detection operates on normalized Unicode, stripped zero-width characters, common homoglyphs, compact fragmented text, percent-decoded text, base64, hexadecimal, and multilingual patterns.
3. High-risk source episodes are quarantined and cannot satisfy completion audit.
4. Source bytes are content-addressed and verified before release-quality use.
5. Sensitive values are classified and redacted from persisted findings, prompts, and rendered reports while immutable source bytes remain available for authorized integrity checks.
6. Agent contracts prohibit embedded source instructions and self-verification.
7. Human interrupts gate high-consequence decisions.
8. Declared missing host capabilities fail closed; strict capability mode fails when discovery is unavailable.
9. The v2 fallback is selected only through an explicit environment switch.
10. Release sealing detects modified, removed, missing, and newly introduced files.

## Findings

### S-01 — Optional release seal — P1 — Closed

Complete-manifest release mode requires deterministic coverage of every shipped file.

### S-02 — Pattern-only injection detection — P2 — Closed for v3 target

The scanner now adds Unicode normalization, homoglyph mapping, fragmented-text detection, multilingual patterns, and percent/base64/hex decoded views. The hostile corpus and dedicated hardening tests cover these classes. Novel semantic attacks remain a continuous red-team concern, not an open release blocker.

### S-03 — No explicit secret-redaction layer — P2 — Closed

Sensitive-data classification covers private keys, bearer tokens, common API keys, secret assignments, email addresses, phone-like values, and payment-card-like values. Persisted findings are redacted and source metadata records the detected classes.

### S-04 — Host capability enforcement depended on implicit declarations — P2 — Closed within host limits

The runtime exposes a capability evaluator and CLI preflight. Declared missing requirements block run creation. `--strict-capabilities` and `EVIDENCE_RESEARCH_STRICT_CAPABILITIES=1` block runs when the host cannot disclose capabilities. The decision is persisted for audit.

### S-05 — Legacy migration preserves unverifiable source hashes — P3 — Accepted limitation

When original v2 bytes are unavailable, migration records `unverified-legacy`. Such episodes cannot become byte-reverified evidence without reacquisition.

### S-06 — Immutable raw source bytes may contain sensitive data — P3 — Accepted controlled risk

Raw bytes are retained to preserve evidentiary integrity. Access control and storage protection remain host responsibilities. Unredacted bytes must never be copied into prompts, findings, logs, or reports.

## Security verdict

No open P1 or P2 security finding remains for the defined v3 release target. Release remains withheld until clean release-workflow evidence is produced and the user gives explicit final approval.
