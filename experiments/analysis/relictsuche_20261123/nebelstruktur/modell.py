"""A spatial visibility adjustment using only the observed terrain around the target cell."""
from functools import lru_cache
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from experiments.analysis.relictsuche_20261123.flottenblick.flotte import PAIR, XY
from experiments.analysis.relictsuche_20261123.flottenblick.vorhersage import OFFSETS, arrays
from experiments.analysis.relictsuche_20261123.zielschaetzer.kandidat import COORD, parameters

HERE = Path(__file__).resolve().parent
MIRROR = 24 * (23 - XY[:, 1]) + 23 - XY[:, 0]
HEAD = (OFFSETS == 0).all(1)
T = np.arange(8)[None, :, None]


def inputs(x, q, last, turn):
    seen = last >= 0
    age = np.where(seen, turn - last.astype(np.int16), 100)
    old = age >= 4
    fog, walls = x[18] > 0, x[17] > 0
    clear = seen & ~fog & ~walls
    recent = np.maximum(0., 1. - age / 32.)
    point = np.stack((q, seen, np.minimum(age, 40) / 40, fog, walls, x[19], x[21],
                      x[14], x[15], x[16], x[23], x[24], x[25]))
    local = np.stack((seen, fog, clear, walls & seen, fog * recent, clear * recent))
    return point.astype(np.float32), local.astype(np.float32), old


class Visibility(nn.Module):
    def __init__(self):
        super().__init__()
        self.point = nn.Sequential(nn.Conv2d(13, 16, 1), nn.ReLU(), nn.Conv2d(16, 8, 1))
        self.first = nn.Conv2d(6, 10, 3, padding=1, bias=False)
        self.second = nn.Conv2d(10, 10, 3, dilation=2, padding=2, bias=False)
        self.horizon = nn.Conv2d(10, 8, 1, bias=False)
        mask = torch.ones(1, 1, 3, 3)
        mask[0, 0, 1, 1] = 0
        self.register_buffer("outside", mask)
        nn.init.zeros_(self.horizon.weight)

    def adjustment(self, terrain):
        first = F.conv2d(terrain, self.first.weight * self.outside, padding=1)
        return self.horizon(F.relu(self.second(F.relu(first))))

    def forward(self, point, terrain):
        central = self.point(point)
        return central, central + self.adjustment(terrain)


@lru_cache(maxsize=1)
def load():
    net = Visibility().eval()
    with np.load(HERE / "gewichte.npz") as archive:
        net.load_state_dict({k: torch.from_numpy(archive[k]) for k in archive.files})
    return net


def predictions(net, point, terrain):
    with torch.no_grad():
        out = net(torch.from_numpy(point[None]), torch.from_numpy(terrain[None]))
        return [torch.sigmoid(head[0]).numpy().reshape(8, 576) for head in out]


def neighbor(q, x, last, turn, net=None):
    point, terrain, old = inputs(x, q, last, turn)
    central, spatial = predictions(net or load(), point, terrain)
    old_weight = np.where(x[18].ravel() > 0, .25, 1.)
    return np.clip(old_weight[None] + (spatial-central)*old.ravel()[None], 0., 1.)


def route_scores(weights, q, paths, last, fog, energy, origin):
    routes = np.vstack((paths, np.full((1, 8), origin, dtype=np.int16)))
    cells, inside = arrays(routes)
    edges = np.where(HEAD[None, None, :], 1., weights[T, cells])
    edges *= inside * (.97**np.arange(1, 9))[None, :, None]
    pooled = np.zeros((len(routes), 576), np.float32)
    rows = np.broadcast_to(np.arange(len(routes))[:, None, None], cells.shape)
    np.maximum.at(pooled, (rows.ravel(), PAIR[cells].ravel()), edges.ravel())
    q = q.ravel()
    union = np.where(np.arange(576) == MIRROR, q, 1 - (1-q)*(1-q[MIRROR]))
    recent = np.maximum(last.ravel(), last.ravel()[MIRROR])
    fresh = np.where(recent < 0, 1., .55*np.maximum(0., 1-recent/50))
    prior = np.ones(576)
    prob, _ = parameters()
    prior[COORD[:, 0]*24 + COORD[:, 1]] = prob/prob.mean()
    cost = .08 * np.sum(fog.ravel()[routes], axis=1) + .025*np.maximum(0., -energy.ravel()[routes]).mean(1)
    return pooled @ (fresh * (1-union) * prior) - cost
