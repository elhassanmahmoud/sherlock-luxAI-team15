"""Netzarchitekturen."""
import torch.nn as nn

N_ACTIONS = 5  # 0 stay, 1-4 move (Sap folgt in Phase 3)


class QNet(nn.Module):
    def __init__(self, obs_dim: int, n_actions: int = N_ACTIONS):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_dim, 128), nn.ReLU(),
            nn.Linear(128, 128), nn.ReLU(),
            nn.Linear(128, n_actions),
        )

    def forward(self, x):
        return self.net(x)
