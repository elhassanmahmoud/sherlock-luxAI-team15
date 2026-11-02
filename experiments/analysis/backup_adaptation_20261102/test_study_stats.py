"""Pure synthetic statistics: literal gates, exact keys and complete two-phase chain."""
import contextlib
import csv
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from test_study_driver import HERE, SyntheticFixture, load, write_json


class StatsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if (HERE / 'study_stats.py').exists():
            cls.stats = load('synthetic_backup_stats', HERE / 'study_stats.py')

    def test_stats_exists(self):
        self.assertTrue((HERE / 'study_stats.py').exists())

    def test_exact_gates_and_only_pt2_nomination(self):
        if not hasattr(self, 'stats'):
            self.skipTest('implementation missing')
        s = self.stats
        panel = dict(delta=.005, low=0.)
        solution = dict(delta=0., low=-.01)
        default = dict(winrate=.99, delta=-.01)
        direct = dict(winrate=.5, low=.5)
        self.assertTrue(all(s.gates('selection', panel, solution, default, direct).values()))
        for group, name, value in [('panel', 'delta', .004), ('solution', 'delta', -.001),
                                   ('default', 'winrate', .989), ('direct', 'winrate', .499)]:
            args = dict(panel=panel.copy(), solution=solution.copy(), default=default.copy(), direct=direct.copy())
            args[group][name] = value
            self.assertFalse(all(s.gates('selection', **args).values()))
        panel.update(delta=.01, low=.000001); direct['low'] = .500001
        self.assertTrue(all(s.gates('confirmation', panel, solution, default, direct).values()))
        for group, name, value in [('panel', 'delta', .009), ('panel', 'low', 0.),
                                   ('solution', 'delta', -.001), ('solution', 'low', -.0101),
                                   ('default', 'winrate', .989), ('default', 'delta', -.0101),
                                   ('direct', 'low', .5)]:
            args = dict(panel=panel.copy(), solution=solution.copy(), default=default.copy(), direct=direct.copy())
            args[group][name] = value
            self.assertFalse(all(s.gates('confirmation', **args).values()))
        self.assertEqual(s.nominee({'PT2': {'passed': True}}), 'PT2')
        self.assertIsNone(s.nominee({'PT2': {'passed': False}}))
        for bad in ({'P': {'passed': True}}, {'PT2': {'passed': True}, 'PT': {'passed': False}}):
            with self.assertRaises(ValueError):
                s.nominee(bad)


class CompleteStudyTests(SyntheticFixture):
    def setUp(self):
        super().setUp()
        if not (HERE / 'study_stats.py').exists():
            self.skipTest('stats implementation missing')
        self.stats = load('backup_synthetic_summary', HERE / 'study_stats.py')
        self.make_freeze()

    def summarize(self, plan, state, out):
        with contextlib.redirect_stdout(io.StringIO()), patch.object(self.stats, 'load_driver', return_value=self.d):
            return self.stats.summarize(plan, state, out)

    def test_both_complete_phases_exact_counts_bootstrap_and_shared_master(self):
        plan, state = self.complete_phase('selection')
        summary_path = self.root / 'selection_summary.json'
        result = self.summarize(plan, state, summary_path)
        self.assertEqual(result['completed_games'], 1500)
        self.assertEqual(set(result['candidates']), {'PT2'})
        self.assertEqual(result['nominee'], 'PT2')
        self.assertEqual(result['bootstrap_samples'], 5000)
        self.assertEqual(result['bootstrap_rng_seed'], 0)
        self.assertEqual(result['candidates']['PT2']['counts']['solution92']['baseline'],
                         dict(games=100, wins=0, draws=100, losses=0))
        self.assertEqual(result['candidates']['PT2']['counts']['solution92']['candidate'],
                         dict(games=100, wins=100, draws=0, losses=0))
        self.assertEqual(result['candidates']['PT2']['panel']['maps'], 50)
        self.assertEqual(result['candidates']['PT2']['panel']['delta'], .5)
        self.assertEqual(result['candidates']['PT2']['panel']['low'], .5)
        plan2, state2 = self.complete_phase('confirmation', candidate='PT2', selection_state=state,
                                            selection_summary=summary_path)
        confirmed = self.summarize(plan2, state2, self.root / 'confirmation_summary.json')
        self.assertEqual(confirmed['completed_games'], 9000)
        self.assertTrue(confirmed['promotion_qualified'])
        self.assertEqual(confirmed['candidates']['PT2']['direct']['wins'], 600)
        self.assertEqual(confirmed['candidates']['PT2']['panel']['maps'], 300)
        self.assertEqual(confirmed['study_freeze_sha256'], result['study_freeze_sha256'])
        self.assertNotIn('torch', sys.modules)

    def test_whole_maps_joint_panel_and_nil_nomination_on_failed_selection(self):
        plan, state_path = self.complete_phase('selection')
        state = json.loads(state_path.read_text())
        job = next(job for job in state['jobs'] if job['name'] == 'PT2_panel')
        path = Path(job['out'])
        with path.open(newline='') as stream:
            reader = csv.DictReader(stream)
            fields = reader.fieldnames
            rows = list(reader)
        for row in rows:
            if row['opponent'] != 'default' and int(row['seed']) % 2:
                row.update(result=0, game_win=0, point_win=0, our_wins=1, opp_wins=2, our_points=10, opp_points=20)
        with path.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader(); writer.writerows(rows)
        job['output_sha256'] = self.d.digest(path)
        write_json(state_path, state)
        summary_path = self.root / 'failed_selection_summary.json'
        result = self.summarize(plan, state_path, summary_path)
        panel = result['candidates']['PT2']['panel']
        self.assertEqual(panel['delta'], 0.)
        self.assertEqual(panel['low'], -.14)
        self.assertEqual(panel['high'], .14)
        self.assertIsNone(result['nominee'])
        with self.assertRaises(ValueError):
            self.d.prepare_phase(self.freeze, self.root / 'confirmation', 'confirmation', candidate='PT2',
                selection_state=state_path, selection_summary=summary_path)
        self.assertFalse(Path(self.frozen['confirmation_reservation']).exists())

    def test_incomplete_or_missing_keys_cannot_create_summary(self):
        plan, state_path = self.complete_phase('selection')
        original = state_path.read_text()
        value = json.loads(original); value['status'] = 'incomplete'; write_json(state_path, value)
        target = self.root / 'rejected.json'
        with self.assertRaises((AssertionError, ValueError)):
            self.summarize(plan, state_path, target)
        self.assertFalse(target.exists())
        state_path.write_text(original)
        value = json.loads(original)
        csvpath = Path(value['jobs'][0]['out'])
        lines = csvpath.read_text().splitlines(True)
        csvpath.write_text(''.join(lines[:-1]))
        value['jobs'][0]['output_sha256'] = self.d.digest(csvpath)
        write_json(state_path, value)
        with self.assertRaises((AssertionError, ValueError)):
            self.summarize(plan, state_path, target)
        self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()
