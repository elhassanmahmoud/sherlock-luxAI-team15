"""Netz fuer den Umbau (15.11.2026): PolicyNet plus gelernter Schussziel-Kopf.

Der Lehrer (Kaggle-Platz-3-Agent) schiesst in rund 41 % der Faelle auf Felder ohne fuer Sherlock sichtbaren
Gegner (Nebel, vorhergesagte Positionen) und oft auf 5-7 Felder Entfernung. Sherlocks Zielheuristik kennt nur
sichtbare Gegner. Darum sagt ein zweiter Kopf eine Zielkarte [W, H] voraus; gewaehlt wird das beste Feld in
Sap-Reichweite der schiessenden Unit.

    Karte --stem--> ResBlocks --> Merkmalskarte --(Unit-Position, Mittel, Unit-MLP)--> 6 Aktions-Logits, Wert
                                       |--Conv3x3--Conv1x1--> Zielkarte (eine Bewertung je Feld)
"""
from __future__ import annotations

import torch
import torch.nn as nn

from .cnn_model import PolicyNet


class ImitationNet(PolicyNet):
    def __init__(self, feat_dim: int, n_actions: int = 6, in_ch: int = 16, ch: int = 64, blocks: int = 6,
                 hidden: int = 256, detach_value: bool = True, sap_head: bool = True):
        super().__init__(feat_dim, n_actions=n_actions, in_ch=in_ch, ch=ch, blocks=blocks, hidden=hidden,
                         detach_value=detach_value)
        self.arch["sap_head"] = bool(sap_head)
        self.sap = nn.Sequential(nn.Conv2d(ch, ch, 3, padding=1), nn.ReLU(), nn.Conv2d(ch, 1, 1))

    def forward_all(self, planes: torch.Tensor, step_idx: torch.Tensor, pos: torch.Tensor, feats: torch.Tensor):
        """(Aktions-Logits [N,6], Wert [N], Zielkarte [B,W,H])."""
        fm = self.blocks(self.stem(planes))
        g = fm.mean(dim=(2, 3))
        local = fm[step_idx, :, pos[:, 0], pos[:, 1]]
        h = self.body(torch.cat([local, g[step_idx], self.unit(feats)], dim=1))
        v = self.vhead(h.detach()) if self.detach_value else self.v(h)
        return self.pi(h), v.squeeze(-1), self.sap(fm).squeeze(1)

    def forward(self, planes, step_idx, pos, feats):
        logits, v, _ = self.forward_all(planes, step_idx, pos, feats)
        return logits, v


def window_mask(pos: torch.Tensor, rng: torch.Tensor, W: int, H: int) -> torch.Tensor:
    """[N, W, H]: Felder in Sap-Reichweite (Chebyshev <= rng) der jeweiligen Unit."""
    xs = torch.arange(W, device=pos.device).view(1, W, 1)
    ys = torch.arange(H, device=pos.device).view(1, 1, H)
    dx = (xs - pos[:, 0].view(-1, 1, 1)).abs()
    dy = (ys - pos[:, 1].view(-1, 1, 1)).abs()
    return torch.maximum(dx, dy) <= rng.view(-1, 1, 1)


def masked_sap_logits(smap: torch.Tensor, step_idx: torch.Tensor, pos: torch.Tensor, rng: torch.Tensor):
    """Eine Zeile je Schuetze. Innerhalb der Karte und Reichweite ist auch sein eigenes Feld ein Ziel."""
    width, height = smap.shape[-2:]
    legal = window_mask(pos, rng, width, height)
    return smap[step_idx].masked_fill(~legal, -torch.inf).flatten(1)
