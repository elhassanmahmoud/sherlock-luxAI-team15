from collections import Counter
from types import SimpleNamespace

import numpy as np
import pytest

from agents.sherlock import geometry as g
from agents.sherlock.main import Agent_x
from scripts import combat_teacher_counterfactual as cf


def setup_scenario():
    pos = np.array([[2, 3], [3, 2], [2, 2], [0, 0]])
    public = dict(steps=4, match_steps=4, units={"position": np.stack([pos, pos]),
                  "energy": np.array([[40, 40, 40, -1], [40, 40, 40, -1]])},
                  units_mask=np.ones((2, 4), bool), sensor_mask=np.ones((6, 6), bool),
                  map_features={"tile_type": np.zeros((6, 6), int)})
    a = SimpleNamespace(team_id=1, belief=SimpleNamespace(mirrored=True),
                        cfg=SimpleNamespace(dodge_shape=False, dodge_distrust=0, dodge_verify=True),
                        env_cfg=dict(unit_move_cost=3, unit_sap_cost=40, unit_sap_range=2),
                        _prev_actions={0:5, 1:0, 2:0}, _pred_pending=[(0,2,3,40,True)], _sap_unknown={0},
                        _sap_hits={0:1}, ep_stats=dict(sap_attempts=1,sap_hits_est=1),
                        _prev_ctx=dict(ally_pos=5-pos[:,::-1], enemy_coords=np.array([[3,3]]),
                                       enemy_energies=np.array([80])))
    base = np.array([[5,1,-1], [0,0,0], [0,0,0], [0,0,0]])
    teacher = np.array([[1,0,0], [2,0,0], [5,0,0], [5,1,1]])
    return a, public, base, teacher


def test_arms_are_disjoint_and_player_one_bookkeeping_uses_final_actions(monkeypatch):
    from agents.sherlock import opp_model
    monkeypatch.setattr(opp_model, "predict_sol92_saps", lambda ctx, belief, shape: [(0,0),(0,2)])
    a, obs, base, teacher = setup_scenario()
    assert cf.substitute(a, obs, base, teacher, "control", Counter()) is base
    out = cf.substitute(a, obs, base, teacher, "combat", Counter())
    assert out.tolist() == [[1,0,0],[0,0,0],[5,0,0],[0,0,0]]
    assert a._prev_actions == {0:g.RIGHT, 1:g.STAY, 2:g.SAP}
    assert a._pred_pending == [(2,3,3,40,True)]
    assert a._sap_hits == {2:1}
    a, obs, base, teacher = setup_scenario()
    assert cf.substitute(a, obs, base, teacher, "movement", Counter()).tolist() == [
        [5,1,-1],[2,0,0],[0,0,0],[0,0,0]]


def test_native_legality_allows_self_sap_and_payable_unknown_moves():
    _, obs, _, _ = setup_scenario()
    cfg = dict(unit_move_cost=3, unit_sap_cost=40, unit_sap_range=2)
    tiles = obs["map_features"]["tile_type"]
    assert cf.native_order([5,0,0], [0,0], 40, cfg, tiles)
    assert not cf.native_order([5,1,1], [0,0], 39, cfg, tiles)
    assert not cf.native_order([5,-1,0], [0,0], 40, cfg, tiles)
    assert not cf.native_order([5,3,0], [0,0], 40, cfg, tiles)
    tiles[1,0] = 2
    assert not cf.native_order([2,0,0], [0,0], 40, cfg, tiles)
    tiles[1,0] = -1
    assert cf.native_order([2,0,0], [0,0], 3, cfg, tiles)
    assert not cf.native_order([2,0,0], [0,0], 2, cfg, tiles)
    assert cf.native_order([1,0,0], [0,0], 3, cfg, tiles)


def test_native_outer_estimator_remembers_only_returned_command_once(monkeypatch):
    a = object.__new__(cf.CounterfactualAgent)
    a.training = False
    a.team_id, a.env_cfg = 1, {}
    a.cfg = SimpleNamespace(frozen=False, nebula_avoid=True, rules_in_training_all=False)
    events = []
    a.param_est = SimpleNamespace(observe=lambda *args: events.append("observe"),
                                  remember=lambda obs, team, actions: events.append(("remember", actions.tolist())))
    base = np.array([[5,-1,1]])
    def v14(self, step, obs):
        events.append("v14")
        return base
    def finish(step, obs, current):
        assert current is base
        events.extend(["opponent", "teacher"])
        return np.array([[0,0,0]])
    monkeypatch.setattr(Agent_x, "_act", v14)
    a.finish_step = finish
    assert a.act(7, {}).tolist() == [[0,0,0]]
    assert events == ["observe","v14","opponent","teacher",("remember", [[0,0,0]])]
