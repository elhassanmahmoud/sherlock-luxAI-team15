"""Compare board knowledge and occupation using only the acting side's recorded observations."""
import argparse
from collections import defaultdict
import gzip
from hashlib import sha256
import inspect
import json
from pathlib import Path
import sys

import numpy as np

from sammeln import HERE, PACKAGES, ROOT, sample


def public_obs(arrays, step):
    result = {}
    for name, values in arrays.items():
        if name == "commands":
            continue
        parts = name.split("/")
        if len(parts) == 1:
            result[name] = values[step]
        else:
            result.setdefault(parts[0], {})[parts[1]] = values[step]
    return result


def summarize(folder, name, seat, flags):
    from sherlock.belief import Belief
    from sherlock.geometry import mirror_positions
    path = folder / f"{name}_{seat['seed']}_{seat['side']}.json"
    rec = json.loads(path.read_text())
    store = folder / rec["filename"]
    if seat != rec["seat"] or sha256(store.read_bytes()).hexdigest() != rec["sha256"]:
        raise ValueError("Observation source mismatch")
    with np.load(store, allow_pickle=False) as data:
        arrays = {k: data[k] for k in data.files if k != "commands"}
    team = int(seat["side"][-1])
    init = inspect.signature(Belief).parameters
    belief = Belief(team, **{k: v for k, v in flags.items() if k in init})
    for k, v in flags.items():
        if k not in init and k != "mirrored":
            setattr(belief, k, v)
    belief.sensor_range = seat["sensor"]
    metrics = []
    for i in range(303):
        obs = public_obs(arrays, i)
        t = int(obs["match_steps"])
        if int(obs["steps"]) != i or t != i % 101:
            raise ValueError("Observation chronology mismatch")
        belief.observe(obs)
        if t not in (10, 25, 50, 75, 100):
            continue
        pos = obs["units"]["position"][team]
        if belief.mirrored:
            pos = mirror_positions(pos)
        live = obs["units_mask"][team] & (obs["units"]["energy"][team] >= 0)
        occupied = {tuple(xy) for xy in pos[live]}
        on_points = sum(1 for x, y in occupied if belief.point_tiles[x, y])
        own, opp = (int(obs["team_points"][k]) for k in (team, 1-team))
        metrics.append(dict(match=i // 101 + 1, turn=t, points=own, enemy_points=opp, margin=own-opp,
                            known=int(belief.point_tiles.sum()), occupied=on_points,
                            seen_ever=int(belief.explored_ever.sum()), relics=len(belief.relic_positions)))
    return metrics


def run(folder, output):
    name, expected = PACKAGES["v16"]
    release = ROOT / "experiments/releases" / name / "agent.zip"
    if sha256(release.read_bytes()).hexdigest() != expected:
        raise ValueError("Unexpected reference package")
    sys.path.insert(0, str(release))
    raw_flags = HERE.parent / "solution/frueh/wissenssprung.json.gz"
    flags = json.loads(gzip.decompress(raw_flags.read_bytes()))["v16"]["7261020"]["flags"]
    result = []
    bins = defaultdict(lambda: defaultdict(list))
    for seat in sample():
        r, v = (summarize(folder, arm, seat, flags) for arm in ("r3", "v16"))
        result.append(dict(seed=seat["seed"], side=seat["side"], group=seat["group"], r3=r, v16=v))
        for first, second in zip(r, v, strict=True):
            for metric in ("margin", "points", "enemy_points", "known", "occupied", "seen_ever", "relics"):
                key = (seat["group"], first["match"], first["turn"], metric)
                bins[key][seat["seed"]].append(first[metric] - second[metric])
    summary = []
    for (group, match, turn, metric), by_map in sorted(bins.items()):
        averages = np.asarray([np.mean(g) for g in by_map.values()])
        summary.append(dict(group=group, match=match, turn=turn, metric=metric, maps=len(averages),
                            seats=sum(map(len, by_map.values())), mean_r3_minus_v16=float(averages.mean()),
                            maps_positive=int((averages > 0).sum()), maps_negative=int((averages < 0).sum())))
    report = dict(seats=46, actual_games=92, summary=summary, per_seat=result)
    target = output / "verlauf.json.gz"
    target.write_bytes(gzip.compress((json.dumps(report, separators=(",", ":")) + "\n").encode(), mtime=0))
    print("92 complete archived courses; public snapshots checked for all 46 seat pairs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    run(args.folder, args.output)
