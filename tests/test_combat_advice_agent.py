import numpy as np
import pytest
import torch

from agents.sherlock import geometry as geo
from agents.sherlock.main import Agent_x
from scripts.combat_advice_agent import (
    CombatAdviceAgent, CombatAdviceNet, CombatBoardHistory, advice_decision,
)


def test_history_uses_only_adjacent_steps_and_copies_channels():
    h = CombatBoardHistory()
    p = np.zeros((16, 24, 24), np.float32)
    p[10:13, 2, 8] = [.25, .75, 1]
    assert not h.build(p, 80, 80, 0)[16:].any()
    p[:] = 0
    np.testing.assert_array_equal(h.build(p, 81, 81, 0)[16:, 2, 8], [.25, .75, 1])
    p[10:13] = 1
    assert not h.build(p, 83, 83, 0)[16:].any()
    assert not h.build(p, 84, 1, 1)[16:].any()
    h.reset()
    assert not h.build(p, 85, 2, 1)[16:].any()


def test_target_logits_are_per_shooter_and_chebyshev_mask_includes_origin():
    torch.manual_seed(12)
    net = CombatAdviceNet()
    boards = torch.randn(1, 19, 24, 24)
    pos = torch.tensor([[8, 5], [8, 5], [0, 0]])
    feats = torch.zeros(3, 79)
    feats[1, 2] = .9
    base = torch.tensor([5, 5, 1])
    fire, targets = net(boards, torch.zeros(3, dtype=torch.long), pos, feats, base, torch.tensor([1, 1, 0]))
    assert fire.shape == (3,) and targets.shape == (3, 24, 24)
    assert torch.isfinite(targets[0]).sum() == 9
    assert torch.isfinite(targets[0, 7, 4]) and torch.isfinite(targets[0, 8, 5])
    assert torch.isfinite(targets[2]).sum() == 1 and torch.isfinite(targets[2, 0, 0])
    assert not torch.allclose(targets[0].flatten().softmax(0), targets[1].flatten().softmax(0))


@pytest.mark.parametrize("base,fire,target,energy,protect,mode,expected", [
    (5, 0, .5, True, False, "aim", True), (5, 0, .499, True, False, "fire", False),
    (0, 1, 1, True, False, "aim", False), (0, .899, 1, True, False, "fire", False),
    (2, .90, .5, True, False, "fire", True), (2, 1, 1, True, True, "fire", False),
    (5, 1, 1, False, False, "fire", False),
])
def test_gates(base, fire, target, energy, protect, mode, expected):
    assert advice_decision(base, fire, target, energy, protect, mode) is expected


def test_native_commands_stats_and_estimator_match_actual_output(monkeypatch):
    from types import SimpleNamespace
    import scripts.combat_advice_agent as combat

    agent = object.__new__(CombatAdviceAgent)
    agent.mode = "fire"
    agent.training = False
    agent.team_id = 1
    agent.env_cfg = {}
    agent._imitation = None
    agent.cfg = SimpleNamespace(nebula_avoid=True)
    agent.history = CombatBoardHistory()
    point = np.zeros((24, 24), dtype=bool)
    point[8, 7] = True
    agent.belief = SimpleNamespace(mirrored=True, point_tiles=point)
    pos = np.array([[7, 7], [7, 8], [8, 8], [0, 0], [0, 0]])
    ctx = dict(match_idx=0, ally_pos=pos, ally_ene=[100, 100, 100, 100, 1],
               ally_count=np.zeros((24, 24)), enemy_coords=np.array([[9, 9]]),
               sap_cost=30, sap_range=3)
    ids = [0, 1, 2, 4]
    feats = {u: np.zeros(79, np.float32) for u in ids}
    original = np.array([[geo.UP, 0, 0], [geo.STAY, 0, 0], [geo.SAP, 2, 2],
                         [0, 0, 0], [geo.STAY, 0, 0]])
    obs = {"steps": 6, "match_steps": 6}
    def original_act(self, step, obs):
        self._prev_ctx = ctx
        self._cache = (6, ctx, ids, feats, None, None)
        self._prev_actions = {0: geo.RIGHT, 1: geo.STAY, 2: geo.SAP, 4: geo.STAY}
        self._sap_hits = {2: 0}
        self._sap_unknown = {2}
        self._shape_pending = []
        self._pred_pending = [(1, 7, 8, 100., False)]
        self.ep_stats = {"sap_attempts": 1, "sap_hits_est": 0}
        return original.copy()
    class FixedHead:
        def __call__(self, boards, step_idx, positions, features, bases, ranges):
            assert bases.tolist() == [geo.RIGHT, geo.STAY, geo.SAP, geo.STAY]
            logits = torch.full((4, 24, 24), -torch.inf)
            logits[:, 9, 9] = 0
            return torch.full((4,), 9.), logits
    agent.advice = FixedHead()
    saved = []
    agent.param_est = SimpleNamespace(observe=lambda *args: None,
                                      remember=lambda obs, team, act: saved.append(act.copy()))
    monkeypatch.setattr(Agent_x, "_act", original_act)
    monkeypatch.setattr(combat, "map_planes", lambda ctx: np.zeros((16, 24, 24), np.float32))
    actions = agent._act_est(6, obs)
    # Spieler 1: kanonische Deltas (+2,+1) und (+1,+1) -> native (-1,-2) und (-1,-1).
    np.testing.assert_array_equal(actions[1:3], [[5, -1, -2], [5, -1, -1]])
    np.testing.assert_array_equal(actions[[0, 3, 4]], original[[0, 3, 4]])
    assert len(saved) == 1
    np.testing.assert_array_equal(saved[0], actions)
    assert agent.ep_stats["sap_attempts"] == agent.ep_stats["sap_hits_est"] == 2
    assert agent._sap_hits == {1: 1, 2: 1} and not agent._sap_unknown
    assert agent._pred_pending[0][-1] and agent._prev_actions[1] == geo.SAP
    agent.training = True
    np.testing.assert_array_equal(agent._act(6, obs), original)
