import unittest
import numpy as np
from politik import choose, utility


class TrainingTarget(unittest.TestCase):
    def test_prediction_abstains_and_ties_choose_shorter(self):
        model = dict(center=[1], scale=[2], weights=[[1.0], [1.0]], bias=[0.0, 0.0])
        self.assertEqual(choose([1.5], model), 0)
        self.assertEqual(choose([2], model), 1)
        model["bias"][1] = 0.1
        self.assertEqual(choose([2], model), 3)

    def test_full_winning_game_counts_after_losing_first_match(self):
        base = dict(win=0, wins=1, sight=40, credit=42, matches=[dict(points=[10, 20])]*3)
        win = dict(base, win=1, wins=2, sight=42)
        self.assertAlmostEqual(utility(win, base), 14.88)
        self.assertEqual(utility(base, base), 0)


if __name__ == "__main__":
    unittest.main()
