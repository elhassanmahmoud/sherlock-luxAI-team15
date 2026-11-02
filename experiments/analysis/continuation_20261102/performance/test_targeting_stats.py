"""Gate/tie unit tests plus wholly synthetic phase files; no torch or games.

For the optional complete-file pipeline, run from the repository root or set
TARGETING_SOURCE_ROOT. Imports locate sibling tools after later integration.
All generated files and the tiny fixture Git repo live beside this test in /tmp
during external preparation. No real model file is opened.
"""
import contextlib
import csv
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SOURCE_ROOT = Path(os.environ.get('TARGETING_SOURCE_ROOT', Path.cwd())).resolve()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


stats = load_module('targeting_stats', HERE / 'targeting_stats.py')


class GateAndNomineeTests(unittest.TestCase):
    def confirmation(self, **changes):
        values = dict(panel=dict(delta=.01, low=.001), solution=dict(delta=0., low=-.01),
                      default=dict(winrate=.99, delta=-.01), direct=dict(low=.500001))
        values.update(changes)
        return stats.gates('confirmation', **values)

    def test_selection_all_gates_pass_at_nonstrict_boundaries(self):
        gates = stats.gates('selection', dict(delta=.005), dict(delta=0.), dict(winrate=.99), dict(winrate=.5))
        self.assertEqual(gates, dict(panel_delta=True, solution_delta=True, default=True, direct=True))

    def test_confirmation_nonstrict_boundaries_pass_with_positive_strict_bounds(self):
        self.assertTrue(all(self.confirmation().values()))

    def test_solution_point_decline_is_rejected(self):
        self.assertFalse(self.confirmation(solution=dict(delta=-.000001, low=0.))['solution_delta'])

    def test_panel_zero_lower_bound_is_rejected(self):
        self.assertFalse(self.confirmation(panel=dict(delta=.01, low=0.))['panel_lower'])

    def test_direct_fifty_percent_lower_bound_is_rejected(self):
        self.assertFalse(self.confirmation(direct=dict(low=.5))['direct_lower'])

    def test_solution_confidence_guard_is_rejected_below_minus_one_pp(self):
        self.assertFalse(self.confirmation(solution=dict(delta=0., low=-.01001))['solution_lower'])

    def test_default_decline_is_rejected_below_minus_one_pp(self):
        self.assertFalse(self.confirmation(default=dict(winrate=.99, delta=-.01001))['default_delta'])

    def test_exact_tie_prefers_p_even_with_reversed_input_order(self):
        data = dict(PT=dict(passed=True, panel=dict(delta=.02)), P=dict(passed=True, panel=dict(delta=.02)))
        self.assertEqual(stats.nominee(data), 'P')

    def test_tie_tolerance_is_fixed_at_one_e_minus_nine(self):
        self.assertEqual(stats.nominee(dict(PT=dict(passed=True, panel=dict(delta=.02 + .5e-9)),
                                           P=dict(passed=True, panel=dict(delta=.02)))), 'P')

    def test_pt_wins_when_delta_is_strictly_greater_than_tolerance(self):
        self.assertEqual(stats.nominee(dict(PT=dict(passed=True, panel=dict(delta=.02 + 2e-9)),
                                           P=dict(passed=True, panel=dict(delta=.02)))), 'PT')

    def test_no_passing_nominee_returns_none(self):
        self.assertIsNone(stats.nominee(dict(P=dict(passed=False, panel=dict(delta=.2)),
                                             PT=dict(passed=False, panel=dict(delta=.3)))))

    def test_failed_higher_score_does_not_nominate(self):
        self.assertEqual(stats.nominee(dict(PT=dict(passed=False, panel=dict(delta=.8)),
                                           P=dict(passed=True, panel=dict(delta=.02)))), 'P')

    def test_unknown_phase_is_rejected(self):
        with self.assertRaises(ValueError):
            stats.gates('unexpected', {}, {}, {}, {})


class SyntheticCompletePhaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=HERE)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'fixture_repo'
        self.root.mkdir()
        driver_path = HERE / 'targeting_eval_driver.py'
        if not driver_path.is_file():
            driver_path = HERE / 'evaluation_runner/targeting_eval_driver.py'
        self.driver = load_module('fixture_targeting_driver', driver_path)
        required = ['scripts/early_curriculum_study.py', 'scripts/protocol.py',
                    'scripts/compare_report.py', 'scripts/league_gates.py',
                    'experiments/analysis/night_20261101/run_jobs.py']
        if not all((SOURCE_ROOT / name).is_file() for name in required):
            self.skipTest('Set TARGETING_SOURCE_ROOT or run from repository root for complete synthetic pipeline')
        for name in required:
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE_ROOT / name, destination)
        subprocess.run(['git', '-C', str(self.root), 'init', '--quiet'], check=True, capture_output=True)
        subprocess.run(['git', '-C', str(self.root), 'add', '.'], check=True, capture_output=True)
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Synthetic Test',
                        '-c', 'user.email=synthetic@example.invalid', 'commit', '--quiet', '-m', 'fixture'],
                       check=True, capture_output=True)
        self.head = subprocess.check_output(['git', '-C', str(self.root), 'rev-parse', 'HEAD'], text=True).strip()
        model_paths = [*self.driver.PANEL, self.driver.DIRECT]
        for label in model_paths:
            if label.startswith('self:'):
                path = self.root / label[5:]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'synthetic model bytes, never loaded')
        for side in (0, 1):
            path = self.root / f'agents/sherlock/weights/agent_p{side}.pth'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'synthetic model bytes, never loaded')
        self.weights = dict(baseline=str(self.root / self.driver.DIRECT[5:]))
        for role in ('P', 'PT'):
            path = self.root / f'experiments/ensembles/{role}.pth'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(('synthetic ' + role + '; never loaded').encode())
            self.weights[role] = str(path)
        protocol = self.root / 'synthetic_protocol.md'
        protocol.write_text('Synthetic fixture only. No real games, model loading, or experiment results.')
        self.freeze = self.root / 'study_freeze.json'
        with patch.object(self.driver, 'SOURCE_SHA', self.driver.digest(self.weights['baseline'])):
            self.frozen = self.driver.create_freeze(self.root, self.freeze, self.weights,
                python=sys.executable, protocols=[protocol], expected_head=self.head)

    def write_complete_phase(self, directory, phase, **kwargs):
        d = self.driver
        plan = d.prepare_phase(self.freeze, directory, phase, **kwargs)
        tools = d.load_tools(self.root)
        fields = tools.early.GAME_FIELDS
        receipts = []
        for job in plan['jobs']:
            with Path(job['out']).open('x', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                for seed in range(job['first_seed'], job['first_seed'] + job['n_maps']):
                    for side in ('player_0', 'player_1'):
                        for opponent in job['opponents']:
                            win = opponent == 'default' or job['role'] != 'baseline'
                            if job['name'].endswith('_direct') and phase == 'selection' and job['role'] == 'P':
                                win = False
                            row = {field: 0 for field in fields}
                            row.update(seed=seed, side=side, opponent=opponent, result=1. if win else .5,
                                       game_win=int(win), point_win=1. if win else .5, our_wins=2 if win else 1,
                                       opp_wins=1, our_points=20 if win else 10, opp_points=10,
                                       point_counting_version=2, steps=303)
                            writer.writerow(row)
            receipts.append(dict(name=job['name'], timing_class=job['timing_class'], status='complete', exit_code=0,
                                 out=job['out'], output_sha256=d.digest(job['out']), actual_games=job['games'],
                                 wall_seconds=2.3 * job['games']))
        plan_path = directory / 'plan.json'
        state = dict(status='complete', phase=phase, plan_path=str(plan_path), plan_sha256=d.digest(plan_path),
                     study_freeze_sha256=d.digest(self.freeze), source_before=self.frozen['identity'],
                     source_after=self.frozen['identity'], jobs=receipts)
        state_path = directory / 'state.json'
        state_path.write_text(json.dumps(state))
        return plan_path, state_path

    def test_complete_selection_and_confirmation_files_with_real_bootstrap_no_torch(self):
        selection_plan, selection_state = self.write_complete_phase(self.root / 'selection', 'selection')
        selection_summary = self.root / 'selection_summary.json'
        with contextlib.redirect_stdout(io.StringIO()):
            summary = stats.summarize(selection_plan, selection_state, selection_summary)
        self.assertEqual(summary['completed_games'], 4600)
        self.assertEqual(summary['status'], 'complete')
        self.assertEqual(summary['nominee'], 'P')
        self.assertEqual(summary['candidates']['P']['counts']['solution92']['baseline'],
                         dict(games=200, wins=0, draws=200, losses=0))
        self.assertEqual(summary['candidates']['P']['counts']['solution92']['candidate'],
                         dict(games=200, wins=200, draws=0, losses=0))
        self.assertEqual(summary['candidates']['P']['direct']['draws'], 200)
        self.assertEqual(summary['candidates']['P']['panel']['maps'], 100)
        self.assertEqual(summary['bootstrap_samples'], 5000)
        confirm_plan, confirm_state = self.write_complete_phase(self.root / 'confirmation', 'confirmation',
            candidate='P', selection_state=selection_state, selection_summary=selection_summary)
        with contextlib.redirect_stdout(io.StringIO()):
            confirmation = stats.summarize(confirm_plan, confirm_state, self.root / 'confirmation_summary.json')
        self.assertEqual(confirmation['completed_games'], 9000)
        self.assertTrue(confirmation['promotion_qualified'])
        self.assertEqual(confirmation['candidates']['P']['direct']['wins'], 600)
        self.assertEqual(confirmation['candidates']['P']['panel']['maps'], 300)
        self.assertEqual(confirmation['study_freeze_sha256'], summary['study_freeze_sha256'])
        self.assertNotIn('torch', sys.modules)

    def test_incomplete_phase_is_rejected_before_summary_creation(self):
        plan, state_path = self.write_complete_phase(self.root / 'selection', 'selection')
        state = json.loads(state_path.read_text())
        state['status'] = 'incomplete'
        state_path.write_text(json.dumps(state))
        target = self.root / 'rejected.json'
        with self.assertRaises(AssertionError):
            stats.summarize(plan, state_path, target)
        self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()
