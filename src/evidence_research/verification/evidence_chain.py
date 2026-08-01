from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from ..runtime.event_store import EventStore, stable_key, utc_now

_WORD_RE = re.compile(r"[A-Za-z0-9]+")
_NUMBER_RE = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:[.,]\d+)?%?")


def _words(text: str) -> set[str]:
    stop = {"the", "a", "an", "of", "to", "and", "or", "in", "on", "for", "with", "by", "is", "was", "are", "were"}
    return {word.lower() for word in _WORD_RE.findall(text) if word.lower() not in stop}


def _numbers(text: str) -> set[str]:
    return {item.replace(",", ".") for item in _NUMBER_RE.findall(text)}


@dataclass(frozen=True)
class ClaimVerification:
    claim_id: str
    status: str
    support_edge_ids: tuple[str, ...]
    contradiction_edge_ids: tuple[str, ...]
    source_episode_ids: tuple[str, ...]
    independence_groups: tuple[str, ...]
    lexical_entailment: float
    numerical_consistency: bool
    issues: tuple[str, ...]
    requires_model_review: bool
    decision_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "status": self.status,
            "support_edge_ids": list(self.support_edge_ids),
            "contradiction_edge_ids": list(self.contradiction_edge_ids),
            "source_episode_ids": list(self.source_episode_ids),
            "independence_groups": list(self.independence_groups),
            "lexical_entailment": self.lexical_entailment,
            "numerical_consistency": self.numerical_consistency,
            "issues": list(self.issues),
            "requires_model_review": self.requires_model_review,
            "decision_id": self.decision_id,
        }


class EvidenceChainVerifier:
    def __init__(self, store: EventStore):
        self.store = store

    def verify_claim(
        self,
        run_id: str,
        claim_id: str,
        *,
        as_of: str | None = None,
        minimum_lexical_signal: float = 0.20,
        require_independent_sources: int = 1,
    ) -> ClaimVerification:
        with self.store.connect() as conn:
            claim = conn.execute(
                "SELECT * FROM graph_nodes WHERE run_id=? AND node_id=? AND node_type='Claim'",
                (run_id, claim_id),
            ).fetchone()
            if claim is None:
                raise KeyError(claim_id)
            clauses = ["run_id=?", "to_id=?", "edge_type IN ('SUPPORTS','CONTRADICTS','QUALIFIES')"]
            params: list[Any] = [run_id, claim_id]
            if as_of is not None:
                clauses.extend(["valid_from<=?", "(valid_to IS NULL OR valid_to>?)"])
                params.extend([as_of, as_of])
            edges = conn.execute("SELECT * FROM graph_edges WHERE " + " AND ".join(clauses), tuple(params)).fetchall()
            evidence_ids = [row["from_id"] for row in edges]
            evidence = {}
            if evidence_ids:
                placeholders = ",".join("?" for _ in evidence_ids)
                rows = conn.execute(
                    f"SELECT * FROM graph_nodes WHERE run_id=? AND node_id IN ({placeholders})",
                    (run_id, *evidence_ids),
                ).fetchall()
                evidence = {row["node_id"]: row for row in rows}
            episode_ids = sorted({row["source_episode_id"] for row in edges if row["source_episode_id"]})
            episodes = {}
            if episode_ids:
                placeholders = ",".join("?" for _ in episode_ids)
                rows = conn.execute(
                    f"SELECT * FROM source_episodes WHERE run_id=? AND episode_id IN ({placeholders})",
                    (run_id, *episode_ids),
                ).fetchall()
                episodes = {row["episode_id"]: row for row in rows}

        claim_data = json.loads(claim["data_json"])
        claim_text = str(claim_data.get("text") or claim_data.get("claim") or "")
        support_edges = [row for row in edges if row["edge_type"] == "SUPPORTS"]
        contradiction_edges = [row for row in edges if row["edge_type"] == "CONTRADICTS"]
        support_texts: list[str] = []
        for edge in support_edges:
            row = evidence.get(edge["from_id"])
            if row:
                data = json.loads(row["data_json"])
                support_texts.append(str(data.get("text") or data.get("value") or ""))

        claim_words = _words(claim_text)
        evidence_words = _words(" ".join(support_texts))
        lexical = len(claim_words & evidence_words) / len(claim_words) if claim_words else 0.0
        claim_numbers = _numbers(claim_text)
        evidence_numbers = _numbers(" ".join(support_texts))
        numerical_consistency = claim_numbers <= evidence_numbers
        independence_groups = sorted({episodes[episode_id]["independence_group"] for episode_id in episode_ids if episode_id in episodes})

        issues: list[str] = []
        if not support_edges:
            issues.append("No supporting evidence edge exists.")
        if claim_numbers and not numerical_consistency:
            issues.append("One or more claim numbers are absent from the supporting evidence spans.")
        if support_edges and lexical < minimum_lexical_signal:
            issues.append("Deterministic lexical entailment signal is below threshold.")
        if len(independence_groups) < require_independent_sources:
            issues.append("Independent-source requirement is not met.")
        quarantined = [episode_id for episode_id in episode_ids if episode_id in episodes and episodes[episode_id]["injection_risk"] == "quarantine"]
        if quarantined:
            issues.append("Supporting evidence includes quarantined source content.")

        requires_model_review = bool(support_edges) and lexical < max(minimum_lexical_signal, 0.45)
        if not support_edges:
            status = "rejected"
        elif contradiction_edges:
            status = "contested"
        elif issues:
            status = "needs_review"
        else:
            status = "verified"

        decision_id = "adjudication:" + stable_key(run_id, claim_id, status, json.dumps(sorted(row["edge_id"] for row in edges)))[:24]
        payload = {
            "decision_id": decision_id,
            "claim_id": claim_id,
            "status": status,
            "issues": issues,
            "requires_model_review": requires_model_review,
        }
        self.store.append_event(run_id, "CLAIM_ADJUDICATED", payload, f"claim-adjudication:{run_id}:{decision_id}")
        with self.store.connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO adjudication_decisions(
                    run_id,decision_id,claim_id,status,support_edge_ids_json,contradiction_edge_ids_json,
                    source_episode_ids_json,independence_groups_json,lexical_entailment,
                    numerical_consistency,issues_json,requires_model_review,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    run_id,
                    decision_id,
                    claim_id,
                    status,
                    json.dumps(sorted(row["edge_id"] for row in support_edges)),
                    json.dumps(sorted(row["edge_id"] for row in contradiction_edges)),
                    json.dumps(episode_ids),
                    json.dumps(independence_groups),
                    lexical,
                    1 if numerical_consistency else 0,
                    json.dumps(issues),
                    1 if requires_model_review else 0,
                    utc_now(),
                ),
            )
        return ClaimVerification(
            claim_id,
            status,
            tuple(sorted(row["edge_id"] for row in support_edges)),
            tuple(sorted(row["edge_id"] for row in contradiction_edges)),
            tuple(episode_ids),
            tuple(independence_groups),
            round(lexical, 6),
            numerical_consistency,
            tuple(issues),
            requires_model_review,
            decision_id,
        )
