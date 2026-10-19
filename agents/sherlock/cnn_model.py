"""CNN-Policy fuer PPO (Empfehlung aus dem Review 16.10.2026).

Eingabe pro Step: Kartenebenen [C, 24, 24] im kanonischen Raum (map_planes)
und pro Unit der bekannte 79er-Merkmalsvektor (features.build_features).

    Karte --Conv3x3--> ResBlocks --> Merkmalskarte [ch, 24, 24]
                                       |-- Wert an der Unit-Position (lokal)
                                       |-- Mittel ueber die Karte (global)
    Unit-Merkmale --MLP-------------------+
                                       --> MLP --> 6 Aktions-Logits (Policy)
                                               --> V(s, Unit) (Critic)

Ein Netz fuer alle Units (geteilte Parameter), jede Unit waehlt ihre Aktion
selbst (dezentral), die Karte liefert den gemeinsamen Ueberblick.
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn

from .belief import TILE_ASTEROID

N_PLANES = 16
PLANE_NAMES = [
    "point_tiles", "candidate", "relic", "explored", "explored_ever", "asteroid",
    "nebula", "energy", "own_units", "own_energy", "enemy_units", "enemy_energy",
    "visible_now", "assigned", "own_half", "dead_tiles",
]


def map_planes(ctx: dict) -> np.ndarray:
    """Kartenebenen fuer einen Step (kanonischer Raum, Werte etwa in [-1, 1])."""
    b = ctx["belief"]
    W, H = ctx["W"], ctx["H"]
    p = np.zeros((N_PLANES, W, H), dtype=np.float32)
    p[0] = b.point_tiles
    p[1] = b.candidate
    for x, y in b.relic_positions:
        p[2, x, y] = 1.0
    p[3] = b.explored
    p[4] = b.explored_ever
    p[5] = b.tile_type == TILE_ASTEROID
    p[6] = b.tile_type == 1
    p[7] = np.clip(b.energy_map / 20.0, -1.0, 1.0)
    for uid in ctx["ally_ids"]:
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        if 0 <= x < W and 0 <= y < H:
            p[8, x, y] += 0.25
            p[9, x, y] += max(float(ctx["ally_ene"][uid]), 0.0) / 400.0
    ec = ctx["enemy_coords"]
    for (x, y), e in zip(ec, ctx["enemy_energies"]):
        p[10, x, y] += 0.25
        p[11, x, y] += max(float(e), 0.0) / 400.0
    p[12] = b.last_seen == b.match_step
    for tx, ty in ctx["assigned"].values():
        p[13, tx, ty] = 1.0
    xs, ys = np.meshgrid(np.arange(W), np.arange(H), indexing="ij")
    p[14] = xs + ys < W - 1
    p[15] = b.dead_tiles
    np.clip(p[8:12], 0.0, 1.0, out=p[8:12])
    return p


class ResBlock(nn.Module):
    def __init__(self, ch: int):
        super().__init__()
        self.c1 = nn.Conv2d(ch, ch, 3, padding=1)
        self.c2 = nn.Conv2d(ch, ch, 3, padding=1)

    def forward(self, x):
        return torch.relu(x + self.c2(torch.relu(self.c1(x))))


class PolicyNet(nn.Module):
    def __init__(self, feat_dim: int, n_actions: int = 6, in_ch: int = N_PLANES,
                 ch: int = 32, blocks: int = 3, hidden: int = 256, detach_value: bool = False):
        super().__init__()
        self.arch = dict(feat_dim=feat_dim, n_actions=n_actions, in_ch=in_ch, ch=ch,
                         blocks=blocks, hidden=hidden, detach_value=detach_value)
        # detach_value: eigener Critic-Kopf auf angehaltenen Merkmalen, damit das
        # Critic-Training die (per Nachahmung gelernte) Policy nicht verschiebt
        self.detach_value = detach_value
        if detach_value:
            self.vhead = nn.Sequential(nn.Linear(hidden, 256), nn.ReLU(), nn.Linear(256, 1))
        self.stem = nn.Sequential(nn.Conv2d(in_ch, ch, 3, padding=1), nn.ReLU())
        self.blocks = nn.Sequential(*[ResBlock(ch) for _ in range(blocks)])
        self.unit = nn.Sequential(nn.Linear(feat_dim, 128), nn.ReLU())
        self.body = nn.Sequential(nn.Linear(2 * ch + 128, hidden), nn.ReLU(),
                                  nn.Linear(hidden, hidden), nn.ReLU())
        self.pi = nn.Linear(hidden, n_actions)
        self.v = nn.Linear(hidden, 1)

    def forward(self, planes: torch.Tensor, step_idx: torch.Tensor, pos: torch.Tensor,
                feats: torch.Tensor):
        """planes [B,C,W,H]; je Unit: step_idx [N] (Index in B), pos [N,2], feats [N,F]."""
        fm = self.blocks(self.stem(planes))
        g = fm.mean(dim=(2, 3))
        local = fm[step_idx, :, pos[:, 0], pos[:, 1]]
        h = torch.cat([local, g[step_idx], self.unit(feats)], dim=1)
        h = self.body(h)
        v = self.vhead(h.detach()) if self.detach_value else self.v(h)
        return self.pi(h), v.squeeze(-1)
