# Evidence Research v3 Security Model

## Threat model

The research system ingests attacker-controlled pages, files, code, metadata, citations, tool output, and agent messages. Threats include instruction injection, credential requests, context exfiltration, encoded payloads, malicious tool requests, sensitive-data persistence, source tampering, dependency confusion, denial through unbounded work, and approval bypass.

Security is fail-closed at evidence and release gates. Detection reduces risk but does not make hostile content trusted.

## Authority boundary

Authority descends from platform/user instructions to repository policy, the scoped contract, persisted approvals, and registered task inputs. Retrieved content is always data. It cannot change the objective, expand tool authority, request credentials, authorize an external write, waive budgets, resolve an interrupt, or declare completion.

Agent messages are also untrusted until their artifacts and persisted state validate.

## Acquisition controls

`SourceEpisodeStore.record` performs these operations on acquired bytes:

1. Compute a SHA-256 content identity.
2. Scan original, normalized, compacted, and supported decoded views.
3. Detect override, credential, tool-execution, context/data-exfiltration, authority-claim, encoded, fragmented, multilingual, and homoglyph patterns.
4. Classify the result as `low`, `medium`, or `quarantine`.
5. Classify sensitive-data categories and redact persisted finding excerpts/metadata.
6. Store immutable bytes by content hash and create a versioned episode.
7. Preserve the preceding episode through `supersedes_episode_id`.

The current implementation lives in `src/evidence_research/acquisition/source_episodes.py` and `src/evidence_research/acquisition/security.py`. The v2 `lib/injection_guard.py` is a fallback-engine component and must not be cited as the v3 control.

## Quarantine policy

A quarantined episode remains available for forensic audit but cannot create qualifying evidence edges, satisfy corroboration, support a publishable adjudication, or pass completion if referenced by the graph. Medium-risk content requires bounded extraction in a context that cannot invoke tools or reveal secrets.

Do not “sanitize” hostile content and then silently treat it as trusted. Preserve the raw episode, risk findings, and any redacted derived representation as distinct records.

## Sensitive data

Raw source bytes may contain sensitive material and are immutable once authorized for acquisition. Minimize acquisition before storage. Derived metadata, excerpts, prompts, logs, reports, and errors must use redaction. The source episode records sensitive-data classes without copying secrets into event payloads.

Operators remain responsible for filesystem access controls, retention, deletion policy, encryption at rest, backup handling, and jurisdictional requirements. The local runtime does not claim to provide a secure multi-tenant secret vault.

## Integrity and provenance

Before release-quality use, `verify_content` must confirm that stored bytes still match the episode hash. Graph edges must resolve to existing nodes and, for evidence, an eligible episode. Report markers must resolve to the same run's Claim, Edge, and Episode.

Migrated v2 material that lacks verifiable bytes is marked `unverified-legacy`; it cannot be represented as cryptographically reverified. This limitation must remain visible.

## Tool and agency controls

- Discovery workers use read-only research tools and cannot write canonical state.
- Curators write only through v3 APIs and do not browse.
- Verifiers are separate from evidence writers.
- Auditors do not repair findings during the audit they perform.
- External messages, purchases, deployments, repository mutations, and account changes are outside autonomous research scope unless separately and explicitly authorized.
- High-consequence and breaking-ontology decisions use persisted interrupts and attributable approvals.

Approval is scoped to one interrupt. It does not authorize unrelated tools or waive evidence/release controls.

## Resource and availability controls

Every task is bounded by attempts, lease duration, tool calls, candidate/accepted sources, parallelism, delegation depth, hop limits, and result/context limits. Exhaustion produces an explicit blocked or partial result; the runtime must not silently exceed a budget.

Idempotency keys and stale-lease recovery reduce duplicate side effects after crashes. An ambiguous external side effect must be reconciled before retry.

## Capability preflight

The host capability decision is persisted at initialization. Strict mode blocks when a required capability is unavailable. Non-strict degradation is permissible only when the missing capability is not required by the contract and the limitation is explicit.

Capability declarations do not prove the host enforces network, filesystem, or tool isolation. Deployment owners must validate actual host controls.

## Security validation

A release candidate must pass hostile-source fixtures, normalization/encoded-view tests, redaction tests, capability tests, integrity/tamper tests, quarantine-leakage tests, replay/recovery tests, complete release sealing, and the Python version matrix.

Security review findings are historical evidence, not a permanent guarantee. Re-open the review when scanners, host permissions, acquisition formats, decoders, adapters, or release contents change.

## Known limitations

- Pattern-based detection cannot prove absence of prompt injection.
- Raw immutable bytes can retain sensitive content.
- Local filesystem protections depend on deployment configuration.
- Legacy imports can lack re-verifiable provenance.
- No external graph adapter or vector store is release-qualified in v3.
- A passing deterministic verifier does not replace semantic expert review for consequential claims.

## Incident procedure

1. Stop affected acquisition or release work.
2. Preserve run ID, episode IDs, hashes, events, and tool destinations.
3. Quarantine implicated episodes and identify dependent edges, Claims, reports, and releases.
4. Revoke exposed credentials outside this plugin when applicable.
5. Create a superseding run or corrected release; do not rewrite completed evidence history.
6. Add a regression fixture and document the control change before resuming promotion.

