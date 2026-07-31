# Evidence Research 2.0

Evidence Research is a research-agent plugin built around one invariant:

> **The task graph executes the research; the evidence graph remembers and verifies it.**

It replaces monolithic “research super-prompts” with a resumable, auditable pipeline. Research plans are explicit DAGs. Sources are treated as untrusted data. Claims are stored separately from evidence. Contradictions are retained rather than smoothed away. Final prose is rendered only after claim and citation gates pass.

## What it provides

- One user entrypoint: `/research <brief>`
- Two operational commands: `/research-resume <run-id>` and `/research-audit <run-id>`
- Nine focused skills with narrow trigger boundaries
- Five bounded agents with structured handoffs and one-writer ownership
- A canonical JSONL claim-evidence graph with stable IDs and provenance
- Resumable run state with legal state transitions and immutable completion
- Task-graph validation: cycle detection, fake-edge detection, parallel-level derivation
- Prompt-injection scanning and explicit untrusted-content boundaries
- Citation and report audits with measurable completion gates
- Offline verification and unit tests using only Python's standard library

## Quick start

```text
/research Compare the current evidence for two industrial inspection technologies. Prioritize primary sources, state the cutoff date, preserve disagreements, and produce an executive report with claim-level citations.
```

The orchestrator creates:

```text
research-runs/<run-id>/
├── run.json
├── task-graph.json
├── sources.jsonl
├── evidence-graph.jsonl
├── decisions.jsonl
├── report.md
└── audit.json
```

## Lifecycle

```text
SCOPED → PLANNED → ACQUIRING → EXTRACTING → RESOLVING
       → VERIFYING → SYNTHESIZING → AUDITING → COMPLETE
```

Any active state may move to `BLOCKED`; a blocked run may resume only to the state recorded in `resume_state`. `COMPLETE` is immutable. Corrections create a superseding run instead of rewriting history.

## Evidence model

The graph stores typed nodes such as `ResearchQuestion`, `Claim`, `EvidenceSpan`, `Source`, `Entity`, `Event`, `Method`, `Dataset`, `Finding`, and `ResearchGap`. Typed edges include `SUPPORTS`, `CONTRADICTS`, `QUALIFIES`, `ASSERTED_BY`, `DERIVED_FROM`, `ABOUT`, `SAME_AS`, `SUPERSEDES`, and `ANSWERS`.

Every evidentiary edge carries source identity, a locator, extraction time, and confidence rationale. A source URL by itself is not evidence; the graph must contain the exact span or structured field that supports the claim.

## Completion gates

A run is not complete until all of the following pass:

1. The task graph is acyclic and contains no dependency whose output is not consumed downstream.
2. Every report claim marker resolves to a graph `Claim` node.
3. Every factual report claim is `verified` or explicitly `contested`.
4. Every included claim has at least one supporting evidence edge; contested claims also expose contradictory evidence.
5. Every cited source exists in `sources.jsonl` and has provenance metadata.
6. Citation coverage and evidence coverage meet the thresholds in `run.json`.
7. The report contains limitations, unresolved gaps, and an as-of date.
8. `python -B verify.py` passes.

## Runtime requirements

- Python 3.10+
- A host capable of skills, commands, and subagents
- At least one read-only research surface: web search, files, connected repositories, scholarly databases, or NotebookLM

NotebookLM and Context7 are optional accelerators, not hard dependencies. The plugin degrades to available read-only sources and records capability gaps in the run audit.

## Verification

```bash
python -B verify.py
python -B scripts/researchctl.py demo /tmp/evidence-research-demo
python -B scripts/researchctl.py audit /tmp/evidence-research-demo
```

## Design provenance

The plugin incorporates the ontology-first and task-graph ideas from `codejunkie99/graph-engineering` under its MIT license, but does not import that repository as a runtime dependency. See `NOTICE` and `references/research-basis.md`.
