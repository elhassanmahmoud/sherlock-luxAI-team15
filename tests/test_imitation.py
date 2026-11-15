"""Umbau mit Imitation Learning (15.11.2026): Labels, Masken, Zielkopf und Agent-Schnittstelle."""
import numpy as np
import torch

from agents.sherlock import geometry as geo
from agents.sherlock.features import FEATURE_DIM
from agents.sherlock.imitation_agent import ImitationAgent, canonical_action, featurize, sap_legal
from agents.sherlock.imitation_net import ImitationNet, window_mask


def test_canonical_action_mirrors_moves_and_sap_deltas():
    assert canonical_action([1, 0, 0], False) == (1, 0, 0)
    assert canonical_action([1, 0, 0], True) == (2, 0, 0)  # up <-> right unter der Antidiagonale
    assert canonical_action([3, 0, 0], True) == (4, 0, 0)
    assert canonical_action([5, 2, -3], False) == (5, 2, -3)
    assert canonical_action([5, 2, -3], True) == (5, 3, -2)  # (dx, dy) -> (-dy, -dx)
    assert canonical_action([9, 0, 0], False) == (0, 0, 0)  # ungueltig -> stehen
    for a in range(5):  # zweimal spiegeln = identisch
        b = canonical_action([a, 0, 0], True)[0]
        assert canonical_action([b, 0, 0], True)[0] == a


def test_sap_legal_only_depends_on_energy():
    masks = np.ones((3, 6), dtype=bool)
    masks[0, 5] = False  # Sherlock sieht kein Ziel
    m = sap_legal(masks, np.array([50.0, 10.0, 30.0]), 30.0)
    assert m[:, 5].tolist() == [True, False, True]
    assert m[:, :5].all()
    assert masks[1, 5]  # Eingabe unveraendert


def test_window_mask_is_chebyshev_square_clipped_to_map():
    pos = torch.tensor([[0, 0], [10, 10]])
    m = window_mask(pos, torch.tensor([2, 1]), 24, 24)
    assert int(m[0].sum()) == 9 and bool(m[0, 2, 2]) and not bool(m[0, 3, 0])
    assert int(m[1].sum()) == 9 and bool(m[1, 9, 11]) and not bool(m[1, 12, 10])


def test_imitation_agent_plays_with_sap_head(tmp_path):
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock.config import AgentConfig
    from agents.sherlock.ppo_agent import save_policy

    torch.manual_seed(0)
    net = ImitationNet(feat_dim=FEATURE_DIM, ch=8, blocks=1, hidden=32)
    with torch.no_grad():
        net.pi.bias.copy_(torch.tensor([0.0, 0.0, 0.0, 0.0, 0.0, 50.0]))  # will immer schiessen
    path = tmp_path / "student.pth"
    save_policy(str(path), net, AgentConfig(), extra={"kind": "imitation"})
    env = LuxAIS3GymEnv(numpy_output=True)
    obs, info = env.reset(seed=7159998)
    agent = ImitationAgent("player_1", agent_path=str(path), train=False)
    assert agent.has_sap_head
    agent.set_env_cfg(info["params"])
    R = int(info["params"]["unit_sap_range"])
    cost = int(info["params"]["unit_sap_cost"])
    saw_sap = False
    for step in range(30):
        acts = agent.act(step, obs["player_1"])
        assert acts.shape == (16, 3)
        own = np.asarray(obs["player_1"]["units_mask"])[1]
        ene = np.asarray(obs["player_1"]["units"]["energy"])[1]
        for u in np.nonzero(acts[:, 0] == 5)[0]:
            saw_sap = True
            assert own[u] and ene[u] >= cost
            assert max(abs(acts[u, 1]), abs(acts[u, 2])) <= R and (acts[u, 1], acts[u, 2]) != (0, 0)
        obs, *_ = env.step({"player_0": np.zeros((16, 3), int), "player_1": acts})
    env.close()
    assert saw_sap


def test_featurize_skips_match_start():
    class Dummy:
        class B:
            def observe(self, obs):
                self.seen = True
        belief = B()
        _prev_ctx = "alt"

    d = Dummy()
    assert featurize(d, {"match_steps": np.int32(0)}) is None
    assert d._prev_ctx is None and d.belief.seen
    assert geo.SAP == 5


def _student(tmp_path, name, seed):
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.ppo_agent import save_policy
    torch.manual_seed(seed)
    net = ImitationNet(feat_dim=FEATURE_DIM, ch=8, blocks=1, hidden=32)
    path = tmp_path / name
    save_policy(str(path), net, AgentConfig(), extra={"kind": "imitation"})
    return path


def test_agent_x_delegates_imitation_checkpoint_and_never_overwrites(tmp_path):
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock.main import Agent_x
    path = _student(tmp_path, "s.pth", 1)
    data = path.read_bytes()
    env = LuxAIS3GymEnv(numpy_output=True)
    obs, info = env.reset(seed=7159996)
    a = Agent_x("player_0", agent_path=str(path))  # wie der Kurs-Runner (train=True)
    assert a._imitation is not None and not a.training
    a.set_env_cfg(info["params"])
    a.save_agent()
    for step in range(5):
        act = a.act(step, obs["player_0"])
        assert np.asarray(act).shape == (16, 3)
        a.update(step, obs["player_0"], 0.0, act, False, obs["player_0"])
        obs, *_ = env.step({"player_0": act, "player_1": np.zeros((16, 3), int)})
    env.close()
    assert path.read_bytes() == data


def test_student_ensemble_loads_all_members(tmp_path):
    import argparse

    from scripts.imitate import cmd_ensemble
    p1, p2 = _student(tmp_path, "a.pth", 1), _student(tmp_path, "b.pth", 2)
    out = tmp_path / "ens" / "ens.pth"
    cmd_ensemble(argparse.Namespace(students=[str(p1), str(p2)], out=str(out)))
    agent = ImitationAgent("player_0", agent_path=str(out), train=False)
    assert agent.has_sap_head and len(agent.extra_nets) == 1
    assert isinstance(agent.extra_nets[0], ImitationNet)
