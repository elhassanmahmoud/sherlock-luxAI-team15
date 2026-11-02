"""Pure dictionary checks: no checkpoint loading, tensors, games or promotion."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('build_targeting_candidates', HERE / 'build_targeting_candidates.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class CandidateStructureTests(unittest.TestCase):
    def setUp(self):
        self.states = [dict(weight=[[i, i + 1]], bias=[i / 100]) for i in range(36)]
        self.source = dict(q=self.states[0], ensemble=self.states[1:],
            cfg=dict(point_pair_swap=False, art_move_guard=False, frozen=True,
                     cand_rescue=True, rescue_after=30, w_discovery=.5, w_explore=.3),
            feature_dim=79, n_actions=6, ensemble_dims=[79]*35,
            env_steps=12345, metadata=dict(label='synthetic source'))

    def test_p_has_no_component_replacement(self):
        p = builder.make_candidate(self.source, {})
        self.assertEqual([p['q'], *p['ensemble']], self.states)
        self.assertEqual(p['ensemble_dims'], [79]*35)

    def test_exactly_two_configuration_flags_change(self):
        p = builder.make_candidate(self.source, {})
        changed = {key for key in p['cfg'] if p['cfg'][key] != self.source['cfg'].get(key)}
        self.assertEqual(changed, {'point_pair_swap', 'art_move_guard'})
        self.assertIs(p['cfg']['point_pair_swap'], True)
        self.assertIs(p['cfg']['art_move_guard'], True)
        self.assertEqual(p['metadata'], {'label': 'synthetic source'})

    def test_pt_replaces_exact_positions_18_and_19_in_q_plus_ensemble(self):
        replacement18, replacement19 = dict(weight=[[1800]]), dict(weight=[[1900]])
        pt = builder.make_candidate(self.source, {18: replacement18, 19: replacement19})
        actual = [pt['q'], *pt['ensemble']]
        self.assertEqual([i for i in range(36) if actual[i] != self.states[i]], [18, 19])
        self.assertEqual(actual[18], replacement18)
        self.assertEqual(actual[19], replacement19)
        self.assertEqual(actual[0], self.states[0])
        self.assertEqual(actual[17], self.states[17])
        self.assertEqual(actual[20], self.states[20])

    def test_p_and_pt_both_keep_exactly_36_ordered_networks(self):
        for changes in ({}, {18: dict(weight=[[1800]]), 19: dict(weight=[[1900]])}):
            with self.subTest(changes=bool(changes)):
                candidate = builder.make_candidate(self.source, changes)
                self.assertEqual(1 + len(candidate['ensemble']), 36)
                self.assertEqual(len(candidate['ensemble_dims']), 35)

    def test_source_and_replacement_objects_are_not_mutated_or_aliased(self):
        before = copy.deepcopy(self.source)
        replacements = {18: dict(weight=[[1800]]), 19: dict(weight=[[1900]])}
        before_replacements = copy.deepcopy(replacements)
        pt = builder.make_candidate(self.source, replacements)
        self.assertEqual(self.source, before)
        pt['q']['weight'][0][0] = -1
        pt['ensemble'][17]['weight'][0][0] = -1
        pt['cfg']['w_discovery'] = -1
        self.assertEqual(self.source, before)
        self.assertEqual(replacements, before_replacements)

    def test_invalid_components_are_rejected_before_returning_a_candidate(self):
        for index in (-1, 0, 1, 17, 20, 35, 36, 37, True, '18'):
            with self.subTest(index=index), self.assertRaises(ValueError):
                builder.make_candidate(self.source, {index: dict(weight=[[999]])})
        self.assertNotIn('torch', sys.modules)


if __name__ == '__main__':
    unittest.main()
