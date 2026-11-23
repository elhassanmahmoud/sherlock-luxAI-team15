"""Eight-turn public fleet forecast and scoring of exclusive scout information."""
from pathlib import Path

import numpy as np
import torch
from torch import nn

from experiments.analysis.relictsuche_20261123.flottenblick.flotte import CHANNELS, PAIR, XY

HERE = Path(__file__).resolve().parent
KINDS = ("now", "next", "straight", "joint")
OFFSETS = np.array([(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1)], dtype=np.int16)


def projection_keys(dist):
    near = np.minimum(dist[0], dist[1]).clip(0, 12)
    ray = dist[2].clip(0, 12)
    return (dist[0].clip(0, 12), near, ray, 13*near.astype(np.int16) + ray)


def probabilities(keys, table):
    return np.asarray(table, dtype=np.float32)[keys]


class Forecast(nn.Module):
    def __init__(self):
        super().__init__()
        self.spatial = nn.Sequential(
            nn.Conv2d(len(CHANNELS), 20, 3, padding=1), nn.ReLU(),
            nn.Conv2d(20, 20, 3, padding=2, dilation=2), nn.ReLU(),
            nn.Conv2d(20, 12, 3, padding=4, dilation=4), nn.ReLU(),
            nn.Conv2d(12, 1, 1),
        )
        nn.init.zeros_(self.spatial[-1].weight)
        nn.init.zeros_(self.spatial[-1].bias)

    def forward(self, board, anchor):
        logits = torch.logit(anchor.clamp(.002, .998))
        return logits + self.spatial(board).squeeze(1)


def arrays(paths):
    xy = XY[paths]
    cells = xy[:, :, None, :] + OFFSETS
    inside = ((cells >= 0) & (cells < 24)).all(-1)
    cells = cells.clip(0, 23)
    idx = cells[..., 0]*24 + cells[..., 1]
    return idx, inside


def coverage(paths):
    idx, inside = arrays(paths)
    mask = np.zeros(576, dtype=bool)
    mask[idx[inside]] = True
    return mask.reshape(24, 24)


def route_scores(q, paths, last, fog, energy):
    idx, inside = arrays(paths)
    # Visiting a known fog cell itself still gives vision. Neighbour vision into fog is uncertain.
    head = np.all(OFFSETS == 0, axis=-1)
    weight = np.where(fog.ravel()[idx] & ~head[None, None], .25, 1)
    weight = weight * inside * (.97 ** np.arange(1, paths.shape[1] + 1))[None, :, None]
    pair_mask = np.zeros((len(paths), 576), np.float32)
    row = np.broadcast_to(np.arange(len(paths))[:, None, None], idx.shape)
    np.maximum.at(pair_mask, (row.ravel(), PAIR[idx].ravel()), weight.ravel())
    physical = q.ravel()
    mirror = (23-XY[:, 1])*24 + (23-XY[:, 0])
    # Opposite sightings can report the same first relic. Keep fixed points single.
    either = np.where(np.arange(576) == mirror, physical, 1 - (1-physical)*(1-physical[mirror]))
    seen = np.maximum(last.ravel(), last.ravel()[mirror])
    new = np.where(seen < 0, 1., .55*np.maximum(0, 1-seen/50))
    gross = pair_mask @ (new * (1 - either))
    movement_cost = .08 * np.sum(fog.ravel()[paths], axis=1)
    movement_cost += .025 * np.maximum(0., -energy.ravel()[paths]).mean(axis=1)
    return gross - movement_cost


def choose(q, paths, last, fog, energy, origin):
    scores = route_scores(q, paths, last, fog, energy)
    wait = np.full((1, paths.shape[1]), origin, dtype=np.int16)
    reference = route_scores(q, wait, last, fog, energy)[0]
    best = int(np.argmax(scores))
    return best if scores[best] >= reference + 1.0 else None


def load():
    import json
    cfg = json.loads((HERE / "modell.json").read_text())
    if list(CHANNELS) != cfg["channels"]:
        raise ValueError("Wrong fleet forecast inputs")
    net = Forecast().eval()
    with np.load(HERE / "flottengewichte.npz", allow_pickle=False) as saved:
        net.load_state_dict({k: torch.from_numpy(saved[k]) for k in saved.files})
    return net, cfg


def predict(net, cfg, x, dist, baseline=False):
    values = projection_keys(dist)
    k = KINDS.index(cfg["reference"]) if baseline else KINDS.index("joint")
    q = probabilities(values[k], cfg["tables"][KINDS[k]])
    if baseline:
        return q
    with torch.no_grad():
        return torch.sigmoid(net(torch.from_numpy(x[None].astype(np.float16).astype(np.float32)), torch.from_numpy(q[None])))[0].numpy()
