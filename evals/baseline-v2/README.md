# v2 Baseline Contract

This directory fixes the control cohort for v3 evaluation.

Required corpus categories:

- 30 conventional research questions
- 20 multi-hop questions
- 15 temporal-change questions
- 10 conflicting-source cases
- 10 entity-resolution cases
- 5 ontology-drift cases
- 10 prompt-injection cases

Required metrics:

- claim-to-evidence coverage
- citation resolvability and entailment
- unsupported material claims
- contested-claim disclosure
- entity-resolution precision
- temporal validity accuracy
- multi-hop Recall@10
- resume and idempotency correctness
- latency, tool calls, source count, and model cost
- successful injection count

Populate immutable fixture inputs and expected judgments before tuning v3 against them.
