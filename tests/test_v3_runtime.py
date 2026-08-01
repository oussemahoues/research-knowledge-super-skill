from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.evidence_research.runtime.event_store import EventStore
from src.evidence_research.runtime.executor import DurableExecutor, TaskResult


class RuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = EventStore(Path(self.tmp.name) / 'state.db')
        self.store.create_run('run:test', 'test target', 'diamond')
        self.executor = DurableExecutor(self.store)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def graph(self):
        def task(tid, consumes, produces, deps, attempts=1):
            return {'id': tid, 'objective': tid, 'owner': tid, 'consumes': consumes, 'produces': produces, 'dependencies': deps, 'done_when': 'artifact exists', 'max_attempts': attempts}
        return {'tasks': [task('plan', ['brief'], ['plan.json'], []), task('left', ['plan.json'], ['left.json'], ['plan']), task('right', ['plan.json'], ['right.json'], ['plan']), task('verify', ['left.json', 'right.json'], ['verified.json'], ['left', 'right'])]}

    def result(self, name):
        return TaskResult([{'artifact_id': name, 'path': name, 'content_hash': f'hash:{name}', 'media_type': 'application/json'}], {})

    def test_diamond_execution_and_checkpoint(self):
        self.executor.register_graph('run:test', self.graph())
        self.assertEqual(['plan'], self.executor.ready_tasks('run:test'))
        self.executor.run_task('run:test', 'plan', 'w1', lambda: self.result('plan.json'))
        self.assertEqual(['left', 'right'], self.executor.ready_tasks('run:test'))
        self.executor.run_task('run:test', 'left', 'w2', lambda: self.result('left.json'))
        self.assertEqual(['right'], self.executor.ready_tasks('run:test'))
        self.executor.run_task('run:test', 'right', 'w3', lambda: self.result('right.json'))
        self.assertEqual(['verify'], self.executor.ready_tasks('run:test'))
        self.executor.run_task('run:test', 'verify', 'verifier', lambda: self.result('verified.json'))
        self.assertTrue(self.executor.complete('run:test'))
        self.assertIsNotNone(self.store.latest_checkpoint('run:test'))

    def test_idempotent_replay(self):
        self.executor.register_graph('run:test', {'tasks': [{'id':'a','objective':'a','owner':'a','consumes':[],'produces':['a'],'dependencies':[],'done_when':'done'}]})
        calls = {'n': 0}
        def fn():
            calls['n'] += 1
            return self.result('a')
        self.executor.run_task('run:test', 'a', 'w', fn)
        replay = self.executor.run_task('run:test', 'a', 'w', fn)
        self.assertEqual(1, calls['n'])
        self.assertTrue(replay.metadata['replayed'])

    def test_retry_is_bounded(self):
        self.executor.register_graph('run:test', {'tasks': [{'id':'a','objective':'a','owner':'a','consumes':[],'produces':['a'],'dependencies':[],'done_when':'done','max_attempts':2}]})
        with self.assertRaises(RuntimeError):
            self.executor.run_task('run:test', 'a', 'w', lambda: (_ for _ in ()).throw(RuntimeError('boom')))
        self.assertEqual(['a'], self.executor.ready_tasks('run:test'))
        with self.assertRaises(RuntimeError):
            self.executor.run_task('run:test', 'a', 'w', lambda: (_ for _ in ()).throw(RuntimeError('boom2')))
        self.assertEqual([], self.executor.ready_tasks('run:test'))

    def test_interrupt_requires_resolution(self):
        self.executor.register_graph('run:test', {'tasks': [{'id':'a','objective':'a','owner':'a','consumes':[],'produces':['a'],'dependencies':[],'done_when':'done'}]})
        interrupt = self.executor.interrupt('run:test', 'a', 'high consequence gate', {'proposal': 'x'})
        self.assertEqual([], self.executor.ready_tasks('run:test'))
        self.executor.approve('run:test', interrupt, 'reviewer-1', 'APPROVE', 'checked')
        self.assertEqual(['a'], self.executor.ready_tasks('run:test'))


if __name__ == '__main__':
    unittest.main()
