# Research Basis and Claim-to-Source Map

## Purpose

This file records design provenance and the limits of what external references justify. A source can motivate a design choice without proving that the local implementation is correct. Shipped behavior is validated by repository code, tests, benchmarks, and audits.

## External basis

| Source | Design area informed | What it does not establish |
|---|---|---|
| Anthropic, “How we built our multi-agent research system” (2025-06-13) | Orchestrator-worker research, bounded parallelism, separate citation work, evaluation lessons | Correctness of this runtime, optimal topology for every task, or provider independence |
| Google Research, “Towards a science of scaling agent systems” (2026-01-28) | Multi-agent gains for decomposable work and degradation for sequential work | That more agents are always better or that the local architecture selector is universally optimal |
| OpenAI, “Deep research system card” (2025-02-25) | Browsing risks including prompt injection, privacy, hallucination, and code execution | That the local scanner eliminates those risks |
| Microsoft Research, Project GraphRAG | Graph-local/global retrieval patterns for complex corpora | That v3 ships Microsoft GraphRAG, vector retrieval, or an external graph backend |
| NIST, “On the Evaluation of Machine-Generated Reports” (SIGIR 2024) | Claim-to-source evaluation, completeness, and report accuracy framing | That lexical overlap is semantic citation entailment |
| OWASP RAG Security Cheat Sheet and LLM01 Prompt Injection | Untrusted-content boundaries, least privilege, and injection controls | That pattern matching proves hostile content is absent |
| `codejunkie99/graph-engineering` (MIT, 2026-07-23) | Ontology-first pipeline and task-graph framing | Runtime dependency, code identity, or endorsement of this implementation |

## Primary links

- https://www.anthropic.com/engineering/multi-agent-research-system
- https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/
- https://openai.com/index/deep-research-system-card/
- https://www.microsoft.com/en-us/research/project/graphrag/overview/
- https://www.nist.gov/publications/evaluation-machine-generated-reports
- https://cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html
- https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- https://github.com/codejunkie99/graph-engineering

## Local validation required

External literature motivates these hypotheses; repository evidence must validate them:

- adaptive topology improves or preserves protected benchmark metrics;
- real artifact dependencies prevent fake DAG parallelism;
- event/idempotency design survives replay and stale-lease recovery;
- immutable episodes preserve version and integrity semantics;
- quarantine and redaction controls resist the shipped hostile fixtures;
- bitemporal queries reconstruct validity correctly;
- fusion is conservative and reversible;
- retrieval is bounded and returns reproducible traces;
- adjudication and report markers expose unsupported or contested Claims;
- migration and fallback do not destroy v2 runs;
- the release manifest covers every shipped file.

## Evidence discipline

Technical claims about external systems must be checked against current primary documentation before use. Date-sensitive sources must record retrieval and effective dates. Quotations, benchmarks, and comparative claims require exact locators and scope.

Model/provider neutrality means the plugin has no mandatory provider dependency. It does not mean every host supplies equivalent tools, isolation, retrieval quality, or model judgment. Capability decisions and evaluation instruments must be named because different systems can produce materially different results.

## Provenance boundary

The project incorporates concepts, not runtime code, from `codejunkie99/graph-engineering` under MIT. `NOTICE` and the license record that provenance. Any future imported code, dataset, fixture, or prompt requires its own license and attribution review.

