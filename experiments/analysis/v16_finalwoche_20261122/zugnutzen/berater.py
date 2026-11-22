"""Build alternative commands and public features without passing in any referee information."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import sys

import numpy as np
import torch
from scipy.special import logsumexp

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from agents.sherlock import geometry as g
from agents.sherlock.features import FEATURE_NAMES

PACKAGE = ROOT / "experiments/releases/20261117_sherlock_v16/agent.zip"
V16 = "0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"
NAMES = [*FEATURE_NAMES, *(f"original_{i}" for i in range(5)), *(f"alternative_{i}" for i in range(5)),
         "score_gap", "planned_original", "planned_alternative", "allies_original", "allies_alternative",
         "point_original", "point_alternative", "enemy_energy_original", "enemy_energy_alternative"]
POINT = [FEATURE_NAMES.index(d + "_point") for d in "curdl"]
IDENTITY = np.eye(5, dtype=np.float32)


class ValueNet(torch.nn.Sequential):
    def __init__(self):
        super().__init__(torch.nn.Linear(len(NAMES), 32), torch.nn.ReLU(), torch.nn.Linear(32, 1))


class Policy:
    def __init__(self, base, net=None):
        self.base = base
        self.net = net
        self.scores = [None, None]
        self.changed = 0
        self.last = []
        p = base._imitation
        if len(p.extra_nets) != 1:
            raise ValueError("Unexpected ensemble")
        for i, network in enumerate((p.net, p.extra_nets[0])):
            def capture(*args, forward=network.forward_all, slot=i):
                prediction = forward(*args)
                self.scores[slot] = prediction[0].detach().numpy()
                return prediction
            network.forward_all = capture

    def __getattr__(self, name):
        return getattr(self.base, name)

    def options(self, actions):
        p = self.base._imitation
        fz = p.last_fz
        if fz is None:
            return []
        ctx, ids, f, masks, _, planes, pos = fz
        if int(ctx["match_step"]) < 81:
            return []
        live = np.asarray([ctx["ally_ene"][u] >= 0 for u in ids])
        masks = masks.copy()
        masks[:, 5] = [ctx["ally_ene"][u] >= ctx["sap_cost"] for u in ids]
        logp = np.zeros(masks.shape, dtype=np.float32)
        for heads in self.scores:
            valid = np.where(masks, heads, -np.inf)
            logp += valid - logsumexp(valid, axis=1, keepdims=True)
        holders = set(p._point_holder_rows(ctx, ids, pos))
        logp[[i for i in range(len(ids)) if i not in holders], 0] -= float(p.cfg.imit_stay_bias)
        original = actions[ids, 0]
        move = np.where(original <= 4, original, 0)
        if p.belief.mirrored:
            move = g.MIRROR_DIR[move]
        destinations = pos + np.stack((g.DIR_DX[move], g.DIR_DY[move]), axis=1)
        planned = Counter(map(tuple, destinations[live]))
        occupied = Counter(map(tuple, pos[live]))
        live &= (original <= 4) & (f[:, POINT].max(axis=1) > 0) & masks[np.arange(len(ids)), move]
        candidates = []
        for k in np.flatnonzero(live):
            a = int(move[k])
            values = logp[k, :5].copy()
            values[a] = -np.inf
            alt = int(values.argmax())
            if not np.isfinite(values[alt]):
                continue
            gap = float(logp[k, a] - values[alt])
            if abs(gap) > 3:
                continue
            bxy = tuple(destinations[k].tolist())
            cxy = (int(pos[k,0]) + int(g.DIR_DX[alt]), int(pos[k,1]) + int(g.DIR_DY[alt]))
            if not all(0 <= z < 24 for z in (*bxy, *cxy)):
                raise ValueError("Movement outside known legal bounds")
            attr = [gap / 3, min(planned[bxy],4)/4, min(planned[cxy],4)/4,
                    min(occupied[bxy],4)/4, min(occupied[cxy],4)/4,
                    float(planes[0][bxy]), float(planes[0][cxy]),
                    float(planes[11][bxy]), float(planes[11][cxy])]
            x = np.concatenate((f[k], IDENTITY[a], IDENTITY[alt], np.asarray(attr, dtype=np.float32)))
            if x.shape != (len(NAMES),) or not np.isfinite(x).all():
                raise ValueError("Invalid public state")
            real = g.mirror_dir(alt) if p.belief.mirrored else alt
            candidates.append((abs(gap), int(ids[k]), real, x))
        return sorted(candidates, key=lambda item: (item[0], item[1]))[:2]

    def act(self, step, obs):
        action = self.base.act(step, obs)
        self.last = self.options(action) if int(obs["match_steps"]) >= (91 if self.net is not None else 81) else []
        if self.net is None or not self.last:
            return action
        with torch.inference_mode():
            predicted = self.net(torch.from_numpy(np.stack([r[3] for r in self.last]))).flatten().numpy()
        i = max(range(len(predicted)), key=lambda j: (float(predicted[j]), -self.last[j][1]))
        if predicted[i] < .25:
            return action
        out = action.copy()
        _, uid, alt, _ = self.last[i]
        out[uid] = [alt, 0, 0]
        self.changed += 1
        return out
