"""Reconstruct the release's holder and unstack decisions from archived teacher episodes."""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import importlib
import json
from pathlib import Path
from types import SimpleNamespace
import sys

import numpy as np
from scipy.special import logsumexp
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "netzwahl"))
from vorhersagen import RELEASE, V16, input_files
from scripts.imitate import prepare_labels
from scripts.r3_package import _module_for


def inspect(row, raw, cache, feature_names, geometry, policy):
    with np.load(cache, allow_pickle=False) as saved, np.load(raw, allow_pickle=False) as source:
        if str(saved["origin"]) != row["sha256"] or sha256(raw.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("The two records do not describe the same game")
        positions, uids, steps = (source[k] for k in ("pos", "uid", "step"))
        feats = source["feats"]
        rows = {k: torch.from_numpy(source[k]) for k in ("pos", "feats", "mask", "act", "sdx", "sdy")}
        prepare_labels(rows, 24, 24)
        eligible = rows["admitted"].numpy()
        legal = saved["legal"]
        if not np.array_equal(rows["mask"][eligible].numpy(), legal):
            raise ValueError("Legal mask reconstruction mismatch")
        first = np.where(legal, saved["a"], -np.inf)
        second = np.where(legal, saved["b"], -np.inf)
    logits = np.zeros((len(uids), 6), np.float32)
    logits[eligible] = first - logsumexp(first, axis=1, keepdims=True) + second - logsumexp(second, axis=1, keepdims=True)
    unit_count = feats[:, feature_names.index("allies_here")]
    on_point = feats[:, feature_names.index("on_point")] > 0
    redundant = feats[:, feature_names.index("redundant_here")] > 0
    dummy = SimpleNamespace(ep_stats=Counter())
    tally = Counter()
    tiles = set()
    for start, stop in zip(np.r_[0, np.flatnonzero(np.diff(steps)) + 1],
                           np.r_[np.flatnonzero(np.diff(steps)) + 1, len(steps)], strict=True):
        tally["recorded_turns"] += 1
        unit_slice = slice(start, stop)
        if not eligible[unit_slice].all():
            continue
        coords = [(int(x), int(y)) for x, y in positions[unit_slice]]
        groups = defaultdict(list)
        for k, xy in enumerate(coords):
            groups[xy].append(k)
        if any(len(ks) >= 4 or round(4 * float(unit_count[start + ks[0]])) != len(ks)
               for ks in groups.values()):
            continue
        owners = {xy: int(uids[start + ks[0]]) for xy, ks in groups.items()}
        if any(redundant[start + ks[0]] for ks in groups.values()):
            raise ValueError("Unresolved owner in an apparently exact stack")
        tally["complete_turns"] += 1
        points = [xy for xy, ks in groups.items() if len(ks) >= 2 and on_point[start + ks[0]]]
        if not points:
            continue
        logp = logits[unit_slice].copy()
        logp[:, 0] -= (~on_point[unit_slice] | redundant[unit_slice]).astype(np.float32)
        actions = policy._unstack_actions(
            dummy, {"first_on_tile": owners}, uids[unit_slice], positions[unit_slice], logp, logp.argmax(axis=1))
        destinations = {xy if a in (0, 5) else (xy[0] + int(geometry.DIR_DX[a]), xy[1] + int(geometry.DIR_DY[a]))
                        for xy, a in zip(coords, actions, strict=True)}
        for xy in points:
            tally["occupied_point_stacks"] += 1
            if xy in destinations:
                continue
            tally["uncovered_stacks"] += 1
            if any(logits[start + k].argmax() == 0 for k in groups[xy]):
                tally["available_handoffs"] += 1
                tiles.add(xy)
    return dict(seed=row["seed"], distinct_fields=len(tiles), **tally)


def run(base, initial):
    if sha256(RELEASE.read_bytes()).hexdigest() != V16:
        raise ValueError("Unexpected release")
    _module_for(RELEASE.resolve())
    feature_names = importlib.import_module("sherlock.features").FEATURE_NAMES
    geometry = importlib.import_module("sherlock.geometry")
    policy = importlib.import_module("sherlock.imitation_agent").ImitationAgent
    results = {"old": [], "new": []}
    for row, path, split in input_files(base, initial):
        if split != "valid":
            cache = base / "vorhersagen" / f"{split}_{row['seed']}.npz"
            results[split].append(inspect(row, path, cache, feature_names, geometry, policy))
    totals = {}
    for split, games in results.items():
        totals[split] = dict(games=len(games), positive=sum(r.get("available_handoffs", 0) > 0 for r in games))
        for metric in ("complete_turns", "recorded_turns", "occupied_point_stacks", "uncovered_stacks", "available_handoffs"):
            totals[split][metric] = sum(r.get(metric, 0) for r in games)
    qualified = (len(results["new"]) == 40 and totals["old"]["positive"] >= 12
                 and totals["new"]["positive"] >= 8 and totals["new"]["available_handoffs"] >= 20)
    target = (base if initial else HERE) / ("halter-vorpruefung.json" if initial else "ergebnis.json")
    target.write_text(json.dumps(dict(qualified=qualified, totals=totals, games=results), indent=2) + "\n")
    print(json.dumps(totals))


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("base", type=Path)
    cli.add_argument("--initial", action="store_true")
    args = cli.parse_args()
    run(args.base, args.initial)
