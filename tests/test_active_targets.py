"""Regression tests for opt-in exclusion of negative-energy target owners."""
import copy
import unittest
from types import SimpleNamespace

import numpy as np

from agents.sherlock.belief import Belief
from agents.sherlock.config import AgentConfig
from agents.sherlock.features import FEATURE_NAMES, build_features, make_context


def fixture(enabled=True, team=0, canonical=True, energies=(-1, 50), stacked=False):
    cfg = AgentConfig(canonical=canonical)
    # Set after construction so baseline RED exposes behavior, not constructor errors.
    cfg.active_targets = enabled
    belief = Belief(team, canonical=canonical)
    belief.match_idx, belief.match_step = 2, 60
    belief.explored[:] = True
    near, far = ((20, 20), (13, 13)) if team == 1 and not canonical else ((3, 3), (10, 10))
    for x, y in (near, far):
        belief._mark_point(x * belief.H + y)
    positions = np.full((2, 4, 2), -1, np.int32)
    energy = np.full((2, 4), -1, np.float32)
    masks = np.zeros((2, 4), bool)
    raw = [(20, 20), (19, 20)] if team else [(3, 3), (3, 4)]
    if stacked:
        raw[1] = raw[0]
    for uid, e in enumerate(energies):
        positions[team, uid] = raw[uid]
        energy[team, uid] = e
        masks[team, uid] = True
    # A visible negative enemy is deliberately retained by the narrow change.
    positions[1 - team, 0] = (15, 15)
    masks[1 - team, 0] = True
    obs = dict(units_mask=masks, units=dict(position=positions, energy=energy),
               team_points=[0, 0], team_wins=[0, 0], match_steps=60, steps=262)
    agent = SimpleNamespace(cfg=cfg, env_cfg={}, belief=belief, _sticky_prev=None)
    return agent, obs, near, far


class ActiveTargetsTests(unittest.TestCase):
    def test_reassigns_negative_owners_target_to_living_neighbour(self):
        agent, obs, near, _ = fixture()
        self.assertEqual(make_context(agent, obs)['assigned'], {1: near})

    def test_zero_energy_survives_even_without_movement_energy(self):
        agent, obs, near, far = fixture(energies=(0, 50))
        self.assertEqual(make_context(agent, obs)['assigned'], {0: near, 1: far})

    def test_only_negative_units_have_no_targets_but_remain_in_context(self):
        agent, obs, _, _ = fixture(energies=(-1, -5))
        ctx = make_context(agent, obs)
        self.assertEqual(ctx['assigned'], {})
        np.testing.assert_array_equal(ctx['ally_ids'], [0, 1])

    def test_no_units_returns_empty_assignments(self):
        agent, obs, _, _ = fixture(energies=())
        ctx = make_context(agent, obs)
        self.assertEqual(ctx['assigned'], {})
        self.assertEqual(len(ctx['ally_ids']), 0)

    def test_both_sides_with_and_without_canonical_coordinates(self):
        for team in (0, 1):
            for canonical in (False, True):
                with self.subTest(team=team, canonical=canonical):
                    agent, obs, near, _ = fixture(team=team, canonical=canonical)
                    self.assertEqual(make_context(agent, obs)['assigned'], {1: near})

    def test_disabled_flag_preserves_original_phantom_assignment(self):
        agent, obs, near, far = fixture(enabled=False)
        ctx = make_context(agent, obs)
        self.assertEqual(ctx['assigned'], {0: near, 1: far})
        np.testing.assert_array_equal(ctx['ally_ids'], [0, 1])
        self.assertEqual(ctx['first_on_tile'][near], 0)

    def test_old_config_defaults_off_and_opt_in_survives_serialization(self):
        agent, obs, near, far = fixture()
        agent.cfg = AgentConfig.from_dict({'canonical': True})
        self.assertEqual(make_context(agent, obs)['assigned'], {0: near, 1: far})
        agent.cfg = AgentConfig.from_dict({'active_targets': True})
        self.assertEqual(make_context(agent, obs)['assigned'], {1: near})
        self.assertIs(agent.cfg.to_dict()['active_targets'], True)

    def test_only_assigned_features_change_for_living_unit(self):
        agent, obs, _, _ = fixture(enabled=False)
        before = make_context(agent, obs)
        agent.cfg.active_targets = True
        after = make_context(agent, obs)
        f_before, f_after = build_features(before, 1), build_features(after, 1)
        assigned = [i for i, name in enumerate(FEATURE_NAMES) if name.startswith('assigned_')]
        others = [i for i in range(len(FEATURE_NAMES)) if i not in assigned]
        np.testing.assert_array_equal(f_before[others], f_after[others])
        self.assertFalse(np.array_equal(f_before[assigned], f_after[assigned]))
        # All context entries except assigned are unchanged, including enemy features.
        self.assertEqual(set(before), set(after))
        for key in set(before) - {'assigned', 'belief'}:
            if isinstance(before[key], np.ndarray):
                np.testing.assert_array_equal(before[key], after[key], err_msg=key)
            else:
                self.assertEqual(before[key], after[key], key)

    def test_stacked_first_owner_and_occupancy_are_not_filtered(self):
        agent, obs, near, _ = fixture(stacked=True)
        ctx = make_context(agent, obs)
        self.assertEqual(ctx['assigned'], {1: near})
        self.assertEqual(ctx['first_on_tile'][near], 0)
        self.assertEqual(ctx['ally_count'][near], 2)
        self.assertEqual(build_features(ctx, 1)[FEATURE_NAMES.index('redundant_here')], 1)
        np.testing.assert_array_equal(ctx['enemy_energies'], [-1])

    def test_energy_column_shape_uses_same_death_boundary(self):
        agent, obs, near, _ = fixture()
        obs['units']['energy'] = obs['units']['energy'][..., None]
        self.assertEqual(make_context(agent, obs)['assigned'], {1: near})

    def test_sticky_history_only_retains_assignments_to_survivors(self):
        agent, obs, near, _ = fixture()
        agent.cfg.sticky = 3
        agent._sticky_prev = (2, {0: near})
        ctx = make_context(agent, obs)
        self.assertEqual(ctx['assigned'], {1: near})
        self.assertEqual(agent._sticky_prev, (2, {1: near}))

    def test_hidden_positive_energy_slots_do_not_receive_targets(self):
        agent, obs, near, _ = fixture()
        obs['units']['energy'][0, 2] = 100
        obs['units']['position'][0, 2] = near
        self.assertEqual(make_context(agent, obs)['assigned'], {1: near})


if __name__ == '__main__':
    unittest.main()
