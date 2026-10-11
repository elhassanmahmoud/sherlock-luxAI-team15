"""Experiment-Varianten: Prof-Baselines und Ablationen von `full`.

Jede Ablation unterscheidet sich von `full` durch GENAU EIN AgentConfig-Feld
(test_variants.py prueft das). Kein kopierter Agent-Code.
"""
from __future__ import annotations

import os
from dataclasses import replace

import numpy as np
import torch

from agents.sherlock.config import AgentConfig

PROF_WEIGHTS = "agents/DQN/agent.pth"

# name -> (Art, AgentConfig-Overrides)
VARIANTS: dict[str, tuple[str, dict]] = {
    "baseline_prof": ("prof_frozen", {}),
    "baseline_prof_retrained": ("prof_train", {}),
    "full": ("sherlock", {}),
    "full_sym": ("sherlock", {"use_symmetry": True}),
    "no_belief": ("sherlock", {"use_belief": False}),
    "no_shaping": ("sherlock", {"use_shaping": False}),
    "no_sap": ("sherlock", {"use_sap": False}),
    "no_guided_explore": ("sherlock", {"guided_prob": 0.0}),
    "no_canonical": ("sherlock", {"canonical": False}),
}

ABLATIONS = [v for v, (k, _) in VARIANTS.items() if k == "sherlock" and not v.startswith("full")]


def variant_cfg(name: str) -> AgentConfig:
    kind, overrides = VARIANTS[name]
    return replace(AgentConfig(), **overrides)


def is_trainable(name: str) -> bool:
    return VARIANTS[name][0] != "prof_frozen"


def separate_sides(name: str) -> bool:
    """Braucht die Variante ein Netz pro Seite?"""
    kind, _ = VARIANTS[name]
    return kind == "sherlock" and not variant_cfg(name).canonical


class ProfAdapter:
    """Unveraenderter Prof-DQN (agents/DQN/main.py) hinter unserer Trainings-API.

    Der Prof-Agent kennt seine Seite nur aus dem Konstruktor; `new_game` setzt
    die Identitaetsfelder von aussen um, statt den Code zu aendern. Netz,
    Optimizer und Epsilon (konstant 0.1, wie im Original) bleiben ueber Spiele
    erhalten - genau das, was der Runner wegen des Speicher-Bugs nicht tut.
    """

    TRAIN_EPSILON = 0.1  # Default des Prof-Agenten

    def __init__(self, player: str, agent_path: str | None):
        from agents.DQN.main import Agent

        self.inner = Agent(player, agent_path=agent_path if agent_path and os.path.isfile(agent_path) else None)
        self.name = "Prof-DQN"
        self.training = True
        self.new_game(player)

    def new_game(self, player: str) -> None:
        a = self.inner
        a.player = player
        a.opp_player = "player_1" if player == "player_0" else "player_0"
        a.team_id = 0 if player == "player_0" else 1
        a.opp_team_id = 1 - a.team_id

    @property
    def player(self) -> str:
        return self.inner.player

    def set_env_cfg(self, env_cfg) -> None:
        self.inner.set_env_cfg(env_cfg)

    def act(self, step, obs):
        return self.inner.act(step, obs)

    def update(self, **kw) -> None:
        self.inner.update(**kw)

    def set_to_eval_mode(self) -> None:
        self.training = False
        self.inner.set_to_eval_mode()

    def set_to_train_mode(self) -> None:
        self.training = True
        self.inner.epsilon = self.TRAIN_EPSILON
        self.inner.q.train()

    @property
    def epsilon(self) -> float:
        return float(self.inner.epsilon)

    def pop_mean_loss(self) -> float:
        return float("nan")  # Prof-Code gibt den Loss nicht nach aussen

    def save_agent(self, path: str) -> None:
        torch.save(self.inner.q.state_dict(), path)


def make_learner(name: str, player: str, agent_path: str | None = None, seed: int | None = None):
    """Agent fuer Variante `name` erzeugen (geladen, falls agent_path existiert)."""
    kind, _ = VARIANTS[name]
    if kind == "prof_frozen":
        a = ProfAdapter(player, PROF_WEIGHTS)
        a.set_to_eval_mode()
        return a
    if kind == "prof_train":
        return ProfAdapter(player, agent_path)
    from agents.sherlock.main import Agent_x

    path = agent_path if agent_path and os.path.isfile(agent_path) else None
    agent = Agent_x(player, agent_path=path, cfg=variant_cfg(name), seed=seed,
                    name=f"sherlock[{name}]")
    agent.agent_path = agent_path
    agent.autosave_on_terminate = False
    return agent


def seed_everything(seed: int) -> None:
    import random

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
