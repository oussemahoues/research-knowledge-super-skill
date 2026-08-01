from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from .event_store import EventStore, stable_key, utc_now


@dataclass(frozen=True)
class TaskResult:
    artifacts: list[dict[str, str]]
    metadata: dict[str, Any]


class DurableExecutor:
    def __init__(self, store: EventStore):
        self.store = store

    def register_graph(self, run_id: str, graph: dict[str, Any]) -> None:
        tasks = graph.get('tasks', [])
        ids = {t['id'] for t in tasks}
        with self.store.connect() as conn:
            for task in tasks:
                deps = task.get('dependencies', [])
                missing = set(deps) - ids
                if missing:
                    raise ValueError(f"{task['id']}: missing dependencies {sorted(missing)}")
                conn.execute(
                    '''INSERT INTO tasks(run_id,task_id,objective,state,owner,max_attempts,consumes_json,produces_json,done_when,failure_policy)
                       VALUES(?,?,?,?,?,?,?,?,?,?)''',
                    (run_id, task['id'], task['objective'], 'PENDING', task['owner'], int(task.get('max_attempts', 1)), json.dumps(task.get('consumes', [])), json.dumps(task.get('produces', [])), task['done_when'], task.get('failure_policy', 'block')),
                )
            for task in tasks:
                for dep in task.get('dependencies', []):
                    conn.execute('INSERT INTO task_dependencies(run_id,task_id,depends_on) VALUES(?,?,?)', (run_id, task['id'], dep))
        self.store.append_event(run_id, 'TASK_GRAPH_REGISTERED', {'task_count': len(tasks)}, f'graph:{run_id}:{stable_key(json.dumps(graph, sort_keys=True))}')
        self.refresh_ready(run_id)

    def refresh_ready(self, run_id: str) -> list[str]:
        ready: list[str] = []
        with self.store.connect() as conn:
            rows = conn.execute("SELECT task_id FROM tasks WHERE run_id=? AND state='PENDING' ORDER BY task_id", (run_id,)).fetchall()
            for row in rows:
                task_id = row['task_id']
                blocked = conn.execute(
                    '''SELECT 1 FROM task_dependencies d JOIN tasks p ON p.run_id=d.run_id AND p.task_id=d.depends_on
                       WHERE d.run_id=? AND d.task_id=? AND p.state!='SUCCEEDED' LIMIT 1''',
                    (run_id, task_id),
                ).fetchone()
                if blocked is None:
                    conn.execute("UPDATE tasks SET state='READY' WHERE run_id=? AND task_id=?", (run_id, task_id))
                    ready.append(task_id)
        for task_id in ready:
            self.store.append_event(run_id, 'TASK_READY', {'task_id': task_id}, f'task-ready:{run_id}:{task_id}')
        return ready

    def ready_tasks(self, run_id: str) -> list[str]:
        self.refresh_ready(run_id)
        with self.store.connect() as conn:
            rows = conn.execute("SELECT task_id FROM tasks WHERE run_id=? AND state='READY' ORDER BY task_id", (run_id,)).fetchall()
        return [r['task_id'] for r in rows]

    def run_task(self, run_id: str, task_id: str, worker_id: str, fn: Callable[[], TaskResult]) -> TaskResult:
        with self.store.connect() as conn:
            task = conn.execute('SELECT * FROM tasks WHERE run_id=? AND task_id=?', (run_id, task_id)).fetchone()
            if task is None:
                raise KeyError(task_id)
            if task['state'] == 'SUCCEEDED':
                artifacts = conn.execute('SELECT * FROM artifacts WHERE run_id=? AND task_id=? ORDER BY artifact_id', (run_id, task_id)).fetchall()
                return TaskResult([dict(a) for a in artifacts], {'replayed': True})
            if task['state'] != 'READY':
                raise ValueError(f"task {task_id} is {task['state']}, expected READY")
            attempt = int(task['attempt_count']) + 1
            conn.execute("UPDATE tasks SET state='RUNNING',attempt_count=?,lease_owner=? WHERE run_id=? AND task_id=?", (attempt, worker_id, run_id, task_id))
            conn.execute('INSERT INTO task_attempts(run_id,task_id,attempt,state,worker_id,started_at) VALUES(?,?,?,?,?,?)', (run_id, task_id, attempt, 'RUNNING', worker_id, utc_now()))
        self.store.append_event(run_id, 'TASK_STARTED', {'task_id': task_id, 'attempt': attempt, 'worker_id': worker_id}, f'task-start:{run_id}:{task_id}:{attempt}')
        try:
            result = fn()
            with self.store.connect() as conn:
                for item in result.artifacts:
                    conn.execute(
                        '''INSERT OR REPLACE INTO artifacts(run_id,artifact_id,task_id,path,content_hash,media_type,created_at)
                           VALUES(?,?,?,?,?,?,?)''',
                        (run_id, item['artifact_id'], task_id, item['path'], item['content_hash'], item.get('media_type', 'application/octet-stream'), utc_now()),
                    )
                output_hash = stable_key(*(sorted(a['content_hash'] for a in result.artifacts)))
                conn.execute("UPDATE tasks SET state='SUCCEEDED',output_hash=?,lease_owner=NULL,last_error=NULL WHERE run_id=? AND task_id=?", (output_hash, run_id, task_id))
                conn.execute("UPDATE task_attempts SET state='SUCCEEDED',finished_at=? WHERE run_id=? AND task_id=? AND attempt=?", (utc_now(), run_id, task_id, attempt))
            self.store.append_event(run_id, 'TASK_SUCCEEDED', {'task_id': task_id, 'attempt': attempt, 'artifact_ids': [a['artifact_id'] for a in result.artifacts]}, f'task-success:{run_id}:{task_id}:{attempt}')
            self.store.checkpoint(run_id, task_id, self.snapshot(run_id))
            self.refresh_ready(run_id)
            return result
        except Exception as exc:
            category = getattr(exc, 'category', 'execution')
            with self.store.connect() as conn:
                task = conn.execute('SELECT * FROM tasks WHERE run_id=? AND task_id=?', (run_id, task_id)).fetchone()
                retry = int(task['attempt_count']) < int(task['max_attempts'])
                next_state = 'READY' if retry else 'FAILED'
                conn.execute('UPDATE tasks SET state=?,lease_owner=NULL,last_error=? WHERE run_id=? AND task_id=?', (next_state, str(exc), run_id, task_id))
                conn.execute('UPDATE task_attempts SET state=?,finished_at=?,error_category=?,error_message=? WHERE run_id=? AND task_id=? AND attempt=?', ('FAILED', utc_now(), category, str(exc), run_id, task_id, attempt))
            self.store.append_event(run_id, 'TASK_FAILED', {'task_id': task_id, 'attempt': attempt, 'category': category, 'retry_scheduled': retry, 'error': str(exc)}, f'task-failed:{run_id}:{task_id}:{attempt}')
            raise

    def interrupt(self, run_id: str, task_id: str | None, reason: str, payload: dict[str, Any]) -> str:
        interrupt_id = 'int:' + stable_key(run_id, task_id or '', reason, json.dumps(payload, sort_keys=True))[:20]
        with self.store.connect() as conn:
            conn.execute('INSERT OR IGNORE INTO interrupts(run_id,interrupt_id,task_id,reason,payload_json,status,created_at) VALUES(?,?,?,?,?,?,?)', (run_id, interrupt_id, task_id, reason, json.dumps(payload, sort_keys=True), 'OPEN', utc_now()))
            if task_id:
                conn.execute("UPDATE tasks SET state='INTERRUPTED' WHERE run_id=? AND task_id=? AND state IN ('READY','RUNNING')", (run_id, task_id))
        self.store.append_event(run_id, 'INTERRUPT_OPENED', {'interrupt_id': interrupt_id, 'task_id': task_id, 'reason': reason}, f'interrupt:{interrupt_id}')
        return interrupt_id

    def approve(self, run_id: str, interrupt_id: str, reviewer: str, decision: str, rationale: str) -> str:
        if decision not in {'APPROVE', 'REJECT'}:
            raise ValueError('decision must be APPROVE or REJECT')
        approval_id = 'approval:' + stable_key(run_id, interrupt_id, reviewer, decision, rationale)[:20]
        with self.store.connect() as conn:
            row = conn.execute('SELECT * FROM interrupts WHERE run_id=? AND interrupt_id=?', (run_id, interrupt_id)).fetchone()
            if row is None or row['status'] != 'OPEN':
                raise ValueError('interrupt is not open')
            conn.execute('INSERT INTO approvals(run_id,approval_id,interrupt_id,reviewer,decision,rationale,created_at) VALUES(?,?,?,?,?,?,?)', (run_id, approval_id, interrupt_id, reviewer, decision, rationale, utc_now()))
            conn.execute('UPDATE interrupts SET status=?,resolved_at=? WHERE run_id=? AND interrupt_id=?', ('APPROVED' if decision == 'APPROVE' else 'REJECTED', utc_now(), run_id, interrupt_id))
            if row['task_id']:
                conn.execute('UPDATE tasks SET state=? WHERE run_id=? AND task_id=?', ('READY' if decision == 'APPROVE' else 'CANCELLED', run_id, row['task_id']))
        self.store.append_event(run_id, 'INTERRUPT_RESOLVED', {'interrupt_id': interrupt_id, 'decision': decision, 'reviewer': reviewer}, f'approval:{approval_id}')
        return approval_id

    def snapshot(self, run_id: str) -> dict[str, Any]:
        with self.store.connect() as conn:
            tasks = [dict(r) for r in conn.execute('SELECT task_id,state,attempt_count,output_hash,last_error FROM tasks WHERE run_id=? ORDER BY task_id', (run_id,)).fetchall()]
            open_interrupts = [dict(r) for r in conn.execute("SELECT interrupt_id,task_id,reason,status FROM interrupts WHERE run_id=? AND status='OPEN' ORDER BY interrupt_id", (run_id,)).fetchall()]
        return {'run_id': run_id, 'tasks': tasks, 'open_interrupts': open_interrupts}

    def complete(self, run_id: str) -> bool:
        with self.store.connect() as conn:
            rows = conn.execute('SELECT state FROM tasks WHERE run_id=?', (run_id,)).fetchall()
        return bool(rows) and all(r['state'] == 'SUCCEEDED' for r in rows)
