from __future__ import annotations

import re

QUERY_CLASSES = {
    "direct", "entity-local", "multi-hop-path", "comparative",
    "temporal", "global-theme", "causal-event", "evidence-gap",
}
TOKEN_RE = re.compile(r"[A-Za-z0-9_:-]+")


def tokens(value: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(value)]


def classify_query(query: str, *, entity_count: int = 0, existing_graph: bool = True) -> str:
    text = query.lower()
    if re.search(r"\b(missing|gap|unsupported|insufficient evidence|unknown)\b", text):
        return "evidence-gap"
    if re.search(r"\b(when|as of|at the time|before|after|historical|changed|latest|current)\b", text):
        return "temporal"
    if re.search(r"\b(cause|caused|causal|led to|triggered|why did|what led)\b", text):
        return "causal-event"
    if re.search(r"\b(compare|versus|vs\.?|difference|similarities)\b", text):
        return "comparative"
    if entity_count >= 2 or re.search(r"\b(path|connected|relationship between|how .* relate)\b", text):
        return "multi-hop-path"
    if re.search(r"\b(theme|overview|landscape|big picture|cluster|community|trend)\b", text):
        return "global-theme"
    if entity_count == 1:
        return "entity-local"
    return "direct" if existing_graph else "entity-local"
