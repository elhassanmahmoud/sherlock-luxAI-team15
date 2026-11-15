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


@pytest.mark.parametrize("mode", ["points", "combat", "sap"])
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
