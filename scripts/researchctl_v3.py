#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evidence_research.audit import audit_run
from src.evidence_research.migration import migrate_v2_run
from src.evidence_research.retrieval import HybridRetriever
from src.evidence_research.runtime import DurableExecutor, EventStore
from src.evidence_research.runtime.event_store import stable_key
from src.evidence_research.taskgraph import WorkProfile, compile_task_graph, select_architecture
from src.evidence_research.verification import EvidenceChainVerifier


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')
    os.replace(tmp, path)


def _slug(value: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')[:48] or 'research'


def _load_run(path: str | Path) -> tuple[Path, EventStore, str]:
    run_dir = Path(path)
    manifest = json.loads((run_dir / 'run.json').read_text(encoding='utf-8'))
    return run_dir, EventStore(run_dir / manifest.get('database', 'state.db')), manifest['run_id']


def cmd_init(args: argparse.Namespace) -> int:
    contract = json.loads(Path(args.contract).read_text(encoding='utf-8')) if args.contract else {
        'target': args.target or 'Research target',
        'as_of': args.as_of or date.today().isoformat(),
        'questions': [{'id': 'q1', 'text': args.target or 'Research target', 'domain': 'general'}],
        'profile': {},
    }
    target = str(contract.get('target', '')).strip()
    if not target:
        raise ValueError('contract.target is required')
    questions = list(contract.get('questions') or [])
    profile_data = dict(contract.get('profile') or {})
    profile_data.setdefault('question_count', len(questions))
    profile_data.setdefault('independent_branches', max(1, len(questions)))
    profile_data.setdefault('dependency_depth', 1)
    profile_data.setdefault('domain_count', max(1, len({str(q.get('domain') or 'general') for q in questions})))
    allowed = set(WorkProfile.__dataclass_fields__)
    profile = WorkProfile(**{k: v for k, v in profile_data.items() if k in allowed})
    decision = select_architecture(profile, max_agents=args.max_agents)
    graph = compile_task_graph(decision, questions)
    digest = stable_key(json.dumps(contract, sort_keys=True))
    run_id = f'run:{_slug(target)}:{digest[:12]}'
    run_dir = Path(args.root) / run_id.replace(':', '_')
    run_dir.mkdir(parents=True, exist_ok=True)
    store = EventStore(run_dir / 'state.db')
    with store.connect() as conn:
        exists = conn.execute('SELECT 1 FROM runs WHERE run_id=?', (run_id,)).fetchone()
    if exists is None:
        store.create_run(run_id, target, decision.architecture)
        DurableExecutor(store).register_graph(run_id, graph.to_dict())
    manifest = {
        'schema_version': '3.0', 'engine': 'v3', 'run_id': run_id, 'target': target,
        'as_of': contract.get('as_of', date.today().isoformat()), 'database': 'state.db',
        'architecture': decision.to_dict(), 'contract_hash': f'sha256:{digest}',
    }
    _write_json(run_dir / 'contract.json', contract)
    _write_json(run_dir / 'task-graph.json', graph.to_dict())
    _write_json(run_dir / 'run.json', manifest)
    print(json.dumps({'run_path': str(run_dir), **manifest}, indent=2))
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    run_dir, store, run_id = _load_run(args.run)
    with store.connect() as conn:
        run = dict(conn.execute('SELECT * FROM runs WHERE run_id=?', (run_id,)).fetchone())
    payload = {'run_path': str(run_dir), 'run': run, 'execution': DurableExecutor(store).snapshot(run_id), 'latest_checkpoint': store.latest_checkpoint(run_id)}
    print(json.dumps(payload, indent=2, default=str))
    return 0


def cmd_ready(args: argparse.Namespace) -> int:
    _root, store, run_id = _load_run(args.run)
    print(json.dumps({'run_id': run_id, 'ready_tasks': DurableExecutor(store).ready_tasks(run_id)}, indent=2))
    return 0


def cmd_recover(args: argparse.Namespace) -> int:
    _root, store, run_id = _load_run(args.run)
    recovered = DurableExecutor(store).recover_stale_leases(run_id, now=args.now)
    print(json.dumps({'run_id': run_id, 'recovered_tasks': recovered}, indent=2))
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    _root, store, run_id = _load_run(args.run)
    approval = DurableExecutor(store).approve(run_id, args.interrupt_id, args.reviewer, args.decision, args.rationale)
    print(json.dumps({'run_id': run_id, 'approval_id': approval, 'decision': args.decision}, indent=2))
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    _root, store, run_id = _load_run(args.run)
    result = HybridRetriever(store).retrieve(run_id, args.query, entity_ids=args.entity, as_of=args.as_of, limit=args.limit, max_hops=args.max_hops)
    print(json.dumps(result.to_dict(), indent=2))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    _root, store, run_id = _load_run(args.run)
    result = EvidenceChainVerifier(store).verify_claim(run_id, args.claim_id, as_of=args.as_of, require_independent_sources=args.independent_sources)
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.status in {'verified', 'contested'} else 1


def cmd_audit(args: argparse.Namespace) -> int:
    run_dir, store, run_id = _load_run(args.run)
    result = audit_run(store, run_id)
    _write_json(run_dir / 'audit.json', result.to_dict())
    print(json.dumps({**result.to_dict(), 'audit_path': str(run_dir / 'audit.json')}, indent=2))
    return 0 if result.passed else 1


def cmd_migrate(args: argparse.Namespace) -> int:
    destination = Path(args.destination)
    destination.mkdir(parents=True, exist_ok=True)
    report = migrate_v2_run(args.v2_run, destination / 'state.db', destination / 'source-episodes')
    manifest = {'schema_version': '3.0', 'engine': 'v3', 'run_id': report.run_id, 'database': 'state.db', 'migration': report.to_dict()}
    _write_json(destination / 'run.json', manifest)
    print(json.dumps({'run_path': str(destination), **manifest}, indent=2))
    return 0


def cmd_engine(_args: argparse.Namespace) -> int:
    print(json.dumps({'selected': 'v3', 'fallback': 'Set EVIDENCE_RESEARCH_ENGINE=v2 to use the sealed legacy CLI.'}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog='researchctl', description='Evidence Research v3 graph runtime')
    sub = p.add_subparsers(dest='command', required=True)
    x = sub.add_parser('init'); x.add_argument('--root', default='research-runs'); x.add_argument('--contract'); x.add_argument('--target'); x.add_argument('--as-of'); x.add_argument('--max-agents', type=int, default=8); x.set_defaults(func=cmd_init)
    x = sub.add_parser('inspect'); x.add_argument('run'); x.set_defaults(func=cmd_inspect)
    x = sub.add_parser('ready'); x.add_argument('run'); x.set_defaults(func=cmd_ready)
    x = sub.add_parser('recover-leases'); x.add_argument('run'); x.add_argument('--now'); x.set_defaults(func=cmd_recover)
    x = sub.add_parser('approve'); x.add_argument('run'); x.add_argument('interrupt_id'); x.add_argument('decision', choices=['APPROVE', 'REJECT']); x.add_argument('--reviewer', required=True); x.add_argument('--rationale', required=True); x.set_defaults(func=cmd_approve)
    x = sub.add_parser('query'); x.add_argument('run'); x.add_argument('query'); x.add_argument('--entity', action='append', default=[]); x.add_argument('--as-of'); x.add_argument('--limit', type=int, default=12); x.add_argument('--max-hops', type=int, default=3); x.set_defaults(func=cmd_query)
    x = sub.add_parser('verify-claim'); x.add_argument('run'); x.add_argument('claim_id'); x.add_argument('--as-of'); x.add_argument('--independent-sources', type=int, default=1); x.set_defaults(func=cmd_verify)
    x = sub.add_parser('audit'); x.add_argument('run'); x.set_defaults(func=cmd_audit)
    x = sub.add_parser('migrate-v2'); x.add_argument('v2_run'); x.add_argument('destination'); x.set_defaults(func=cmd_migrate)
    x = sub.add_parser('engine'); x.set_defaults(func=cmd_engine)
    return p


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == '__main__':
    raise SystemExit(main())
