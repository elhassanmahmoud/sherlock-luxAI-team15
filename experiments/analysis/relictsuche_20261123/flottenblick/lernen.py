"""Fit an eight-step spatial forecast and compare with separately calibrated baselines."""
import argparse
import gzip
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
import torch
from torch.nn import functional as F

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from flotte import CHANNELS, DIRECTIONS, PAIR, POWER, XY
from sammeln import OUT, panel
from vorhersage import (
    Forecast, KINDS, choose, coverage, load, probabilities, projection_keys,
)

METRICS = ("near_brier", "all_brier", "fresh_brier", "factual_observed_brier", "observed_exclusive_error",
           "potential_new_pairs", "potential_selected", "reference_same_first", "outside_next_brier")


def read(split):
    folder = OUT / split
    samples, records = [], []
    for i, seed in enumerate(panel(split)):
        meta = folder/f"{seed}.json"
        data = folder/f"{seed}.npz"
        m = json.loads(meta.read_text())
        if (m["seed"] != seed or m["index"] != i or m["sha256"] != sha256(data.read_bytes()).hexdigest()
                or (records and records[0]["source"] != m["source"])):
            raise ValueError("Data coverage, identity or provenance differs")
        with np.load(data, allow_pickle=False) as src:
            raw = dict(src)
        if (len(raw["turn"]) != m["samples"] or int(raw["team"]) != i%2
                or str(raw["opponent"]) != ("solution92", "v16")[(i//2)%2]
                or (m["samples"] > 0 and m["checks"] < 2)):
            raise ValueError("Incorrect panel balance or missing engine checks")
        records.append(m)
        for k, step in enumerate(raw["turn"]):
            a,b = raw["offsets"][k:k+2]
            paths = raw["paths"][a:b]
            x = raw["x"][k]
            rest = raw["remaining"][k]
            y = np.any(rest > 0, axis=0)
            seen = raw["last"][k]
            if not np.all(~y | raw["full"][k]):
                raise ValueError("Rest-of-fleet future sight must be a subset of full-team sight")
            samples.append(dict(seed=seed, index=i, team=i%2, opponent=str(raw["opponent"]), turn=int(step),
                                x=x, dist=raw["projections"][k], last=seen, paths=paths, route=raw["route"][a:b],
                                origin=int(np.argmax(x[12])), near=coverage(paths), weight=1/m["samples"],
                                y=y, full=raw["full"][k], remaining=rest))
    if not records or not samples:
        raise ValueError("Empty dataset")
    return samples, records


def calibrate(samples):
    sizes = [13, 13, 13, 169]
    counts = [np.zeros(n) for n in sizes]
    hits = [np.zeros(n) for n in sizes]
    for s in samples:
        for k, key in enumerate(projection_keys(s["dist"])):
            cell = key.ravel()
            counts[k] += np.bincount(cell, minlength=sizes[k]) * s["weight"]
            hits[k] += np.bincount(cell, weights=s["y"].ravel(), minlength=sizes[k]) * s["weight"]
    tables = {}
    for k, name in enumerate(KINDS):
        if name == "joint":
            prior = np.tile(tables["straight"], 13)
        else:
            prior = np.repeat(hits[k].sum() / counts[k].sum(), sizes[k])
        tables[name] = (hits[k] + 10 * prior)/(counts[k] + 10)
    return tables


def dataset(samples, tables):
    x = torch.from_numpy(np.stack([s["x"] for s in samples]))
    y = torch.from_numpy(np.stack([s["y"] for s in samples]).astype(np.float32))
    region = torch.from_numpy(np.stack([s["near"] for s in samples]).astype(np.float32))
    w = torch.tensor([s["weight"] for s in samples], dtype=torch.float32)
    q = torch.from_numpy(np.stack([probabilities(projection_keys(s["dist"])[3], tables["joint"])
                                   for s in samples]))
    return x,y,region,w,q


def cnn_predictions(net, samples, tables):
    net.eval()
    with torch.no_grad():
        xs, _, _, _, anchors = dataset(samples, tables)
        return torch.cat([torch.sigmoid(net(xs[i:i+32].float(), anchors[i:i+32]))
                          for i in range(0, len(samples), 32)]).numpy()


def simple_predictions(samples, tables, kind):
    k = KINDS.index(kind)
    return np.stack([probabilities(projection_keys(s["dist"])[k], tables[kind]) for s in samples])


def map_brier(samples, pred):
    groups = {}
    for s,q in zip(samples, pred, strict=True):
        groups.setdefault(s["seed"], []).append(float(np.mean((q[s["near"]]-s["y"][s["near"]])**2)))
    return float(np.mean([np.mean(a) for a in groups.values()]))


def train(samples, tables, epochs, development=None):
    torch.set_num_threads(1)
    torch.manual_seed(2311234)
    net = Forecast()
    opt = torch.optim.AdamW(net.parameters(), lr=.0015, weight_decay=.002)
    x,y,region,w,q = dataset(samples, tables)
    history = []
    for epoch in range(1, max(epochs)+1):
        net.train()
        total = 0.
        for idx in torch.randperm(len(x)).split(32):
            logits = net(x[idx].float(), q[idx])
            weights = (.4 + 1.6 * region[idx]) * w[idx, None, None]
            loss = (F.binary_cross_entropy_with_logits(logits, y[idx], reduction="none") * weights).sum()/weights.sum()
            opt.zero_grad()
            loss.backward()
            opt.step()
            total += float(loss.detach()) * len(idx)
        if epoch in epochs:
            brier = map_brier(development, cnn_predictions(net, development, tables)) if development else None
            history.append(dict(epoch=epoch, brier=brier, loss=total/len(x)))
    return net, history


def true_exclusive(paths, remaining, last):
    # Add the hypothetical scout to the actual no-scout fleet power independently at every future tick.
    # Paths obey current public terrain, so this is potential exposure at the supplied positions.
    # Engine-played scout positions are measured separately in the later active probe.
    current = remaining.reshape(remaining.shape[0], -1)
    other = np.any(current > 0, axis=0)
    mirror = (23-XY[:, 1])*24 + 23-XY[:, 0]
    blocked = (other | other[mirror] | (last.ravel() >= 0) | (last.ravel()[mirror] >= 0))
    new = np.any(current[None, :, :] + POWER[paths] > 0, axis=1)
    reps = np.unique(PAIR)
    return ((new | new[:, mirror])[:, reps] & ~blocked[reps]).sum(1)


def candidate_choice(s, q):
    fog = s["x"][18].astype(bool)
    energy = s["x"][19].astype(np.float32) * 20
    return choose(q, s["paths"], s["last"], fog, energy, s["origin"])


def row_values(s, q, first_dir, best):
    y, near = s["y"], s["near"]
    error = (q-y)**2
    never = s["last"] < 0
    fresh = near & never
    observed = fresh & s["full"]
    abs_error = abs(float(np.sum(1-q[observed])) - int((~y & observed).sum())) if np.any(observed) else np.nan
    channels = [
        np.mean(error[near]), np.mean(error), np.mean(error[fresh]) if np.any(fresh) else np.nan,
        np.mean(error[observed]) if np.any(observed) else np.nan, abs_error,
    ]
    idx = candidate_choice(s, q)
    value = best[idx] if idx is not None else best[-1]
    direction = int(DIRECTIONS[s["route"][idx], 0]) if idx is not None else 0
    next_unknown = near & (np.minimum(s["dist"][0], s["dist"][1]) > 1)
    unseen_ahead = np.mean(error[next_unknown]) if np.any(next_unknown) else np.nan
    return channels + [value, float(idx is not None), float(direction == first_dir), unseen_ahead], direction


def aggregate(rows):
    matrix = np.array(rows, float)
    count = np.isfinite(matrix).sum(0)
    return np.divide(np.nansum(matrix, axis=0), count, out=np.full(matrix.shape[1], np.nan), where=count>0)


def stats(values):
    values = values[np.isfinite(values)]
    if not len(values):
        return dict(maps=0, mean=None, ci95=None)
    rng = np.random.default_rng(2311234)
    boots = values[rng.integers(len(values), size=(4000, len(values)))].mean(1)
    return dict(maps=len(values), mean=float(np.mean(values)), ci95=np.quantile(boots, [.025,.975]).tolist())


def score(samples, preds, ref):
    methods = list(preds)
    results, log = {}, []
    for i, s in enumerate(samples):
        options = np.vstack((s["paths"], np.full((1, s["paths"].shape[1]), s["origin"], dtype=np.int16)))
        truth = true_exclusive(options, s["remaining"], s["last"])
        ref_index = candidate_choice(s, preds[ref][i])
        ref_dir = int(DIRECTIONS[s["route"][ref_index], 0]) if ref_index is not None else 0
        record = dict(seed=s["seed"], team=s["team"], turn=s["turn"], opponent=s["opponent"], options=len(s["paths"]),
                      reachable_cells=int(s["near"].sum()),
                      actually_exclusive_physical_cells=int((s["full"] & ~s["y"] & s["near"] & (s["last"]<0)).sum()), methods={})
        group = results.setdefault(s["seed"], {m: [] for m in methods})
        for m in methods:
            val, d = row_values(s, preds[m][i], ref_dir, truth)
            group[m].append(val)
            record["methods"][m] = {"direction": d, "values": [float(v) if np.isfinite(v) else None for v in val]}
        log.append(record)
    pool = {m: np.asarray([aggregate(r[m]) for r in results.values()]) for m in methods}
    summary = {m: {k: stats(v[:, j]) for j,k in enumerate(METRICS)} for m,v in pool.items()}
    effects = {}
    for baseline in KINDS:
        # Positive numbers mean that the neural model improves the measurement.
        diff = (pool["cnn"] - pool[baseline]) * [-1,-1,-1,-1,-1,1,1,1,-1]
        effects[baseline] = {name: stats(diff[:, j]) for j, name in enumerate(METRICS)}
    return summary, effects, log


def save(file, value):
    file.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def fit_sources():
    return {name: sha256((HERE / name).read_bytes()).hexdigest() for name in (
        "AUSWERTUNGSPLAN.md", "lernen.py", "vorhersage.py", "kandidat.py")}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("fit","valid"))
    args = p.parse_args()
    if args.mode == "fit":
        training, records = read("train")
        first = [x for x in training if x["index"] < 384]
        development = [x for x in training if x["index"] >= 384]
        tables = calibrate(first)
        scores = {k: map_brier(development, simple_predictions(development, tables, k)) for k in KINDS}
        ref = min(scores, key=scores.get)
        _, inner = train(first, tables, [2,5,10], development)
        epochs = min(inner, key=lambda v:v["brier"])["epoch"]
        all_tables = calibrate(training)
        net, fit = train(training, all_tables, [epochs])
        np.savez_compressed(HERE/"flottengewichte.npz", **{k: v.detach().numpy() for k,v in net.state_dict().items()})
        cfg = dict(channels=list(CHANNELS), reference=ref, tables={k:v.tolist() for k,v in all_tables.items()})
        save(HERE/"modell.json", cfg)
        save(HERE/"fit.json", dict(maps=len(records), active_maps=len({s["seed"] for s in training}), samples=len(training),
                                   updates=epochs * int(np.ceil(len(training)/32)), epochs=epochs, inner=inner,
                                   fit=fit, reference_scores=scores, source=records[0]["source"],
                                   fit_sources=fit_sources(), engine_checks=sum(r["checks"] for r in records),
                                   maps_sha256={str(r["seed"]):r["sha256"] for r in records}))
        print("fit", epochs, fit, ref, flush=True)
    else:
        val, records = read("valid")
        net, cfg = load()
        fit = json.loads((HERE/"fit.json").read_text())
        if (records[0]["source"] != fit["source"] or fit["fit_sources"] != fit_sources()
                or set(fit["maps_sha256"]) & {str(r["seed"]) for r in records}):
            raise ValueError("Different data generation or overlapping maps")
        pred = {k: simple_predictions(val, cfg["tables"], k) for k in KINDS}
        pred["cnn"] = cnn_predictions(net, val, cfg["tables"])
        summary, effects, rows = score(val, pred, cfg["reference"])
        ref = cfg["reference"]
        report = dict(maps=len(records), active_maps=len({s["seed"] for s in val}), samples=len(val),
                      reference=ref, metrics=summary, cnn_improvement=effects,
                      pass_brier_against_reference=effects[ref]["near_brier"]["ci95"][0] > 0,
                      engine_checks=sum(r["checks"] for r in records), actual_exclusive_cells=sum(
                          r["actually_exclusive_physical_cells"] for r in rows),
                      source=records[0]["source"], weights_sha256=sha256((HERE/"flottengewichte.npz").read_bytes()).hexdigest(),
                      maps_sha256={str(r["seed"]):r["sha256"] for r in records})
        save(HERE/"pruefung.json", report)
        with gzip.GzipFile(filename=HERE/"vorhersagen.jsonl.gz", mode="wb", mtime=0) as result:
            for r in rows:
                result.write((json.dumps(r, separators=(",", ":"), allow_nan=False)+"\n").encode())
        print("valid", len(val), ref, report["pass_brier_against_reference"], effects[ref], flush=True)


if __name__ == "__main__":
    main()
