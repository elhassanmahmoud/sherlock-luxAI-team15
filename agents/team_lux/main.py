"""Team-Agent für Lux AI S3 – Einstiegspunkt für runner.py (Klasse Agent_x)."""
import os
from typing import Optional

import numpy as np
import torch

from agents.team_lux.belief import Belief
from agents.team_lux.features import unit_features, FEATURE_DIM
from agents.team_lux.model import QNet, N_ACTIONS
from agents.team_lux.replay_buffer import ReplayBuffer
from agents.team_lux.reward import shaped_rewards


class Agent_x:
    def __init__(self, player: str, agent_path: Optional[str] = None, name: str = "Team Name Agent_X") -> None:
        self.player = player
        self.name = name
        self.team_id = 0 if player == "player_0" else 1
        self.opp_team_id = 1 - self.team_id
        self.agent_path = agent_path
        self.env_cfg = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.belief = Belief(self.team_id)
        self.q = QNet(FEATURE_DIM, N_ACTIONS).to(self.device)
        self.target_q = QNet(FEATURE_DIM, N_ACTIONS).to(self.device)
        self.buffer = ReplayBuffer(capacity=100_000)
        self.epsilon = 1.0
        self.training = True

        if agent_path is not None:
            self.load_agent(agent_path)
        self.target_q.load_state_dict(self.q.state_dict())

    # ---------- runner API ----------
    def set_env_cfg(self, env_cfg):
        self.env_cfg = env_cfg

    def set_to_eval_mode(self):
        self.training = False
        self.epsilon = 0.0
        self.q.eval()

    def act(self, step: int, obs) -> np.ndarray:
        self.belief.update(step, obs)
        actions = np.zeros((int(self.env_cfg["max_units"]), 3), dtype=int)
        # TODO (Phase 2): pro Einheit Features bauen, epsilon-greedy über self.q wählen
        return actions

    def update(self, step: int, obs, reward, action, terminated: bool, next_obs):
        if not self.training:
            return
        # TODO (Phase 2): shaped_rewards -> Transitions in self.buffer, Batch-Update, Target-Sync
        if terminated:
            self.save_agent()  # Workaround: runner speichert sonst nie Gelerntes

    def save_agent(self):
        if self.agent_path:
            os.makedirs(os.path.dirname(self.agent_path) or ".", exist_ok=True)
            torch.save(self.q.state_dict(), self.agent_path)

    def load_agent(self, load_path: str):
        if os.path.isfile(load_path):
            self.q.load_state_dict(torch.load(load_path, map_location=self.device))
        else:
            print(f"{load_path} nicht gefunden – starte untrainiert.")
