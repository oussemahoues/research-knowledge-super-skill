---
name: running-evidence-research
description: Orchestrate a complete, resumable, evidence-first research run from a complex question to an audited cited report. Use when the user asks for deep research, a comprehensive investigation, an evidence-backed report, competitive or technical research, literature synthesis, due diligence, multi-source comparison, or to resume an existing research run. Coordinates focused skills and agents; does not replace their stage-specific logic. Do not use for quick factual lookups, ordinary web search, simple summaries, or requests that only need one known source.
---

# Run Evidence Research

## Inputs

- `mode`: `start` or `resume`
- `brief`: target, scope, constraints, as-of date, and deliverable
- `run_path` for resume

## Procedure

1. In `start` mode, invoke `scoping-research-question`. Create `run.json` only after the target and measurable acceptance criteria are explicit. Infer reasonable defaults rather than blocking on optional details.
2. Initialize the run with `python -B ${CLAUDE_PLUGIN_ROOT}/scripts/researchctl.py init --brief-file <file> --root research-runs`.
3. Invoke `planning-research-task-graph`. Validate the resulting graph with `researchctl.py validate-task-graph` before delegating.
4. Execute tasks by DAG level. Parallelize only tasks in the same level with no shared write target. Enforce each task's source, tool-call, and child-agent budgets.
5. Route acquisition tasks to `acquiring-research-sources`; persist accepted source records through the evidence curator.
6. Route extraction to `extracting-claim-evidence`, then entity resolution to `resolving-research-entities`.
7. Route material claims to `adjudicating-research-claims` in a context separate from extraction. Add targeted acquisition tasks only for explicit evidence gaps.
8. Invoke `synthesizing-cited-research` only after material claims are verified, contested, rejected, or marked unknown.
9. Transition to `AUDITING`; invoke `auditing-research-run`.
10. Mark `COMPLETE` only when `audit.json` has `passed: true`. Otherwise transition to `BLOCKED`, record failing gates and `resume_state`, and stop without claiming completion.

## Resume

Validate existing files, hashes, and legal state. Never repeat completed tasks unless their inputs changed. Re-run downstream tasks when an upstream artifact hash changed. Preserve prior decisions and append superseding records.

## Output

Return the run path, final state, report path, audit path, acceptance-criteria results, unresolved gaps, and any capability limitation.
