# Research basis

The architecture was checked against the following primary or authoritative sources before implementation:

- Anthropic, “How we built our multi-agent research system,” 2025-06-13. Orchestrator-worker research, bounded parallelism, separate citation processing, and evaluation lessons.
  https://www.anthropic.com/engineering/multi-agent-research-system
- Google Research, “Towards a science of scaling agent systems,” 2026-01-28. Controlled evidence that multi-agent coordination helps decomposable work and can degrade sequential work.
  https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/
- OpenAI, “Deep research system card,” 2025-02-25. Multi-step browsing risks including prompt injection, privacy, hallucination, and code execution.
  https://openai.com/index/deep-research-system-card/
- Microsoft Research, Project GraphRAG. Graph-based retrieval and community/local search patterns for complex corpora.
  https://www.microsoft.com/en-us/research/project/graphrag/overview/
- NIST, “On the Evaluation of Machine-Generated Reports,” SIGIR 2024. Completeness, accuracy, and claim-to-source citation evaluation.
  https://www.nist.gov/publications/evaluation-machine-generated-reports
- OWASP, RAG Security Cheat Sheet and LLM01 Prompt Injection. Retrieved content must be treated as untrusted and delimited from instructions.
  https://cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html
  https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- codejunkie99/graph-engineering, MIT, 2026-07-23. Ontology-first knowledge graph pipeline and task-graph framing.
  https://github.com/codejunkie99/graph-engineering

The plugin deliberately avoids depending on any one model, provider, search engine, graph database, or citation verifier. Verification instruments must be named and calibrated because different verifiers can produce materially different unsupported-citation rates.
