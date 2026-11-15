"""Recount historical public board observations and separately check final truth on Solution traces."""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent / "combat_advice_20261115"
TRACES = HERE.parent / "continuation_20261102/targeting"
DEFAULT_DATA = HERE.parents[1] / "imitation/final_20261115_v14_advice"
OPPONENTS = ("kaggle3", "solution92")
SEEDS = range(7271000, 7271040)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def neighbors(cells):
    """Orthogonal neighbors, no wrapping. Array order is board, x, y."""
    result = np.zeros_like(cells)
    result[:, 1:] |= cells[:, :-1]
    result[:, :-1] |= cells[:, 1:]
    result[:, :, 1:] |= cells[:, :, :-1]
    result[:, :, :-1] |= cells[:, :, 1:]
    return result


def increment(counter, name, history, eligible, outcome):
    for label, group in (("seen", history), ("unseen", ~history)):
        selected = eligible & group
        counter[name, label, "total"] += int(selected.sum())
        counter[name, label, "yes"] += int((selected & outcome).sum())


def first_score(steps, features):
    """The first score after 0:0 can gain at most 16 points per team in one turn."""
    for step, row in zip(steps, features):
        own = int(round(float(row[10]) * 200))
        difference = float(row[11])
        if own or difference:
            require(np.array_equal(steps[:step], np.arange(1, step+1)), "Gap before the first score")
            require(own <= 16 and abs(difference) < 0.9, "First score features saturated")
            enemy = own - int(round(20 * np.arctanh(difference)))
            require(0 <= enemy <= 16, "Invalid first enemy score")
            return "both" if own and enemy else ("v14" if own else "opponent")
    raise ValueError("Missing first score")


def count_npz(path, metadata, counter):
    with np.load(path, allow_pickle=False) as data:
        require(json.loads(data["meta"].item()) == metadata, f"Archive metadata mismatch: {path.name}")
        steps = data["global_step"].astype(int)
        planes = data["planes"]
        frame_index = data["step"]
        require(len(steps) == len(planes) and np.all(np.diff(steps) > 0), "Unordered boards")
        require(np.all((0 < steps) & (steps < 303) & (steps % 101 != 0)), "Invalid decision steps")
        require(np.all(np.diff(frame_index) >= 0), "Unordered unit rows")
        require(np.array_equal(steps[frame_index] % 101, data["mstep"]), "Unit/board clocks disagree")
        require(np.array_equal(np.unique(frame_index), np.arange(len(steps))), "Missing board rows")
        # All unit rows on a board share the public team scores. Read one row per board.
        features = data["feats"][np.searchsorted(frame_index, np.arange(len(steps)))]
    counter["boards"] += len(steps)
    t = np.arange(2, len(steps)-1)
    t = t[(steps[t+1] - steps[t-2] == 3) & (steps[t+1]//101 == steps[t-2]//101)]
    counter["windows"] += len(t)
    present = planes[:, 10] > 0
    known_point = planes[t, 0] > 0
    current_single = known_point & (planes[t, 10] == 32)  # round(127 * 1/4)
    next_seen = present[t+1]
    increment(counter, "singleton", present[t-1], current_single, next_seen)
    adjacent = known_point & ~present[t] & neighbors(present[t])
    increment(counter, "empty_neighbor", present[t-2] | present[t-1], adjacent, next_seen)

    first = first_score(steps[steps < 101], features[steps < 101])
    m1_wins = int(round(float(features[steps//101 == 1][0, 12]) * 3))
    counter["first", first, "games"] += 1
    counter["first", first, "match1_wins"] += m1_wins
    counter["first", first, "game_wins"] += int(metadata["our_wins"] > metadata["opp_wins"])


def summarize(grouped, name):
    """Pool cell counts, but count the sign only once per underlying seed."""
    combined = sum(grouped.values(), Counter())
    result = {}
    for label in ("seen", "unseen"):
        result[label] = {k: combined[name, label, k] for k in ("yes", "total")}
    eligible = [c for c in grouped.values() if c[name, "seen", "total"] and c[name, "unseen", "total"]]
    result["comparable_maps"] = len(eligible)
    result["positive_maps"] = sum(
        c[name, "seen", "yes"] * c[name, "unseen", "total"] >
        c[name, "unseen", "yes"] * c[name, "seen", "total"] for c in eligible)
    return result


def read_advice(data_dir, hashes):
    protocol = json.loads((STUDY / "data_protocol.json").read_text())
    require(sha(data_dir/"protocol.json") == hashes["data_protocol.json"], "Wrong data protocol")
    audit = json.loads((STUDY / "v14_advice_audit.json").read_text())["map_sides"]
    expected = {(seed, f"player_{side}") for seed in SEEDS for side in (0, 1)}
    groups = {opponent: defaultdict(Counter) for opponent in OPPONENTS}
    for item in audit:
        meta = item["metadata"]
        seed, side, opponent = meta["seed"], meta["side"], meta["opponent"]
        key = seed, side
        require(key in expected, "Unexpected or duplicate archive key")
        expected.remove(key)
        require(opponent == protocol["rotation"][(seed-protocol["rotation_origin"]) % 3], "Wrong opponent")
        require(meta["protocol_sha256"] == hashes["data_protocol.json"] and meta["steps"] == 303, "Wrong game binding")
        path = data_dir / f"g{seed}_{side}_{opponent}.npz"
        require(sha(path) == item["input_sha256"], f"Wrong archive bytes: {path.name}")
        if opponent in groups:
            count_npz(path, meta, groups[opponent][seed])
    require(not expected, "Incomplete 40-map collection")
    result = {}
    for opponent, maps in groups.items():
        pooled = sum(maps.values(), Counter())
        result[opponent] = {
            "maps": len(maps), "games": len(maps)*2, "boards": pooled["boards"], "windows": pooled["windows"],
            "occupied_singleton": summarize(maps, "singleton"),
            "empty_adjacent": summarize(maps, "empty_neighbor"),
            "first_score": {who: {k: pooled["first", who, k] for k in ("games", "match1_wins", "game_wins")}
                            for who in ("v14", "opponent", "both")},
        }
    return result


def read_truth():
    manifest = json.loads((TRACES/"manifest.json").read_text())
    maps = defaultdict(Counter)
    games = manifest["games"]
    require(manifest["status"] == "complete" and len(games) == 12, "Incomplete historical manifest")
    for game in games:
        key = game["key"]
        seed, side = key["seed"], key["side"]
        path = TRACES / game["trace"]["path"]
        require(game["complete"] and sha(path) == game["trace"]["sha256"], f"Wrong trace: {path.name}")
        counter = maps[seed]
        previous = None
        frames = 0
        with gzip.open(path, "rt") as lines:
            for i, line in enumerate(lines):
                frame = json.loads(line)
                clock, public = frame["key"], frame.get("public")
                require((clock["seed"], clock["side"], clock["obs_step"]) == (seed, side, i), "Wrong trace order")
                frames += 1
                if frame["status"] != "decision" or not public or not 1 <= clock["match_step"] <= 99:
                    previous = None
                    continue
                current = Counter(map(tuple, public["enemy_coords"]))
                if previous is not None:
                    before, old_sensor = previous
                    # The agent's prediction uses public only. The post-step state supplies the label.
                    after = frame["posthoc"]["after"]
                    team = 1-int(side[-1])
                    active = {tuple(pos) for pos, energy, valid in zip(
                        after["positions"][team], after["energy"][team], after["unit_mask"][team])
                        if valid and energy >= 0}
                    for (x, y), count in current.items():
                        if count == 1 and public["point_tiles"][x][y] and old_sensor[x][y]:
                            group = "seen" if (x, y) in before else "unseen"
                            counter["truth", group, "total"] += 1
                            counter["truth", group, "yes"] += int((x, y) in active)
                previous = current, public["sensor_mask"]
        require(frames == 303, "Incomplete historical game")
    return dict(games=len(games), maps=len(maps), occupied_singleton=summarize(maps, "truth"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="Directory of the original 80 V14 NPZ archives")
    args = parser.parse_args()
    sources = (STUDY/"data_protocol.json", STUDY/"v14_advice_audit.json", TRACES/"manifest.json")
    hashes = {p.name: sha(p) for p in sources}
    report = dict(source_sha256=hashes, checked_npz=80, public_next_seen=read_advice(args.data, hashes),
                  true_next_active_solution=read_truth())
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
