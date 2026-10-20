"""CNN-Policy-Ensemble (20.10.2026): Laden, Mitteln, Bau-Skript."""
import subprocess
import sys

import numpy as np
import torch

from agents.sherlock.cnn_model import PolicyNet
from agents.sherlock.config import AgentConfig
from agents.sherlock.features import FEATURE_DIM
from agents.sherlock.ppo_agent import PPOAgent, save_policy
from tests.conftest import ENV_CFG, make_obs


def _net(seed):
    torch.manual_seed(seed)
    return PolicyNet(FEATURE_DIM, ch=8, blocks=1, hidden=16)


def _actions(path, obs_list):
    agent = PPOAgent("player_0", agent_path=str(path), train=False)
    agent.set_env_cfg(ENV_CFG)
    return agent, [agent.act(o["steps"], o).copy() for o in obs_list]


def test_ensemble_of_identical_nets_acts_like_single_net(tmp_path):
    cfg = AgentConfig()
    net = _net(1)
    single = tmp_path / "a.pth"
    save_policy(str(single), net, cfg)
    out = tmp_path / "ens.pth"
    subprocess.run([sys.executable, "-m", "scripts.build_cnn_ensemble", "--out", str(out),
                    str(single), str(single), str(single)], check=True)
    obs = [make_obs(s, s, units=[(2, 3, 100), (5, 5, 80)], relics=[(6, 6)]) for s in (1, 2, 3)]
    _, a1 = _actions(single, obs)
    agent, a3 = _actions(out, obs)
    assert len(agent.extra_nets) == 2
    for x, y in zip(a1, a3):
        assert np.array_equal(x, y)


def test_ensemble_averages_log_probabilities(tmp_path):
    cfg = AgentConfig()
    paths = []
    for s in (1, 2):
        p = tmp_path / f"n{s}.pth"
        save_policy(str(p), _net(s), cfg)
        paths.append(str(p))
    out = tmp_path / "ens.pth"
    subprocess.run([sys.executable, "-m", "scripts.build_cnn_ensemble", "--out", str(out),
                    *paths], check=True)
    agent = PPOAgent("player_0", agent_path=str(out), train=False)
    assert len(agent.extra_nets) == 1
    x = (torch.zeros(1, 16, 24, 24), torch.zeros(2, dtype=torch.long),
         torch.tensor([[1, 1], [3, 4]]), torch.randn(2, FEATURE_DIM))
    with torch.no_grad():
        want = (torch.log_softmax(agent.net(*x)[0], 1)
                + torch.log_softmax(agent.extra_nets[0](*x)[0], 1)) / 2
        n1 = PPOAgent("player_0", agent_path=paths[0], train=False).net
        n2 = PPOAgent("player_0", agent_path=paths[1], train=False).net
        manual = (torch.log_softmax(n1(*x)[0], 1) + torch.log_softmax(n2(*x)[0], 1)) / 2
    assert torch.allclose(want, manual, atol=1e-6)
