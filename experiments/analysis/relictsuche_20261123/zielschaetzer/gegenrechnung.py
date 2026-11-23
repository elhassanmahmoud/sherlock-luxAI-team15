"""Recount immutable prefix rows and check public negative-evidence algebra by explicit enumeration."""
from collections import defaultdict
import gzip
import hashlib
import json

import numpy as np

from kandidat import COORD, HERE, PACKAGE, Evidence


def check_formula():
    e = Evidence()
    rng = np.random.default_rng(2311)
    for turn in range(1, 65):
        sensor = rng.random((24, 24)) < .004
        pos = rng.integers(0, 24, (2, 4, 2))
        obs = {"sensor_mask": sensor, "units_mask": np.ones((2, 4), bool),
               "units": {"position": pos, "energy": np.full((2, 4), 50)}}
        e.observe(turn, obs, 0)
    actual = e.density(41, 6)
    for i, (cx, cy) in enumerate(COORD.tolist()):
        total = 0.
        for spawn in range(1, 48):
            if spawn <= e.seen[cx, cy]:
                continue
            inactive = 0
            for x in range(max(0, cx-2), min(24, cx+3)):
                for y in range(max(0, cy-2), min(24, cy+3)):
                    inactive += int(max(e.occupied[x, y], e.occupied[23-y, 23-x]) >= spawn)
            total += (1.-e.point_rate)**inactive
        if not np.isclose(total/50, actual[i]):
            raise ValueError("Failed explicit posterior enumeration")
    return len(actual)


def main():
    r = json.loads((HERE/"sichtpruefung.json").read_bytes())
    for file, expected in r["sources"].items():
        p = PACKAGE if file == "agent.zip" else HERE/file
        assert hashlib.sha256(p.read_bytes()).hexdigest() == expected
    with gzip.open(HERE/"beobachtungen.jsonl.gz", "rt") as f:
        rows = [json.loads(line) for line in f]
    assert len(rows) == len({(row["seed"], row["side"]) for row in rows}) == 64
    assert all({v["side"] for v in rows if v["seed"] == seed} == {"player_0", "player_1"} for seed in {v["seed"] for v in rows})
    for key, value in r["totals"].items():
        assert sum(row[key] for row in rows) == value
    per_map = defaultdict(list)
    for row in rows:
        for snap in row["snapshots"]:
            assert snap["step"] < min(row["first_seen"] or 101, row["first_point"] or 101)
            per_map[row["seed"]].append(snap["scores"])
    all_snaps = [s for v in per_map.values() for s in v]
    for arm, metrics in r["quality"].items():
        for stat, v in metrics.items():
            assert np.isclose(np.mean([s[arm][stat] for s in all_snaps]), v)
    # Resample both starts and all their nested timepoints together. A map with zero snapshots is retained.
    seeds = sorted({r["seed"] for r in rows})
    rng = np.random.default_rng(231123)
    sample = rng.integers(0, len(seeds), (20000, len(seeds)))
    count = np.array([len(per_map[i]) for i in seeds])
    deltas = {}
    for comparator in ("flat_visibility", "learned_visibility"):
        sums = np.array([sum(a["learned_full"]["logloss"]-a[comparator]["logloss"] for a in per_map[i]) for i in seeds])
        rep = sums[sample].sum(1)/count[sample].sum(1)
        deltas[comparator] = {"logloss_delta": float(sums.sum()/count.sum()),
                              "paired_map_ci95": np.percentile(rep, [2.5, 97.5]).tolist()}
    report = dict(seats=len(rows), snapshots=len(all_snaps), maps_with_snapshots=int((count > 0).sum()),
                  changed_maps=len({r["seed"] for r in rows if r["changes"]}),
                  paired_vs=deltas, enumeration_positions=check_formula())
    (HERE/"gegenrechnung.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
