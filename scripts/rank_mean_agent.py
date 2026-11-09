"""Instance-local, eval-only legal-rank aggregation of the 36 original nets."""
from collections import Counter
import weakref

import numpy as np
import torch
from torch import nn

from agents.sherlock.main import Agent_x


def legal_midrank_mean(member_q, masks):
    """Mean legal midranks for [members, units, 6], with illegal output -1.

    Sum integer twice-rank numerators before division: equal mathematical rank
    means remain exact ties regardless of member order or floating-point sums.
    """
    if (not isinstance(member_q, torch.Tensor) or not isinstance(masks, torch.Tensor)
            or member_q.ndim != 3 or member_q.shape[-1] != 6
            or member_q.shape[0] == 0 or member_q.shape[1] == 0
            or not member_q.is_floating_point() or masks.dtype != torch.bool
            or masks.shape != member_q.shape[1:] or masks.device != member_q.device):
        raise ValueError("Expected floating [M,N,6] values and boolean [N,6] masks")
    legal_count = masks.sum(-1)
    if not torch.isfinite(member_q).all() or (legal_count == 0).any():
        raise ValueError("Nonfinite Q value or no legal action")
    own, other = member_q.unsqueeze(-1), member_q.unsqueeze(-2)
    legal_other = masks[None, :, None, :]
    lower = ((other < own) & legal_other).sum(-1)
    equal = ((other == own) & legal_other).sum(-1)
    numerator = (2*lower+equal-1).sum(0)
    denominator = 2*member_q.shape[0]*(legal_count-1).clamp_min(1)
    result = numerator.to(member_q.dtype)/denominator[:, None]
    result = torch.where(legal_count[:, None] == 1, .5, result)
    return result.masked_fill(~masks, -1)


class _RankMeanModule(nn.Module):
    def __init__(self, owner, members):
        super().__init__()
        self._owner = weakref.ref(owner)
        self.members = nn.ModuleList(members)  # References, never weight copies.
        self.feat_dim = owner.feat_dim
        self.eval()

    def train(self, mode=True):
        if mode:
            raise RuntimeError("Rank-mean module is eval only")
        return super().train(False)

    def forward(self, inputs):
        return self._owner()._aggregate(inputs)


class RankMeanAgent(Agent_x):
    def __init__(self, player, agent_path=None, name="Rank-mean prototype", cfg=None,
                 train=False, seed=None, *, rank_enabled=False):
        if train:
            raise ValueError("Rank-mean prototype is eval only")
        self.rank_enabled = bool(rank_enabled)
        super().__init__(player, agent_path, name, cfg, False, seed)
        if self.cfg.frozen:
            raise ValueError("Rank-mean requires frozen=False so technical errors propagate")
        members = (self.q, *self.extra_q)
        if (len(members) != 36 or len({id(m) for m in members}) != 36
                or self.n_actions != 6 or members[0].feat_dim != self.feat_dim
                or any(not isinstance(m, nn.Module) or not isinstance(m.feat_dim, int)
                       or not 0 < m.feat_dim <= self.feat_dim for m in members)
                or self.cnn_policy is not None):
            raise ValueError("Expected 36 distinct original six-action members with valid feature widths")
        self._aggregation_members = members
        if self.rank_enabled:
            self.q = _RankMeanModule(self, members)
            self.extra_q = []
        self.autosave_on_terminate = False
        self.learn_enabled = False

    @property
    def aggregation_members(self):
        return self._aggregation_members

    def _reset_episode_state(self):
        super()._reset_episode_state()
        self.aggregation_stats = Counter(calls=0, proposal_changes=0, proposal_changed_steps=0)
        self.aggregation_last = None
        self._rank_active_frame = None
        self._rank_batch_used = False

    def _act(self, step, obs):
        if self.training:
            raise RuntimeError("Rank-mean prototype is eval only")
        self.aggregation_last = None
        self._rank_batch_used = False
        self._rank_active_frame = (int(np.asarray(obs["steps"])), int(np.asarray(obs["match_steps"])))
        try:
            return super()._act(step, obs)
        finally:
            self._rank_active_frame = None

    def _aggregate(self, inputs):
        cache, active = self._cache, self._rank_active_frame
        if self.training or self._rank_batch_used:
            raise RuntimeError("Expected one eval forward per active batch")
        if (active is None or active[1] == 0 or cache is None or cache[0] != active[0]
                or self._prev_ctx is not cache[1]
                or (cache[1]["step"], cache[1]["match_step"]) != active):
            raise ValueError("Rank aggregation lacks the current decision cache")
        _, ctx, ids, feature_map, mask_map, _ = cache
        if (not ids or len(set(ids)) != len(ids)
                or list(ids) != list(map(int, ctx["ally_ids"]))):
            raise ValueError("Decision row IDs differ from current context")
        expected = torch.as_tensor(np.stack([feature_map[u] for u in ids]),
                                   dtype=inputs.dtype, device=inputs.device)
        if (inputs.shape != (len(ids), self.feat_dim) or not torch.equal(inputs, expected)):
            raise ValueError("Actual feature rows differ from the decision cache")
        masks = torch.as_tensor(np.stack([mask_map[u] for u in ids]),
                                dtype=torch.bool, device=inputs.device)
        self._rank_batch_used = True
        member_q = torch.stack([m(inputs[:, :m.feat_dim]) for m in self.aggregation_members])
        rank_mean = legal_midrank_mean(member_q, masks)
        raw_mean = member_q.mean(0)
        raw_greedy = raw_mean.masked_fill(~masks, -torch.inf).argmax(1)
        rank_greedy = rank_mean.argmax(1)
        changes = int((raw_greedy != rank_greedy).sum())
        self.aggregation_stats["calls"] += 1
        self.aggregation_stats["proposal_changes"] += changes
        self.aggregation_stats["proposal_changed_steps"] += int(changes > 0)
        self.aggregation_last = dict(step=active[0], ids=tuple(ids),
            **{name: value.detach().clone() for name, value in dict(
                masks=masks, member_q=member_q, raw_mean=raw_mean, rank_mean=rank_mean,
                raw_greedy=raw_greedy, rank_greedy=rank_greedy).items()})
        return rank_mean

    def set_to_train_mode(self):
        raise RuntimeError("Rank-mean prototype is eval only")

    def update(self, *args, **kwargs):
        raise RuntimeError("Rank-mean prototype cannot update")

    def save_agent(self, *args, **kwargs):
        raise RuntimeError("Rank-mean prototype cannot save checkpoints")

    def save_buffer(self, *args, **kwargs):
        raise RuntimeError("Rank-mean prototype cannot save replay")

    def load_agent(self, *args, **kwargs):
        if hasattr(self, "_aggregation_members"):
            raise RuntimeError("Rank-mean members are fixed after construction")
        return super().load_agent(*args, **kwargs)
