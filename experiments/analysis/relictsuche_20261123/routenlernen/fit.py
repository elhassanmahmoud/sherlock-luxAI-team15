"""Train a shared route-value regressor and evaluate choices with map-level weighting."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch
from torch import nn

from collect import OUT, ROOT, SPLITS, seeds_for
from routes import DIRECTIONS, HERE, NAMES
sys.path.insert(0, str(ROOT))
from experiments.analysis.relictsuche_20261123.routenlernen.kandidat import values

ORIGINAL = NAMES.index("original_first_move")
REFERENCE = NAMES.index("never_seen")


def partition(split):
    folder = OUT / ("direction_" + split)
    expected = seeds_for(split).tolist()
    found = sorted(int(p.stem) for p in folder.glob("*.npz"))
    if expected != found:
        raise ValueError(f"Incomplete {split} collection: {len(found)} of {len(expected)}")
    groups, records = [], []
    for i, seed in enumerate(expected):
        path = folder / f"{seed}.npz"
        with np.load(path, allow_pickle=False) as d:
            x, y, sel = d["x"], d["y"], d["selections"]
            offsets, ticks = d["offsets"], d["ticks"]
            if (len(x) != len(y) or len(sel) != len(x) or offsets[-1] != len(x) or int(d["team"]) != i % 2
                    or len(ticks) != len(offsets) - 1 or x.shape[1] != len(NAMES)
                    or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y))):
                raise ValueError("Bad offline sample")
            off_asteroid = 0
            for j, tick in enumerate(ticks):
                sl = slice(offsets[j], offsets[j + 1])
                if sel[sl][0] != 0:
                    off_asteroid += 1
                    continue
                if y[sl][0] < 0:
                    raise ValueError("Missing stay comparator")
                groups.append((seed, x[sl], y[sl], sel[sl]))
            records.append(dict(seed=seed, team=i % 2, groups=len(ticks), without_stay=off_asteroid, paths=len(x),
                                sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    return groups, records


def training(groups, epochs):
    torch.manual_seed(2311)
    torch.set_num_threads(1)
    x = np.concatenate([r[1] for r in groups])
    y = np.concatenate([r[2] - r[2][0] for r in groups])
    lengths = np.array([len(r[1]) for r in groups])
    row_weight = 1 / np.repeat(lengths, lengths)
    mean, scale = x.mean(0), np.maximum(x.std(0), .12)
    X = torch.from_numpy((x - mean) / scale)
    Y = torch.from_numpy(y)
    weights = torch.from_numpy((row_weight / row_weight.mean()).astype(np.float32))
    model = nn.Sequential(nn.Linear(x.shape[1], 32), nn.ReLU(), nn.Linear(32, 1))
    opt = torch.optim.AdamW(model.parameters(), lr=.002, weight_decay=.01)
    history = []
    for ep in range(1, max(epochs) + 1):
        total = 0.
        for idx in torch.randperm(len(x)).split(768):
            pred = model(X[idx]).flatten()
            loss = (weights[idx] * (pred - Y[idx]).square()).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
            total += float(loss.detach()) * len(idx)
        if ep in epochs:
            exported = {"mean": mean, "scale": scale}
            for i, layer in ((1, model[0]), (2, model[2])):
                exported["w" + str(i)] = layer.weight.detach().numpy().T.copy()
                exported["b" + str(i)] = layer.bias.detach().numpy().copy()
            history.append((ep, total / len(x), exported))
    return history


def evaluate(groups, model):
    by_map = {}
    for seed, x, y, ids in groups:
        score = values(x, model)
        rank = score + .15 * x[:, ORIGINAL]
        k = int(np.argmax(rank))
        if score[k] < score[0] + .35:
            k = 0
        # The medoid continuation is the straight course if it exists; otherwise compare all
        # public options beginning with V16's direction without consulting their gold scores.
        same = np.flatnonzero(x[:, ORIGINAL])
        if len(same):
            nearest = same[np.argmin(np.count_nonzero(DIRECTIONS[ids[same]] != DIRECTIONS[ids[same], :1], axis=1))]
        else:
            nearest = 0
        area = np.flatnonzero(x[:, REFERENCE] == np.max(x[:, REFERENCE]))[0]
        row = np.asarray([y[k] - y[nearest], y[k] - y[area], y[k] - y[0],
                          y.max() - y[k], abs(float(score[k] - score[0]) - (y[k] - y[0])),
                          x[k, ORIGINAL] == 0 and k != 0, len(same) > 0, len(x), y[k]], float)
        by_map.setdefault(seed, []).append(row)
    columns = ("vs_original_direction", "vs_largest_fresh_fraction", "vs_stay", "regret",
               "selected_abs_error", "new_first_direction_fraction", "original_direction_available",
               "mean_choices", "selected_value")
    seeds = sorted(by_map)
    array = np.array([np.mean(by_map[s], axis=0) for s in seeds])
    rng = np.random.default_rng(231123)
    boot = array[rng.integers(len(seeds), size=(4000, len(seeds)))].mean(1)
    result = {name: {"mean": float(array[:, k].mean()), "ci95": np.percentile(boot[:, k], (2.5, 97.5)).tolist()}
              for k, name in enumerate(columns)}
    result.update(maps=len(seeds), groups=len(groups), paths=sum(len(g[1]) for g in groups))
    return result


def dump(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("fit", "validate"))
    args = parser.parse_args()
    if args.mode == "fit":
        train, records = partition("train")
        tr = {r["seed"] for r in records[:256]}
        # Separate inner maps select only the length of training. One final full-data fit.
        first = [r for r in train if r[0] in tr]
        last = [r for r in train if r[0] not in tr]
        tuning = []
        for ep, loss, model in training(first, [4, 10, 20]):
            val = evaluate(last, model)
            tuning.append(dict(epoch=ep, train_loss=loss, selection=val["selected_value"]["mean"],
                               inner_maps=val["maps"], inner_groups=val["groups"]))
        chosen = max(tuning, key=lambda row: row["selection"])["epoch"]
        _, loss, params = training(train, [chosen])[0]
        dump(HERE / "routengewichte.json", dict(features=list(NAMES), **{k: v.tolist() for k, v in params.items()}))
        dump(HERE / "training.json", dict(input_files=records, training_maps=len(records), active_maps=len(set(r[0] for r in train)),
                                         groups=len(train), paths=sum(len(r[1]) for r in train), epochs=chosen,
                                         updates=chosen * int(np.ceil(sum(len(r[1]) for r in train) / 768)),
                                         final_loss=loss, inner=tuning))
        print(chosen, loss, flush=True)
    else:
        valid, records = partition("valid")
        from experiments.analysis.relictsuche_20261123.routenlernen.kandidat import load_model
        val = evaluate(valid, load_model())
        dump(HERE / "offline.json", dict(weights_sha256=hashlib.sha256((HERE / "routengewichte.json").read_bytes()).hexdigest(),
                                        heldout_maps=len(records), measured=val, input_files=records))
        print(json.dumps(val, indent=1), flush=True)


if __name__ == "__main__":
    main()
