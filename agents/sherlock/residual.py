"""Experimental additive correction of a frozen V14 ensemble (not mean37).

The stock Agent_x checkpoint format is intentionally unchanged. Residual
checkpoints require this explicit loader and the exact original base file.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import numpy as np
import torch
from torch import nn

from .main import Agent_x

SCHEMA = 'sherlock.residual-additive.v1'
V14_SHA = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ResidualPolicy(nn.Module):
    def __init__(self, bases):
        super().__init__()
        self.bases = nn.ModuleList(bases)
        self.residual = copy.deepcopy(bases[18])
        for module in (self.residual.value[-1], self.residual.adv[-1]):
            nn.init.zeros_(module.weight)
            nn.init.zeros_(module.bias)
        self.residual.requires_grad_(True)
        self.bases.requires_grad_(False).eval()

    def baseline(self, features):
        with torch.no_grad():
            return torch.stack([m(features[:, :m.feat_dim]) for m in self.bases]).mean(0)

    def values(self, features):
        return self.baseline(features) + self.residual(features)

    def checkpoint(self, base_sha):
        return dict(schema=SCHEMA, base_sha256=base_sha,
                    residual=copy.deepcopy(self.residual.state_dict()))


def validate_residual_checkpoint(cp, base_sha, model):
    if (not isinstance(cp, dict) or cp.get('schema') != SCHEMA
            or cp.get('base_sha256') != base_sha or not isinstance(cp.get('residual'), dict)):
        raise ValueError('Missing additive schema, residual weights, or matching base hash')
    expected = model.state_dict()
    if cp['residual'].keys() != expected.keys():
        raise ValueError('Residual tensor keys differ')
    for key, value in cp['residual'].items():
        if (not isinstance(value, torch.Tensor) or value.shape != expected[key].shape
                or value.dtype != expected[key].dtype or not torch.isfinite(value).all()):
            raise ValueError(f'Invalid residual tensor: {key}')


class ResidualActor(Agent_x):
    """Normal evaluation rules, with optional exploration before those rules."""
    def __init__(self, player, base_path, residual_path=None, *, exploration=0.0, seed=0):
        if file_sha(base_path) != V14_SHA:
            raise ValueError('Residual actor requires the pinned original V14 file')
        cfg = self._cfg_from_checkpoint(str(base_path))
        if cfg is None:
            raise ValueError('Missing V14 config')
        cfg.frozen = False  # experiments must surface errors
        super().__init__(player, str(base_path), cfg=cfg, train=False, seed=seed)
        if (len(self.extra_q) != 35 or self.feat_dim != 79 or self.n_actions != 6
                or self.cfg.hidden != 256 or not self.cfg.dueling
                or any(m.feat_dim != 79 for m in self.extra_q)):
            raise ValueError('Residual actor requires the original homogeneous 36-member V14')
        self.policy = ResidualPolicy([self.q] + self.extra_q)
        self.target_q.requires_grad_(False)
        self.opt = None  # only the external residual learner owns an optimizer
        self.buffer = None
        self.autosave_on_terminate = False
        self.learn_enabled = False
        if not 0 <= exploration <= 1:
            raise ValueError('Invalid exploration probability')
        self.exploration = float(exploration)
        self.last_network = None
        self.last_proposals = None
        self.residual_diagnostics = dict(unit_steps=0, raw_changes=0, explored=0,
                                         final_differs_from_proposal=0, returned_to_raw_base=0)
        if residual_path is not None:
            cp = torch.load(residual_path, map_location=self.device, weights_only=True)
            validate_residual_checkpoint(cp, V14_SHA, self.policy.residual)
            self.policy.residual.load_state_dict(cp['residual'], strict=True)

    def _network_values(self, features):
        base = self.policy.baseline(features)
        residual = self.policy.residual(features)
        self.last_network = (features.cpu().numpy().copy(), base.cpu().numpy().copy(),
                             residual.cpu().numpy().copy())
        return base + residual

    def _policy_greedy(self, ctx, ids, masks, greedy):
        base = self.last_network[1].copy()
        base[~masks] = -np.inf
        base_choice = base.argmax(1)
        proposed = greedy.copy()
        d = self.residual_diagnostics
        d['unit_steps'] += len(ids)
        d['raw_changes'] += int((base_choice != greedy).sum())
        if self.exploration:
            for i in range(len(ids)):
                if self.rng.random() < self.exploration:
                    proposed[i] = self.rng.choice(np.flatnonzero(masks[i]))
                    d['explored'] += 1
        self.last_proposals = (list(ids), base_choice, proposed.copy())
        return proposed

    def act(self, step, obs):
        self.last_network = self.last_proposals = None
        actions = super().act(step, obs)
        if self.last_proposals is not None:
            ids, baseline, proposals = self.last_proposals
            final = np.array([actions[u,0] for u in ids])
            if self.belief.mirrored:
                from .geometry import MIRROR_DIR
                moving = final < 5
                final[moving] = MIRROR_DIR[final[moving]]
            # Descriptive counts only: baseline is a raw proposal, not its
            # counterfactual final rule output. Exploration is included.
            self.residual_diagnostics['final_differs_from_proposal'] += int((final != proposals).sum())
            self.residual_diagnostics['returned_to_raw_base'] += int(
                ((proposals != baseline) & (final == baseline)).sum())
        return actions
