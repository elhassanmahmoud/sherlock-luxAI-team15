"""Focused regression checks for pairing, activation-independent gates and lock-safe writes."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from auswerten import analyze, describe, gates, check_complete, score
from spielen import stamp, write_once


def game(seed, team, name, opponent, *, event=False):
    changed = [[10, 3, 0, 1]] if event else []
    return dict(phase="discovery", seed=seed, team=team, id=name, opponent=opponent, source=stamp(name), sensor=1,
                sight=31, credit=64, after_70=[3, 2], matches=[{"win": 1, "points": [10, 8]}] * 3,
                events=changed, steps=303, actions_checked=[303, 303], caught_errors=[0, 0], point_counting_version=2,
                wins=3, win=1, points=[30, 24], action_hash="a"*64)


class Regression(unittest.TestCase):
    def test_complete_pairing_and_direct_distinct(self):
        cards = [1, 2]
        rows = [game(s, t, n, o) for s in cards for t in (0, 1) for n, o in
                (("reference", "solution92"), ("blue", "solution92"), ("blue", "v16"))]
        sources = {"reference": "reference", "blue": "blue"}
        result = analyze("discovery", cards, ["blue"], rows, sources)
        self.assertEqual(result["games"], 12)
        self.assertEqual(result["candidates"]["blue"]["direct_rate"]["mean"], 1.0)
        self.assertEqual(result["candidates"]["blue"]["paired"]["whole"]["mean"], 0)
        self.assertIsNone(result["nominee"])
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            analyze("discovery", cards, ["blue"], rows[:-1], sources)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            analyze("discovery", cards, ["blue"], [*rows, rows[-1]], sources)
        wrong = copy.deepcopy(rows)
        wrong[1]["action_hash"] = "f"*64
        with self.assertRaisesRegex(ValueError, "Inactive"):
            analyze("discovery", cards, ["blue"], wrong, sources)
        wrong = copy.deepcopy(rows)
        wrong[0]["source"] = "wrong"
        with self.assertRaisesRegex(ValueError, "identity"):
            analyze("discovery", cards, ["blue"], wrong, sources)

    def test_map_bootstrap_keeps_both_seats_together(self):
        result = describe([.5, -.5], np.array([[0, 0], [1, 1], [1, 0], [0, 1]]))
        self.assertEqual(result["mean"], 0)
        np.testing.assert_allclose(result["ci95"], [-.4625, .4625])

    def test_selection_timing_sign_and_thresholds(self):
        cards = list(range(8))
        groups = {(n, o): {(s, t): game(s, t, n, o, event=n=="blue") for s in cards for t in (0, 1)}
                  for n, o in (("reference", "solution92"), ("blue", "solution92"), ("blue", "v16"))}
        for r in groups["reference", "solution92"].values():
            r["sight"] = 101
        d = score("blue", cards, groups, np.random.default_rng(0).integers(0, 8, size=(50, 8)))
        self.assertEqual(d["paired"]["sight"]["mean"], 70)
        self.assertTrue(gates("discovery", d)[1])
        self.assertTrue(gates("confirm", d)[1])
        d["paired"]["sight"]["ci95"][0] = 0
        self.assertFalse(gates("confirm", d)[1])

    def test_two_independent_release_routes(self):
        d = {"paired": {"whole": {"ci95": [.001, .02]}}, "direct_rate": {"mean": .50, "ci95": [.45, .55]}}
        self.assertTrue(gates("general", d)[1])
        d["direct_rate"]["mean"] = .49
        self.assertFalse(gates("general", d)[1])
        d["direct_rate"] = {"mean": .57, "ci95": [.51, .65]}
        d["paired"]["whole"]["ci95"][0] = -.01
        self.assertTrue(gates("general", d)[1])
        d["paired"]["whole"]["ci95"][0] = -.010001
        self.assertFalse(gates("general", d)[1])

    def test_incomplete_panel_not_opened(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / "discovery/reference/1_0_solution92.json"
            p.parent.mkdir(parents=True)
            p.write_text("not even valid JSON")
            with self.assertRaisesRegex(ValueError, "no scores opened"):
                check_complete(root, "discovery", [1], ["blue"])

    def test_existing_evidence_immutable(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "data.json"
            write_once(p, {"a": 1})
            write_once(p, {"a": 1})
            with self.assertRaisesRegex(ValueError, "differs"):
                write_once(p, {"a": 2})
            self.assertEqual(json.loads(p.read_text()), {"a": 1})


if __name__ == "__main__":
    unittest.main()
