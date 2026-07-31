from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
from typing import Any

TIER_BASE = {"A": 4.0, "B": 3.0, "C": 1.5, "D": 0.0}


@dataclass(frozen=True)
class SourceAssessment:
    authority: float
    freshness: float
    provenance: float
    independence: float
    injection_penalty: float
    total: float
    admissible_as_evidence: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["reasons"] = list(self.reasons)
        return data


def _parse_day(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def assess(source: dict[str, Any], *, as_of: str, max_age_days: int | None = None) -> SourceAssessment:
    reasons: list[str] = []
    tier = source.get("authority_tier", "D")
    authority = TIER_BASE.get(tier, 0.0)
    provenance = 1.0 if source.get("content_hash") and source.get("locator") and source.get("publisher") else 0.0
    if provenance == 0:
        reasons.append("incomplete provenance")
    independence = 1.0 if source.get("independence_group") else 0.0
    if independence == 0:
        reasons.append("missing independence group")
    freshness = 1.0
    published = _parse_day(source.get("published_at"))
    cutoff = _parse_day(as_of)
    if max_age_days is not None:
        if not published or not cutoff:
            freshness = 0.0
            reasons.append("freshness cannot be established")
        else:
            age = (cutoff - published).days
            if age < 0:
                freshness = 0.0
                reasons.append("source post-dates as-of date")
            elif age > max_age_days:
                freshness = max(0.0, 1.0 - (age - max_age_days) / max(max_age_days, 1))
                reasons.append(f"source is {age} days old")
    risk = source.get("injection_risk", "none")
    penalty = {"none": 0.0, "low": 0.1, "medium": 0.5, "high": 2.0}.get(risk, 1.0)
    if penalty:
        reasons.append(f"prompt-injection risk: {risk}")
    total = round(authority + freshness + provenance + independence - penalty, 4)
    admissible = tier in {"A", "B"} and provenance == 1.0 and risk != "high" and freshness > 0
    return SourceAssessment(authority, freshness, provenance, independence, penalty, total, admissible, tuple(reasons))


def independent_groups(sources: list[dict[str, Any]]) -> int:
    return len({s.get("independence_group") for s in sources if s.get("independence_group")})
