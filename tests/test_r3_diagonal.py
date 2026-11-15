import unittest

import torch

from agents.sherlock.features import FEATURE_NAMES
from scripts import r3_diagonal


class ReflectionTests(unittest.TestCase):
    def test_every_compass_input_has_its_physical_counterpart(self):
        expected = {"self_x": "self_y", "assigned_dy": "assigned_dx", "enemy_dx": "enemy_dy",
                    "l_allies": "u_allies", "d_energy": "r_energy", "c_passable": "c_passable",
                    "cfg_sap_range": "cfg_sap_range", "point_exists": "point_exists"}
        permutation = r3_diagonal.FEATURES
        for before, after in expected.items():
            self.assertEqual(FEATURE_NAMES[permutation[FEATURE_NAMES.index(before)]], after)
        self.assertEqual([permutation[i] for i in permutation], list(range(79)))
        self.assertEqual(r3_diagonal.ACTIONS, (0, 4, 3, 2, 1, 5))

    def test_positions_and_board_reach_the_same_reflected_cell(self):
        probe = Probe()
        agent = r3_diagonal.TwoViews(probe)
        board = torch.zeros((1, 16, 5, 5))
        board[0, 7, 1, 4] = 3.0
        features = torch.zeros(1, 79)
        features[0, 0] = 1.0
        logits, value, sap = agent.forward_all(board, torch.tensor([0]), torch.tensor([[1, 4]]), features)
        self.assertEqual(probe.positions, [(1, 4), (4, 1)])
        self.assertEqual(probe.at_cell, [3.0, 3.0])
        self.assertEqual(probe.feature_x, [1.0, 0.0])
        self.assertTrue(torch.equal(logits[0], torch.tensor([0., 2.5, 2.5, 2.5, 2.5, 5.])))
        self.assertEqual(value.item(), 1.0)
        self.assertEqual(sap[0, 1, 4].item(), 3.0)


class Probe:
    arch = {"feat_dim": 79, "in_ch": 16}

    def __init__(self):
        self.positions, self.at_cell, self.feature_x = [], [], []

    def forward_all(self, board, step, pos, features):
        x, y = pos[0].tolist()
        self.positions.append((x, y))
        self.at_cell.append(board[0, 7, x, y].item())
        self.feature_x.append(features[0, 0].item())
        return torch.arange(6).float()[None, :], features[:, 0], board[:, 7]


class AdviceTests(unittest.TestCase):
    def test_mask_threshold_and_both_shot_boundaries_after_the_average(self):
        logits = torch.zeros(5, 6)
        logits[0, 1:3] = torch.tensor([100., 20.])
        logits[1, 2] = 15.
        logits[2, 5] = 15.
        logits[4, 1] = 15.
        mask = torch.ones(5, 6, dtype=torch.bool)
        mask[0, 1] = False
        base = torch.tensor([0, 5, 1, 2, 1])
        self.assertEqual(r3_diagonal.played_action(logits,mask,base).tolist(),[2,5,1,2,1])

    def test_both_registered_checks_apply_to_mixed_only(self):
        for gained,lost,hurt,expected in [(2,1,10,True),(1,1,10,False),(2,1,11,False),(0,1,0,False)]:
            checks = r3_diagonal.gates({"pair":{"gained":gained,"lost":lost},
                                        "original":{"hurt":10},"reflected":{"hurt":hurt}})
            self.assertEqual(all(checks.values()),expected)

    def test_two_archived_units_keep_their_own_direction_and_shot_protection(self):
        import tempfile
        import numpy as np
        from pathlib import Path
        class FixedPair:
            def pair(self, board, step, positions, features):
                original = torch.zeros(len(step),6)
                original[:,1] = 15.
                both = torch.zeros_like(original)
                both[:,2] = 15.
                return (original,None,None),both
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/"archive.npz"
            np.savez(p,planes=np.zeros((1,16,3,3),np.int8),step=np.array([0,0]),pos=np.array([[0,1],[1,0]]),
                     feats=np.zeros((2,79),np.float16),mask=np.ones((2,6),bool),act=np.array([2,5]),
                     base_act=np.array([0,5]),sdx=np.zeros(2,int),sdy=np.zeros(2,int),played_act=np.array([0,5]))
            result = r3_diagonal.measure(FixedPair(),p)
        self.assertEqual(dict(result["pair"]),{"rows":2,"changed":1,"gained":1,"lost":0})
        self.assertEqual(result["original"]["base_matches"],1)
        self.assertEqual(result["reflected"]["advised_matches"],2)
        self.assertEqual(result["by_teacher_direction"]["right"]["gained"],1)
        self.assertEqual(result["by_teacher_direction"]["sap"]["changed"],0)
