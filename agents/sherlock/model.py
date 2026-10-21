"""Netzarchitekturen.

`QNet` entspricht der Vorlesungsfolie 47 (MLP -> Q-Werte pro Aktion), erweitert um
eine optionale Dueling-Zerlegung Q(s,a) = V(s) + (A(s,a) - mean_a A(s,a)).
Die Zerlegung hilft hier, weil die meisten Steps "Lagebewertung" sind (V) und die
Aktionswahl oft kaum einen Unterschied macht (A).
"""
from __future__ import annotations

from numbers import Integral

import torch
import torch.nn as nn

# 0 stay, 1 up, 2 right, 3 down, 4 left, 5 sap
N_ACTIONS = 6


def checkpoint_ensemble_dims(checkpoint: dict, feature_dim: int) -> list[int]:
    """Validate input widths before loading or combining a DQN checkpoint.

    Missing/None/empty dimensions are the legacy homogeneous format. Explicit
    dimensions must describe every extra net; never let zip discard a member.
    """
    if isinstance(feature_dim, bool) or not isinstance(feature_dim, Integral) or feature_dim <= 0:
        raise ValueError("feature_dim muss eine positive ganze Zahl sein")
    ensemble = checkpoint.get("ensemble", [])
    dims = checkpoint.get("ensemble_dims")
    if dims is not None and not isinstance(dims, (list, tuple)):
        raise ValueError("ensemble_dims muss eine Liste von Eingabegroessen sein")
    if dims is None or len(dims) == 0:
        dims = [feature_dim] * len(ensemble)
    if len(dims) != len(ensemble):
        raise ValueError("ensemble_dims muss genau einen Eintrag pro Ensemble-Netz enthalten")
    for index, dim in enumerate(dims):
        if isinstance(dim, bool) or not isinstance(dim, Integral) or not 0 < dim <= feature_dim:
            raise ValueError(f"ensemble_dims[{index}] muss ganzzahlig und zwischen 1 "
                             f"und feature_dim ({feature_dim}) sein")

    states = [("q", checkpoint["q"], feature_dim)]
    states.extend((f"ensemble[{index}]", state, dim)
                  for index, (state, dim) in enumerate(zip(ensemble, dims)))
    for name, state, dim in states:
        weight = state.get("body.0.weight") if isinstance(state, dict) else None
        if not isinstance(weight, torch.Tensor) or weight.ndim != 2 or weight.shape[1] != dim:
            raise ValueError(f"{name}: Eingabedimension von body.0.weight passt nicht zu {dim}")
    return [int(dim) for dim in dims]


class QNet(nn.Module):
    def __init__(self, obs_dim: int, n_actions: int = N_ACTIONS,
                 hidden: int = 256, dueling: bool = True):
        super().__init__()
        self.feat_dim = obs_dim  # Eingabegroesse (gemischte Ensembles, main.py)
        self.dueling = dueling
        self.body = nn.Sequential(
            nn.Linear(obs_dim, hidden), nn.ReLU(),
            nn.Linear(hidden, hidden), nn.ReLU(),
        )
        if dueling:
            self.value = nn.Sequential(nn.Linear(hidden, 128), nn.ReLU(), nn.Linear(128, 1))
            self.adv = nn.Sequential(nn.Linear(hidden, 128), nn.ReLU(), nn.Linear(128, n_actions))
        else:
            self.head = nn.Linear(hidden, n_actions)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.body(x)
        if not self.dueling:
            return self.head(h)
        v = self.value(h)
        a = self.adv(h)
        return v + a - a.mean(dim=-1, keepdim=True)
