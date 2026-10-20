"""Run only after the inference freeze: registry isolation and real epsilon property."""
from types import SimpleNamespace
import unittest

from agents.sherlock.main import Agent_x
from scripts.variants import ABLATIONS, VARIANTS, variant_cfg


def epsilon(cfg, steps, training=True):
    # Exercise the production property without allocating networks/replay buffers.
    stub = SimpleNamespace(cfg=cfg, env_steps=steps, training=training)
    return Agent_x.epsilon.fget(stub)


class SlowExplorationTests(unittest.TestCase):
    def test_variant_exists_and_differs_only_in_decay(self):
        self.assertIn("full_rules_v3_slowexplore", VARIANTS)
        base = variant_cfg("full_rules_v3").to_dict()
        slow = variant_cfg("full_rules_v3_slowexplore").to_dict()
        self.assertEqual(base.keys(), slow.keys())
        self.assertEqual({key for key in base if base[key] != slow[key]}, {"eps_decay_steps"})
        self.assertEqual(base["eps_decay_steps"], 60000)
        self.assertEqual(slow["eps_decay_steps"], 454500)
        self.assertEqual(VARIANTS["full_rules_v3_slowexplore"][0], "sherlock")
        self.assertNotIn("full_rules_v3_slowexplore", ABLATIONS)

    def test_registry_owns_independent_override_copy(self):
        self.assertIn("full_rules_v3_slowexplore", VARIANTS)
        base = dict(VARIANTS["full_rules_v3"][1])
        slow = dict(VARIANTS["full_rules_v3_slowexplore"][1])
        self.assertNotIn("eps_decay_steps", base)
        self.assertEqual(slow, {**base, "eps_decay_steps": 454500})
        self.assertIsNot(VARIANTS["full_rules_v3"][1], VARIANTS["full_rules_v3_slowexplore"][1])
        local = variant_cfg("full_rules_v3_slowexplore")
        local.eps_decay_steps = 17
        local.far_opp = 99
        self.assertEqual(VARIANTS["full_rules_v3"][1], base)
        self.assertEqual(VARIANTS["full_rules_v3_slowexplore"][1], slow)
        self.assertEqual(variant_cfg("full_rules_v3").eps_decay_steps, 60000)
        self.assertEqual(variant_cfg("full_rules_v3_slowexplore").eps_decay_steps, 454500)

    def test_reward_and_inference_experiments_remain_off(self):
        for name in ("full_rules_v3", "full_rules_v3_slowexplore"):
            cfg = variant_cfg(name)
            with self.subTest(name=name):
                for key in ("terminal_death_potential", "active_targets", "sap_geometry",
                            "contest_sap", "opp_infer", "smart_sap"):
                    self.assertIs(getattr(cfg, key), False)
                self.assertTrue(cfg.reward_fix)
                self.assertTrue(cfg.use_shaping)

    def test_slow_decay_spans_the_mixed_opponent_phase(self):
        cfg = variant_cfg("full_rules_v3_slowexplore")
        self.assertEqual(cfg.eps_start, 1.0)
        self.assertEqual(cfg.eps_end, .05)
        self.assertAlmostEqual(epsilon(cfg, 0), 1.0)
        self.assertAlmostEqual(epsilon(cfg, 750 * 303), .525)
        self.assertGreater(epsilon(cfg, 1499 * 303), .05)
        self.assertAlmostEqual(epsilon(cfg, 1500 * 303), .05)
        self.assertAlmostEqual(epsilon(cfg, 3000 * 303), .05)

    def test_baseline_decay_remains_unchanged(self):
        cfg = variant_cfg("full_rules_v3")
        self.assertAlmostEqual(epsilon(cfg, 0), 1.0)
        self.assertGreater(epsilon(cfg, 198 * 303), .05)
        self.assertAlmostEqual(epsilon(cfg, 60000), .05)
        self.assertAlmostEqual(epsilon(cfg, 199 * 303), .05)
        self.assertAlmostEqual(epsilon(cfg, 750 * 303), .05)

    def test_evaluation_disables_exploration_for_both_variants(self):
        for name in ("full_rules_v3", "full_rules_v3_slowexplore"):
            for steps in (0, 60000, 750 * 303, 1500 * 303):
                with self.subTest(name=name, steps=steps):
                    self.assertEqual(epsilon(variant_cfg(name), steps, training=False), 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
