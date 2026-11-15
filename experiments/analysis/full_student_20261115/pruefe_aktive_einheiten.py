"""Recover rigorous bounds on dead teacher rows in the sealed 15 November corpus, without replay."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np


CORPUS_SHA256 = "bd6744c9d4ac08eda6958e3dff637f257ac96b5ae8a3b6098238c4453a0bebea"
DIRECTORIES = {"expert": "expert", "mixed": "movement_dagger", "v14": "v14_advice"}


def delta_intervals():
    # The engine stores signed int16 energy and caps positive energy at 400.
    # Feature 72 is tanh((own - nearest_enemy) / 100), then float32, then float16.
    limit = 400 - np.iinfo(np.int16).min
    possible = np.arange(-limit, limit + 1, dtype=np.int32)
    bounds = {}
    for precision in (np.float32, np.float64):
        values = np.tanh(possible.astype(precision) / 100).astype(np.float32).astype(np.float16)
        unique, starts = np.unique(values, return_index=True)
        for key, first, last in zip(unique, starts, [*starts[1:] - 1, len(values) - 1]):
            low, high = bounds.get(float(key), (limit, -limit))
            bounds[float(key)] = min(low, int(possible[first])), max(high, int(possible[last]))
    return bounds


def check_rows(file, bounds, counts, examples):
    with np.load(file, allow_pickle=False) as z:
        feat, step, pos, mask, label, uid = (z[k] for k in ("feats", "step", "pos", "mask", "act", "uid"))
    e = np.rint(feat[:, 2].astype(np.float32) * 400).astype(int)
    mask[:, 5] = e >= np.rint(feat[:, 7].astype(np.float32) * 50).astype(int)
    zero = e == 0
    only_stay = mask[:, 0] & ~mask[:, 1:].any(axis=1)
    counts.update(rows=len(e), zero_energy_code=int(zero.sum()),
                  zero_stay_teacher=int((zero & (label == 0)).sum()),
                  zero_other_teacher=int((zero & (label != 0)).sum()),
                  zero_not_forced_stay=int((zero & ~only_stay).sum()))

    visible = feat[:, 74] > 0
    nearest = pos.astype(int) + np.rint(feat[:, 69:71].astype(np.float32) * 24).astype(int)
    # All units that select this same occupied tile select the same first enemy ID
    # there (ascending enemy IDs and np.argmin). Never combine two frames.
    target = step.astype(int) * 24 * 24 + nearest[:, 0] * 24 + nearest[:, 1]
    unknown = np.flatnonzero(zero & visible)
    enemy_bound = {}
    for i in np.flatnonzero(~zero & visible & np.isin(target, target[unknown])):
        dlo, dhi = bounds[float(feat[i, 72])]
        lo, hi = enemy_bound.get(target[i], (np.iinfo(np.int16).min, 400))
        interval = max(lo, e[i] - dhi), min(hi, e[i] - dlo)
        if interval[0] > interval[1]:
            raise ValueError(f"Contradictory enemy energy in {file}, frame {step[i]}")
        enemy_bound[target[i]] = interval

    for i in unknown:
        dlo, dhi = bounds[float(feat[i, 72])]
        lo, hi = enemy_bound.get(target[i], (np.iinfo(np.int16).min, 400))
        if lo + dlo > 0:
            raise ValueError(f"Contradictory own energy clamp in {file}, row {i}")
        if hi + dhi < 0:
            counts["proven_negative"] += 1
            counts["negative_stay_teacher"] += int(label[i] == 0)
            counts["negative_not_forced_stay"] += int(not only_stay[i])
            if len(examples) < 5:
                examples.append(dict(file=file.name, frame=int(step[i]), uid=int(uid[i]), label=int(label[i]),
                                     enemy_energy=[int(lo), int(hi)], energy_difference=[dlo, dhi]))
        elif lo + dlo == 0:
            counts["proven_true_zero"] += 1


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("imitation", type=Path, help="Parent folder of the three final_20261115_* datasets")
    p.add_argument("--corpus", type=Path, default=Path(__file__).with_name("corpus.json"))
    args = p.parse_args()
    data = args.corpus.read_bytes()
    if hashlib.sha256(data).hexdigest() != CORPUS_SHA256:
        raise ValueError("Unexpected registered study manifest")

    # Every unclamped energy 1..400 round-trips through the exact archived encoding.
    integers = np.arange(401)
    encoded = (integers / 400).astype(np.float32).astype(np.float16)
    if not np.array_equal(integers, np.rint(encoded.astype(np.float32) * 400)):
        raise ValueError("Integer energy does not round-trip")
    bounds = delta_intervals()
    totals, examples = defaultdict(Counter), []
    for row in json.loads(data)["files"]:
        group = row["cohort"]
        file = args.imitation / ("final_20261115_" + DIRECTORIES[group]) / row["file"]
        if hashlib.sha256(file.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError(f"Input archive changed: {file}")
        check_rows(file, bounds, totals[group + "/" + row["split"]], examples)
    print(json.dumps(dict(corpus_sha256=CORPUS_SHA256, counts=totals, examples=examples), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
