from __future__ import annotations

import math
from collections import Counter
from typing import Any

from .query import tokens


def lexical_rank(rows: list[Any], query: str, *, limit: int = 20) -> list[tuple[str, float]]:
    query_terms = tokens(query)
    if not query_terms:
        return []
    documents = {row["node_id"]: tokens(row["node_type"] + " " + row["data_json"]) for row in rows}
    if not documents:
        return []
    document_frequency: Counter[str] = Counter()
    for terms in documents.values():
        for term in set(terms):
            document_frequency[term] += 1
    average_length = sum(len(terms) for terms in documents.values()) / len(documents)
    scores: list[tuple[str, float]] = []
    for node_id, terms in documents.items():
        counts = Counter(terms)
        score = 0.0
        for term in query_terms:
            frequency = counts[term]
            if not frequency:
                continue
            inverse = math.log(1 + (len(documents) - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5))
            denominator = frequency + 1.2 * (0.25 + 0.75 * len(terms) / max(average_length, 1))
            score += inverse * frequency * 2.2 / denominator
        if score > 0:
            scores.append((node_id, round(score, 6)))
    return sorted(scores, key=lambda item: (-item[1], item[0]))[:limit]
