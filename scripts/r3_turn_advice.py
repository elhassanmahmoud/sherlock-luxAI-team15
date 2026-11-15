"""Use the original R3 adviser at medium confidence for changes between two moving directions."""
from hashlib import sha256
from pathlib import Path

import numpy as np
import torch

from agents.sherlock import geometry as geo
from agents.sherlock.cnn_model import map_planes
from agents.sherlock.imitation_agent import canonical_action, sap_legal
from scripts.combat_teacher_counterfactual import substitute
from scripts.selective_advice_agent import SelectiveAdviceAgent


def extra(score, choice, base):
    """Additional eligibility for equally oriented, canonical action codes."""
    return ((score >= 0.50) & (score < 0.70)
            & (choice >= 1) & (choice <= 4) & (base >= 1) & (base <= 4) & (choice != base))


class TurnAdviceAgent(SelectiveAdviceAgent):
    def __init__(self, *args, advice_path, mode="movement", **kwargs):
        if mode != "movement" or sha256(Path(advice_path).read_bytes()).hexdigest() != (
                "99b07775582e68efef8b63f545980e969cb0ed3c7d65052b48179508b87dd7b9"):
            raise ValueError("Expected the registered R3 movement checkpoint")
        super().__init__(*args, advice_path=advice_path, mode=mode, **kwargs)
        if len(self.members) != 1:
            raise ValueError("Expected one original R3 adviser")

    def _advise(self, step, obs, base):
        if self.training or int(obs["match_steps"]) == 0:
            return base
        ctx, cached_ids, feats, mask_map, _ = self._decide(obs)
        ids = [u for u in cached_ids if ctx["ally_ene"][u] >= 0]
        if not ids:
            return base

        planes = torch.from_numpy(map_planes(ctx)[None])
        step_idx = torch.zeros(len(ids), dtype=torch.long)
        pos = torch.as_tensor(np.asarray(ctx["ally_pos"])[ids], dtype=torch.long)
        features = torch.from_numpy(np.stack([feats[u] for u in ids]))
        masks = sap_legal(np.stack([mask_map[u] for u in ids]), np.asarray(ctx["ally_ene"])[ids], ctx["sap_cost"])
        mirrored = self.belief.mirrored
        base_canonical = torch.tensor([canonical_action(base[u], mirrored)[0] for u in ids])
        advice = base.copy()
        with torch.inference_mode():
            logits, _, _ = self.members[0].forward_all(planes, step_idx, pos, features)
            score, choice = logits.masked_fill(~torch.from_numpy(masks), -torch.inf).softmax(1).max(1)
            additional = extra(score, choice, base_canonical)
            moves = torch.where(((score >= 0.70) | additional) & (choice != geo.SAP))[0]
            for row in moves.tolist():
                direction = int(choice[row])
                advice[ids[row]] = [geo.mirror_dir(direction) if mirrored else direction, 0, 0]

        played = substitute(self, obs, base, advice, self.mode, self.selective_counts)
        for row in torch.where(additional)[0].tolist():
            uid = ids[row]
            if played[uid, 0] != base[uid, 0]:
                self.selective_counts["turn_extra_played"] += 1
        return played
