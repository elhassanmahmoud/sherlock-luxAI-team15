"""Attribute actual match-one scores to fields occupied before turn 71, separately per trajectory."""
import gzip
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def gains(game, team, start, stop):
    frames = game["frames"]
    history = [
        {tuple(xy) for frame in frames[:71] for xy in frame["fields"][side]}
        for side in (team, 1 - team)
    ]
    counts = np.zeros((2, 3), dtype=int)
    for frame in frames[start:stop + 1]:
        for side, actor in enumerate((team, 1 - team)):
            for field in map(tuple, frame["fields"][actor]):
                category = 0 if field in history[side] else 1 if field in history[1 - side] else 2
                counts[side, category] += 1
    actual = np.subtract(frames[stop]["points"], frames[start - 1]["points"])
    assert counts.sum(axis=1).tolist() == [actual[team], actual[1 - team]]
    return counts


def main():
    with gzip.open(HERE / "verlaeufe.jsonl.gz", "rt") as file:
        games = {(g["seed"], g["side"]): g for g in map(json.loads, file)}
    seeds = sorted({s for s, _ in games})
    assert len(games) == 120 and len(seeds) == 40
    draw = np.random.default_rng(231123).integers(0, 40, (20000, 40))

    def estimate(values):
        return dict(mean=round(float(values.mean()), 4),
                    ci95=np.round(np.percentile(values[draw].mean(axis=1), [2.5, 97.5]), 4).tolist())

    result = {}
    for start, stop in ((71, 100), (71, 80), (81, 90), (91, 100)):
        # Pair both seats on their original map before resampling.
        by_map = np.array([np.mean([
            gains(games[s, t], t, start, stop) - gains(games[s, -1], t, start, stop)
            for t in (0, 1)], axis=0) for s in seeds])
        own, rival = by_map[:, 0], by_map[:, 1]
        net = own - rival
        result[f"{start}-{stop}"] = dict(
            own=estimate(own.sum(axis=1)), rival=estimate(rival.sum(axis=1)),
            net=estimate(net.sum(axis=1)), own_prior=estimate(net[:, 0]),
            rival_prior_only=estimate(net[:, 1]), new=estimate(net[:, 2]))
    (HERE / "schlussphase.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
