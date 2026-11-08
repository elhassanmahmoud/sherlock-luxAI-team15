"""Controller safety tests and synthetic analysis; no real children or games."""
from contextlib import ExitStack, contextmanager, redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


MODULE = 'scripts.ensemble_diversity_eval_supervisor'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.s = importlib.import_module(MODULE)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.out = self.root / 'experiments/analysis/ensemble_diversity_20261107/results'
        self.out.mkdir(parents=True)
        (self.out / 'receipts').mkdir()
        self.state = dict(root=str(self.root), out=str(self.out), python='/usr/bin/python3',
            stop_file=str(self.root / 'STOP'), owner_pid=os.getpid(), phase='selection',
            jobs={}, active=[], queue=['one', 'two', 'three'], receipts={}, expected_games=6,
            job_plan={name: dict(name=name, role='V14', weights='model.pth',
                seed_list='seeds.json', opponent='solution92', expected_games=2,
                workers=1, seeds=[1400000]) for name in ('one', 'two', 'three')},
            source={'head': 'a' * 40}, expected_head='a' * 40, plans=[], protected={},
            inputs={}, model_sha256={'V14': 'b' * 64}, opponent_sha256={'opponent.pth': 'c' * 64})

    def test_import_does_not_load_model_or_analysis_stack(self):
        before = set(sys.modules)
        importlib.reload(self.s)
        self.assertFalse({'torch', 'numpy', 'scripts.ensemble_diversity_compare'} & (set(sys.modules) - before))

    def test_command_uses_exact_absolute_seed_path_and_one_worker(self):
        command = self.s.job_command(self.state, 'one')
        self.assertEqual(command, ['/usr/bin/python3', '-B', '-m', 'scripts.par_eval',
            '--weights', str(self.root / 'model.pth'), '--seed-list', str(self.root / 'seeds.json'),
            '--workers', '1', '--opponents', 'solution92', '--out', str(self.out / 'one.csv')])
        (self.out / 'one.csv').write_text('partial')
        with self.assertRaisesRegex(ValueError, 'exists'):
            self.s.job_command(self.state, 'one')

    def test_quota_rejects_unknown_stale_future_disallowed_and_65_percent(self):
        now = datetime(2026, 11, 7, 12, tzinfo=timezone.utc).timestamp()
        path = self.root / 'usage.json'
        good = dict(timestamp='2026-11-07T11:40:00Z', ordinaryUsageAllowed=True, usedPercent=64)
        with self.assertRaises(ValueError):
            self.s.check_usage(path, now=now)
        path.write_text(json.dumps(good))
        self.assertEqual(self.s.check_usage(path, now=now)['usedPercent'], 64)
        for change in (dict(timestamp='2026-11-07T11:39:59Z'), dict(timestamp='2026-11-07T12:00:01Z'),
                       dict(timestamp='unknown'), dict(usedPercent=None), dict(ordinaryUsageAllowed=False),
                       dict(usedPercent=65), dict(usedPercent=True),
                       dict(usedPercent=float('nan'))):
            with self.subTest(change=change):
                path.write_text(json.dumps({**good, **change}))
                with self.assertRaises(ValueError):
                    self.s.check_usage(path, now=now)

    def test_explicit_quota_ceiling_accepts_remaining_budget_but_not_exhaustion(self):
        now = datetime(2026, 11, 7, 12, tzinfo=timezone.utc).timestamp()
        path = self.root / 'usage.json'
        for used in (65, 99, 100):
            with self.subTest(used=used):
                path.write_text(json.dumps(dict(timestamp='2026-11-07T12:00:00Z',
                    ordinaryUsageAllowed=True, usedPercent=used)))
                if used < 100:
                    self.assertEqual(self.s.check_usage(path, now=now,
                        max_used_percent=100)['usedPercent'], used)
                else:
                    with self.assertRaises(ValueError):
                        self.s.check_usage(path, now=now, max_used_percent=100)

    def test_quota_ceiling_rejects_invalid_caps_and_preserves_receipt_safety(self):
        now = datetime(2026, 11, 7, 12, tzinfo=timezone.utc).timestamp()
        path = self.root / 'usage.json'
        good = dict(timestamp='2026-11-07T12:00:00Z', ordinaryUsageAllowed=True, usedPercent=0)
        path.write_text(json.dumps(good))
        for cap in (True, False, 0, -1, float('nan'), float('inf'), -float('inf'), 101, None, '100'):
            with self.subTest(cap=cap), self.assertRaises(ValueError):
                self.s.check_usage(path, now=now, max_used_percent=cap)
        for change in (dict(timestamp='2026-11-07T11:39:59Z'),
                       dict(timestamp='2026-11-07T12:00:01Z'),
                       dict(ordinaryUsageAllowed=False), dict(usedPercent=None),
                       dict(usedPercent=True), dict(usedPercent=float('nan'))):
            with self.subTest(change=change):
                path.write_text(json.dumps({**good, **change}))
                with self.assertRaises(ValueError):
                    self.s.check_usage(path, now=now, max_used_percent=100)

    def test_guard_uses_persisted_ceiling_and_defaults_legacy_state_to_65(self):
        path = self.root / 'usage.json'
        path.write_text(json.dumps(dict(timestamp=datetime.now(timezone.utc).isoformat(),
            ordinaryUsageAllowed=True, usedPercent=99)))
        st = dict(self.state, usage_file=str(path), max_used_percent=100)
        with patch.object(self.s, 'check_inputs'), \
             patch.object(self.s.helpers(), 'check_model_processes'), \
             patch.object(self.s.helpers(), 'read_power', return_value={'ac': True, 'percent': 90}):
            self.s.guard(st, {})
            self.assertEqual(st['last_usage']['usedPercent'], 99)
            del st['max_used_percent']
            with self.assertRaises(ValueError):
                self.s.guard(st, {})
            st['max_used_percent'] = float('nan')
            with self.assertRaises(ValueError):
                self.s.guard(st, {})

    def test_cli_forwards_default_and_explicit_quota_ceiling(self):
        argv = ['controller', 'start', '--jobs', 'jobs', '--admission', 'admission',
            '--out', 'out', '--python', sys.executable, '--expected-head', 'a' * 40,
            '--usage-file', 'usage']
        for options, expected in (([], 65), (['--max-used-percent', '100'], 100)):
            with self.subTest(options=options), patch.object(sys, 'argv', argv + options), \
                 patch.object(self.s, 'run_supervisor', return_value=dict(
                     status='complete', out='out', completed_games=7800)) as run, \
                 redirect_stdout(io.StringIO()):
                self.s.main()
                self.assertEqual(run.call_args.kwargs['max_used_percent'], expected)

    def test_receipt_requires_successful_exit_full_csv_and_current_input_hashes(self):
        st = self.state
        (self.root / 'seeds.json').write_text('[1400000]')
        command = self.s.job_command(st, 'one')
        (self.out / 'one.csv').write_text('complete csv bytes')
        st['jobs']['one'] = dict(returncode=1, argv=command)
        with patch.object(self.s, 'check_inputs'), patch.object(self.s, 'validate_job_csv', return_value=[{}, {}]):
            with self.assertRaisesRegex(ValueError, 'exit'):
                self.s.write_receipt(st, 'one')
            st['jobs']['one']['returncode'] = 0
            with patch.object(self.s, 'validate_job_csv', side_effect=ValueError('incomplete')):
                with self.assertRaisesRegex(ValueError, 'incomplete'):
                    self.s.write_receipt(st, 'one')
            self.assertFalse((self.out / 'receipts/one.json').exists())
            receipt = self.s.write_receipt(st, 'one')
        saved = json.loads((self.out / 'receipts/one.json').read_text())
        self.assertEqual(saved['status'], 'complete')
        self.assertEqual(saved['rows'], 2)
        self.assertEqual(saved['model_sha256'], 'b' * 64)
        self.assertEqual(saved['opponent_sha256'], {'opponent.pth': 'c' * 64})
        self.assertEqual(saved['csv_sha256'], sha(self.out / 'one.csv'))
        self.assertEqual(saved['seed_list_sha256'], sha(self.root / 'seeds.json'))
        self.assertEqual(receipt['rows'], 2)

    def test_guard_checks_stop_before_launch_and_refreshes_quota(self):
        h = self.s.helpers()
        st = self.state
        st['usage_file'] = str(self.root / 'usage.json')
        with patch.object(self.s, 'check_inputs'), patch.object(h, 'check_model_processes'), \
             patch.object(h, 'read_power', return_value={'ac': True, 'percent': 75}), \
             patch.object(self.s, 'check_usage', side_effect=ValueError('quota stale')):
            with self.assertRaisesRegex(ValueError, 'quota stale'):
                self.s.guard(st, {})
            self.s.request_stop(st['stop_file'])
            with self.assertRaises(self.s.StopRequested):
                self.s.guard(st, {})

    def test_changed_frozen_inputs_protected_files_or_source_are_rejected(self):
        st = self.state
        target = self.root / 'input.json'
        target.write_text('original')
        st['inputs'] = {str(target): sha(target)}
        with patch.object(self.s.helpers(), 'source_identity', return_value=st['source']):
            self.s.check_inputs(st)
            target.write_text('changed')
            with self.assertRaisesRegex(ValueError, 'inputs'):
                self.s.check_inputs(st)
            st['inputs'] = {}
            st['protected'] = {str(target): '0' * 64}
            with self.assertRaisesRegex(ValueError, 'Protected'):
                self.s.check_inputs(st)
        with patch.object(self.s.helpers(), 'source_identity', return_value={'head': 'd' * 40}):
            with self.assertRaisesRegex(ValueError, 'source'):
                self.s.check_inputs(st)

    def test_launch_reservation_cannot_be_reused_with_another_output(self):
        st = self.state
        st.update(max_used_percent=100, reservation=str(self.root / 'selection_launch.json'), provenance=dict(
            model_sha256=st['model_sha256'], source_identity=st['source']))
        self.s.reserve_launch(st)
        self.assertEqual(json.loads(Path(st['reservation']).read_text())['max_used_percent'], 100)
        self.assertTrue((self.out / 'provenance.json').exists())
        self.assertIn(str(self.out / 'provenance.json'), st['inputs'])
        st['out'] = str(self.root / 'second')
        Path(st['out']).mkdir()
        with self.assertRaises(FileExistsError):
            self.s.reserve_launch(st)

    def test_queue_keeps_two_slots_and_stops_all_peers_after_failure(self):
        for failure in (None, 'exit', 'csv', 'quota', 'stop'):
            with self.subTest(failure=failure):
                st = dict(self.state, queue=['one', 'two', 'three'], jobs={}, receipts={}, active=[])
                launches, cleaned, counts, ticks = [], [], [], [0]
                def guard(st, owned):
                    if ticks[0] and failure == 'quota':
                        raise ValueError('quota stale')
                    if ticks[0] and failure == 'stop':
                        raise self.s.StopRequested('STOP')
                    return {'ac': True, 'percent': 90}
                def spawn(st, name, command, owned):
                    launches.append(name)
                    code = 1 if failure == 'exit' and name == 'one' else 0
                    p = SimpleNamespace(pid=100 + len(launches), poll=lambda: code)
                    owned[name] = dict(process=p, owner_pid=os.getpid(), pgid=p.pid)
                    st['jobs'][name] = dict(returncode=None, argv=command)
                    counts.append(len(owned))
                def receipt(st, name):
                    if failure == 'csv' and name == 'one':
                        raise ValueError('incomplete CSV')
                    return dict(rows=2)
                with ExitStack() as stack:
                    for name, value in [('guard', guard), ('spawn_owned', spawn),
                                        ('write_receipt', receipt)]:
                        stack.enter_context(patch.object(self.s, name, value))
                    stack.enter_context(patch.object(self.s.helpers(), 'group_exists', return_value=False))
                    stack.enter_context(patch.object(self.s, 'shutdown_owned',
                        side_effect=lambda owned: cleaned.extend(owned)))
                    stack.enter_context(redirect_stdout(io.StringIO()))
                    stack.enter_context(patch.object(self.s.time, 'sleep',
                        side_effect=lambda _: ticks.__setitem__(0, ticks[0] + 1)))
                    if failure:
                        with self.assertRaises((ValueError, self.s.StopRequested)):
                            self.s.run_queue(st)
                        self.assertEqual(launches, ['one', 'two'])
                        self.assertEqual(st['queue'], ['three'])
                        self.assertTrue(cleaned)
                    else:
                        self.s.run_queue(st)
                        self.assertEqual(st['status'], 'complete')
                        self.assertEqual(launches, ['one', 'two', 'three'])
                        self.assertEqual(st['completed_games'], 6)
                self.assertLessEqual(max(counts), 2)

    def test_build_state_rejects_nonadmitted_wrong_hash_and_unsafe_output(self):
        # Real hash/path and admission handling; only source and fixed-plan parsing are external seams.
        st = self.state
        model = self.root / 'model.pth'
        model.write_text('fixed model')
        seeds = self.root / 'seeds.json'
        seeds.write_text('[1400000]')
        opponent = self.root / 'opponent.pth'
        opponent.write_text('fixed opponent')
        jobs = self.root / 'jobs.json'
        jobs.write_text(json.dumps(dict(roles={'V14': 'model.pth'}, opponent_sha256={'opponent.pth': sha(opponent)})))
        admission = self.root / 'admission.json'
        admitted = dict(status='admitted', roles={'V14': dict(path='model.pth', sha256=sha(model))})
        admission.write_text(json.dumps(admitted))
        for name in ('agent_p0.pth', 'agent_p1.pth'):
            target = self.root / 'agents/sherlock/weights' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('fixed model')
        (self.root / 'Gruppe15.zip').write_text('zip')
        for relative in self.s.PLANS:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('fixed plan')
        fresh = self.out.parent / 'fresh'
        with ExitStack() as stack:
            stack.enter_context(patch.object(self.s, 'ROOT', self.root))
            stack.enter_context(patch.object(self.s, 'SOURCE_SHA', sha(model)))
            stack.enter_context(patch.object(self.s.helpers(), 'source_identity', return_value=st['source']))
            stack.enter_context(patch.object(self.s, 'validate_plan', return_value=list(st['job_plan'].values())))
            stack.enter_context(patch.object(self.s.Path, 'cwd', return_value=self.root))
            built = self.s.build_state(jobs, admission, fresh, sys.executable, 'a' * 40,
                usage_file=self.root / 'usage.json')
            self.assertEqual(built['model_sha256'], {'V14': sha(model)})
            self.assertIn(str(admission), built['inputs'])
            self.assertEqual(built['max_used_percent'], 65)
            built = self.s.build_state(jobs, admission, fresh, sys.executable, 'a' * 40,
                usage_file=self.root / 'usage.json', max_used_percent=100)
            self.assertEqual(built['max_used_percent'], 100)
            compact_base = self.root / 'experiments/analysis/ensemble_diversity_20261108_compact'
            protocol = self.root / 'docs/superpowers/plans/2026-11-08-ensemble-compact.md'
            protocol.write_text('compact protocol')
            plan = json.loads(jobs.read_text())
            jobs.write_text(json.dumps({**plan, 'profile': 'compact20261108'}))
            compact = self.s.build_state(jobs, admission, compact_base / 'fresh', sys.executable, 'a' * 40,
                usage_file=self.root / 'usage.json', profile='compact20261108', max_used_percent=100)
            self.assertEqual(compact['profile'], 'compact20261108')
            self.assertEqual(compact['provenance']['profile'], 'compact20261108')
            self.assertEqual(compact['reservation'], str(compact_base / 'selection_launch.json'))
            self.assertIn(str(protocol), compact['plans'])
            with self.assertRaisesRegex(ValueError, 'profile'):
                self.s.build_state(jobs, admission, compact_base / 'fresh', sys.executable, 'a' * 40,
                    usage_file=self.root / 'usage.json')
            with patch.object(self.s, 'validate_plan', side_effect=AssertionError('confirmation seeds read early')), \
                 patch.object(self.s, 'selection_evidence', side_effect=ValueError('missing compact selection')):
                with self.assertRaisesRegex(ValueError, 'missing compact selection'):
                    self.s.build_state(jobs, admission, compact_base / 'fresh', sys.executable, 'a' * 40,
                        usage_file=self.root / 'usage.json', profile='compact20261108',
                        phase='confirmation', nominee='A39')
            jobs.write_text(json.dumps(plan))
            for cap in (True, 0, -1, float('nan'), float('inf'), 101):
                with self.subTest(cap=cap), self.assertRaises(ValueError):
                    self.s.build_state(jobs, admission, fresh, sys.executable, 'a' * 40,
                        usage_file=self.root / 'usage.json', max_used_percent=cap)
            with patch.object(self.s, 'validate_plan', side_effect=AssertionError('confirmation seeds read early')), \
                 patch.object(self.s, 'selection_evidence', side_effect=ValueError('missing selection')):
                with self.assertRaisesRegex(ValueError, 'missing selection'):
                    self.s.build_state(jobs, admission, fresh, sys.executable, 'a' * 40,
                        usage_file=self.root / 'usage.json', phase='confirmation', nominee='A39')
            for changed in (dict(admitted, status='partial'), dict(admitted, roles={'V14': dict(path='model.pth', sha256='0' * 64)})):
                admission.write_text(json.dumps(changed))
                with self.assertRaises(ValueError):
                    self.s.build_state(jobs, admission, fresh, sys.executable, 'a' * 40,
                        usage_file=self.root / 'usage.json')
            admission.write_text(json.dumps(admitted))
            with self.assertRaisesRegex(ValueError, 'output'):
                self.s.build_state(jobs, admission, self.root / 'agents/new', sys.executable, 'a' * 40,
                    usage_file=self.root / 'usage.json')


    def test_group_permission_race_requires_independent_empty_process_snapshot(self):
        with patch.object(self.s.helpers(), 'group_exists', side_effect=PermissionError), \
             patch.object(self.s.subprocess, 'check_output', return_value='111\n222\n'):
            self.assertFalse(self.s.group_alive(333))
        with patch.object(self.s.helpers(), 'group_exists', side_effect=PermissionError), \
             patch.object(self.s.subprocess, 'check_output', return_value='111\n333\n'):
            with self.assertRaises(PermissionError):
                self.s.group_alive(333)
        with patch.object(self.s.helpers(), 'group_exists', side_effect=PermissionError), \
             patch.object(self.s.subprocess, 'check_output', side_effect=OSError('ps failed')):
            with self.assertRaises(OSError):
                self.s.group_alive(333)

    def test_shutdown_reaps_before_probe_and_only_signals_owned_groups(self):
        events = []
        p = SimpleNamespace(pid=401, poll=lambda: events.append('poll') or 0,
                            wait=lambda timeout: events.append('wait') or 0)
        child = dict(process=p, pgid=401, owner_pid=os.getpid())
        def alive(pgid):
            self.assertEqual(events[0], 'poll')
            events.append('probe')
            return False
        with patch.object(self.s, 'group_alive', side_effect=alive):
            self.s.shutdown_owned({'one': child})
        self.assertIn('wait', events)
        with self.assertRaisesRegex(ValueError, 'unowned'):
            self.s.shutdown_owned({'one': dict(child, owner_pid=-1)})

    def test_confirmation_rejects_arbitrary_digest_bound_evidence(self):
        st = self.state
        reservation = self.out.parent / 'selection_launch.json'
        provenance = dict(model_sha256={'V14': 'b' * 64, 'A39': 'c' * 64}, source_identity=st['source'])
        (self.out / 'provenance.json').write_text(json.dumps(provenance))
        (self.out / 'state.json').write_text(json.dumps(dict(status='complete', completed_games=7800)))
        reservation.write_text(json.dumps(dict(out=str(self.out), source_identity=st['source'])))
        jobs = self.root / 'selection_jobs.json'
        jobs.write_text('{}')
        selected = dict(status='complete', phase='selection', jobs=39, games=7800, nominee='A39',
            input_sha256=dict(plan=sha(jobs), provenance=sha(self.out / 'provenance.json'), csv={}, receipts={}))
        for i in range(39):
            name = f'job_{i}'
            csv = self.out / f'{name}.csv'
            receipt = self.out / 'receipts' / f'{name}.json'
            csv.write_text('csv')
            receipt.write_text('{}')
            selected['input_sha256']['csv'][name] = sha(csv)
            selected['input_sha256']['receipts'][name] = sha(receipt)
        summary = self.out / 'summary.json'
        summary.write_text(json.dumps(selected))
        reservation.write_text(json.dumps(dict(out=str(self.out), jobs_path=str(jobs), source_identity=st['source'])))
        with patch.object(self.s, 'ROOT', self.root), self.assertRaises(ValueError):
            self.s.selection_evidence('A39', st['source'], {'V14': 'b' * 64, 'A39': 'c' * 64})

    def test_confirmation_recomputes_ranking_and_accepts_only_the_exact_saved_report(self):
        # Reuse the analysis suite's complete synthetic 39-job/7800-row fixture.
        # Only opponent byte pins are replaced; plan/receipt/row/stat validation is real.
        import pytest
        from scripts import ensemble_diversity_compare as compare
        spec = importlib.util.spec_from_file_location('comparison_test_fixtures',
            Path(__file__).with_name('test_ensemble_diversity_compare.py'))
        fixtures = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixtures)
        with pytest.MonkeyPatch.context() as monkeypatch:
            planned = fixtures.planned.__wrapped__(self.root, monkeypatch)
            block = fixtures.completed_block(planned)
            root = block['root']
            output = root / self.s.ANALYSIS / 'selection_results'
            block['result_dir'].rename(output)
            block.update(result_dir=output, provenance=output / 'provenance.json')
            for path in (output / 'receipts').glob('*.json'):
                receipt = json.loads(path.read_text())
                receipt['command'][-1] = str(output / f'{path.stem}.csv')
                path.write_text(json.dumps(receipt))
            report = compare.analyze(**block)
            self.assertEqual(report['nominee'], 'A39')
            summary = output / 'summary.json'
            summary.write_text(json.dumps(report))
            (output / 'state.json').write_text(json.dumps(dict(status='complete', completed_games=7800)))
            provenance = json.loads(block['provenance'].read_text())
            source, models = provenance['source_identity'], provenance['model_sha256']
            reservation = root / self.s.ANALYSIS / 'selection_launch.json'
            reservation.write_text(json.dumps(dict(out=str(output), jobs_path=str(block['jobs_json']),
                                                  source_identity=source)))
            with patch.object(self.s, 'ROOT', root):
                paths = self.s.selection_evidence('A39', source, {role: models[role] for role in ('V14', 'A39')})
                self.assertIn(summary, paths)
                summary.write_text(json.dumps({**report, 'nominee': 'B39'}))
                with self.assertRaisesRegex(ValueError, 'recomputed'):
                    self.s.selection_evidence('B39', source, {role: models[role] for role in ('V14', 'B39')})
                summary.write_text(json.dumps(report))
                (output / 'A39_panel_0.csv').write_text('changed')
                with self.assertRaisesRegex(ValueError, 'hash'):
                    self.s.selection_evidence('A39', source, {role: models[role] for role in ('V14', 'A39')})

    def test_controller_captures_error_and_cleans_owned_wake_on_failure(self):
        st = dict(self.state, out=str(self.out.parent / 'fresh'), reservation=str(self.root / 'reservation.json'))
        st['provenance'] = dict(model_sha256=st['model_sha256'], source_identity=st['source'])
        events, inherited_masks = [], []
        @contextmanager
        def lock(root):
            events.append('lock')
            try:
                yield
            finally:
                events.append('unlock')
        wake = SimpleNamespace(pid=900, poll=lambda: None, returncode=0,
            terminate=lambda: events.append('terminate'), wait=lambda timeout: 0)
        def spawn_wake(*args, **kwargs):
            inherited_masks.append(self.s.signal.pthread_sigmask(self.s.signal.SIG_BLOCK, []))
            return wake
        with ExitStack() as stack:
            stack.enter_context(patch.object(self.s.helpers(), 'compute_lock', lock))
            stack.enter_context(patch.object(self.s.helpers(), 'check_model_processes'))
            build = stack.enter_context(patch.object(self.s, 'build_state', return_value=st))
            stack.enter_context(patch.object(self.s, 'guard', return_value={'ac': True, 'percent': 80}))
            stack.enter_context(patch.object(self.s, 'run_queue', side_effect=ValueError('bad CSV')))
            stack.enter_context(patch.object(self.s.subprocess, 'Popen', side_effect=spawn_wake))
            with self.assertRaisesRegex(ValueError, 'bad CSV'):
                self.s.run_supervisor('jobs', 'admission', 'out', sys.executable, 'a' * 40,
                                      usage_file='usage', stop_file=st['stop_file'], max_used_percent=100)
            self.assertEqual(build.call_args.kwargs['max_used_percent'], 100)
        self.assertEqual(events.count('lock'), 1)
        self.assertEqual(events.count('unlock'), 1)
        self.assertEqual(events.count('terminate'), 1)
        self.assertNotIn(self.s.signal.SIGTERM, inherited_masks[0])
        self.assertIn('bad CSV', (Path(st['out']) / 'controller.log').read_text())
        saved = json.loads((Path(st['out']) / 'state.json').read_text())
        self.assertEqual(saved['status'], 'failed')
        self.assertEqual(saved['wake']['returncode'], 0)



    def test_queue_waits_at_34_and_starts_at_35_percent(self):
        st = self.state
        ticks, launches = [0], []
        def guard(state, owned):
            return {'ac': False, 'percent': 34 if ticks[0] == 0 else 35}
        def spawn(state, name, command, owned):
            self.assertGreater(ticks[0], 0)
            launches.append(name)
            p = SimpleNamespace(pid=100 + len(launches), poll=lambda: 0)
            owned[name] = dict(process=p, pgid=p.pid, owner_pid=os.getpid())
            state['jobs'][name] = dict(pid=p.pid, returncode=None)
        with ExitStack() as stack:
            for name, value in [('guard', guard), ('spawn_owned', spawn)]:
                stack.enter_context(patch.object(self.s, name, value))
            stack.enter_context(patch.object(self.s, 'write_receipt', return_value=dict(rows=2)))
            stack.enter_context(patch.object(self.s, 'group_alive', return_value=False))
            stack.enter_context(patch.object(self.s, 'shutdown_owned'))
            stack.enter_context(patch.object(self.s.time, 'sleep',
                side_effect=lambda _: ticks.__setitem__(0, ticks[0] + 1)))
            stack.enter_context(redirect_stdout(io.StringIO()))
            self.s.run_queue(st)
        self.assertEqual(launches, ['one', 'two', 'three'])
        self.assertEqual(st['status'], 'complete')

    def test_live_guard_stops_at_25_without_ac(self):
        self.state['usage_file'] = 'usage.json'
        with patch.object(self.s, 'check_usage', return_value={}), \
             patch.object(self.s, 'check_inputs'), \
             patch.object(self.s.helpers(), 'check_model_processes'), \
             patch.object(self.s.helpers(), 'read_power', return_value={'ac': False, 'percent': 25}):
            with self.assertRaisesRegex(ValueError, 'Battery'):
                self.s.guard(self.state, {})

    def test_spawn_registers_own_group_and_refuses_third_or_duplicate_job(self):
        st, owned = self.state, {}
        calls = []
        def popen(command, **kwargs):
            calls.append((command, kwargs))
            return SimpleNamespace(pid=500 + len(calls))
        with patch.object(self.s.helpers().subprocess, 'Popen', side_effect=popen):
            self.s.spawn_owned(st, 'one', self.s.job_command(st, 'one'), owned)
            self.s.spawn_owned(st, 'two', self.s.job_command(st, 'two'), owned)
            with self.assertRaisesRegex(ValueError, 'Duplicate/excess'):
                self.s.spawn_owned(st, 'three', self.s.job_command(st, 'three'), owned)
            with self.assertRaisesRegex(ValueError, 'Duplicate/excess'):
                self.s.spawn_owned(st, 'one', self.s.job_command(st, 'one'), owned)
        self.assertEqual(st['jobs']['one']['pid'], 501)
        self.assertEqual(st['jobs']['one']['pgid'], 501)
        self.assertEqual(owned['one']['owner_pid'], os.getpid())
        self.assertTrue(calls[0][1]['start_new_session'])
        self.assertEqual(calls[0][1]['env']['OMP_NUM_THREADS'], '1')
        self.assertEqual(calls[0][0][4:], st['jobs']['one']['argv'])

    def test_shutdown_signals_both_peers_then_waits_grace_before_kill(self):
        events, now = [], [0.0]
        children = {str(pid): dict(owner_pid=os.getpid(), pgid=pid,
            process=SimpleNamespace(pid=pid, poll=lambda: None, wait=lambda timeout: 0)) for pid in (801, 802)}
        with patch.object(self.s, 'group_alive', side_effect=lambda _: now[0] < 181), \
             patch.object(self.s.os, 'getpgid', side_effect=lambda pid: pid), \
             patch.object(self.s.os, 'killpg', side_effect=lambda pid, sig: events.append((pid, sig, now[0]))), \
             patch.object(self.s.time, 'monotonic', side_effect=lambda: now[0]), \
             patch.object(self.s.time, 'sleep', side_effect=lambda seconds: now.__setitem__(0, now[0] + seconds)):
            self.s.shutdown_owned(children, grace=180)
        self.assertEqual(events[:2], [(801, self.s.signal.SIGTERM, 0), (802, self.s.signal.SIGTERM, 0)])
        self.assertTrue(all(at >= 180 for _, sig, at in events if sig == self.s.signal.SIGKILL))

    def test_paths_reject_symlinks_hardlinks_and_repository_escape(self):
        source = self.root / 'model'
        source.write_text('bytes')
        (self.root / 'symlink').symlink_to(source)
        os.link(source, self.root / 'hardlink')
        for relative in ('symlink', 'hardlink', '../foreign'):
            with self.subTest(path=relative), self.assertRaises(ValueError):
                self.s.repo_path(self.root, relative)


def test_compact_confirmation_binds_profile_and_recomputes_before_accepting(tmp_path, monkeypatch):
    """A complete compact selection is accepted only under its exact profile/ranking."""
    import pytest
    from scripts import ensemble_diversity_compare as compare
    supervisor = importlib.import_module(MODULE)
    spec = importlib.util.spec_from_file_location('compact_test_fixtures',
        Path(__file__).with_name('test_ensemble_diversity_compare.py'))
    fixtures = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)
    planned = fixtures.compact_plan(*fixtures.planned.__wrapped__(tmp_path, monkeypatch))
    block = fixtures.completed_block(planned)
    root = block['root']
    base = root / 'experiments/analysis/ensemble_diversity_20261108_compact'
    output = base / 'selection_results'
    block['result_dir'].rename(output)
    block.update(result_dir=output, provenance=output / 'provenance.json')
    for path in (output / 'receipts').glob('*.json'):
        receipt = json.loads(path.read_text())
        receipt['command'][-1] = str(output / f'{path.stem}.csv')
        path.write_text(json.dumps(receipt))
    report = compare.analyze(**block)
    summary = output / 'summary.json'
    summary.write_text(json.dumps(report))
    completed = dict(profile='compact20261108', status='complete', completed_games=1560)
    (output / 'state.json').write_text(json.dumps(completed))
    provenance = json.loads(block['provenance'].read_text())
    source, models = provenance['source_identity'], provenance['model_sha256']
    launch = dict(profile='compact20261108', out=str(output), jobs_path=str(block['jobs_json']),
                  source_identity=source)
    reservation = base / 'selection_launch.json'
    reservation.write_text(json.dumps(launch))
    monkeypatch.setattr(supervisor, 'ROOT', root)
    selected_models = {role: models[role] for role in ('V14', 'A39')}
    paths = supervisor.selection_evidence('A39', source, selected_models, profile='compact20261108')
    assert summary in paths
    # Saved summary nominee tampering cannot authorize a different confirmation.
    summary.write_text(json.dumps({**report, 'nominee': 'B39'}))
    with pytest.raises(ValueError, match='recomputed'):
        supervisor.selection_evidence('B39', source, {role: models[role] for role in ('V14', 'B39')},
                                      profile='compact20261108')
    summary.write_text(json.dumps(report))
    for target, original in ((reservation, launch), (summary, report),
                             (output / 'state.json', completed)):
        target.write_text(json.dumps({**original, 'profile': 'full20261107'}))
        with pytest.raises(ValueError, match='profile'):
            supervisor.selection_evidence('A39', source, selected_models, profile='compact20261108')
        target.write_text(json.dumps(original))
    with pytest.raises(ValueError, match='provenance'):
        supervisor.selection_evidence('A39', {**source, 'head': 'f' * 40}, selected_models,
                                      profile='compact20261108')


def test_compact_cli_requires_explicit_profile_and_persists_launch(tmp_path):
    supervisor = importlib.import_module(MODULE)
    argv = ['controller', 'start', '--jobs', 'jobs', '--admission', 'admission', '--out', 'out',
            '--python', sys.executable, '--expected-head', 'a' * 40, '--usage-file', 'usage',
            '--profile', 'compact20261108', '--max-used-percent', '100']
    with patch.object(sys, 'argv', argv), patch.object(supervisor, 'run_supervisor',
            return_value=dict(status='complete', out='out', completed_games=1560)) as run, \
            redirect_stdout(io.StringIO()):
        supervisor.main()
        assert run.call_args.kwargs['profile'] == 'compact20261108'
        assert run.call_args.kwargs['max_used_percent'] == 100
    out = tmp_path / 'out'
    out.mkdir()
    state = dict(profile='compact20261108', reservation=str(tmp_path / 'selection_launch.json'),
                 phase='selection', out=str(out), jobs_path='jobs', source={'head': 'a' * 40},
                 provenance={'profile': 'compact20261108'}, inputs={})
    supervisor.reserve_launch(state)
    assert json.loads(Path(state['reservation']).read_text())['profile'] == 'compact20261108'


if __name__ == '__main__':
    unittest.main()
