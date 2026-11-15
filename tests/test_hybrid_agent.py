"""Hybrid aus V14 und nachgeahmter Policy (15.11.2026): gueltige Aktionen und Aufteilung je Modus."""
import numpy as np
import pytest
import torch

from agents.sherlock.features import FEATURE_DIM
from agents.sherlock.imitation_net import ImitationNet

V14 = "agents/sherlock/weights/agent_p0.pth"


@pytest.fixture()
def student(tmp_path):
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.ppo_agent import save_policy
    torch.manual_seed(0)
    path = tmp_path / "s.pth"
    save_policy(str(path), ImitationNet(feat_dim=FEATURE_DIM, ch=8, blocks=1, hidden=32), AgentConfig(),
                extra={"kind": "imitation", "sap_own_tile": True})
    return str(path)


@pytest.mark.parametrize("mode", ["points", "combat", "sap", "mixed"])
def test_hybrid_plays_valid_actions(student, mode):
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock.hybrid_agent import HybridAgent
    env = LuxAIS3GymEnv(numpy_output=True)
    obs, info = env.reset(seed=7159994)
    agent = HybridAgent("player_1", V14, student, mode=mode)
    agent.new_game("player_1")
    agent.set_env_cfg(info["params"])
    for step in range(20):
        acts = agent.act(step, obs["player_1"])
        assert acts.shape == (16, 3) and acts[:, 0].min() >= 0 and acts[:, 0].max() <= 5
        obs, *_ = env.step({"player_0": np.zeros((16, 3), int), "player_1": acts})
    env.close()
    assert sum(agent.stats.values()) > 0
    if mode == "sap":  # untrainierter Schueler schiesst kaum -> fast alles V14
        assert agent.stats["v14"] >= agent.stats["student"]


def test_hybrid_rejects_unknown_mode(student):
    from agents.sherlock.hybrid_agent import HybridAgent
    with pytest.raises(ValueError):
        HybridAgent("player_0", V14, student, mode="chaos")


@pytest.mark.parametrize("team,shot,move", [(0, (5, 1, 2), 2), (1, (5, -2, -1), 1)])
def test_hybrid_estimator_uses_played_world_actions(team, shot, move):
    from types import SimpleNamespace

    from agents.sherlock.hybrid_agent import HybridAgent
    from agents.sherlock.param_est import ParamEstimator

    canonical = np.array([(3, 3), (5, 5), (1, 1)])
    pos = np.zeros((2, 3, 2), int)
    pos[team] = canonical if team == 0 else 7 - canonical[:, ::-1]
    energy = np.full((2, 3), 100, int)
    mask = np.zeros((2, 3), bool)
    mask[team] = True
    tiles = np.zeros((8, 8), int)
    tiles[tuple(pos[team, 0])] = 1
    obs = dict(units=dict(position=pos, energy=energy), units_mask=mask,
               sensor_mask=np.ones_like(tiles, bool), map_features=dict(energy=np.zeros_like(tiles), tile_type=tiles),
               match_steps=10)

    # A points-mode hybrid uses the two student orders and keeps V14's third ship on its point.
    # The two subagents already output native world directions and SAP offsets for their seat.
    base = np.array([[0, 0, 0], [3, 0, 0], [0, 0, 0]])
    advice = np.array([shot, (move, 0, 0), (4, 0, 0)])
    ctx = dict(ally_ids=np.arange(3), ally_pos=canonical, first_on_tile={(1, 1): 2}, assigned={})
    points = np.zeros_like(tiles, bool)
    points[1, 1] = True
    estimator = ParamEstimator()

    def v14_act(step, public):
        estimator.remember(public, team, base)
        return base

    hybrid = HybridAgent.__new__(HybridAgent)
    hybrid.mode = "points"
    hybrid.v14 = SimpleNamespace(act=v14_act, _prev_ctx=ctx, belief=SimpleNamespace(point_tiles=points),
                                 param_est=estimator)
    hybrid.student = SimpleNamespace(act=lambda step, public: advice)
    hybrid.stats = {"v14": 0, "student": 0}
    played = hybrid.act(10, obs)
    assert played.tolist() == [list(shot), [move, 0, 0], [0, 0, 0]]
    assert np.array_equal(estimator._prev["act"], played)

    # 100 – 30 SAP – 3 nebula = 67. Remembering V14's unused STAY would imply an impossible loss of 33.
    energy[team, :2] = (67, 98)
    pos[team, 1] += (1, 0) if move == 2 else (0, -1)
    estimator.observe(dict(obs, match_steps=11), team, None, {"unit_sap_cost": 30})
    assert estimator.n_neb == 1
    assert estimator.nebula() == 3


def test_packed_hybrid_loads_through_agent_x_and_never_overwrites(student, tmp_path):
    import argparse

    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock.main import Agent_x
    from scripts.imitate import cmd_pack_hybrid
    out = tmp_path / "run" / "weights" / "agent.pth"
    cmd_pack_hybrid(argparse.Namespace(student=student, mode="mixed", combat_radius=4,
                                       set=["imit_stay_bias=1.5", "imit_unstack=true"], out=str(out)))
    data = out.read_bytes()
    a = Agent_x("player_0", agent_path=str(out))  # wie der Kurs-Runner
    assert a._imitation is not None and a._imitation.mode == "mixed" and a._imitation.combat_radius == 4
    assert a._imitation.student.cfg.imit_stay_bias == 1.5 and a._imitation.student.cfg.imit_unstack
    env = LuxAIS3GymEnv(numpy_output=True)
    obs, info = env.reset(seed=7159993)
    a.set_env_cfg(info["params"])
    a.save_agent()
    for step in range(5):
        act = a.act(step, obs["player_0"])
        assert np.asarray(act).shape == (16, 3)
        a.update(step, obs["player_0"], 0.0, act, False, obs["player_0"])
        obs, *_ = env.step({"player_0": act, "player_1": np.zeros((16, 3), int)})
    env.close()
    assert out.read_bytes() == data
