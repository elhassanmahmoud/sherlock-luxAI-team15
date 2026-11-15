"""Historical FT18 vote for normal movement from match two, before V14's rules."""
from __future__ import annotations

import numpy as np
import torch

from agents.sherlock import geometry as geo
from agents.sherlock.main import Agent_x


class FT18MovementAgent(Agent_x):
    def _reset_episode_state(self):
        super()._reset_episode_state()
        self._reset_study()

    def _reset_study(self):
        self.study_stats = [
            dict(match=i+1, proposal_pairs=np.zeros((6, 6), dtype=np.int64),
                 before_rules_changed=0, final_matches_ft18=0, final_matches_v14_vote=0,
                 final_other_move=0, final_sap=0)
            for i in range(3)
        ]
        self._ft_values = None
        self._changed = {}

    def _network_values(self, features):
        if self.training or self.cnn_policy is not None or len(self.extra_q) != 35:
            raise ValueError("FT18 movement requires the unmodified 36-member V14 eval policy")
        if self.belief.match_idx == 0:
            return super()._network_values(features)
        # Same order, feature slices, stack layout and reduction as Agent_x._network_values.
        values = torch.stack([self.q(features)] + [
            member(features[:, :member.feat_dim]) for member in self.extra_q])
        self._ft_values = values[18:].mean(dim=0).cpu().numpy()
        return values.mean(dim=0)

    def _policy_greedy(self, ctx, ids, masks, greedy):
        if ctx["match_idx"] == 0:
            return super()._policy_greedy(ctx, ids, masks, greedy)
        ft = np.where(masks, self._ft_values, -np.inf).argmax(axis=1)
        rows = np.arange(len(ids))
        if not (masks[rows, greedy].all() and masks[rows, ft].all()):
            raise ValueError("No legal proposal for a V14 decision row")
        stats = self.study_stats[ctx["match_idx"]]
        np.add.at(stats["proposal_pairs"], (greedy, ft), 1)
        changed = (greedy < geo.SAP) & (ft < geo.SAP) & (greedy != ft)
        self._changed = {ids[i]: (int(greedy[i]), int(ft[i])) for i in np.flatnonzero(changed)}
        stats["before_rules_changed"] += len(self._changed)
        return super()._policy_greedy(ctx, ids, masks, np.where(changed, ft, greedy))

    def _act(self, step, obs):
        self._changed = {}
        self._ft_values = None
        actions = super()._act(step, obs)
        self._count_final(actions)
        return actions

    def _count_final(self, actions):
        # Final command for each changed proposal. This is descriptive, not a second rules simulation.
        stats = self.study_stats[self.belief.match_idx]
        for uid, (old, new) in self._changed.items():
            final = int(actions[uid, 0])
            if final == geo.SAP:
                key = "final_sap"
            else:
                if self.belief.mirrored:
                    final = geo.mirror_dir(final)
                key = ("final_matches_ft18" if final == new else
                       "final_matches_v14_vote" if final == old else "final_other_move")
            stats[key] += 1

    def movement_statistics(self):
        return [dict(row, proposal_pairs=row["proposal_pairs"].tolist()) for row in self.study_stats]
