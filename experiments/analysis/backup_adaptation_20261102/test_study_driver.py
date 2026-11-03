"""Synthetic, stdlib-only integrity tests; never import models or execute games."""
import csv
from contextlib import nullcontext
import importlib.util
import json
import signal
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tests.archive_import_isolation import assert_isolated_imports

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return path


class SyntheticFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = HERE / 'study_driver.py'
        if path.exists():
            cls.d = load('synthetic_backup_driver', path)

    def setUp(self):
        if not hasattr(self, 'd'):
            if self._testMethodName == 'test_tools_exist':
                return
            self.skipTest('implementation missing')
        self.tmp = tempfile.TemporaryDirectory(dir=Path('/tmp').resolve())
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        d = self.d
        real_tools = d.load_tools(REPO)
        self.source = self.root / 'original.py'
        self.source.write_text('SYNTHETIC = True\n')
        self.protocol = self.root / 'protocol.md'
        self.protocol.write_text('Synthetic protocol, no experiment results')
        self.head = d.PARENT_HEAD
        self.models = {}
        for label in (*d.PANEL, d.DIRECT):
            if label.startswith('self:'):
                target = self.root / label[5:]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b'synthetic model, never loaded')
                self.models[str(target)] = d.digest(target)
        for side in (0, 1):
            target = self.root / f'agents/sherlock/weights/agent_p{side}.pth'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b'synthetic model, never loaded')
            self.models[str(target)] = d.digest(target)
        self.baseline = self.root / d.DIRECT[5:]
        self.p = self.root / 'P.pth'
        self.p.write_bytes(b'old synthetic P, never loaded')
        self.models[str(self.p)] = d.digest(self.p)
        self.old_driver = self.root / 'old_driver.py'
        self.old_driver.write_text('# synthetic frozen supervisor\n')
        self.source_names = [self.source, self.protocol, self.old_driver]

        def source_identity(root, python, protocols):
            return dict(head=self.head, python=str(python), executable=str(Path(python).resolve()),
                executable_sha256=d.digest(python),
                files=real_tools.early.hashes(set(self.source_names) | set(map(Path, protocols))))

        self.tools = SimpleNamespace(early=SimpleNamespace(
            source_identity=source_identity, hashes=real_tools.early.hashes,
            read_rows=real_tools.early.read_rows, GAME_FIELDS=real_tools.early.GAME_FIELDS,
            resource_lock=lambda root: nullcontext(), THREAD_ENV={}),
            jobs=SimpleNamespace(validate_inputs=lambda *args: None))
        self.patches = [patch.object(d, 'load_tools', return_value=self.tools),
                        patch.object(d, 'SOURCE_SHA', d.digest(self.baseline))]
        for item in self.patches:
            item.start(); self.addCleanup(item.stop)
        self.parent_dir = self.root / 'parent'
        self.parent_dir.mkdir()
        old = dict(schema_version=1, root=str(self.root), python=sys.executable,
            expected_head=d.PARENT_HEAD, weights=dict(baseline=str(self.baseline), P=str(self.p)),
            protocols=[str(self.protocol)], frozen_weights=self.models,
            driver=dict(path=str(self.old_driver), sha256=d.digest(self.old_driver)))
        old['identity'] = dict(source=source_identity(self.root, sys.executable, old['protocols']),
            weights=self.models, driver=old['driver'])
        self.old = old
        self.old_master = write_json(self.parent_dir / 'study_freeze.json', old)
        select = self.parent_dir / 'selection'
        select.mkdir()
        jobs = d.build_parent_jobs(self.root, select, old['weights'])
        old_plan = dict(schema_version=1, phase='selection', candidate=None,
            study_freeze_path=str(self.old_master), study_freeze_sha256=d.digest(self.old_master),
            initial_seconds_per_game=dict(combined_panel=2.22, direct=3.),
            prior_observed_seconds_per_game=dict(combined_panel=[], direct=[]),
            deadline_utc='2026-11-03T04:30:00+00:00', reserve_seconds=3600,
            future_confirmation_games=dict(combined_panel=8400, direct=600), jobs=jobs)
        self.old_plan = write_json(select / 'plan.json', old_plan)
        records = self.write_jobs(jobs, candidate_win=False, rates=(2.5, 4.))
        self.old_state = write_json(select / 'state.json', dict(status='complete', phase='selection',
            plan_path=str(self.old_plan), plan_sha256=d.digest(self.old_plan),
            study_freeze_sha256=d.digest(self.old_master), source_before=old['identity'],
            source_after=old['identity'], completed_games=3000, jobs=records))
        self.old_summary = write_json(self.parent_dir / 'selection_summary.json', dict(status='complete',
            phase='selection', completed_games=3000, nominee=None, candidates={'P': {'passed': False}},
            plan_path=str(self.old_plan), plan_sha256=d.digest(self.old_plan), state_sha256=d.digest(self.old_state),
            study_freeze_sha256=d.digest(self.old_master),
            csv_sha256={r['out']: r['output_sha256'] for r in records}))
        self.old_audit = write_json(self.parent_dir / 'independent_audit.json', dict(verdict='ACCEPTED',
            phase='selection', failed=[], results={'selection': dict(status='complete', nominee=None, passed=False,
                completed_games=3000, plan_sha256=d.digest(self.old_plan), state_sha256=d.digest(self.old_state),
                study_freeze_sha256=d.digest(self.old_master),
                csv_sha256={r['out']: r['output_sha256'] for r in records})},
            evidence_sha256={str(self.old_plan): d.digest(self.old_plan), str(self.old_master): d.digest(self.old_master),
                str(self.old_state): d.digest(self.old_state), str(self.old_summary): d.digest(self.old_summary),
                **{r['out']: r['output_sha256'] for r in records}}, checks=['synthetic complete audit']))
        self.close = write_json(self.parent_dir / 'freeze_close.json', dict(status='closed', phase='selection',
            head=d.PARENT_HEAD, master_sha256=d.digest(self.old_master),
            selection_state_sha256=d.digest(self.old_state), selection_summary_sha256=d.digest(self.old_summary),
            independent_audit_sha256=d.digest(self.old_audit), source_unchanged=True, weights_unchanged=True))
        self.parent = dict(state_path=str(self.old_state), summary_path=str(self.old_summary),
                           audit_path=str(self.old_audit), close_path=str(self.close))
        self.head = 'b' * 40  # legal new-tool commit after historical freeze closure
        self.source_names.append(HERE / 'study_driver.py')
        self.pt2 = self.root / 'PT2.pth'
        self.pt2.write_bytes(b'new synthetic PT2, never loaded')
        audit = write_json(self.root / 'training_audit.json', dict(verdict='ACCEPTED_TWO_ARM_BACKUP', failed=[], warnings=[],
            arms={arm: dict(seed=seed, train_games=600, prefill_games=120, validation_games=96)
                  for arm, seed in [('adapt18', 30), ('adapt19', 31)]}, evidence_sha256={}))
        checkpoints = {}
        for arm in ('adapt18', 'adapt19'):
            target = self.root / arm / 'weights_end.pth'
            target.parent.mkdir(); target.write_bytes(arm.encode())
            checkpoints[str(target)] = d.digest(target)
        training_audit = json.loads(audit.read_text())
        training_audit['evidence_sha256'] = checkpoints
        write_json(audit, training_audit)
        admission = dict(verdict='ACCEPTED_PT2', source_sha256=d.SOURCE_SHA,
            candidate=dict(path=str(self.pt2), sha256=d.digest(self.pt2)),
            components=dict(total=36, replaced=[18, 19], ordered_sha256=['a'*64] * 36),
            training=dict(arms=['adapt18', 'adapt19'], seeds=[30, 31],
                each_games=dict(prefill=120, train=600, val=96), checkpoints=checkpoints,
                accepted_audit=dict(path=str(audit), sha256=d.digest(audit))), warnings=[])
        self.admission = write_json(self.root / 'admission.json', admission)
        self.freeze = self.root / 'study_freeze.json'

    def write_jobs(self, jobs, *, candidate_win=True, rates=(2.5, 4.)):
        d = self.d
        records = []
        for job in jobs:
            with Path(job['out']).open('x', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=self.tools.early.GAME_FIELDS)
                writer.writeheader()
                for seed in range(job['first_seed'], job['first_seed'] + job['n_maps']):
                    for side in ('player_0', 'player_1'):
                        for opponent in job['opponents']:
                            win = opponent == 'default' or (candidate_win and job['role'] != 'baseline')
                            row = {field: 0 for field in self.tools.early.GAME_FIELDS}
                            row.update(seed=seed, side=side, opponent=opponent, result=1. if win else .5,
                                game_win=int(win), point_win=1. if win else .5, our_wins=2 if win else 1,
                                opp_wins=1, our_points=20 if win else 10, opp_points=10,
                                point_counting_version=2, steps=303)
                            writer.writerow(row)
            records.append(dict(name=job['name'], timing_class=job['timing_class'], status='complete', exit_code=0,
                out=job['out'], output_sha256=d.digest(job['out']), actual_games=job['games'],
                wall_seconds=job['games'] * rates[job['timing_class'] == 'direct']))
        return records

    def make_freeze(self):
        with patch.object(self.d.time, 'time', return_value=1):
            self.frozen = self.d.create_freeze(self.root, self.freeze,
                dict(baseline=str(self.baseline), PT2=str(self.pt2)), python=sys.executable,
                protocols=[self.protocol], expected_head=self.head, parent=self.parent,
                candidate_admission=self.admission)
        return self.frozen

    def complete_phase(self, phase, **kwargs):
        d = self.d
        plan_dir = self.freeze.parent / phase
        with patch.object(d.time, 'time', return_value=1):
            plan = d.prepare_phase(self.freeze, plan_dir, phase, **kwargs)
        records = self.write_jobs(plan['jobs'])
        plan_path = plan_dir / 'plan.json'
        state = write_json(plan_dir / 'state.json', dict(status='complete', phase=phase,
            plan_path=str(plan_path), plan_sha256=d.digest(plan_path), study_freeze_sha256=d.digest(self.freeze),
            source_before=self.frozen['identity'], source_after=self.frozen['identity'],
            completed_games=sum(r['actual_games'] for r in records), jobs=records))
        return plan_path, state


class DriverTests(SyntheticFixture):
    def test_empty_and_all_missing_hash_manifests_are_refused(self):
        for values in ({}, {str(self.root / 'missing'): '0'*64}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.d.checked_hashes(values, 'synthetic archive')

    def test_tools_exist(self):
        self.assertTrue((HERE / 'study_driver.py').is_file())

    def test_exact_jobs_reject_late_roles_and_wrong_candidate(self):
        d = self.d
        weights = dict(baseline='v14', PT2='new')
        selection = d.build_jobs(self.root, self.root / 's', weights, 'selection')
        self.assertEqual([j['games'] for j in selection], [700, 700, 100])
        self.assertEqual([j['first_seed'] for j in selection], [844000, 844000, 844000])
        self.assertEqual({j['n_maps'] for j in selection}, {50})
        confirm = d.build_jobs(self.root, self.root / 'c', weights, 'confirmation', candidate='PT2')
        self.assertEqual([j['games'] for j in confirm], [4200, 4200, 600])
        self.assertEqual([j['first_seed'] for j in confirm], [842000, 842000, 843000])
        for bad in (dict(baseline='x', P='x'), dict(weights, P='x'), dict(weights, PT='x'), {'PT2': 'x'}):
            with self.assertRaises(ValueError):
                d.build_jobs(self.root, self.root, bad, 'selection')
        for nominee in (None, 'P', 'PT'):
            with self.assertRaises(ValueError):
                d.build_jobs(self.root, self.root, weights, 'confirmation', candidate=nominee)

    def test_archived_parent_accepts_legal_head_and_extra_source(self):
        bound = self.d.check_parent(self.parent)
        self.assertEqual(bound['observed_seconds_per_game'], dict(combined_panel=[2.5, 2.5], direct=[4.]))
        self.assertEqual(bound['head'], self.d.PARENT_HEAD)
        self.make_freeze()
        self.assertEqual(self.d.check_freeze(self.freeze)['expected_head'], 'b'*40)

    def test_parent_rejects_nominee_incomplete_missing_and_confirmation_attempt(self):
        d = self.d
        for path, change in ((self.old_summary, {'nominee': 'P'}), (self.old_state, {'status': 'incomplete'}),
                             (self.old_audit, {'verdict': 'REJECTED'}), (self.close, {'source_unchanged': False})):
            original = path.read_text()
            write_json(path, dict(json.loads(original), **change))
            with self.subTest(change=change), self.assertRaises(ValueError):
                d.check_parent(self.parent)
            path.write_text(original)
        for suffix in ('confirmation/plan.json', 'confirmation/state.json', 'confirmation_reservation.json'):
            target = self.parent_dir / suffix
            target.parent.mkdir(exist_ok=True); target.write_text('{}')
            with self.subTest(suffix=suffix), self.assertRaises(ValueError):
                d.check_parent(self.parent)
            target.unlink()
            if target.parent.name == 'confirmation':
                target.parent.rmdir()
        self.old_audit.unlink()
        with self.assertRaises((ValueError, FileNotFoundError)):
            d.check_parent(self.parent)

    def test_dangling_parent_confirmation_marker_is_rejected(self):
        marker = self.parent_dir / 'confirmation'
        marker.symlink_to(self.root / 'missing-confirmation', target_is_directory=True)
        with self.assertRaises(ValueError):
            self.d.check_parent(self.parent)

    def test_parent_checks_actual_old_source_weights_csv_and_nonempty_manifests(self):
        for target in (self.source, self.baseline, Path(json.loads(self.old_state.read_text())['jobs'][0]['out'])):
            old = target.read_bytes(); target.write_bytes(b'changed')
            with self.subTest(target=target), self.assertRaises(ValueError):
                self.d.check_parent(self.parent)
            target.write_bytes(old)
        old = self.old_master.read_text()
        value = json.loads(old); value['identity']['source']['files'] = {}; value['identity']['weights'] = {}
        write_json(self.old_master, value)
        with self.assertRaises(ValueError):
            self.d.check_parent(self.parent)

    def test_admission_binds_exact_new_training_and_files(self):
        d = self.d
        result = d.check_candidate_admission(self.admission, str(self.pt2))
        self.assertEqual(len(result['training']['checkpoints']), 2)
        original = self.admission.read_text()
        for change in ({'seeds': [28, 29]}, {'arms': ['adapt18', 'adapt19', 'control18', 'control19']},
                       {'each_games': dict(prefill=120, train=599, val=96)}, {'checkpoints': {}}):
            value = json.loads(original); value['training'].update(change); write_json(self.admission, value)
            with self.subTest(change=change), self.assertRaises(ValueError):
                d.check_candidate_admission(self.admission, str(self.pt2))
        self.admission.write_text(original)
        end = Path(next(iter(json.loads(original)['training']['checkpoints'])))
        end.write_bytes(b'drift')
        with self.assertRaises(ValueError):
            d.check_candidate_admission(self.admission, str(self.pt2))

    def test_canonical_phase_path_and_persistent_confirmation_reservation(self):
        d = self.d
        self.make_freeze()
        with self.assertRaises(ValueError):
            d.prepare_phase(self.freeze, self.root / 'other', 'selection')
        self.assertFalse((self.root / 'other').exists())
        self.complete_phase('selection')
        state_path = self.root / 'selection/state.json'
        state = json.loads(state_path.read_text())
        summary = write_json(self.root / 'summary.json', dict(status='complete', phase='selection', nominee='PT2',
            completed_games=1500, candidates={'PT2': {'passed': True, 'gates': {'panel_delta': True, 'solution_delta': True, 'default': True, 'direct': True}}}, plan_sha256=state['plan_sha256'], study_freeze_sha256=d.digest(self.freeze),
            state_sha256=d.digest(state_path), csv_sha256={r['out']: r['output_sha256'] for r in state['jobs']}))
        with patch.object(d.time, 'time', return_value=1):
            plan = d.prepare_phase(self.freeze, self.root / 'confirmation', 'confirmation', candidate='PT2',
                selection_state=state_path, selection_summary=summary)
        reservation = Path(self.frozen['confirmation_reservation'])
        self.assertTrue(reservation.is_file())
        self.assertEqual(plan['prior_observed_seconds_per_game'],
            dict(combined_panel=[2.5, 2.5, 2.5, 2.5], direct=[4., 4.]))
        (self.root / 'confirmation/plan.json').unlink(); (self.root / 'confirmation').rmdir()
        with patch.object(d.time, 'time', return_value=1), self.assertRaises(FileExistsError):
            d.prepare_phase(self.freeze, self.root / 'confirmation', 'confirmation', candidate='PT2',
                selection_state=state_path, selection_summary=summary)

    def test_selection_nominee_requires_complete_matching_state_and_passed_gates(self):
        d = self.d
        self.make_freeze()
        plan, state_path = self.complete_phase('selection')
        receipt = json.loads(state_path.read_text())
        value = dict(status='complete', phase='selection', nominee='PT2', completed_games=1500,
            candidates={'PT2': {'passed': True, 'gates': {'panel_delta': True, 'solution_delta': True, 'default': True, 'direct': True}}},
            plan_sha256=d.digest(plan), state_sha256=d.digest(state_path), study_freeze_sha256=d.digest(self.freeze),
            csv_sha256={r['out']: r['output_sha256'] for r in receipt['jobs']})
        path = write_json(self.root / 'summary.json', value)
        d.check_selection_summary(path, 'PT2', receipt)
        for change in ({'completed_games': 1499}, {'state_sha256': 'c'*64}, {'candidates': {}},
                       {'candidates': {'PT2': {'passed': False, 'gates': {'panel_delta': False}}}}):
            write_json(path, dict(value, **change))
            with self.subTest(change=change), self.assertRaises(ValueError):
                d.check_selection_summary(path, 'PT2', receipt)

    def test_refused_confirmation_after_reservation_keeps_consumed_slot(self):
        d = self.d
        self.make_freeze()
        self.complete_phase('selection')
        state_path = self.root / 'selection/state.json'
        receipt = json.loads(state_path.read_text())
        summary = write_json(self.root / 'summary.json', dict(status='complete', phase='selection', nominee='PT2',
            completed_games=1500, candidates={'PT2': {'passed': True, 'gates': {'panel_delta': True, 'solution_delta': True, 'default': True, 'direct': True}}},
            plan_sha256=receipt['plan_sha256'], state_sha256=d.digest(state_path), study_freeze_sha256=d.digest(self.freeze),
            csv_sha256={r['out']: r['output_sha256'] for r in receipt['jobs']}))
        mkdir = Path.mkdir

        def fail_confirmation(path, *args, **kwargs):
            if path == self.root / 'confirmation':
                raise OSError('synthetic post-reservation filesystem failure')
            return mkdir(path, *args, **kwargs)

        with patch.object(d.time, 'time', return_value=1), patch.object(Path, 'mkdir', fail_confirmation):
            with self.assertRaises(OSError):
                d.prepare_phase(self.freeze, self.root / 'confirmation', 'confirmation', candidate='PT2',
                    selection_state=state_path, selection_summary=summary)
        self.assertTrue(Path(self.frozen['confirmation_reservation']).is_file())
        self.assertFalse((self.root / 'confirmation').exists())
        with patch.object(d.time, 'time', return_value=1), self.assertRaises(FileExistsError):
            d.prepare_phase(self.freeze, self.root / 'confirmation', 'confirmation', candidate='PT2',
                selection_state=state_path, selection_summary=summary)

    def test_macos_tmp_aliases_work_and_user_symlinks_are_refused(self):
        d = self.d
        self.make_freeze()
        alias = self.root / 'user_alias'
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            d.prepare_phase(self.freeze, alias / 'selection', 'selection')
        logical = Path('/tmp') / self.root.relative_to(Path('/tmp').resolve()) / 'selection'
        with patch.object(d.time, 'time', return_value=1):
            d.prepare_phase(self.freeze, logical, 'selection')
        plan, frozen = d.check_plan(logical / 'plan.json')
        self.assertEqual(plan['jobs'][0]['out'], str(self.root / 'selection/baseline_panel.csv'))

    def test_live_freeze_rejects_source_and_admission_drift(self):
        self.make_freeze()
        self.source.write_text('DRIFT = True\n')
        with self.assertRaises(ValueError):
            self.d.check_freeze(self.freeze)

    def test_every_phase_admission_preserves_twenty_minute_setup(self):
        d = self.d
        games = dict(combined_panel=100, direct=10)
        observed = dict(combined_panel=[], direct=[])
        self.assertAlmostEqual(d.admit(games, observed, now=1, deadline=5103.5), 1502.4)
        with self.assertRaises(ValueError):
            d.admit(games, observed, now=1, deadline=5103.4)

    def test_time_admission_retains_parent_slowdown_and_setup(self):
        d = self.d
        observed = dict(combined_panel=[2.5, 2.5], direct=[4.])
        rates, slowdown = d.effective_rates(observed)
        self.assertAlmostEqual(rates['combined_panel'], 2.96)
        self.assertEqual(rates['direct'], 4.)
        expected = 1.2 * (9800*2.96 + 700*4.) + 1200 + 3000
        self.assertAlmostEqual(d.admit_backup(self.parent, now=1, deadline=expected+3602), expected)
        with self.assertRaises(ValueError):
            d.admit_backup(self.parent, now=1, deadline=expected+3601)

    def test_backup_estimate_always_includes_complete_training_setup_and_close(self):
        estimate = self.d.estimate_backup(self.parent)
        self.assertEqual(estimate['remaining_games'], dict(combined_panel=9800, direct=700))
        self.assertEqual(estimate['training_seconds'], 3000)
        self.assertEqual(estimate['setup_audit_seconds'], 1200)
        self.assertEqual(estimate['closing_reserve_seconds'], 3600)
        self.assertAlmostEqual(estimate['total_seconds'], 1.2*(9800*2.96+700*4.)+7800)

    def synthetic_job(self, job, *args, **kwargs):
        record = self.write_jobs([job], rates=(3., 5.))[0]
        Path(job['log']).write_text('synthetic CSV rows only')
        result = kwargs.get('record', {})
        result.update(record)
        return result

    def run_synthetic(self, plan, **kwargs):
        with patch.object(self.d, 'check_foreign_jobs'), patch.object(self.d, 'current_power', return_value=(True, 5)), \
             patch.object(self.d.time, 'time', return_value=1), \
             patch.object(self.d, 'run_job', side_effect=kwargs.pop('effect', self.synthetic_job)):
            return self.d.run_phase(plan, **kwargs)

    def test_run_phase_requires_start_and_inherits_and_increases_parent_rates(self):
        d = self.d
        self.make_freeze()
        with patch.object(d.time, 'time', return_value=1):
            d.prepare_phase(self.freeze, self.root / 'selection', 'selection')
        plan = self.root / 'selection/plan.json'
        with self.assertRaises(ValueError):
            self.run_synthetic(plan)
        self.assertFalse((plan.parent / 'state.json').exists())
        state = self.run_synthetic(plan, start=True)
        self.assertEqual(state['status'], 'complete')
        self.assertEqual(state['completed_games'], 1500)
        self.assertEqual(state['source_before'], state['source_after'])
        self.assertEqual(state['observed_seconds_per_game'],
                         dict(combined_panel=[2.5, 2.5, 3., 3.], direct=[4., 5.]))
        self.assertEqual(state['projection']['setup_audit_seconds'], 1200)
        self.assertEqual(state['projection']['remaining_games'], dict(combined_panel=8400, direct=700))
        self.assertAlmostEqual(state['projection']['effective_wall_seconds_per_game']['direct'], 4.054054054054054)
        with self.assertRaises(FileExistsError):
            self.run_synthetic(plan, start=True)

    def test_lock_race_preserves_another_owners_receipt(self):
        d = self.d
        self.make_freeze()
        with patch.object(d.time, 'time', return_value=1):
            d.prepare_phase(self.freeze, self.root / 'selection', 'selection')
        state_path = self.root / 'selection/state.json'
        sentinel = '{"owner":"other supervisor"}'

        def racing_lock(root):
            state_path.write_text(sentinel)
            return nullcontext()

        self.tools.early.resource_lock = racing_lock
        with self.assertRaises(FileExistsError):
            self.run_synthetic(self.root / 'selection/plan.json', start=True)
        self.assertEqual(state_path.read_text(), sentinel)

    def test_failed_phase_and_last_plan_drift_are_incomplete(self):
        d = self.d
        self.make_freeze()
        with patch.object(d.time, 'time', return_value=1):
            d.prepare_phase(self.freeze, self.root / 'selection', 'selection')
        plan_path = self.root / 'selection/plan.json'

        def drift(job, *args, **kwargs):
            result = self.synthetic_job(job, *args, **kwargs)
            if job['name'] == 'PT2_direct':
                with plan_path.open('a') as stream:
                    stream.write('\n')
            return result

        with self.assertRaises(ValueError):
            self.run_synthetic(plan_path, start=True, effect=drift)
        state = json.loads((plan_path.parent / 'state.json').read_text())
        self.assertEqual(state['status'], 'incomplete')
        self.assertEqual(len(state['jobs']), 3)
        with self.assertRaises(ValueError):
            d.check_complete_state(plan_path.parent / 'state.json', d.digest(self.freeze))

    def test_battery_failure_stops_only_registered_process_and_restores_signal_mask(self):
        d = self.d
        self.make_freeze()
        out = self.root / 'synthetic_child'
        out.mkdir()
        job = d.build_jobs(self.root, out, self.frozen['weights'], 'selection')[0]
        plan = dict(study_freeze_path=str(self.freeze), study_freeze_sha256=d.digest(self.freeze))
        process = SimpleNamespace(pid=12345, returncode=None, poll=lambda: None)
        termination = {signal.SIGHUP, signal.SIGINT, signal.SIGTERM}
        before = signal.pthread_sigmask(signal.SIG_BLOCK, set())
        stopped = []

        def spawn(*args, **kwargs):
            self.assertTrue(termination <= signal.pthread_sigmask(signal.SIG_BLOCK, set()))
            return process

        def stop(child):
            self.assertIs(child, process)
            self.assertIs(self.tools.early.CURRENT['process'], child)
            self.assertEqual(self.tools.early.CURRENT['owner_pid'], __import__('os').getpid())
            self.assertTrue(termination <= signal.pthread_sigmask(signal.SIG_BLOCK, set()))
            stopped.append(child.pid)
            child.returncode = -15

        self.tools.early.group_exists = lambda pid: process.returncode is None
        self.tools.early.stop_group = stop
        receipt = {}
        with patch.object(d, 'current_power', side_effect=[(False, 65), (False, 25)]), \
             patch.object(d.subprocess, 'Popen', side_effect=spawn), patch.object(d.time, 'time', return_value=1):
            with self.assertRaises(ValueError):
                d.run_job(job, self.root / 'plan.json', plan, self.frozen, self.tools, record=receipt)
        self.assertEqual(stopped, [12345])
        self.assertEqual(receipt['status'], 'incomplete')
        self.assertEqual(receipt['exit_code'], -15)
        self.assertIsNone(self.tools.early.CURRENT)
        self.assertEqual(signal.pthread_sigmask(signal.SIG_BLOCK, set()), before)

    def test_csv_duplicate_missing_out_of_block_and_all_missing_rejected(self):
        d = self.d
        job = d.build_jobs(self.root, self.root, dict(baseline='b', PT2='p'), 'selection')[2]
        rows = self.write_jobs([job])
        path = Path(job['out'])
        self.assertEqual(d.validate_output(path, job), 100)
        original = path.read_text(); lines = original.splitlines(True)
        for content in (''.join(lines[:1]), ''.join(lines[:-1]), ''.join([*lines[:-1], lines[1]]),
                        original.replace('844000', '843000', 1)):
            path.write_text(content)
            with self.assertRaises(ValueError):
                d.validate_output(path, job)
        assert_isolated_imports(self)


if __name__ == '__main__':
    unittest.main()
