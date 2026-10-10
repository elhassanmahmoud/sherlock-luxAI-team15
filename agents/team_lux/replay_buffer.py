"""Replay Buffer (vorallokierter Ringpuffer).

Transitions werden PRO EINHEIT gespeichert: ein Env-Step liefert bis zu 16
Transitions. Der Puffer bricht die zeitliche Korrelation der Samples auf
(Voraussetzung fuer stabiles DQN-Training).
"""
from __future__ import annotations

import numpy as np


class ReplayBuffer:
    def __init__(self, capacity: int, obs_dim: int):
        self.capacity = int(capacity)
        self.obs_dim = int(obs_dim)
        self.s = np.zeros((self.capacity, obs_dim), dtype=np.float32)
        self.ns = np.zeros((self.capacity, obs_dim), dtype=np.float32)
        self.a = np.zeros(self.capacity, dtype=np.int64)
        self.r = np.zeros(self.capacity, dtype=np.float32)
        self.done = np.zeros(self.capacity, dtype=np.float32)
        self.mask = np.ones((self.capacity, 1), dtype=bool)  # wird in push ersetzt
        self._mask_dim = 1
        self.pos = 0
        self.size = 0

    def _ensure_mask(self, n_actions: int) -> None:
        if self._mask_dim != n_actions:
            self.mask = np.ones((self.capacity, n_actions), dtype=bool)
            self._mask_dim = n_actions

    def push(self, s, a, r, ns, done, next_mask) -> None:
        self._ensure_mask(len(next_mask))
        i = self.pos
        self.s[i] = s
        self.a[i] = a
        self.r[i] = r
        self.ns[i] = ns
        self.done[i] = float(done)
        self.mask[i] = next_mask
        self.pos = (i + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def sample(self, batch_size: int, rng: np.random.Generator | None = None):
        rng = rng or np.random.default_rng()
        idx = rng.integers(0, self.size, size=batch_size)
        return (self.s[idx], self.a[idx], self.r[idx], self.ns[idx],
                self.done[idx], self.mask[idx])

    def __len__(self) -> int:
        return self.size
