"""Terminal shaping on the existing per-unit lifecycle; no lifecycle rewrite."""
from types import SimpleNamespace
import unittest

import numpy as np

from agents.sherlock.config import AgentConfig
from agents.sherlock.reward import _phi, surviving, unit_rewards


def config(enabled=True, **overrides):
    cfg = AgentConfig(reward_fix=True, gamma=0.9, w_shape=0.5,
                      w_point=0, w_energy=0, w_stack=0, w_explore=0,
                      w_discovery=0, w_match=0, w_sap_hit=0, w_death=0.5)
    # Lets baseline RED exercise real behavior, not an absent constructor field.
    cfg.terminal_death_potential = enabled
    for key, value in overrides.items():
        setattr(cfg, key, value)
    return cfg


def context(pos=(2, 2), energy=50, alive=True, goal=(14, 2), step=60):
    points = np.zeros((24, 24), bool)
    return dict(
        W=24, H=24, ally_ids=np.array([0] if alive else [], np.int32),
        ally_pos=np.array([pos], np.int32),
        ally_ene=np.array([energy], np.float32),
        assigned={} if goal is None else {0: goal},
        point_tiles=points, first_on_tile={pos: 0} if alive else {},
        match_step=step, own_wins=0, opp_wins=0,
        belief=SimpleNamespace(newly_explored=0, newly_proven=0, opp_gain=0),
    )


def reward(cfg, before, after):
    return unit_rewards(cfg, before, after, {0: 0}, {})[0]


class TerminalDeathPotentialTests(unittest.TestCase):
    def test_removed_unit_gets_one_terminal_potential_term(self):
        before = context()
        after = context(pos=(-1, -1), alive=False, goal=None)
        # phi(before)=-2.5; terminal correction 1.25 minus explicit death 0.5.
        self.assertAlmostEqual(reward(config(), before, after), 0.75)

    def test_far_respawn_ends_old_units_potential(self):
        before = context(pos=(10, 10), goal=(22, 10))
        after = context(pos=(0, 0), goal=(20, 20))
        self.assertEqual(surviving(config(), before, after), set())
        self.assertAlmostEqual(reward(config(), before, after), 0.75)

    def test_match_end_and_death_apply_term_once(self):
        before = context(step=100)
        after = context(pos=(-1, -1), alive=False, goal=None, step=0)
        self.assertAlmostEqual(reward(config(), before, after), 0.75)

    def test_survivor_shaping_is_unchanged(self):
        before = context()
        after = context(pos=(3, 2))
        for enabled in (False, True):
            self.assertAlmostEqual(reward(config(enabled), before, after), 0.21875)

    def test_survivor_at_match_end_keeps_existing_terminal_term(self):
        before = context(step=100)
        after = context(pos=(3, 2), step=0)
        for enabled in (False, True):
            self.assertAlmostEqual(reward(config(enabled), before, after), 1.25)

    def test_shaping_off_is_unchanged_even_at_death(self):
        before = context()
        after = context(pos=(-1, -1), alive=False, goal=None)
        after["own_wins"] = 1
        for enabled in (False, True):
            cfg = config(enabled, use_shaping=False, w_match=2)
            self.assertEqual(reward(cfg, before, after), 2.0)

    def test_flag_off_is_original_death_reward(self):
        self.assertEqual(reward(config(False), context(),
                                context(alive=False, goal=None)), -0.5)

    def test_discounted_complete_life_telescopes(self):
        cfg = config(w_death=0)
        states = [context(), context(pos=(3, 2), goal=(9, 2)),
                  context(pos=(-1, -1), alive=False, goal=None)]
        # phi: -2.5 -> -1.25 -> terminal0. F: .6875 -> .625.
        first = reward(cfg, states[0], states[1])
        final = reward(cfg, states[1], states[2])
        self.assertAlmostEqual(first, 0.6875)
        self.assertAlmostEqual(final, 0.625)
        self.assertAlmostEqual(first + 0.9 * final, 1.25)

    def test_negative_energy_is_not_early_done_without_active_targets(self):
        cfg = config(w_death=0)
        before = context()
        negative = context(energy=-1)
        removed = context(pos=(-1, -1), alive=False, goal=None)
        self.assertEqual(surviving(cfg, before, negative), {0})
        self.assertEqual(surviving(cfg, negative, removed), set())
        self.assertAlmostEqual(reward(cfg, before, negative), 0.125)
        self.assertAlmostEqual(reward(cfg, negative, removed), 1.25)
        self.assertAlmostEqual(reward(cfg, before, negative)
                               + 0.9 * reward(cfg, negative, removed), 1.25)

    def test_active_targets_clears_potential_one_step_before_done(self):
        # This is the context effect of active_targets: negative masked units
        # still exist for learning but receive no assigned target.
        cfg = config(w_death=0)
        before = context()
        negative = context(energy=-1, goal=None)
        removed = context(pos=(-1, -1), alive=False, goal=None)
        self.assertEqual(_phi(negative, 0), 0.0)
        self.assertEqual(surviving(cfg, before, negative), {0})
        self.assertEqual(surviving(cfg, negative, removed), set())
        self.assertAlmostEqual(reward(cfg, before, negative), 1.25)
        self.assertAlmostEqual(reward(cfg, negative, removed), 0.0)
        self.assertAlmostEqual(reward(cfg, before, negative)
                               + 0.9 * reward(cfg, negative, removed), 1.25)

    def test_target_change_before_terminal_still_telescopes(self):
        cfg = config(w_death=0)
        # A target can change without movement. Phi: -2.5 -> -3.75 -> -1.25 ->0.
        states = [context(), context(goal=(20, 2)),
                  context(goal=(8, 2)), context(alive=False, goal=None)]
        discounted = sum(0.9**t * reward(cfg, states[t], states[t+1])
                         for t in range(3))
        self.assertAlmostEqual(discounted, 1.25)

    def test_complete_discounted_reward_differs_only_by_initial_potential(self):
        cfg = config(w_match=2)
        unshaped_potential = config(w_match=2, w_shape=0)
        states = [context(), context(pos=(3, 2), goal=(9, 2)),
                  context(pos=(-1, -1), alive=False, goal=None, step=0)]
        states[-1]["own_wins"] = 1
        shaped_return = sum(0.9**t * reward(cfg, states[t], states[t+1])
                            for t in range(2))
        base_return = sum(0.9**t * reward(unshaped_potential, states[t], states[t+1])
                          for t in range(2))
        # Includes the same discounted explicit death penalty and match reward.
        self.assertAlmostEqual(base_return, 1.35)
        self.assertAlmostEqual(shaped_return, 2.60)
        self.assertAlmostEqual(shaped_return - base_return, 1.25)

    def test_zero_potential_death_does_not_add_bonus(self):
        self.assertEqual(reward(config(), context(goal=None),
                                context(alive=False, goal=None)), -0.5)

    def test_zero_energy_does_not_change_lifecycle(self):
        cfg = config()
        before, after = context(), context(energy=0)
        self.assertEqual(surviving(cfg, before, after), {0})
        self.assertEqual(reward(cfg, before, after),
                         reward(config(False), before, after))

    def test_old_config_defaults_off_and_new_flag_roundtrips(self):
        before, after = context(), context(alive=False, goal=None)
        cfg = AgentConfig.from_dict({"reward_fix": True})
        self.assertEqual(reward(cfg, before, after), -0.5)
        cfg = AgentConfig.from_dict({"reward_fix": True,
                                    "terminal_death_potential": True})
        self.assertAlmostEqual(reward(cfg, before, after), 0.75)
        self.assertTrue(cfg.to_dict()["terminal_death_potential"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
