import unittest
import numpy as np

from steuern import StationaryHistory, outcome, value_of


class WaitingTests(unittest.TestCase):
    def test_requires_repeated_stay_same_live_ship_and_place(self):
        h = StationaryHistory()
        for energy in (90, 95, 100):
            h.update([4], np.array([[2, 4]]), [0], [energy])
        self.assertEqual(h.stays[4], 3)
        self.assertEqual(h.energy_gain[4], 10)
        h.update([4], np.array([[2, 5]]), [0], [110])
        self.assertEqual(h.stays[4], 1)
        h.update([], np.empty((0, 2)), [], [])
        self.assertEqual(h.stays[4], 0)

    def test_value_compares_physical_times_and_final_margin(self):
        y = outcome(80, 70, 30, 22)
        self.assertEqual(y, [80, 70, 8])
        self.assertGreater(value_of(y, [70, 68, 9]), 0)
        self.assertEqual(value_of(y, y), 0)


if __name__ == "__main__":
    unittest.main()
