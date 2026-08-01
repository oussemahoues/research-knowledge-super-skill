# ADR 0004: Query-adaptive hybrid retrieval

## Decision

Classify each query before retrieval and combine only the necessary lexical, semantic, path, temporal, and community retrieval methods. Return evidence chains and retrieval traces, not unstructured context dumps.

## Query classes

`direct`, `entity-local`, `multi-hop-path`, `comparative`, `temporal`, `global-theme`, `causal-event`, and `evidence-gap`.
