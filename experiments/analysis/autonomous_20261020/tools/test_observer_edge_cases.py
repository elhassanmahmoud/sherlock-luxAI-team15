"""Cross-review counterexamples: ordinary unittest, NumPy, no Torch."""
import unittest

import numpy as np

from observe_sap_geometry import observe_sap_geometry


def fixture(enemies, energies):
    return dict(
        W=24, H=24, ally_pos=np.array([[2, 5]], np.int32),
        enemy_coords=np.array(enemies, np.int32),
        enemy_energies=np.array(energies, np.float32), sap_range=5,
        point_tiles=np.zeros((24, 24), bool),
    )


class ObserverEdgeCases(unittest.TestCase):
    def test_smart_sap_is_unsupported_even_when_actual_target_matches(self):
        ctx = fixture([(4, 4), (4, 6), (6, 4), (6, 6)], [100]*4)
        r = observe_sap_geometry(ctx, [0], {0: (2, -1, 1)},
                                 np.array([[5, 2, -1]], np.int32), smart_sap=True)
        self.assertEqual(r["counters"]["executed_saps"], 1)
        self.assertEqual(r["counters"]["executed_saps_with_unsupported_override"], 1)
        self.assertEqual(r["counters"]["eligible_executed_saps"], 0)
        self.assertEqual(r["counters"]["strictly_better_proxy_centers"], 0)

    def test_negative_enemy_context_is_excluded_separately(self):
        ctx = fixture([(5, 5), (4, 5)], [100, -150])
        r = observe_sap_geometry(ctx, [0], {0: (3, 0, 2)},
                                 np.array([[5, 3, 0]], np.int32))
        counts = r["counters"]
        self.assertEqual(counts["executed_saps"], 1)
        self.assertEqual(counts.get("executed_saps_with_negative_enemy_context", 0), 1)
        self.assertEqual(counts["eligible_executed_saps"], 0)
        self.assertEqual(counts["strictly_better_proxy_centers"], 0)
        self.assertEqual(counts["proxy_score_gain_sum"], 0)
        self.assertEqual(r["examples"], [])

    def test_empty_point_bonus_does_not_create_shadow_improvement(self):
        ctx = fixture([(5, 5)], [100])
        ctx["point_tiles"][6, 5] = True
        r = observe_sap_geometry(ctx, [0], {0: (3, 0, 1)},
                                 np.array([[5, 3, 0]], np.int32), sap_pt_first=True)
        self.assertEqual(r["counters"]["eligible_executed_saps"], 1)
        self.assertEqual(r["counters"]["strictly_better_proxy_centers"], 0)

    def test_empty_cluster_point_center_score_has_no_priority_bonus(self):
        ctx = fixture([(4, 4), (4, 6), (6, 4), (6, 6)], [100]*4)
        ctx["point_tiles"][5, 5] = True
        r = observe_sap_geometry(ctx, [0], {0: (2, -1, 1)},
                                 np.array([[5, 2, -1]], np.int32), sap_pt_first=True)
        self.assertEqual(r["counters"]["strictly_better_proxy_centers"], 1)
        self.assertEqual(r["counters"]["proxy_score_before_sum"], 100)
        self.assertEqual(r["counters"]["proxy_score_after_sum"], 200)
        self.assertEqual(r["counters"]["proxy_score_gain_sum"], 100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
