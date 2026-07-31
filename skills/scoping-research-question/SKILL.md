---
name: scoping-research-question
description: Convert an ambiguous or broad research request into an executable research contract with atomic questions, explicit exclusions, timeframe, source constraints, volatility, risk, and measurable completion criteria. Use at the start of substantive research or when a run's target has drifted. Do not acquire sources, answer the research question, or design a multi-agent topology.
---

# Scope the Research Question

1. Restate the target as one outcome sentence.
2. Split it into atomic research questions and label each as descriptive, comparative, causal, predictive, normative, or verification.
3. Define scope boundaries, excluded topics, audience, as-of date, geography, and required output.
4. Classify volatility and consequence. Current or high-consequence claims require primary and recent sources.
5. Define acceptance criteria that can be tested against artifacts, including required sections, source tiers, citation coverage, and uncertainty treatment.
6. List assumptions explicitly. Use reasonable defaults when optional information is absent; mark them as assumptions instead of stopping.
7. Emit a `research_contract` JSON object conforming to `schemas/research-run.schema.json` fields used by `run.json`.

Do not phrase completion as “comprehensive” or “high quality.” Use measurable conditions.
