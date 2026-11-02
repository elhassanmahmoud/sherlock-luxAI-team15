"""Pure stdlib checks. No real environment, model loading, or policy execution."""
import csv
from contextlib import nullcontext
import importlib.util
import contextlib
import io
import json
import os
import signal
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get('TARGETING_SOURCE_ROOT', Path.cwd())).resolve()


class DriverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = HERE / 'targeting_eval_driver.py'
        if not path.is_file():
            return
        spec = importlib.util.spec_from_file_location('targeting_eval_driver', path)
        cls.driver = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.driver)

    def test_runner_exists(self):
        self.assertTrue((HERE / 'targeting_eval_driver.py').is_file())

    def setUp(self):
        if not hasattr(self, 'driver') and self._testMethodName != 'test_runner_exists':
            self.skipTest('driver has not been implemented')
        self.temporary = tempfile.TemporaryDirectory(dir=Path('/tmp').resolve())
        self.addCleanup(self.temporary.cleanup)
        self.out = Path(self.temporary.name)
        self.weights = dict(baseline='/weights/v14.pth', P='/weights/p.pth', PT='/weights/pt.pth')

    def test_exact_selection_jobs_counts_and_full_release_labels(self):
        jobs = self.driver.build_jobs(REPO, self.out, self.weights, 'selection')
        self.assertEqual(len(jobs), 5)
        self.assertEqual(sum(j['games'] for j in jobs), 4600)
        self.assertEqual({who: sum(j['games'] for j in jobs if j['role'] == who)
                          for who in ('baseline', 'P', 'PT')}, dict(baseline=1400, P=1600, PT=1600))
        panel = next(j for j in jobs if j['name'] == 'baseline_panel')
        self.assertEqual(panel['opponents'], ['solution92', 'sol92_sq',
            'self:experiments/releases/20261022_all18_v3/agent_p0.pth',
            'self:experiments/releases/20261022_v7_Bsnpd/agent_p0.pth',
            'self:experiments/releases/20261022_v10_baseline/agent_p0.pth',
            'self:experiments/releases/20261101_v13_neb/agent_p0.pth', 'default'])
        self.assertTrue(all(j['first_seed'] == 841000 and j['n_maps'] == 100 for j in jobs))
        self.assertTrue(all(j['workers'] == 2 and j['engine'] == 'par_eval' for j in jobs))
        self.assertEqual([j['games'] for j in jobs], [1400, 1400, 200, 1400, 200])
        self.assertEqual([j['timing_class'] for j in jobs],
                         ['combined_panel', 'combined_panel', 'direct', 'combined_panel', 'direct'])
        self.assertTrue(all(j['overrides'] == ['point_pair_swap=false', 'art_move_guard=false']
                            for j in jobs if j['role'] == 'baseline'))
        self.assertTrue(all(j['overrides'] == ['point_pair_swap=true', 'art_move_guard=true']
                            for j in jobs if j['role'] in ('P', 'PT')))

    def test_confirmation_has_exact_9000_keys_and_only_one_nominee(self):
        jobs = self.driver.build_jobs(REPO, self.out, self.weights, 'confirmation', candidate='PT')
        self.assertEqual(len(jobs), 3)
        self.assertEqual(sum(j['games'] for j in jobs), 9000)
        self.assertEqual({j['role'] for j in jobs}, {'baseline', 'PT'})
        self.assertEqual(sum(j['games'] for j in jobs if j['name'].endswith('_direct')), 600)
        self.assertEqual({j['first_seed'] for j in jobs if j['name'].endswith('_direct')}, {843000})
        self.assertEqual({j['first_seed'] for j in jobs if not j['name'].endswith('_direct')}, {842000})
        with self.assertRaises(ValueError):
            self.driver.build_jobs(REPO, self.out, self.weights, 'confirmation', candidate='backup')

    def test_predeclared_p_only_has_three_selection_jobs_and_no_pt_confirmation(self):
        d = self.driver
        weights = {key: self.weights[key] for key in ('baseline', 'P')}
        try:
            jobs = d.build_jobs(REPO, self.out, weights, 'selection')
        except ValueError as exc:
            self.fail(f'Predeclared P-only weight roster must be accepted: {exc}')
        self.assertEqual([j['name'] for j in jobs], ['baseline_panel', 'P_panel', 'P_direct'])
        self.assertEqual([j['games'] for j in jobs], [1400, 1400, 200])
        self.assertEqual(sum(j['games'] for j in jobs), 3000)
        self.assertTrue(all(j['workers'] == 2 for j in jobs))
        self.assertEqual({j['role'] for j in jobs}, {'baseline', 'P'})
        confirm = d.build_jobs(REPO, self.out, weights, 'confirmation', candidate='P')
        self.assertEqual(len(confirm), 3)
        self.assertEqual(sum(j['games'] for j in confirm), 9000)
        with self.assertRaises(ValueError):
            d.build_jobs(REPO, self.out, weights, 'confirmation', candidate='PT')
        for invalid in ({'baseline': 'b'}, {'baseline': 'b', 'PT': 'pt'}, dict(weights, extra='x')):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                d.build_jobs(REPO, self.out, invalid, 'selection')

    def test_freeze_accepts_exact_p_only_roster_and_rejects_missing_p(self):
        d = self.driver
        tools, frozen, freeze = self.phase_fixture()
        frozen.update(schema_version=1, expected_head='f'*40,
                      driver=dict(path=str(Path(d.__file__).resolve()), sha256=d.digest(d.__file__)))
        frozen['weights'] = {key: self.weights[key] for key in ('baseline', 'P')}
        freeze.write_text(json.dumps(frozen))
        with patch.object(d, 'identity', return_value=frozen['identity']), patch.object(d, 'load_tools', return_value=tools):
            try:
                checked = d.check_freeze(freeze)
            except ValueError as exc:
                self.fail(f'Frozen P-only roster is valid: {exc}')
            self.assertEqual(set(checked['weights']), {'baseline', 'P'})
            frozen['weights'] = dict(baseline=self.weights['baseline'], PT=self.weights['PT'])
            freeze.write_text(json.dumps(frozen))
            with self.assertRaises(ValueError):
                d.check_freeze(freeze)

    def test_power_thresholds_and_ac(self):
        d = self.driver
        for text, want in [
            ("Now drawing from 'Battery Power'\n -InternalBattery-0 65%; discharging;", (False,65)),
            ("Now drawing from 'AC Power'\n -InternalBattery-0 12%; charging;", (True,12))]:
            self.assertEqual(d.parse_power(text), want)
        self.assertTrue(d.power_allowed((False,35), start=True))
        self.assertFalse(d.power_allowed((False,34), start=True))
        self.assertTrue(d.power_allowed((False,26), start=False))
        self.assertFalse(d.power_allowed((False,25), start=False))
        self.assertTrue(d.power_allowed((True,2), start=True))
        with self.assertRaises(ValueError):
            d.parse_power('unknown state')

    def test_projection_includes_twenty_percent_and_hour_reserve(self):
        d = self.driver
        self.assertTrue(hasattr(d, 'effective_rates'), 'two-class projection is missing')
        observed = dict(combined_panel=[], direct=[])
        games = dict(combined_panel=100, direct=10)
        self.assertAlmostEqual(d.project_seconds(games, observed), 302.4)
        d.admit(games, observed, now=100, deadline=4002.5)
        with self.assertRaises(ValueError):
            d.admit(games, observed, now=100, deadline=4002.4)
        with self.assertRaises(ValueError):
            d.project_seconds(games, dict(combined_panel=[float('nan')], direct=[]))

    def test_class_costs_and_global_slowdown_never_reduce_known_costs(self):
        d = self.driver
        self.assertTrue(hasattr(d, 'effective_rates'), 'two-class projection is missing')
        rates, slowdown = d.effective_rates(dict(combined_panel=[2.0], direct=[2.9848]))
        self.assertEqual(rates, dict(combined_panel=2.22, direct=3.0))
        self.assertEqual(slowdown, 1.)
        for observed in (dict(combined_panel=[4.44, 2.0], direct=[2.9]),
                         dict(combined_panel=[2.0], direct=[6.0, 3.0])):
            with self.subTest(observed=observed):
                rates, slowdown = d.effective_rates(observed)
                self.assertEqual(rates, dict(combined_panel=4.44, direct=6.0))
                self.assertEqual(slowdown, 2.)
                self.assertAlmostEqual(d.project_seconds(dict(combined_panel=100, direct=10), observed), 604.8)
        with self.assertRaises(ValueError):
            d.effective_rates(dict(combined_panel=[0.], direct=[]))
        with self.assertRaises(ValueError):
            d.project_seconds(dict(combined_panel=True, direct=0), dict(combined_panel=[], direct=[]))

    def test_no_default_adapter_cli_and_all_commands_use_par_eval(self):
        d = self.driver
        self.assertFalse(hasattr(d, 'default_worker'), 'default monkeypatch adapter must be removed')
        jobs = d.build_jobs(REPO, self.out, self.weights, 'selection')
        self.assertTrue(hasattr(d, 'job_command'), 'fixed evaluator command boundary missing')
        for job in jobs:
            command = d.job_command(job, '/explicit/python')
            self.assertEqual(command[:4], ['/explicit/python', '-B', '-m', 'scripts.par_eval'])
            self.assertEqual(command[command.index('--workers') + 1], '2')
            self.assertEqual(command[command.index('--opponents') + 1].split(','), job['opponents'])
        with patch.object(__import__('sys'), 'argv', ['driver', 'worker', '--help']), \
             contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as stopped:
                d.main()
        self.assertEqual(stopped.exception.code, 2)

    def test_fresh_output_rejects_existing_symlink_and_inputs(self):
        d = self.driver
        target = self.out / 'fresh'
        self.assertEqual(d.new_path(target), target)
        target.write_text('keep')
        with self.assertRaises(FileExistsError):
            d.new_path(target)
        alias = self.out / 'alias'
        alias.symlink_to(self.out, target_is_directory=True)
        with self.assertRaises(ValueError):
            d.new_path(alias / 'new')
        self.assertEqual(target.read_text(), 'keep')

    def test_macos_system_tmp_alias_is_canonicalized_without_allowing_user_symlinks(self):
        if not Path('/tmp').is_symlink():
            self.skipTest('macOS system /tmp alias only')
        logical = Path('/tmp') / self.out.relative_to(Path('/tmp').resolve()) / 'fresh'
        self.assertEqual(self.driver.new_path(logical), self.out / 'fresh')

    def test_csv_exact_keys_v2_303_and_numerical_semantics(self):
        d = self.driver
        tools = d.load_tools(REPO)
        job = dict(first_seed=841000, n_maps=1, opponents=['default'], games=2)
        fields = tools.early.GAME_FIELDS
        row = {key: 0 for key in fields}
        row.update(seed=841000, opponent='default', result=1, game_win=1, point_win=1,
                   our_wins=2, opp_wins=1, our_points=10, opp_points=9,
                   point_counting_version=2, steps=303)
        path = self.out / 'games.csv'

        def write(rows):
            with path.open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader(); writer.writerows(rows)

        rows = [dict(row, side=side) for side in ('player_0', 'player_1')]
        write(rows)
        self.assertEqual(d.validate_csv(path, job, tools), 2)
        for change in (dict(steps=302), dict(point_counting_version=1), dict(result=.5),
                       dict(seed=900000), dict(secs='nan'), dict(wait_frac=2), dict(seed=841000.5)):
            write([dict(rows[0], **change), rows[1]])
            with self.subTest(change=change), self.assertRaises(ValueError):
                d.validate_csv(path, job, tools)
        write([rows[0], rows[0]])
        with self.assertRaises(ValueError):
            d.validate_csv(path, job, tools)

    def test_execution_entrypoints_exist_without_starting_on_import(self):
        for name in ('create_freeze', 'prepare_phase', 'run_phase', 'run_job',
                     'job_command', 'check_selection_summary'):
            self.assertTrue(hasattr(self.driver, name), name)

    def test_selection_summary_binds_nominee_plan_freeze_and_every_csv(self):
        d = self.driver
        self.assertTrue(hasattr(d, 'check_selection_summary'), 'summary guard missing')
        csvpath = self.out / 'one.csv'
        csvpath.write_text('synthetic')
        selection = dict(phase='selection', status='complete', nominee='PT',
                         plan_sha256='a'*64, study_freeze_sha256='b'*64,
                         csv_sha256={str(csvpath): d.digest(csvpath)})
        receipt = dict(status='complete', phase='selection', plan_sha256='a'*64,
                       study_freeze_sha256='b'*64,
                       jobs=[dict(out=str(csvpath), output_sha256=d.digest(csvpath))])
        summary = self.out / 'summary.json'
        summary.write_text(json.dumps(selection))
        d.check_selection_summary(summary, 'PT', receipt)
        for change in (dict(nominee='P'), dict(status='running'), dict(phase='confirmation'),
                       dict(plan_sha256='c'*64), dict(study_freeze_sha256='c'*64), dict(csv_sha256={})):
            summary.write_text(json.dumps(dict(selection, **change)))
            with self.subTest(change=change), self.assertRaises(ValueError):
                d.check_selection_summary(summary, 'PT', receipt)
        summary.write_text(json.dumps(selection))
        csvpath.write_text('changed')
        with self.assertRaises(ValueError):
            d.check_selection_summary(summary, 'PT', receipt)

    def phase_fixture(self, weights=None):
        d = self.driver
        tools = d.load_tools(REPO)
        tools.early = SimpleNamespace(GAME_FIELDS=tools.early.GAME_FIELDS, read_rows=tools.early.read_rows,
                                     resource_lock=lambda root: nullcontext(), THREAD_ENV={})
        tools.jobs = SimpleNamespace(validate_inputs=lambda *args: None)
        frozen = dict(root=str(REPO), python='/synthetic/python', weights=weights or self.weights,
                      frozen_weights={}, identity=dict(source=dict(head='f'*40), weights={}))
        freeze_path = self.out / 'study_freeze.json'
        freeze_path.write_text(json.dumps(frozen))
        return tools, frozen, freeze_path

    def synthetic_job(self, job, plan_path, plan, frozen, tools, **kwargs):
        d = self.driver
        fields = tools.early.GAME_FIELDS
        row = {key: 0 for key in fields}
        row.update(result=.5, point_win=.5, point_counting_version=2, steps=303)
        with Path(job['out']).open('x', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for seed in range(job['first_seed'], job['first_seed'] + job['n_maps']):
                for side in ('player_0', 'player_1'):
                    for opponent in job['opponents']:
                        writer.writerow(dict(row, seed=seed, side=side, opponent=opponent))
        Path(job['log']).write_text('synthetic episode rows only; no environment')
        receipt = kwargs.get('record', {})
        receipt.update(name=job['name'], timing_class=job['timing_class'], status='complete', out=job['out'], log=job['log'], exit_code=0,
                       actual_games=d.validate_csv(job['out'], job, tools), output_sha256=d.digest(job['out']),
                       wall_seconds=job['games'] * 2.3)
        return receipt

    def test_full_synthetic_phase_and_confirmation_plan_reuse_shared_freeze(self):
        d = self.driver
        tools, frozen, freeze = self.phase_fixture()
        with patch.object(d, 'check_freeze', return_value=frozen), patch.object(d, 'load_tools', return_value=tools), \
             patch.object(d, 'identity', return_value=frozen['identity']), patch.object(d, 'check_foreign_jobs'), \
             patch.object(d, 'current_power', return_value=(True, 10)), patch.object(d.time, 'time', return_value=1), \
             patch.object(d, 'run_job', side_effect=self.synthetic_job):
            d.prepare_phase(freeze, self.out / 'selection', 'selection')
            plan = self.out / 'selection/plan.json'
            with self.assertRaises(ValueError):
                d.run_phase(plan)
            self.assertFalse((plan.parent / 'state.json').exists())
            state = d.run_phase(plan, start=True)
            self.assertEqual(state['status'], 'complete')
            self.assertEqual(state['completed_games'], 4600)
            self.assertEqual(state['source_before'], state['source_after'])
            self.assertAlmostEqual(state['projection']['effective_wall_seconds_per_game']['combined_panel'], 2.3)
            self.assertAlmostEqual(state['projection']['effective_wall_seconds_per_game']['direct'], 3.0 * 2.3 / 2.22)
            self.assertEqual(state['projection']['remaining_games'], dict(combined_panel=8400, direct=800))
            self.assertEqual(len(state['jobs']), 5)
            summary = self.out / 'summary.json'
            summary.write_text(json.dumps(dict(phase='selection', status='complete', nominee='PT',
                plan_sha256=d.digest(plan), study_freeze_sha256=d.digest(freeze),
                csv_sha256={r['out']: r['output_sha256'] for r in state['jobs']})))
            confirm = d.prepare_phase(freeze, self.out / 'confirmation', 'confirmation',
                candidate='PT', selection_state=plan.parent / 'state.json', selection_summary=summary)
            self.assertEqual(confirm['study_freeze_sha256'], state['study_freeze_sha256'])
            self.assertEqual(confirm['selection_summary_sha256'], d.digest(summary))
            self.assertEqual(sum(j['games'] for j in confirm['jobs']), 9000)
            self.assertEqual(confirm['initial_seconds_per_game'], dict(combined_panel=2.22, direct=3.0))
            self.assertEqual(confirm['future_confirmation_games'], dict(combined_panel=0, direct=0))
            self.assertEqual(confirm['prior_observed_seconds_per_game'],
                             dict(combined_panel=[2.3, 2.3, 2.3], direct=[2.3, 2.3]))
            with self.assertRaises(FileExistsError):
                d.run_phase(plan, start=True)
        self.assertNotIn('torch', __import__('sys').modules)

    def test_p_only_same_freeze_confirmation_and_late_pt_addition_is_rejected(self):
        d = self.driver
        weights = {key: self.weights[key] for key in ('baseline', 'P')}
        tools, frozen, freeze = self.phase_fixture(weights)
        with patch.object(d, 'check_freeze', return_value=frozen), patch.object(d, 'load_tools', return_value=tools), \
             patch.object(d, 'identity', return_value=frozen['identity']), patch.object(d, 'check_foreign_jobs'), \
             patch.object(d, 'current_power', return_value=(True, 10)), patch.object(d.time, 'time', return_value=1), \
             patch.object(d, 'run_job', side_effect=self.synthetic_job):
            try:
                d.prepare_phase(freeze, self.out / 'p_only_selection', 'selection')
            except ValueError as exc:
                self.fail(f'P-only prepare should bind the fixed smaller study before outcomes: {exc}')
            plan_path = self.out / 'p_only_selection/plan.json'
            state = d.run_phase(plan_path, start=True)
            self.assertEqual(state['completed_games'], 3000)
            summary = self.out / 'p_only_summary.json'
            summary.write_text(json.dumps(dict(phase='selection', status='complete', nominee='P',
                plan_sha256=d.digest(plan_path), study_freeze_sha256=d.digest(freeze),
                csv_sha256={row['out']: row['output_sha256'] for row in state['jobs']})))
            confirmation = d.prepare_phase(freeze, self.out / 'p_only_confirmation', 'confirmation', candidate='P',
                selection_state=plan_path.parent / 'state.json', selection_summary=summary)
            self.assertEqual(confirmation['study_freeze_sha256'], state['study_freeze_sha256'])
            self.assertEqual(sum(j['games'] for j in confirmation['jobs']), 9000)
            with self.assertRaises(ValueError):
                d.prepare_phase(freeze, self.out / 'forbidden_pt', 'confirmation', candidate='PT',
                    selection_state=plan_path.parent / 'state.json', selection_summary=summary)
            self.assertFalse((self.out / 'forbidden_pt').exists())
            frozen['weights'] = dict(self.weights)
            freeze.write_text(json.dumps(frozen))
            with self.assertRaises(ValueError):
                d.prepare_phase(freeze, self.out / 'late_extended_master', 'confirmation', candidate='PT',
                    selection_state=plan_path.parent / 'state.json', selection_summary=summary)

    def test_logical_tmp_plan_input_uses_canonical_output_and_receipt_paths(self):
        if not Path('/tmp').is_symlink():
            self.skipTest('macOS system /tmp alias only')
        d = self.driver
        tools, frozen, freeze = self.phase_fixture()
        with patch.object(d, 'check_freeze', return_value=frozen), patch.object(d, 'load_tools', return_value=tools), \
             patch.object(d, 'identity', return_value=frozen['identity']), patch.object(d, 'check_foreign_jobs'), \
             patch.object(d, 'current_power', return_value=(True, 80)), patch.object(d.time, 'time', return_value=1), \
             patch.object(d, 'run_job', side_effect=self.synthetic_job):
            d.prepare_phase(freeze, self.out / 'selection', 'selection')
            canonical_plan = self.out / 'selection/plan.json'
            logical_plan = Path('/tmp') / canonical_plan.relative_to(Path('/tmp').resolve())
            try:
                d.check_plan(logical_plan)
                state = d.run_phase(logical_plan, start=True)
            except ValueError as exc:
                self.fail(f'Logical /tmp input must match canonical jobs: {exc}')
            self.assertEqual(state['plan_path'], str(canonical_plan))
            self.assertEqual(state['status'], 'complete')
            receipt = logical_plan.parent / 'state.json'
            d.check_complete_state(receipt, d.digest(freeze))

    def test_phase_failure_is_incomplete_and_cannot_be_selection_evidence(self):
        d = self.driver
        tools, frozen, freeze = self.phase_fixture()
        calls = []

        def fail_third(*args, **kwargs):
            calls.append(args[0]['name'])
            if len(calls) == 3:
                raise OSError('synthetic child failed')
            return self.synthetic_job(*args, **kwargs)

        with patch.object(d, 'check_freeze', return_value=frozen), patch.object(d, 'load_tools', return_value=tools), \
             patch.object(d, 'identity', return_value=frozen['identity']), patch.object(d, 'check_foreign_jobs'), \
             patch.object(d, 'current_power', return_value=(True, 80)), patch.object(d.time, 'time', return_value=1), \
             patch.object(d, 'run_job', side_effect=fail_third):
            d.prepare_phase(freeze, self.out / 'selection', 'selection')
            plan = self.out / 'selection/plan.json'
            with self.assertRaises(OSError):
                d.run_phase(plan, start=True)
            state = json.loads((plan.parent / 'state.json').read_text())
            self.assertEqual(state['status'], 'incomplete')
            self.assertEqual([r['status'] for r in state['jobs']], ['complete', 'complete', 'incomplete'])
            self.assertEqual(len(calls), 3)
            with self.assertRaises(ValueError):
                d.check_complete_state(plan.parent / 'state.json', d.digest(freeze))

    def test_last_job_plan_tampering_cannot_produce_complete_phase(self):
        d = self.driver
        tools, frozen, freeze = self.phase_fixture()

        def tamper_last(job, plan_path, *args, **kwargs):
            receipt = self.synthetic_job(job, plan_path, *args, **kwargs)
            if job['name'] == 'PT_direct':
                with plan_path.open('a') as stream:
                    stream.write('\n')
            return receipt

        with patch.object(d, 'check_freeze', return_value=frozen), patch.object(d, 'load_tools', return_value=tools), \
             patch.object(d, 'identity', return_value=frozen['identity']), patch.object(d, 'check_foreign_jobs'), \
             patch.object(d, 'current_power', return_value=(True, 80)), patch.object(d.time, 'time', return_value=1), \
             patch.object(d, 'run_job', side_effect=tamper_last):
            d.prepare_phase(freeze, self.out / 'selection', 'selection')
            plan = self.out / 'selection/plan.json'
            with self.assertRaises(ValueError):
                d.run_phase(plan, start=True)
            self.assertEqual(json.loads((plan.parent / 'state.json').read_text())['status'], 'incomplete')

    def test_lock_race_never_overwrites_another_supervisors_receipt(self):
        d = self.driver
        tools, frozen, freeze = self.phase_fixture()
        sentinel = '{"owner":"another supervisor","status":"running"}\n'
        for reject_lock in (True, False):
            with self.subTest(reject_lock=reject_lock):
                directory = self.out / ('lock_rejected' if reject_lock else 'lock_acquired')
                state_path = directory / 'state.json'

                def racing_lock(root):
                    # Another invocation wins state creation after our first
                    # path check and before this invocation gets the lock.
                    state_path.write_text(sentinel)
                    if reject_lock:
                        raise ValueError('shared resource lock held elsewhere')
                    return nullcontext()

                tools.early.resource_lock = racing_lock
                with patch.object(d, 'check_freeze', return_value=frozen), patch.object(d, 'load_tools', return_value=tools), \
                     patch.object(d, 'identity', return_value=frozen['identity']), patch.object(d, 'check_foreign_jobs'), \
                     patch.object(d, 'current_power', return_value=(True, 80)), patch.object(d.time, 'time', return_value=1), \
                     patch.object(d, 'run_job', side_effect=self.synthetic_job):
                    d.prepare_phase(freeze, directory, 'selection')
                    with self.assertRaises((ValueError, FileExistsError)):
                        d.run_phase(directory / 'plan.json', start=True)
                    self.assertEqual(state_path.read_text(), sentinel)

    def test_battery_stop_keeps_failed_child_receipt_and_only_stops_owned_group(self):
        d = self.driver
        self.assertIn('record', __import__('inspect').signature(d.run_job).parameters,
                      'active child receipt must survive failure')
        tools, frozen, freeze = self.phase_fixture()
        process = SimpleNamespace(pid=12345, returncode=None, poll=lambda: None)
        stopped = []

        def stop(child):
            self.assertIs(child, process)
            self.assertIs(tools.early.CURRENT['process'], child)
            self.assertEqual(tools.early.CURRENT['pgid'], 12345)
            stopped.append(child.pid)
            child.returncode = -15

        tools.early.group_exists = lambda pid: process.returncode is None
        tools.early.stop_group = stop
        job = d.build_jobs(REPO, self.out, self.weights, 'selection')[0]
        plan = dict(study_freeze_path=str(freeze), study_freeze_sha256=d.digest(freeze))
        receipt = {}
        with patch.object(d, 'check_freeze', return_value=frozen), \
             patch.object(d, 'current_power', side_effect=[(False, 65), (False, 25)]), \
             patch.object(d.subprocess, 'Popen', return_value=process), patch.object(d.time, 'time', return_value=1):
            with self.assertRaises(ValueError):
                d.run_job(job, self.out / 'plan.json', plan, frozen, tools, record=receipt)
        self.assertEqual(stopped, [12345])
        self.assertEqual(receipt['status'], 'incomplete')
        self.assertEqual(receipt['exit_code'], -15)
        self.assertIn('Battery', receipt['error'])
        self.assertIsNone(tools.early.CURRENT)

    def test_spawn_registration_and_cleanup_mask_signals_without_leaving_parent_blocked(self):
        d = self.driver
        tools, frozen, freeze = self.phase_fixture()
        process = SimpleNamespace(pid=12345, returncode=None, poll=lambda: None)
        termination = {signal.SIGHUP, signal.SIGINT, signal.SIGTERM}
        before = signal.pthread_sigmask(signal.SIG_BLOCK, set())
        observed = []

        def spawn(*args, **kwargs):
            masked = signal.pthread_sigmask(signal.SIG_BLOCK, set())
            self.assertTrue(termination <= masked, 'spawn must be registered before signals are unblocked')
            observed.append('spawn')
            return process

        def stop(child):
            masked = signal.pthread_sigmask(signal.SIG_BLOCK, set())
            self.assertTrue(termination <= masked, 'a second signal must not interrupt cleanup')
            self.assertIs(tools.early.CURRENT['process'], child)
            observed.append('stop')
            child.returncode = -15

        powers = []

        def power():
            powers.append(1)
            if len(powers) == 1:
                return False, 65
            self.assertEqual(signal.pthread_sigmask(signal.SIG_BLOCK, set()), before)
            return False, 25

        tools.early.group_exists = lambda pid: process.returncode is None
        tools.early.stop_group = stop
        job = d.build_jobs(REPO, self.out, self.weights, 'selection')[0]
        plan = dict(study_freeze_path=str(freeze), study_freeze_sha256=d.digest(freeze))
        with patch.object(d, 'check_freeze', return_value=frozen), patch.object(d, 'current_power', side_effect=power), \
             patch.object(d.subprocess, 'Popen', side_effect=spawn), patch.object(d.time, 'time', return_value=1):
            with self.assertRaises(ValueError):
                d.run_job(job, self.out / 'plan.json', plan, frozen, tools)
        self.assertEqual(observed, ['spawn', 'stop'])
        self.assertEqual(signal.pthread_sigmask(signal.SIG_BLOCK, set()), before)


if __name__ == '__main__':
    unittest.main()
