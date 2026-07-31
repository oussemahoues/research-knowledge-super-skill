from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from typing import Any


def normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-zA-Z0-9]+", " ", value).lower()
    return " ".join(value.split())


def tokens(value: str) -> set[str]:
    return set(normalize_name(value).split())


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b) if a | b else 0.0


@dataclass(frozen=True)
class MatchScore:
    string: float
    aliases: float
    identifiers: float
    attributes: float
    neighborhood: float
    total: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def _best_alias_similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
    left_names = [left.get("name", ""), *left.get("aliases", [])]
    right_names = [right.get("name", ""), *right.get("aliases", [])]
    best = 0.0
    for a in left_names:
        for b in right_names:
            best = max(best, SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio())
    return best


def score_pair(left: dict[str, Any], right: dict[str, Any]) -> MatchScore:
    if left.get("entity_type") != right.get("entity_type"):
        return MatchScore(0, 0, 0, 0, 0, 0)
    string = SequenceMatcher(None, normalize_name(left.get("name", "")), normalize_name(right.get("name", ""))).ratio()
    aliases = _best_alias_similarity(left, right)
    li, ri = left.get("identifiers", {}), right.get("identifiers", {})
    common_id_keys = set(li) & set(ri)
    identifiers = 1.0 if any(li[k] == ri[k] for k in common_id_keys) else 0.0
    la, ra = left.get("attributes", {}), right.get("attributes", {})
    common_attrs = set(la) & set(ra)
    attributes = (sum(1 for k in common_attrs if la[k] == ra[k]) / len(common_attrs)) if common_attrs else 0.0
    neighborhood = jaccard(set(left.get("neighbors", [])), set(right.get("neighbors", [])))
    total = 0.25 * string + 0.20 * aliases + 0.30 * identifiers + 0.10 * attributes + 0.15 * neighborhood
    return MatchScore(string, aliases, identifiers, attributes, neighborhood, round(total, 6))


def decision(score: MatchScore, *, merge_at: float = 0.90, review_at: float = 0.65) -> str:
    if score.total >= merge_at:
        return "auto_merge"
    if score.total >= review_at:
        return "review"
    return "reject"


def reversible_merge_record(canonical_id: str, merged_id: str, score: MatchScore, rationale: str) -> dict[str, Any]:
    return {
        "decision_type": "entity_merge",
        "canonical_id": canonical_id,
        "merged_from": [merged_id],
        "score": score.to_dict(),
        "rationale": rationale,
        "reversal": {"restore_id": merged_id, "remove_alias_from": canonical_id},
    }
