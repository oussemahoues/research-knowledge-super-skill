# ADR 0005: Untrusted Source and Least-Authority Boundaries

- Status: accepted and implemented with deployment responsibilities
- Decision owners: security architecture
- Affects: acquisition, agent tools, graph writes, verification, reporting, release

## Context

Research systems ingest arbitrary attacker-controlled text and files. Source content can attempt to override instructions, request credentials/tools, exfiltrate context, exploit encodings, or persist sensitive material. Tool-capable agents and long-running retries increase impact unless authority and writes are narrowly bounded.

## Decision

Treat all retrieved bytes, metadata, tool output, citations, and agent messages as untrusted data. Source content never enters the authority chain. Separate discovery, canonical writing, adjudication, synthesis, and audit roles; grant only the tools required by each role.

At acquisition, hash and store immutable bytes, scan multiple normalized/decoded views, classify sensitive data, redact derived excerpts, and quarantine high-risk episodes. Quarantined or integrity-failing episodes cannot qualify as evidence or pass completion when used.

Persist high-consequence and breaking-schema decisions as scoped interrupts requiring attributable approval. Bound resources and recover external side effects by idempotency reconciliation.

## Trust zones

1. **Authority zone**: platform/user instructions, repository policy, scoped contract, persisted approvals.
2. **Control zone**: runtime APIs and registered task inputs.
3. **Untrusted acquisition zone**: pages, files, bytes, metadata, citations, search/tool output.
4. **Derived evidence zone**: validated nodes/edges linked to eligible episodes.
5. **Presentation zone**: reports/exports that remain non-canonical and require marker validation.

Data can move inward only through the specified validators. Content never moves upward into authority.

## Role controls

- Source scout: read-only discovery; no canonical writes or delegation.
- Evidence curator: canonical acquisition/graph APIs; no browsing or adjudication.
- Claim verifier: independent decision writer; cannot rewrite evidence.
- Synthesis editor: deterministic report output; cannot acquire or change decisions.
- Independent auditor: evaluates persisted state and derived artifacts without repairing the work under audit.
- Orchestrator: coordinates registered tasks and interrupts; cannot self-approve or substitute orchestration metadata for evidence.

## Content controls

The v3 scanner checks original, Unicode-normalized, compacted, and supported percent/base64/hex decoded views for direct, fragmented, multilingual, homoglyph, credential, execution, authority, and exfiltration patterns. Findings and redacted excerpts are persisted for audit.

Detection is advisory at low/medium risk and exclusionary at quarantine. It is not a proof of safety. Decoding is bounded and never treated as an instruction to execute.

## Sensitive-data policy

Minimize acquisition. Authorized raw bytes remain immutable for integrity, which creates retention risk. Redact secrets and personal/sensitive values from metadata, findings, event payloads, prompts, logs, and reports. Deployment owners provide access control, encryption, backup, retention, and lawful deletion processes.

## Alternatives considered

### Trust authoritative domains

Rejected because trusted sites can be compromised and legitimate documents can contain instruction-like text.

### Sanitize and discard originals

Rejected because it destroys reproducibility and forensic evidence. Preserve originals under access controls and keep redacted derivatives separate.

### Give every agent all tools

Rejected because it expands blast radius and blurs ownership.

### Pattern scanning as complete defense

Rejected. Scanning is one control alongside least privilege, provenance, isolation, approval, integrity checks, and audits.

## Failure and incident handling

- High-risk pattern: quarantine episode and block evidentiary use.
- Sensitive finding: redact derivatives; assess whether raw-byte retention is authorized.
- Hash mismatch/missing bytes: block dependent evidence and investigate tampering/storage failure.
- Ambiguous external action: reconcile by idempotency key before retry.
- Capability missing in strict mode: block initialization.
- Suspected credential/context exposure: stop affected work, preserve audit evidence, revoke externally, and add a regression fixture.

## Verification

Release tests cover direct/fragmented/multilingual/homoglyph and encoded injection fixtures, credential/context/data exfiltration patterns, sensitive-data redaction, source integrity, quarantine leakage, role contracts, capability preflight, bounded retries, migration provenance, and complete release sealing.

## Deployment requirements

The plugin cannot guarantee OS/process isolation by prose. Operators must configure filesystem permissions, network egress, credential injection, subprocess policy, secure deletion/retention, backups, and concurrency appropriate to the environment. Capability declarations must reflect enforced reality.

## Consequences and limitations

The design reduces authority confusion and makes hostile evidence auditable. It can generate false positives and false negatives, retains authorized raw bytes, and depends on deployment controls outside the repository. Security reviews must be reopened when input formats, decoders, tools, adapters, permissions, or release contents change.

