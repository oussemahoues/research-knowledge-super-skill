# Evaluation, Completion, and Release Gates

## Purpose

Evaluation has three layers that must not be collapsed: deterministic run completion, report traceability, and repository release qualification. Passing one layer does not imply the others passed.

## Layer 1: deterministic run-completion audit

`python -B scripts/researchctl.py audit <run>` executes `audit_run` and writes a derived `audit.json`. The shipped audit checks:

- every registered task is `SUCCEEDED`;
- task dependencies reference existing tasks and carry a real artifact intersection;
- a verification task does not share ownership with the parent output it verifies;
- no human interrupt remains open;
- every material Claim has a latest adjudication;
- no material Claim remains `needs_review`;
- every source episode used by a graph edge exists;
- used source bytes still match their SHA-256 hash;
- no quarantined source episode is used by the graph;
- legacy-unverified episodes and unresolved fusion reviews remain visible as warnings.

The result contains `passed`, sorted errors/warnings, and counts for tasks, claims, adjudications, source episodes, quarantined/tampered sources, legacy sources, and fusion reviews.

### Important limitation

The current run audit does not itself parse `report.md`, verify marker resolution, recompute citation entailment, prove semantic correctness, or run release benchmarks. Those are separate gates below. A document or agent must not describe them as part of `audit_run` until the implementation changes.

## Layer 2: claim and report validation

### Claim adjudication

`verify-claim` evaluates the active evidence chain for one Claim. It checks support/contradiction edges, source independence groups, quarantined episodes, numeric token consistency, and a deterministic lexical-overlap signal.

Statuses mean:

- `verified`: configured deterministic conditions passed and no material contradiction is present;
- `contested`: support and contradiction are both present;
- `needs_review`: support exists but one or more deterministic conditions remain unresolved;
- `rejected`: no usable support edge exists.

Lexical overlap is triage, not semantic entailment. `requires_model_review=true` identifies a case needing separately recorded review; it is not an automatic upgrade.

### Report marker audit

`researchctl render` writes the report atomically and immediately invokes `audit_rendered_report`. Publishability requires every included Claim, evidence Edge, and source Episode marker to resolve to current canonical records and to obey adjudication/quarantine rules.

Run completion should be reported together with report-marker status when a report is a required deliverable. Until the completion auditor calls the marker audit directly, operators must run both commands explicitly.

## Layer 3: release qualification

A release candidate requires all of the following evidence:

1. Python 3.10-3.13 development verification.
2. Fixed 100-case v3 benchmark results.
3. Comparison with protected v2 critical metrics and promotion thresholds.
4. Security, hostile-source, capability, replay, recovery, and fault tests.
5. Non-destructive migration and v2 fallback evidence.
6. Deterministic `MANIFEST.json` generation in a clean checkout.
7. `python -B verify.py --release` with no missing, modified, or extra shipped files.
8. Architecture and security review findings resolved or explicitly accepted at the permitted severity.
9. Explicit final human approval.

No run-level approval or successful benchmark substitutes for the final human release gate.

## Metrics and denominators

Every reported rate must name its denominator, sampling method, and treatment of contested/legacy records.

| Metric | Definition | Required interpretation |
|---|---|---|
| Task completion | succeeded required tasks / required tasks | Must equal 1.00 for completion |
| Adjudication coverage | material Claims with latest decisions / material Claims | Must equal 1.00 |
| Publishable-claim coverage | verified or contested material Claims / material Claims | Report rejected/omitted claims separately |
| Marker resolvability | valid claim/edge/episode markers / emitted markers | Must equal 1.00 for a publishable report |
| Independent corroboration | Claims meeting configured independence count / Claims requiring it | Count independence groups, not URLs |
| Quarantine leakage | used quarantined episodes / used episodes | Must equal 0 |
| Integrity failure | used episodes failing byte verification / used episodes | Must equal 0 |
| Contradiction exposure | contested Claims visibly rendered with both sides / rendered contested Claims | Must equal 1.00 |

Do not report citation entailment as measured unless a named evaluator actually performed the semantic check. The built-in lexical signal is not citation entailment.

## Threshold governance

Run-specific thresholds may be stricter than defaults. A lowering must be explicit in the contract or persisted decision, justified, attributable, and visible in the final limitations. It cannot waive quarantine, integrity, provenance, independence, or human-release requirements.

## Reproducibility record

An evaluation record should include run ID, commit/ref, engine version, contract hash, as-of time, command versions, random seed when relevant, corpus/fixture hashes, exact commands, timestamps, result hashes, environment limitations, and the identity of the reviewer or approving human.

