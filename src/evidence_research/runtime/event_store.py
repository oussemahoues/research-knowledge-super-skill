from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def stable_key(*parts: str) -> str:
    payload = '\x1f'.join(str(part) for part in parts)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  target TEXT NOT NULL,
  state TEXT NOT NULL,
  architecture TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS run_events (
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL REFERENCES runs(run_id),
  event_type TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks (
  run_id TEXT NOT NULL REFERENCES runs(run_id),
  task_id TEXT NOT NULL,
  objective TEXT NOT NULL,
  state TEXT NOT NULL,
  owner TEXT NOT NULL,
  max_attempts INTEGER NOT NULL,
  attempt_count INTEGER NOT NULL DEFAULT 0,
  consumes_json TEXT NOT NULL,
  produces_json TEXT NOT NULL,
  done_when TEXT NOT NULL,
  failure_policy TEXT NOT NULL,
  lease_owner TEXT,
  lease_expires_at TEXT,
  input_hash TEXT,
  output_hash TEXT,
  last_error TEXT,
  PRIMARY KEY(run_id, task_id)
);
CREATE TABLE IF NOT EXISTS task_dependencies (
  run_id TEXT NOT NULL,
  task_id TEXT NOT NULL,
  depends_on TEXT NOT NULL,
  PRIMARY KEY(run_id, task_id, depends_on),
  FOREIGN KEY(run_id, task_id) REFERENCES tasks(run_id, task_id),
  FOREIGN KEY(run_id, depends_on) REFERENCES tasks(run_id, task_id)
);
CREATE TABLE IF NOT EXISTS task_attempts (
  run_id TEXT NOT NULL,
  task_id TEXT NOT NULL,
  attempt INTEGER NOT NULL,
  state TEXT NOT NULL,
  worker_id TEXT,
  started_at TEXT,
  finished_at TEXT,
  error_category TEXT,
  error_message TEXT,
  PRIMARY KEY(run_id, task_id, attempt),
  FOREIGN KEY(run_id, task_id) REFERENCES tasks(run_id, task_id)
);
CREATE TABLE IF NOT EXISTS artifacts (
  run_id TEXT NOT NULL,
  artifact_id TEXT NOT NULL,
  task_id TEXT NOT NULL,
  path TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  media_type TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY(run_id, artifact_id),
  FOREIGN KEY(run_id, task_id) REFERENCES tasks(run_id, task_id)
);
CREATE TABLE IF NOT EXISTS checkpoints (
  run_id TEXT NOT NULL,
  checkpoint_id TEXT NOT NULL,
  task_id TEXT,
  state_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY(run_id, checkpoint_id)
);
CREATE TABLE IF NOT EXISTS interrupts (
  run_id TEXT NOT NULL,
  interrupt_id TEXT NOT NULL,
  task_id TEXT,
  reason TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  resolved_at TEXT,
  PRIMARY KEY(run_id, interrupt_id)
);
CREATE TABLE IF NOT EXISTS approvals (
  run_id TEXT NOT NULL,
  approval_id TEXT NOT NULL,
  interrupt_id TEXT NOT NULL,
  reviewer TEXT NOT NULL,
  decision TEXT NOT NULL,
  rationale TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY(run_id, approval_id)
);
"""


@dataclass(frozen=True)
class Event:
    seq: int
    run_id: str
    event_type: str
    payload: dict[str, Any]
    idempotency_key: str
    created_at: str


class EventStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON')
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def create_run(self, run_id: str, target: str, architecture: str = 'single') -> None:
        now = utc_now()
        with self.connect() as conn:
            conn.execute(
                'INSERT INTO runs(run_id,target,state,architecture,created_at,updated_at) VALUES(?,?,?,?,?,?)',
                (run_id, target, 'SCOPED', architecture, now, now),
            )
        self.append_event(run_id, 'RUN_CREATED', {'target': target, 'architecture': architecture}, f'run-created:{run_id}')

    def append_event(self, run_id: str, event_type: str, payload: dict[str, Any], idempotency_key: str) -> Event:
        now = utc_now()
        encoded = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        with self.connect() as conn:
            try:
                cur = conn.execute(
                    'INSERT INTO run_events(run_id,event_type,payload_json,idempotency_key,created_at) VALUES(?,?,?,?,?)',
                    (run_id, event_type, encoded, idempotency_key, now),
                )
                seq = int(cur.lastrowid)
            except sqlite3.IntegrityError:
                row = conn.execute('SELECT * FROM run_events WHERE idempotency_key=?', (idempotency_key,)).fetchone()
                if row is None:
                    raise
                if row['run_id'] != run_id or row['event_type'] != event_type or row['payload_json'] != encoded:
                    raise ValueError(f'idempotency key collision: {idempotency_key}')
                return Event(int(row['seq']), row['run_id'], row['event_type'], json.loads(row['payload_json']), row['idempotency_key'], row['created_at'])
        return Event(seq, run_id, event_type, payload, idempotency_key, now)

    def events(self, run_id: str) -> list[Event]:
        with self.connect() as conn:
            rows = conn.execute('SELECT * FROM run_events WHERE run_id=? ORDER BY seq', (run_id,)).fetchall()
        return [Event(int(r['seq']), r['run_id'], r['event_type'], json.loads(r['payload_json']), r['idempotency_key'], r['created_at']) for r in rows]

    def checkpoint(self, run_id: str, task_id: str | None, state: dict[str, Any]) -> str:
        checkpoint_id = 'cp:' + stable_key(run_id, task_id or '', json.dumps(state, sort_keys=True))[:20]
        with self.connect() as conn:
            conn.execute(
                'INSERT OR IGNORE INTO checkpoints(run_id,checkpoint_id,task_id,state_json,created_at) VALUES(?,?,?,?,?)',
                (run_id, checkpoint_id, task_id, json.dumps(state, sort_keys=True), utc_now()),
            )
        self.append_event(run_id, 'CHECKPOINT_WRITTEN', {'checkpoint_id': checkpoint_id, 'task_id': task_id}, f'checkpoint:{checkpoint_id}')
        return checkpoint_id

    def latest_checkpoint(self, run_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute('SELECT * FROM checkpoints WHERE run_id=? ORDER BY created_at DESC, rowid DESC LIMIT 1', (run_id,)).fetchone()
        return None if row is None else {'checkpoint_id': row['checkpoint_id'], 'task_id': row['task_id'], 'state': json.loads(row['state_json']), 'created_at': row['created_at']}
