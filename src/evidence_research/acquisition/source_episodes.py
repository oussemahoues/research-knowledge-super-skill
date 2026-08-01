from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..runtime.event_store import EventStore, stable_key, utc_now


@dataclass(frozen=True)
class InjectionFinding:
    code: str
    severity: str
    excerpt: str


@dataclass(frozen=True)
class SourceEpisode:
    run_id: str
    episode_id: str
    source_id: str
    version: int
    locator: str
    media_type: str
    content_hash: str
    content_path: str
    authority: str
    independence_group: str
    injection_risk: str
    effective_at: str | None
    retrieved_at: str
    supersedes_episode_id: str | None
    metadata: dict[str, Any]


_PATTERNS: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    ("instruction_override", "high", re.compile(r"\b(ignore|disregard|override)\b.{0,40}\b(previous|system|developer|all)\b.{0,30}\binstruction", re.I | re.S)),
    ("credential_request", "high", re.compile(r"\b(api[- ]?key|password|access token|secret|credential)\b", re.I)),
    ("tool_execution", "high", re.compile(r"\b(run|execute|invoke|call)\b.{0,30}\b(command|shell|terminal|tool|function)\b", re.I)),
    ("context_exfiltration", "high", re.compile(r"\b(system prompt|developer message|hidden instruction|conversation history)\b", re.I)),
    ("data_exfiltration", "high", re.compile(r"\b(send|upload|post|transmit)\b.{0,80}\b(data|file|secret|token|prompt)\b.{0,40}\b(to|http|https|server|endpoint)\b", re.I | re.S)),
    ("encoded_payload", "medium", re.compile(r"\b(base64|rot13|hex[- ]?encoded|decode this)\b", re.I)),
    ("authority_claim", "high", re.compile(r"\b(this document|the webpage|the source)\b.{0,40}\b(is authoritative|must be obeyed|has priority)\b", re.I | re.S)),
)


def scan_untrusted_content(content: str, *, excerpt_limit: int = 160) -> tuple[str, list[InjectionFinding]]:
    findings: list[InjectionFinding] = []
    for code, severity, pattern in _PATTERNS:
        match = pattern.search(content)
        if match:
            start = max(0, match.start() - 40)
            end = min(len(content), match.end() + 80)
            excerpt = " ".join(content[start:end].split())[:excerpt_limit]
            findings.append(InjectionFinding(code, severity, excerpt))
    if any(f.severity == "high" for f in findings):
        return "quarantine", findings
    if findings:
        return "medium", findings
    return "low", findings


class SourceEpisodeStore:
    def __init__(self, store: EventStore, content_dir: str | Path):
        self.store = store
        self.content_dir = Path(content_dir)
        self.content_dir.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        run_id: str,
        source_id: str,
        locator: str,
        content: bytes | str,
        *,
        media_type: str = "text/plain",
        authority: str = "unknown",
        independence_group: str = "unknown",
        effective_at: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SourceEpisode:
        raw = content.encode("utf-8") if isinstance(content, str) else bytes(content)
        digest = hashlib.sha256(raw).hexdigest()
        content_hash = f"sha256:{digest}"
        text = raw.decode("utf-8", errors="replace")
        injection_risk, findings = scan_untrusted_content(text)
        retrieved_at = utc_now()
        metadata = dict(metadata or {})

        with self.store.connect() as conn:
            existing = conn.execute(
                "SELECT * FROM source_episodes WHERE run_id=? AND source_id=? AND content_hash=?",
                (run_id, source_id, content_hash),
            ).fetchone()
            if existing is not None:
                return self._from_row(existing)
            previous = conn.execute(
                "SELECT * FROM source_episodes WHERE run_id=? AND source_id=? ORDER BY version DESC LIMIT 1",
                (run_id, source_id),
            ).fetchone()
            version = 1 if previous is None else int(previous["version"]) + 1
            supersedes = None if previous is None else previous["episode_id"]

        episode_id = "episode:" + stable_key(run_id, source_id, content_hash)[:24]
        path = self.content_dir / f"{digest}.bin"
        if not path.exists():
            fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(raw)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(tmp, path)
            finally:
                if os.path.exists(tmp):
                    os.unlink(tmp)

        payload = {
            "episode_id": episode_id,
            "source_id": source_id,
            "version": version,
            "content_hash": content_hash,
            "injection_risk": injection_risk,
            "supersedes_episode_id": supersedes,
        }
        self.store.append_event(run_id, "SOURCE_EPISODE_RECORDED", payload, f"source-episode:{episode_id}")
        with self.store.connect() as conn:
            conn.execute(
                """INSERT INTO source_episodes(
                    run_id,episode_id,source_id,version,locator,media_type,content_hash,content_path,
                    authority,independence_group,injection_risk,effective_at,retrieved_at,
                    supersedes_episode_id,metadata_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    run_id,
                    episode_id,
                    source_id,
                    version,
                    locator,
                    media_type,
                    content_hash,
                    str(path),
                    authority,
                    independence_group,
                    injection_risk,
                    effective_at,
                    retrieved_at,
                    supersedes,
                    json.dumps(metadata, sort_keys=True),
                ),
            )
            for finding in findings:
                conn.execute(
                    "INSERT INTO source_episode_findings(run_id,episode_id,finding_code,severity,excerpt) VALUES(?,?,?,?,?)",
                    (run_id, episode_id, finding.code, finding.severity, finding.excerpt),
                )
            row = conn.execute(
                "SELECT * FROM source_episodes WHERE run_id=? AND episode_id=?",
                (run_id, episode_id),
            ).fetchone()
        return self._from_row(row)

    def verify_content(self, run_id: str, episode_id: str) -> bool:
        with self.store.connect() as conn:
            row = conn.execute(
                "SELECT content_path,content_hash FROM source_episodes WHERE run_id=? AND episode_id=?",
                (run_id, episode_id),
            ).fetchone()
        if row is None:
            raise KeyError(episode_id)
        path = Path(row["content_path"])
        if not path.exists():
            return False
        actual = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        return actual == row["content_hash"]

    def versions(self, run_id: str, source_id: str) -> list[SourceEpisode]:
        with self.store.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM source_episodes WHERE run_id=? AND source_id=? ORDER BY version",
                (run_id, source_id),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def findings(self, run_id: str, episode_id: str) -> list[InjectionFinding]:
        with self.store.connect() as conn:
            rows = conn.execute(
                "SELECT finding_code,severity,excerpt FROM source_episode_findings WHERE run_id=? AND episode_id=? ORDER BY finding_code",
                (run_id, episode_id),
            ).fetchall()
        return [InjectionFinding(row["finding_code"], row["severity"], row["excerpt"]) for row in rows]

    @staticmethod
    def _from_row(row: Any) -> SourceEpisode:
        return SourceEpisode(
            run_id=row["run_id"],
            episode_id=row["episode_id"],
            source_id=row["source_id"],
            version=int(row["version"]),
            locator=row["locator"],
            media_type=row["media_type"],
            content_hash=row["content_hash"],
            content_path=row["content_path"],
            authority=row["authority"],
            independence_group=row["independence_group"],
            injection_risk=row["injection_risk"],
            effective_at=row["effective_at"],
            retrieved_at=row["retrieved_at"],
            supersedes_episode_id=row["supersedes_episode_id"],
            metadata=json.loads(row["metadata_json"]),
        )
