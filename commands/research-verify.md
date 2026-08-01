---
description: Independently adjudicate one atomic Claim against its active v3 evidence chain.
argument-hint: <run-path> <claim-id> [--as-of <timestamp>] [--independent-sources <n>]
model: inherit
---

# /research-verify

## Purpose

Run the deterministic Claim verifier and persist an adjudication. This is not a search command, a report rewrite, or proof of semantic truth.

## Preconditions

Require an existing v3 run, a `Claim` node ID, an independent verifier, and a defensible independence threshold. Supply `--as-of` for historically scoped Claims.

## Procedure

1. Inspect the Claim text and active `SUPPORTS`, `CONTRADICTS`, and `QUALIFIES` edges.
2. Confirm every evidence span and source episode resolves and that the verifier did not write the evidence being judged.
3. Run:

```bash
python -B $CLAUDE_PLUGIN_ROOT/scripts/researchctl.py verify-claim \
  <run-path> <claim-id> [--as-of <timestamp>] \
  [--independent-sources <n>]
```

4. Preserve the exit code. `verified` and `contested` return success; `needs_review` and `rejected` return nonzero without implying a runtime failure.
5. Report status, support/contradiction edge IDs, episode IDs, independence groups, lexical signal, numeric consistency, issues, model-review flag, and decision ID.

## Interpretation

Lexical overlap is a deterministic triage signal, not semantic entailment. Numeric consistency only checks that Claim numbers appear in supporting spans; it does not validate units, denominators, or causal interpretation by itself. A contradiction produces `contested`, not an averaged consensus.

`requires_model_review=true` requires a separately recorded review path. It cannot erase quarantine, missing provenance, insufficient independence, numeric mismatch, or material contradiction.

## Failure handling

Unknown Claim is an input/data error. Missing support normally yields `rejected`; insufficient independence or low signal yields `needs_review`. Tool/auth failures do not upgrade or delete the previous adjudication.

## Output

Return the raw verifier result plus a concise explanation of publishability, unresolved issues, time basis, and the owning next action.

