"""Train the pointwise sensor and its separate spatial adjustment from original remaining powers."""
import argparse
import json
from pathlib import Path

import numpy as np
import torch
from torch.nn import functional as F

from experiments.analysis.relictsuche_20261123.flottenblick.vorhersage import coverage, load as fleet
from experiments.analysis.relictsuche_20261123.nebelstruktur.modell import HERE, Visibility, inputs
from experiments.analysis.relictsuche_20261123.zeitlicher_flottenblick.lernen import samples
from experiments.analysis.relictsuche_20261123.vergleich.spielen import sha
from scripts.experiment import limit_threads


def read(folder):
    files = sorted((folder / "train").glob("*.npz"))
    assert len(files) == 480
    groups = [[] for _ in range(5)]
    seen = 0
    original = fleet()
    for file in files:
        count = 0
        for q, _, rest, x, t, paths, last, weight in samples(file, original):
            central, terrain, old = inputs(x, q, last, t)
            region = coverage(paths) & old
            for group, value in zip(groups, (central.astype(np.float16), terrain.astype(np.float16),
                                             rest.astype(np.int8), region, np.float32(weight)), strict=True):
                group.append(value)
            count += 1
        seen += count > 0
    return [torch.from_numpy(np.stack(part)) for part in groups], seen


def optimize(net, tensors, stage):
    point, terrain, rest, region, weight = tensors
    center = stage == "central"
    for parameter in net.point.parameters():
        parameter.requires_grad_(center)
    for layer in (net.first, net.second, net.horizon):
        for parameter in layer.parameters():
            parameter.requires_grad_(not center)
    opt = torch.optim.AdamW((p for p in net.parameters() if p.requires_grad), lr=.003, weight_decay=.0005)
    losses = []
    for epoch in range(10):
        total = 0.
        for idx in torch.randperm(len(point)).split(32):
            y = (rest[idx] == 0).float()
            w = (rest[idx] <= 0) * (1. + 3.*region[idx, None]) * weight[idx, None, None, None]
            basic = net.point(point[idx].float())
            pred = basic if center else basic + net.adjustment(terrain[idx].float())
            loss = (w * F.binary_cross_entropy_with_logits(pred, y, reduction="none")).sum() / w.sum().clamp_min(1.)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total += float(loss.detach()) * len(idx)
        losses.append(total / len(point))
    return losses


def main(folder):
    limit_threads()
    torch.set_num_threads(1)
    torch.manual_seed(16496001)
    data, nonempty = read(folder)
    print("Lerndaten", len(data[0]), nonempty, flush=True)
    net = Visibility()
    basic = optimize(net, data, "central")
    print("Punktweises Modell", basic[-1], flush=True)
    state = {k: v.clone() for k, v in net.point.state_dict().items()}
    extra = optimize(net, data, "spatial")
    assert all(torch.equal(v, net.point.state_dict()[k]) for k, v in state.items())
    assert (net.adjustment(torch.zeros(1, 6, 24, 24)) == 0).all()
    np.savez_compressed(HERE / "gewichte.npz", **{k: v.numpy() for k, v in net.state_dict().items()})
    sources = [HERE / "PLAN.md", HERE / "lernen.py", HERE / "modell.py",
               HERE.parent / "flottenblick/flottengewichte.npz", HERE.parent / "zielschaetzer/ort.json"]
    out = {"cards": 480, "with_cases": nonempty, "samples": len(data[0]), "center_loss": basic,
           "spatial_loss": extra, "weights": sha(HERE / "gewichte.npz"),
           "source": {str(p.relative_to(HERE.parent)): sha(p) for p in sources}}
    (HERE / "fit.json").write_text(json.dumps(out, indent=2) + "\n")
    print("Räumliches Modell", extra[-1], out["weights"], flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder", type=Path)
    main(p.parse_args().folder)
