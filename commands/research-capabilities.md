---
description: Inspect and persist host capability availability before starting consequential research.
argument-hint: [--capability <name>] [--strict-capabilities]
model: inherit
---

# /research-capabilities

## Purpose

Determine whether the current host exposes capabilities required by a research contract. Capability preflight reports availability; it does not prove that host isolation or policy enforcement is correctly configured.

## Procedure

Run the standalone check before initialization when capability uncertainty would change architecture or safety:

```bash
python -B $CLAUDE_PLUGIN_ROOT/scripts/researchctl.py capabilities \
  [--capability <name>] [--strict-capabilities]
```

Repeat `--capability` for each required capability. During `init`, pass the same declarations so the decision is included in run metadata.

Use strict mode when a missing required capability must block execution. In non-strict mode, proceed only if the contract permits degradation and the limitation is explicit.

## Interpretation

Distinguish available, unavailable, undeclared, and host-unverifiable controls. A declared browser or filesystem capability does not establish network allowlists, credential isolation, sandboxing, encryption, or retention compliance.

## Output

Return requested capabilities, availability, warnings, strict-mode result, effect on architecture/scope, and the next safe command.

