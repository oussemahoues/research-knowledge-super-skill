# Evidence Research v3 Documentation and Contract Review

## Review scope

- Branch: `upgrade-research-operations-docs`
- Surfaces: root agent contract, eight specialist agents, command guides, architecture/ADRs, references, and documentation regression tests
- Validation basis: `scripts/researchctl_v3.py` and shipped runtime modules for execution, acquisition, graph, retrieval, verification, synthesis, audit, migration, benchmark, and release
- Review objective: ensure prose is operational, internally consistent, explicit about failure/recovery, and no stronger than implemented behavior

## Severity model

- `P1`: false canonical/security/release claim that can cause integrity loss or unsafe promotion.
- `P2`: material correctness, audit, provenance, or operational gap that can produce a false conclusion or false pass.
- `P3`: bounded completeness, usability, or maintainability gap.

## Closed documentation findings

### DC-01: References restored v2 JSONL canonical-state semantics - P1 - Closed

**Evidence:** `references/architecture.md` described `sources.jsonl`, `evidence-graph.jsonl`, and `decisions.jsonl` as canonical, contradicting v3 `state.db` and the event store.

**Impact:** Operators could reconstruct or mutate state from incomplete exports, causing duplicate work and false completion.

**Resolution:** Replaced the architecture reference with a canonical-state and artifact-role matrix grounded in `EventStore` and `DurableExecutor`. Added a regression assertion that rejects the stale v2 sentence.

### DC-02: Security reference pointed to the fallback-engine scanner - P2 - Closed

**Evidence:** `references/security.md` directed v3 operators to `lib/injection_guard.py` instead of `src/evidence_research/acquisition/source_episodes.py` and `security.py`.

**Impact:** The guide omitted v3 normalized/decoded views, multilingual/fragmented patterns, episode quarantine, and sensitive-data classification.

**Resolution:** Rewrote the security model around the v3 acquisition path and explicitly labeled the `lib/` scanner as v2 fallback behavior.

### DC-03: Retrieval ADR claimed an unimplemented semantic method - P2 - Closed

**Evidence:** ADR 0004 listed semantic retrieval, while `HybridRetriever` implements lexical, neighborhood, path, temporal, community, and gap methods only.

**Impact:** Capability and evaluation claims could misrepresent retrieval coverage.

**Resolution:** ADR 0004 and the implementation-status matrix now state that no vector/learned semantic retriever is shipped. Future adapters require an ADR, benchmarks, provenance, and capability controls.

### DC-04: Audit documentation collapsed completion, report, and release gates - P2 - Closed

**Evidence:** The auditor contract claimed that the run-completion audit performs report marker and release checks that `audit_run` does not call.

**Impact:** A passing `audit.json` could be reported as report-valid or release-eligible without those checks running.

**Resolution:** Rewrote the auditor and `/research-audit` contracts into separate completion, report, migration, and release gates. The guide requires `checked` status and evidence for each gate.

### DC-05: `/research-audit` was a three-line routing stub - P2 - Closed

**Evidence:** The command contained only a skill pointer, one CLI invocation, and one boundary sentence.

**Impact:** It did not define preconditions, actual checks, limitations, result interpretation, remediation ownership, or reproducibility.

**Resolution:** Expanded the command into an executable operating contract with structured output and explicit non-goals.

### DC-06: Material CLI gates lacked command contracts - P3 - Closed

**Evidence:** `verify-claim`, `capabilities`, and `migrate-v2` existed in the CLI but had no corresponding command guide.

**Impact:** Operators had to read Python to discover consequential status/exit semantics and migration limitations.

**Resolution:** Added `/research-verify`, `/research-capabilities`, and `/research-migrate` guides.

### DC-07: ADRs were decision blurbs without verification or failure semantics - P3 - Closed

**Evidence:** ADRs 0001-0005 ranged from roughly 400 to 760 characters and omitted alternatives, invariants, failure modes, and verification.

**Impact:** Architecture changes could not be reviewed against enforceable consequences.

**Resolution:** Expanded all five ADRs and added minimum-section/size regression checks.

## Open runtime findings exposed by documentation validation

### RC-01: Completion audit does not invoke report-marker validation - P2 - Open

**Evidence:** `cmd_audit` calls `audit_run`; `cmd_render` separately calls `audit_rendered_report`.

**Risk:** A run can pass completion while a required report is missing, stale, or has unresolved markers.

**Recommended enhancement:** Add an explicit audit policy flag or required-artifact contract. When a report is required, invoke marker validation from completion audit without rewriting the report. Add tests for missing, stale, malformed, cross-run, quarantined, and non-publishable markers.

### RC-02: Rejected material Claims do not fail the built-in completion audit - P2 - Open

**Evidence:** `audit_run` fails missing and `needs_review` adjudications but does not fail `rejected` material Claims.

**Risk:** A run may pass even though a material acceptance question has no usable support, unless task/report policy catches it separately.

**Recommended enhancement:** Add contract-level policy for allowed terminal Claim states and required question coverage. Default consequential runs to fail rejected material Claims unless explicitly accepted as an answered negative/gap with rationale.

### RC-03: Numerical consistency is token-presence, not dimensional validation - P2 - Open

**Evidence:** `EvidenceChainVerifier` checks whether numeric tokens from the Claim occur in supporting evidence.

**Risk:** Unit, currency, denominator, period, interval, percentage-point, and adjusted/unadjusted mismatches can pass the deterministic numeric check.

**Recommended enhancement:** Parse normalized quantities with units, denominators, currencies, time bases, ranges, and tolerances. Keep model review separate and benchmark adversarial numeric cases.

### RC-04: Lexical overlap is insufficient for semantic entailment - P2 - Open/controlled

**Evidence:** The verifier uses word-set overlap and flags low signal for model review.

**Risk:** Negation, modality, causal direction, population, exception, and scope mismatches can share vocabulary.

**Recommended enhancement:** Add an optional calibrated semantic adjudicator behind an explicit capability, preserve deterministic blockers, store evaluator/version/prompt/result, and benchmark false-positive/false-negative rates. Do not silently upgrade Claims.

### RC-05: Injection detection remains pattern-based - P3 - Open/accepted limitation

**Evidence:** Acquisition scans original and transformed views using regex patterns.

**Risk:** Novel or context-dependent attacks may evade detection; benign text may be quarantined.

**Recommended enhancement:** Continue layered least privilege and quarantine; expand fixtures from incidents; consider a separately sandboxed classifier only after calibration. Never treat classifier pass as trust.

### RC-06: Local SQLite is not multi-host coordination - P3 - Open/accepted limitation

**Evidence:** The canonical store uses local SQLite WAL and filesystem source bytes.

**Risk:** Uncoordinated hosts or live database copies can violate locking and artifact assumptions.

**Recommended enhancement:** Document deployment ownership and, if remote execution is needed, define an adapter conformance suite for transaction, lease, event, and idempotency semantics before claiming support.

### RC-07: Raw immutable episodes require deployment privacy controls - P3 - Open/accepted limitation

**Evidence:** Sensitive classes are recorded and derived excerpts are redacted, but authorized raw bytes remain content-addressed on disk.

**Risk:** Retention, access, backup, deletion, and jurisdictional obligations remain outside the runtime.

**Recommended enhancement:** Add deployment profiles for encryption, permissions, retention, secure deletion/tombstone policy, and backup handling. Do not weaken integrity silently.

## Validation performed

- Compared every upgraded statement with the relevant CLI function and runtime API.
- Added `tests/test_documentation_quality.py` with six checks covering required sections, anti-stub size floors, canonical-state semantics, current security paths, implemented retrieval boundaries, audit-gate separation, and command coverage.
- Ran the new suite locally: six tests passed.
- Confirmed the remote branch contains the consolidated commit and remains based directly on current `main` with zero commits behind at validation time.

## Residual validation gap

The full repository suite and Python 3.10-3.13 matrix have not run for this branch because no PR exists and the workspace cannot clone GitHub through its network boundary. The change is documentation plus one unittest module, but full CI remains required before merge.

## Verdict

The upgraded documentation is materially more comprehensive and accurately bounded to shipped v3 behavior. Documentation findings DC-01 through DC-07 are closed. Runtime findings RC-01 through RC-07 remain explicit backlog or accepted limitations and must not be reported as fixed by this branch.

