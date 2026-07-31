---
name: resolving-research-entities
description: Resolve duplicate entities, source versions, aliases, and repeated claims in an evidence graph using reversible blocking, matching, and merge decisions. Use after extraction, during graph hygiene, or when broken multi-hop paths indicate duplicate identities. Do not silently overwrite conflicts, merge solely on name similarity, or adjudicate the truth of claims.
---

# Resolve Research Entities

1. Block candidates by compatible type and normalized keys; never compare every pair at scale.
2. Score candidates using names/aliases, stable attributes, source identifiers, and graph neighborhoods.
3. Auto-reject low scores. Queue ambiguous cases. Auto-merge only above the configured high threshold.
4. Prefer false negatives over false-positive merges when identity is uncertain.
5. Preserve all aliases, source-specific attributes, and conflicting values with provenance.
6. Record every merge in `decisions.jsonl` with score components, rationale, `merged_from`, canonical ID, and reversal data.
7. Add `SAME_AS` or `SUPERSEDES` edges as appropriate. Never delete original records from the append-only log.
8. Run graph validation and report duplicate-rate estimates and unresolved identity clusters.
