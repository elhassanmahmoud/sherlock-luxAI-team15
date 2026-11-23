import unittest
import numpy as np
from kandidat import landmarks, move_towards, paired_gain, choose_path


class ScoutTests(unittest.TestCase):
    def test_paths_have_different_lanes_and_beatable_barrier(self):
        goals = landmarks()
        self.assertLess(goals[0][1], goals[0][0])
        self.assertLess(goals[1][0], goals[1][1])
        self.assertEqual(goals[2][0], goals[2][1])
        legal = np.array([True, False, True, True, False])
        grid = np.zeros((24, 24), dtype=bool)
        grid[4, :5] = True
        self.assertEqual(move_towards((3, 3), (8, 3), legal, grid, 2), 3)
        self.assertIsNone(move_towards((3, 3), (3, 3), legal, grid, 2))

    def test_gain_sign_and_policy_abstention(self):
        self.assertGreater(paired_gain([60, 65, 0], [50, 50, 10]), 0)
        self.assertLess(paired_gain([60, 65, 0], [80, 85, -5]), 0)
        self.assertIsNone(choose_path([0.2, 0.9, -0.1], 1.0))
        self.assertEqual(choose_path([3., 1., 0.], 1.0), 0)


if __name__ == "__main__":
    unittest.main()
