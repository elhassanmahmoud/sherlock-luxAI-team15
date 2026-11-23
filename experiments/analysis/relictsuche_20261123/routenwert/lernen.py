"""Fit public route utility on training maps and evaluate once on held-out matched outcomes."""
import argparse
import gzip
import json
from pathlib import Path

import numpy as np

from kandidat import HERE, choose_path, paired_gain


def load(directory, split, expected):
    rows = [json.loads(p.read_text()) for p in sorted((directory/split).glob("*.json"))]
    if len(rows) != expected or len({r["seed"] for r in rows}) != expected:
        raise ValueError(f"{split}: expected {expected}, found {len(rows)}")
    if len({json.dumps(r["sources"], sort_keys=True) for r in rows}) != 1:
        raise ValueError("Incompatible sources in matched games")
    for row in rows:
        if row["original"]["changes"] or len(row["trials"]) != (3 if row["event"] else 0):
            raise ValueError("Invalid untreated seat or incomplete arms")
        for trial in [row["original"], *row["trials"]]:
            if not all(0 <= v <= 101 for v in trial["y"][:2]) or trial["win"] not in (0, 1):
                raise ValueError("Invalid opening endpoint")
    return rows


def train(rows):
    x, y = [], []
    for r in rows:
        if r["event"]:
            x.extend(r["event"]["x"])
            y.extend(paired_gain(r["original"]["y"], a["y"]) for a in r["trials"])
    x, y = np.asarray(x), np.asarray(y)
    mean = x.mean(0)
    scale = np.where(x.std(0) >= .01, x.std(0), 1.)
    z = (x - mean) / scale
    weights = np.linalg.solve(z.T @ z + np.eye(z.shape[1]) * (len(rows) / 10), z.T @ (y - y.mean()))
    return dict(mean=mean.tolist(), scale=scale.tolist(), weights=weights.tolist(),
                intercept=float(y.mean()), threshold=1., feature_count=z.shape[1],
                examples=len(y), eligible_cards=len(y)//3)


def evaluate(rows, model):
    predictions, potential = [], []
    actual, oracle, original = [], [], []
    selected = changed = 0
    for row in rows:
        base = row["original"]
        best = chosen = base
        if row["event"]:
            x = (np.asarray(row["event"]["x"]) - model["mean"]) / model["scale"]
            p = model["intercept"] + x @ model["weights"]
            a = choose_path(p, model["threshold"])
            if a is not None:
                selected += 1
                chosen = row["trials"][a]
                changed += bool(chosen["changes"])
            arms = [base, *row["trials"]]
            utility = [paired_gain(base["y"], trial["y"]) for trial in arms]
            best = arms[np.argmax(utility)]
            predictions.extend(p.tolist())
            potential.extend(utility[1:])
        for target, trial in ((actual, chosen), (oracle, best), (original, base)):
            target.append([*trial["y"], trial["win"]])
    def summary(data):
        m = np.asarray(data)
        diff = m - np.asarray(original)
        delta = diff * [-1, -1, 1, 1]
        return dict(average=m.mean(0).tolist(), wins=int(m[:, 3].sum()),
                    gain=delta.mean(0).tolist(), earlier=int((delta[:, 0] > 0).sum()),
                    later=int((delta[:, 0] < 0).sum()))
    corr = float(np.corrcoef(predictions, potential)[0, 1])
    return dict(cards=len(rows), selected=selected, changed_cards=int(changed), actual=summary(actual),
                incumbent=summary(original), hindsight=summary(oracle), prediction_correlation=corr)


def write(path, data):
    payload = json.dumps(data, indent=2, allow_nan=False) + "\n"
    if path.exists() and path.read_text() != payload:
        raise ValueError(f"Existing output differs: {path}")
    path.write_text(payload)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    p.add_argument("stage", choices=("fit", "check"))
    args = p.parse_args()
    trainset = load(args.directory, "train", 320)
    model = train(trainset)
    if args.stage == "fit":
        write(HERE/"modell.json", model)
        return
    if json.loads((HERE/"modell.json").read_text()) != model:
        raise ValueError("Model is not the frozen train-only fit")
    held = load(args.directory, "check", 80)
    if {r["seed"] for r in trainset} & {r["seed"] for r in held}:
        raise ValueError("Map leakage")
    write(HERE/"offline.json", dict(training=evaluate(trainset, model), held=evaluate(held, model)))
    for label, batch in (("training", trainset), ("pruefung", held)):
        payload = "".join(json.dumps(r, separators=(",", ":"))+"\n" for r in batch).encode()
        (HERE/(label+".jsonl.gz")).write_bytes(gzip.compress(payload, mtime=0))


if __name__ == "__main__":
    main()
