"""Find immediately distinct scoring squares among shipped V16 moves from genuine observations."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
from agents.sherlock import geometry as g
from agents.sherlock.features import FEATURE_NAMES

POINT = np.array([FEATURE_NAMES.index(f"{d}_point") for d in "curdl"])
THREAT = FEATURE_NAMES.index("enemies_in_sap")
ENERGY = FEATURE_NAMES.index("self_low_energy")


def choices(positions, feats, masks, actions):
    directions = np.where((actions >= 1) & (actions <= 4), actions, 0)
    final = positions + np.stack((g.DIR_DX[directions], g.DIR_DY[directions]), axis=1)
    flat = final[:, 0] * 24 + final[:, 1]
    if (flat.min() < 0 or flat.max() >= 576):
        raise ValueError("Actual command points outside the board")
    counts = np.bincount(flat, minlength=576)
    on = feats[:, POINT] > .5
    rows = np.flatnonzero((directions > 0) & (counts[flat] >= 2) & on[np.arange(len(actions)), directions]
                         & (feats[:, THREAT] == 0) & (feats[:, ENERGY] == 0))
    result = []
    for k in rows:
        if not masks[k, directions[k]]:
            continue
        for alt in np.flatnonzero(on[k] & masks[k, :5]):
            x, y = positions[k, 0] + g.DIR_DX[alt], positions[k, 1] + g.DIR_DY[alt]
            if 0 <= x < 24 and 0 <= y < 24 and counts[x*24+y] == 0:
                result.append((int(k), int(alt)))
    return result


def measure(base, out):
    logs = sorted(base.glob("v16_*.json"))
    if len(logs) != 46:
        raise ValueError("Need the complete archive")
    rows = []
    for f in logs:
        receipt = json.loads(f.read_text())
        raw = base / receipt["file"]
        if sha256(raw.read_bytes()).hexdigest() != receipt["sha256"]:
            raise ValueError("Source changed")
        with np.load(raw, allow_pickle=False) as z:
            pos, feats, masks, acts, uid, steps = [z[k] for k in ("pos", "feats", "mask", "act", "uid", "step")]
        turns = 0
        stays = 0
        changed_rows = 0
        distinct_starts = 0
        for idx in np.split(np.arange(len(acts)), np.flatnonzero(np.diff(steps)) + 1):
            if len(idx) == 0:
                continue
            vals = choices(pos[idx], feats[idx], masks[idx], acts[idx])
            if vals:
                turns += 1
                stays += int(any(a == 0 for _, a in vals))
                changed_rows += len(vals)
                dests = pos[idx] + np.stack((g.DIR_DX[np.where(acts[idx] <= 4, acts[idx], 0)],
                                             g.DIR_DY[np.where(acts[idx] <= 4, acts[idx], 0)]), axis=1)
                separate = False
                for k, _ in vals:
                    same = (dests == dests[k]).all(axis=1)
                    separate |= len(np.unique(pos[idx][same], axis=0)) > 1
                distinct_starts += int(separate)
        rows.append(dict(seed=receipt["seed"], side=receipt["side"], group=receipt["group"],
                         turns=turns, includes_stay=stays, distinct_starts=distinct_starts,
                         unit_options=changed_rows, sha256=receipt["sha256"]))
    totals = {k: sum(r[k] for r in rows) for k in ("turns", "includes_stay", "distinct_starts", "unit_options")}
    maps = len({r["seed"] for r in rows if r["turns"]})
    report = dict(plan_sha256=sha256((HERE / "PLAN.md").read_bytes()).hexdigest(), totals=totals,
                  maps_with_cases=maps, passes_archive=totals["turns"] >= 30 and maps >= 10,
                  per_game=rows)
    (out / "archiv.json").write_text(json.dumps(report, indent=2) + "\n")
    print(totals, maps)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("base", type=Path)
    cli.add_argument("out", type=Path)
    args = cli.parse_args()
    measure(args.base, args.out)
