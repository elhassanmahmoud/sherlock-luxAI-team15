"""Speichern/Laden: identische Q-Werte, Trainingszaehler bleiben, Config wandert mit."""
from dataclasses import replace

import numpy as np
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.features import FEATURE_DIM
from agents.sherlock.main import Agent_x


def test_save_load_gives_identical_q_and_counters(tmp_path, env):
    from agents.default.default import DefaultAgent
    from scripts.common import play_game

    cfg = replace(AgentConfig(), learn_start=500, batch_size=32)
    a = Agent_x("player_0", cfg=cfg, seed=1)
    a.autosave_on_terminate = False
    play_game(env, a, DefaultAgent("player_1"), seed=5, our_side="player_0", train=True)
    assert a.learn_steps > 0
    path = tmp_path / "agent.pth"
    a.save_agent(str(path))

    b = Agent_x("player_0", agent_path=str(path), seed=2)
    x = torch.randn(64, FEATURE_DIM)
    with torch.no_grad():
        assert torch.equal(a.q(x), b.q(x))
        assert torch.equal(a.target_q(x), b.target_q(x))
    assert (b.env_steps, b.learn_steps) == (a.env_steps, a.learn_steps)
    assert b.epsilon == a.epsilon
    assert b.cfg == cfg

    # Training laeuft weiter: Zaehler wachsen ab dem geladenen Stand
    b.autosave_on_terminate = False
    steps0 = b.env_steps
    play_game(env, b, DefaultAgent("player_1"), seed=6, our_side="player_1", train=True)
    assert b.env_steps > steps0


def test_config_is_restored_from_checkpoint(tmp_path):
    a = Agent_x("player_0", cfg=AgentConfig(use_sap=False))
    a.save_agent(str(tmp_path / "x.pth"))
    b = Agent_x("player_0", agent_path=str(tmp_path / "x.pth"))
    assert b.n_actions == 5 and not b.cfg.use_sap
