from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from itertools import combinations
from typing import Any

from ..runtime.event_store import EventStore, stable_key, utc_now


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[^a-zA-Z0-9]+", " ", value).lower()
    return " ".join(value.split())


@dataclass(frozen=True)
class MatchScore:
    name: float
    aliases: float
    identifiers: float
    attributes: float
    neighborhood: float
    hard_conflicts: tuple[str, ...]
    total: float


@dataclass(frozen=True)
class FusionProposal:
    left_id: str
    right_id: str
    canonical_id: str
    decision: str
    score: MatchScore
    rationale: str


class FusionEngine:
    def __init__(self, store: EventStore):
        self.store = store

    def proposals(
        self,
        run_id: str,
        *,
        merge_at: float = 0.90,
        review_at: float = 0.65,
    ) -> list[FusionProposal]:
        features = self._features(run_id)
        pairs = self._candidate_pairs(features)
        proposals: list[FusionProposal] = []
        for left_id, right_id in sorted(pairs):
            score = self._score(features[left_id], features[right_id])
            if score.hard_conflicts:
                decision = "reject"
            elif score.identifiers == 1.0 and score.total >= merge_at:
                decision = "auto_merge"
            elif score.total >= review_at:
                decision = "review"
            else:
                decision = "reject"
            canonical_id = self._canonical_id(features[left_id], features[right_id])
            rationale = self._rationale(score, decision)
            proposals.append(FusionProposal(left_id, right_id, canonical_id, decision, score, rationale))
        return proposals

    def apply(self, run_id: str, proposal: FusionProposal, *, reviewer: str = "fusion-engine") -> str:
        if proposal.decision not in {"auto_merge", "review-approved"}:
            raise ValueError("only approved merge proposals can be applied")
        merged_id = proposal.right_id if proposal.canonical_id == proposal.left_id else proposal.left_id
        decision_id = "resolution:" + stable_key(run_id, proposal.canonical_id, merged_id, proposal.rationale)[:24]
        score_json = json.dumps(
            {
                "name": proposal.score.name,
                "aliases": proposal.score.aliases,
                "identifiers": proposal.score.identifiers,
                "attributes": proposal.score.attributes,
                "neighborhood": proposal.score.neighborhood,
                "hard_conflicts": list(proposal.score.hard_conflicts),
                "total": proposal.score.total,
            },
            sort_keys=True,
        )
        reversal = {"deactivate_members": [merged_id], "canonical_id": proposal.canonical_id}
        payload = {
            "decision_id": decision_id,
            "canonical_id": proposal.canonical_id,
            "merged_id": merged_id,
            "reviewer": reviewer,
        }
        self.store.append_event(run_id, "ENTITY_MERGE_APPLIED", payload, f"entity-merge:{run_id}:{decision_id}")
        with self.store.connect() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO resolution_decisions(
                    run_id,decision_id,candidate_a,candidate_b,canonical_id,decision,score_json,
                    rationale,reversal_json,reviewer,created_at,applied_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    run_id,
                    decision_id,
                    proposal.left_id,
                    proposal.right_id,
                    proposal.canonical_id,
                    proposal.decision,
                    score_json,
                    proposal.rationale,
                    json.dumps(reversal, sort_keys=True),
                    reviewer,
                    utc_now(),
                    utc_now(),
                ),
            )
            for member_id in {proposal.canonical_id, merged_id}:
                conn.execute(
                    "INSERT OR REPLACE INTO canonical_members(run_id,canonical_id,member_id,decision_id,active) VALUES(?,?,?,?,1)",
                    (run_id, proposal.canonical_id, member_id, decision_id),
                )
        return decision_id

    def reverse(self, run_id: str, decision_id: str, *, reviewer: str, rationale: str) -> None:
        with self.store.connect() as conn:
            decision = conn.execute(
                "SELECT * FROM resolution_decisions WHERE run_id=? AND decision_id=?",
                (run_id, decision_id),
            ).fetchone()
        if decision is None:
            raise KeyError(decision_id)
        if decision["reversed_at"] is not None:
            return
        payload = {"decision_id": decision_id, "reviewer": reviewer, "rationale": rationale}
        self.store.append_event(run_id, "ENTITY_MERGE_REVERSED", payload, f"entity-merge-reverse:{run_id}:{decision_id}")
        with self.store.connect() as conn:
            conn.execute(
                "UPDATE canonical_members SET active=0 WHERE run_id=? AND decision_id=?",
                (run_id, decision_id),
            )
            conn.execute(
                "UPDATE resolution_decisions SET reversed_at=?,reversal_reviewer=?,reversal_rationale=? WHERE run_id=? AND decision_id=?",
                (utc_now(), reviewer, rationale, run_id, decision_id),
            )

    def canonical_for(self, run_id: str, member_id: str) -> str:
        with self.store.connect() as conn:
            row = conn.execute(
                "SELECT canonical_id FROM canonical_members WHERE run_id=? AND member_id=? AND active=1 ORDER BY rowid DESC LIMIT 1",
                (run_id, member_id),
            ).fetchone()
        return member_id if row is None else row["canonical_id"]

    def _features(self, run_id: str) -> dict[str, dict[str, Any]]:
        with self.store.connect() as conn:
            nodes = conn.execute("SELECT * FROM graph_nodes WHERE run_id=?", (run_id,)).fetchall()
            edges = conn.execute("SELECT from_id,to_id FROM graph_edges WHERE run_id=?", (run_id,)).fetchall()
        neighbors: dict[str, set[str]] = {}
        for edge in edges:
            neighbors.setdefault(edge["from_id"], set()).add(edge["to_id"])
            neighbors.setdefault(edge["to_id"], set()).add(edge["from_id"])
        result: dict[str, dict[str, Any]] = {}
        for row in nodes:
            data = json.loads(row["data_json"])
            result[row["node_id"]] = {
                "node_id": row["node_id"],
                "entity_type": row["node_type"],
                "name": str(data.get("name", "")),
                "aliases": [str(item) for item in data.get("aliases", [])],
                "identifiers": dict(data.get("identifiers", {})),
                "attributes": dict(data.get("attributes", {})),
                "neighbors": neighbors.get(row["node_id"], set()),
            }
        return result

    def _candidate_pairs(self, features: dict[str, dict[str, Any]]) -> set[tuple[str, str]]:
        blocks: dict[str, set[str]] = {}
        for node_id, item in features.items():
            entity_type = item["entity_type"]
            identifiers = item["identifiers"]
            for key, value in identifiers.items():
                if value:
                    blocks.setdefault(f"{entity_type}:id:{key}:{_normalize(str(value))}", set()).add(node_id)
            name_tokens = _normalize(item["name"]).split()
            if name_tokens:
                blocks.setdefault(f"{entity_type}:name:{name_tokens[0]}", set()).add(node_id)
            for alias in item["aliases"]:
                alias_tokens = _normalize(alias).split()
                if alias_tokens:
                    blocks.setdefault(f"{entity_type}:alias:{alias_tokens[0]}", set()).add(node_id)
        pairs: set[tuple[str, str]] = set()
        for members in blocks.values():
            for left, right in combinations(sorted(members), 2):
                pairs.add((left, right))
        return pairs

    def _score(self, left: dict[str, Any], right: dict[str, Any]) -> MatchScore:
        if left["entity_type"] != right["entity_type"]:
            return MatchScore(0, 0, 0, 0, 0, ("entity_type",), 0)
        name = SequenceMatcher(None, _normalize(left["name"]), _normalize(right["name"])).ratio()
        left_names = [left["name"], *left["aliases"]]
        right_names = [right["name"], *right["aliases"]]
        aliases = max(
            (SequenceMatcher(None, _normalize(a), _normalize(b)).ratio() for a in left_names for b in right_names),
            default=0.0,
        )
        common_identifier_keys = set(left["identifiers"]) & set(right["identifiers"])
        identifier_matches = [left["identifiers"][key] == right["identifiers"][key] for key in common_identifier_keys]
        identifiers = 1.0 if any(identifier_matches) else 0.0
        conflicts: list[str] = []
        if common_identifier_keys and any(not match for match in identifier_matches):
            for key in sorted(common_identifier_keys):
                if left["identifiers"][key] != right["identifiers"][key]:
                    conflicts.append(f"identifier:{key}")
        critical_attributes = {"jurisdiction", "birth_date", "registration_number", "model"}
        common_attributes = set(left["attributes"]) & set(right["attributes"])
        for key in sorted(common_attributes & critical_attributes):
            if left["attributes"][key] != right["attributes"][key]:
                conflicts.append(f"attribute:{key}")
        attributes = (
            sum(left["attributes"][key] == right["attributes"][key] for key in common_attributes) / len(common_attributes)
            if common_attributes
            else 0.0
        )
        union = left["neighbors"] | right["neighbors"]
        neighborhood = len(left["neighbors"] & right["neighbors"]) / len(union) if union else 0.0
        total = round(0.15 * name + 0.15 * aliases + 0.60 * identifiers + 0.05 * attributes + 0.05 * neighborhood, 6)
        if conflicts:
            total = 0.0
        return MatchScore(name, aliases, identifiers, attributes, neighborhood, tuple(conflicts), total)

    @staticmethod
    def _canonical_id(left: dict[str, Any], right: dict[str, Any]) -> str:
        left_has_id = bool(left["identifiers"])
        right_has_id = bool(right["identifiers"])
        if left_has_id != right_has_id:
            return left["node_id"] if left_has_id else right["node_id"]
        return min(left["node_id"], right["node_id"])

    @staticmethod
    def _rationale(score: MatchScore, decision: str) -> str:
        if score.hard_conflicts:
            return "Rejected because hard identity conflicts were detected: " + ", ".join(score.hard_conflicts)
        if decision == "auto_merge":
            return "Auto-merge allowed because stable identifiers agree and the aggregate score exceeds the high-confidence threshold."
        if decision == "review":
            return "Ambiguous match requires independent review; no stable-identifier basis for automatic fusion."
        return "Insufficient identity evidence to merge safely."
