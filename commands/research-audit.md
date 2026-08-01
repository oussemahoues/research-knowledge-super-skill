---
description: Run and interpret the deterministic v3 completion audit without repairing the run under audit.
argument-hint: <run-path> [--with-report-check]
model: inherit
---

# /research-audit

## Purpose

Evaluate persisted run-completion gates and save `audit.json`. A failed audit is a valid, reproducible result. This command does not acquire evidence, retry tasks, resolve interrupts, adjudicate Claims, or repair the report.

## Preconditions

Require an existing v3 run directory containing a readable `run.json` locator and `state.db`. Resolve the run ID from canonical state. Do not audit a report directory, JSONL export, or chat transcript as if it were a run.

The auditor must be independent from material task, evidence, adjudication, and report writers. Running the CLI writes only the derived `audit.json`; it must not mutate canonical research state.

## Procedure

1. Read `${CLAUDE_PLUGIN_ROOT}/skills/auditing-research-run/SKILL.md`.
2. Inspect the run first:

```bash
python -B ${CLAUDE_PLUGIN_ROOT}/scripts/researchctl.py inspect <run-path>
```

3. Record run ID/status, task counts, open interrupts, latest checkpoint, and any obvious locator/database inconsistency.
4. Run the deterministic completion audit:

```bash
python -B ${CLAUDE_PLUGIN_ROOT}/scripts/researchctl.py audit <run-path>
```

5. Preserve the command exit code and returned JSON. Confirm `audit.json` contains the same run ID, pass/fail result, errors, warnings, metrics, and timestamp.
6. Classify every error by remediation owner without fixing it during this audit.
7. When a report is part of the deliverable, perform the separate report gate. The shipped `audit_run` does not parse report markers:

```bash
python -B ${CLAUDE_PLUGIN_ROOT}/scripts/researchctl.py render <run-path>
```

Use an authorized existing output path/title/as-of configuration when supplied. If rerendering would overwrite an externally edited deliverable, stop and run the marker-audit API in a controlled workflow instead of destroying user work.

## What the completion audit checks

- all registered tasks succeeded;
- dependencies reference real artifact flow;
- verification ownership is separated from the producer being verified;
- no human interrupt remains open;
- each material Claim has a latest adjudication and none remains `needs_review`;
- used source episodes exist, pass byte integrity, and are not quarantined;
- legacy-unverified provenance and unresolved entity-fusion reviews remain visible.

## What it does not check

- semantic truth or full citation entailment;
- report marker resolution unless the separate render/marker gate is run;
- benchmark or v2 promotion thresholds;
- Python-version CI matrix;
- migration/fallback behavior;
- repository manifest completeness or release seal;
- architecture/security review closure;
- final human release approval.

Never report release eligibility from `audit_run` alone.

## Result interpretation

`passed=true` means the implemented deterministic completion errors are empty. Warnings remain material limitations and must be surfaced. A `contested` adjudication is publishable only with contradiction preserved; a passing run does not convert it to verified.

The current audit treats only missing and `needs_review` material adjudications as completion errors. If policy requires rejected material Claims to block completion, enforce that in the research contract or an additional gate and record the limitation; do not imply the built-in audit already does so.

## Failure handling

- Unknown run or missing/corrupt database: data-integrity block; do not initialize a replacement in place.
- Nonzero audit exit: preserve `audit.json` and report the exact errors.
- Missing/tampered episode: evidence-curator/storage owner investigates; dependent Claims must be re-adjudicated after repair in a superseding workflow.
- Incomplete task or open interrupt: research-orchestrator owns remediation.
- Missing/needs-review adjudication: claim-verifier owns remediation.
- Broken report marker: synthesis-editor or evidence owner repairs canonical inputs, then rerenders.
- Ambiguous command outcome: inspect the file/run state before retry; rerunning the deterministic audit is safe when inputs are unchanged.

## Output

Return:

```json
{
  "schema_version": "3.0",
  "run_id": "run:...",
  "completion_audit": {
    "passed": false,
    "errors": [],
    "warnings": [],
    "metrics": {},
    "audit_path": ".../audit.json"
  },
  "report_gate": {
    "required": true,
    "checked": false,
    "passed": null,
    "errors": []
  },
  "release_gate": {
    "checked": false,
    "eligible": false,
    "missing_evidence": []
  },
  "remediation": [],
  "next_action": "..."
}
```

Keep observed tool output distinct from policy inferences. Never suppress warnings or mark an unchecked gate as passed.

