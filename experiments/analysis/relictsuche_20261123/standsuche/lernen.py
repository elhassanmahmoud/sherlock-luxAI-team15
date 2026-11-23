"""Fit the incremental value of a short departure using matched, legal game branches."""
import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn

from steuern import FEATURES, HERE, select, value_of

RNG_SEED = 231123


def read(directory, split, n):
    batch = sorted((json.loads(p.read_text()) for p in (directory/split).glob("*.json")), key=lambda r:r["index"])
    if [r["index"] for r in batch] != list(range(n)) or len({r["seed"] for r in batch}) != n:
        raise ValueError(f"Need complete map-indexed {split} batch")
    if len({json.dumps(r["files"], sort_keys=True) for r in batch}) != 1:
        raise ValueError("Different branch sources")
    for r in batch:
        if r["original"]["changes"] != 0 or (r["event"] and r["trials"].keys() != r["event"]["x"].keys()):
            raise ValueError("Incomplete controls")
        if any(not 1 <= t["changes"] <= 3 for t in r["trials"].values()):
            raise ValueError("Wrong number of actual moves")
    return batch


def arrays(rows):
    x, y, weights = [], [], []
    for r in rows:
        for key, t in r["trials"].items():
            x.append(r["event"]["x"][key])
            y.append(value_of(r["original"]["y"], t["y"]))
            weights.append(1/len(r["trials"]))
    if not x:
        raise ValueError("No usable directions")
    return np.array(x, dtype=float), np.array(y), np.array(weights)


def fit(rows, kind):
    if kind == "prior":
        return dict(kind=kind)
    x, y, w = arrays(rows)
    mean, scale = x.mean(0), np.maximum(x.std(0), .025)
    z = (x - mean)/scale
    common = dict(kind=kind, mean=mean.tolist(), scale=scale.tolist())
    if kind == "ridge":
        offset = np.average(y, weights=w)
        gram = z.T @ (z*w[:, None])
        penalty = len(rows) / 15
        beta = np.linalg.solve(gram + np.eye(z.shape[1])*penalty, z.T @ (w*(y-offset)))
        return dict(**common, w=beta.tolist(), b=float(offset))
    torch.manual_seed(RNG_SEED)
    torch.set_num_threads(1)
    net = nn.Sequential(nn.Linear(z.shape[1], 12), nn.ReLU(), nn.Linear(12, 1))
    opt = torch.optim.AdamW(net.parameters(), lr=.006, weight_decay=.03)
    tx, ty, tw = [torch.as_tensor(a, dtype=torch.float32) for a in (z, y, w)]
    for _ in range(30):
        for idx in torch.randperm(len(tx)).split(128):
            loss = nn.functional.huber_loss(net(tx[idx]).flatten(), ty[idx], reduction="none", delta=8)
            opt.zero_grad()
            (loss*tw[idx]).sum().div(tw[idx].sum()).backward()
            opt.step()
    return dict(**common, hidden_w=net[0].weight.detach().T.tolist(), hidden_b=net[0].bias.detach().tolist(),
                w=net[2].weight.detach()[0].tolist(), b=float(net[2].bias.detach()[0]))


def gains(rows, model, oracle=False):
    values = []
    for r in rows:
        base = r["original"]
        trial = base
        if r["event"]:
            if oracle:
                trial = max([base, *r["trials"].values()], key=lambda t:value_of(base["y"], t["y"]))
            else:
                direction = select(r["event"]["x"], model)
                if direction is not None:
                    trial = r["trials"][str(direction)]
        delta = (np.asarray(trial["y"])-base["y"]) * [-1,-1,1]
        values.append([*map(float, delta), trial["win"]-base["win"], value_of(base["y"], trial["y"]),
                       int(trial is not base), int(r["event"] is not None)])
    return np.array(values)


def summary(matrix):
    x = np.asarray(matrix)
    rng = np.random.default_rng(RNG_SEED)
    metric = x[:, :5]
    draws = np.array([metric[idx].mean(0) for idx in rng.integers(len(x), size=(5000, len(x)))])
    return dict(maps=len(x), eligible=int(x[:, 6].sum()), changed=int(x[:, 5].sum()),
                metrics=["earlier_relic", "earlier_credit", "m1_margin_gain", "m1_win_difference", "utility"],
                means=metric.mean(0).tolist(), ci95=np.quantile(draws,[.025,.975],axis=0).tolist(),
                earlier_later=[int((x[:,0]>0).sum()), int((x[:,0]<0).sum())])


def saved(path, data):
    content = json.dumps(data, indent=2, allow_nan=False)+"\n"
    if path.exists() and path.read_text() != content:
        raise ValueError(f"Different existing artifact {path}")
    path.write_text(content)


def training(train):
    a, dev = train[:576], train[576:]
    trials = []
    finalists = {}
    for kind in ("ridge","mlp","prior"):
        model = fit(a, kind)
        cuts = [.0001, .01, .035] if kind == "prior" else [.25, 1., 2., 3.5]
        group = []
        for cut in cuts:
            candidate = dict(**model, threshold=cut)
            x = gains(dev, candidate)
            n = int(x[:,5].sum())
            # A single fortunate card should not select a threshold.
            score = float(x[:,4].mean() - x[:,4].std(ddof=1)/np.sqrt(len(x)))
            group.append(dict(kind=kind, threshold=cut, changed=n, conservative_utility=score,
                              average_gain=x[:, :5].mean(0).tolist()))
        good = [r for r in group if r["changed"] >= 12] or group
        finalists[kind] = max(good,key=lambda r:(r["conservative_utility"],r["changed"]))
        trials.extend(group)
    eligible = [v for k,v in finalists.items() if k != "prior" and v["changed"] >= 12]
    best = max(eligible or [finalists["ridge"],finalists["mlp"]],
               key=lambda r:(r["conservative_utility"],r["changed"],r["kind"]=="ridge"))
    fitted = dict(**fit(train, best["kind"]), threshold=best["threshold"])
    prior = dict(kind="prior", threshold=finalists["prior"]["threshold"])
    return fitted, prior, trials


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder", type=Path)
    p.add_argument("stage", choices=("fit", "hold"))
    a = p.parse_args()
    train = read(a.folder, "train", 768)
    if a.stage == "fit":
        model, prior, trials = training(train)
        saved(HERE/"modell.json", model)
        saved(HERE/"priorregel.json", prior)
        saved(HERE/"entwicklung.json", dict(features=FEATURES, validation=trials,
              maps=len(train), informative=sum(bool(r["event"]) for r in train),
              trajectories=sum(1+len(r["trials"]) for r in train),
              seed_ranges=[train[0]["seed"], train[-1]["seed"]]))
        return
    held = read(a.folder,"hold",160)
    if {r["seed"] for r in train} & {r["seed"] for r in held}:
        raise ValueError("Overlapping train and held-out maps")
    model = json.loads((HERE/"modell.json").read_text())
    prior = json.loads((HERE/"priorregel.json").read_text())
    saved(HERE/"pruefung.json", dict(model=summary(gains(held, model)), prior=summary(gains(held, prior)),
                                      hindsight=summary(gains(held, None, oracle=True)),
                                      trajectories=sum(1+len(r["trials"]) for r in held)))
    for name, rows in (("lernen",train), ("pruefen",held)):
        payload = "".join(json.dumps(r,separators=(",",":"))+"\n" for r in rows).encode()
        (HERE/(name+".jsonl.gz")).write_bytes(gzip.compress(payload, mtime=0))


if __name__ == "__main__":
    main()
