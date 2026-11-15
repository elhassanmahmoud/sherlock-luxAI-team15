"""Route whole games by one start-public parameter, chosen on the fixed 80-map partition.

From the Sherlock repo use its venv: python selector.py select . result_dir
Then run python selector.py confirm . result_dir. No step(), agent, model, or map generation.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from luxai_s3 import params, wrappers


ORDER = ("unit_move_cost", "unit_sap_cost", "unit_sap_range", "unit_sensor_range")
HALVES = ("low", "high")
PHASE = {"select": ("selection", 851000, 80), "confirm": ("confirmation", 852000, 400)}
BOOTSTRAP = 10000
RNG_SEED = 2711


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class SkipTerrain:
    def reset(self, key, params):
        return {}, None


def public_values(seeds):
    # Original parameter draw and public filtration, but no numerical terrain or episode initialization.
    env = wrappers.LuxAIS3GymEnv.__new__(wrappers.LuxAIS3GymEnv)
    env.numpy_output = False
    env.jax_env = SkipTerrain()
    values = []
    for seed in seeds:
        _, info = env.reset(seed=seed)
        values.append({k: int(info["params"][k]) for k in ORDER})
    return values


def read_pair(root, phase):
    label, first, n = PHASE[phase]
    folder = root / "experiments/analysis/final_battle_20261103" / ("performance_" + label) / label
    seeds = list(range(first, first + n))
    keys = [(s, f"player_{p}") for s in seeds for p in (0, 1)]
    datasets = {}
    hashes = {}
    for role in ("baseline", "FT18"):
        csv_path = folder / (role + "_panel.csv")
        outcomes = {}
        with csv_path.open() as stream:
            for row in csv.DictReader(stream):
                if row["opponent"] != "solution92":
                    continue
                key = int(row["seed"]), row["side"]
                game, matches, opposing = (int(row[k]) for k in ("game_win", "our_wins", "opp_wins"))
                if (key in outcomes or game != int(matches > opposing) or
                        matches + opposing != 3 or int(row["steps"]) != 303 or
                        int(row["point_counting_version"]) != 2):
                    raise ValueError(f"Invalid game {key} in {csv_path}")
                outcomes[key] = (game, matches)
        if set(outcomes) != set(keys):
            raise ValueError(f"Missing or extra seats in {csv_path}")
        datasets[role] = np.array([outcomes[key] for key in keys], np.int64).reshape(n, 2, 2)
        hashes[role] = sha(csv_path)
    return seeds, datasets, hashes


def score(datasets, take):
    v14 = datasets["baseline"]
    ft18 = datasets["FT18"]
    chosen = np.where(take[:, None, None], ft18, v14)
    delta = chosen - v14
    game_delta = delta[:, :, 0]
    match_delta = delta[:, :, 1]
    return {
        "ft_maps": int(take.sum()), "maps": len(v14), "seats": len(v14) * 2,
        "v14_game_wins": int(v14[:, :, 0].sum()), "ft18_game_wins": int(ft18[:, :, 0].sum()),
        "chosen_game_wins": int(chosen[:, :, 0].sum()), "delta_game_wins": int(game_delta.sum()),
        "new_seat_wins": int((game_delta > 0).sum()), "lost_seat_wins": int((game_delta < 0).sum()),
        "maps_more_seat_wins": int((game_delta.sum(1) > 0).sum()),
        "maps_fewer_seat_wins": int((game_delta.sum(1) < 0).sum()),
        "v14_match_wins": int(v14[:, :, 1].sum()), "chosen_match_wins": int(chosen[:, :, 1].sum()),
        "delta_match_wins": int(match_delta.sum()),
    }, game_delta, match_delta


def stats_for_rule(values, datasets, key, half, mid):
    low = np.array([row[key] <= mid for row in values])
    take = low if half == "low" else ~low
    summary, games, matches = score(datasets, take)
    return {"parameter": key, "half": half, "midpoint": mid, **summary}, games, matches


def paired_interval(deltas, scale):
    rng = np.random.default_rng(RNG_SEED)
    per_map = deltas.sum(axis=1)
    samples = []
    for _ in range(BOOTSTRAP // 100):
        draw = rng.integers(len(per_map), size=(100, len(per_map)))
        samples.extend(per_map[draw].mean(1) * scale)
    return np.quantile(samples, (0.025, 0.975)).tolist()


def exclusive_json(path, data):
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=PHASE)
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    selection_file = args.output / "selection.json"
    environment = {"wrapper_sha": sha(wrappers.__file__), "params_sha": sha(params.__file__),
                   "script_sha": sha(__file__)}
    if args.phase == "confirm":
        selected = json.loads(selection_file.read_text())
        if selected["environment"] != environment or not selected["chosen"]:
            raise SystemExit("No eligible rule recorded, or sources changed")
        chosen = selected["chosen"]
    seeds, datasets, hashes = read_pair(args.root, args.phase)
    values = public_values(seeds)
    common = {"environment": environment, "panel_sha": hashes, "first_seed": seeds[0], "last_seed": seeds[-1]}
    if args.phase == "select":
        ranked = []
        for key in ORDER:
            possible = tuple(params.env_params_ranges[key])
            mid = (min(possible) + max(possible)) / 2
            for half in HALVES:
                info, _, _ = stats_for_rule(values, datasets, key, half, mid)
                ranked.append(info)
        # max() keeps the first equal pair; ORDER and HALVES define the final tiebreak.
        top = max(ranked, key=lambda r: (r["delta_game_wins"], r["delta_match_wins"]))
        chosen = top if top["delta_game_wins"] > 0 else None
        exclusive_json(selection_file, {**common, "rules_in_protocol_order": ranked, "chosen": chosen})
        print("selected", json.dumps(chosen, sort_keys=True))
        return
    info, games, matches = stats_for_rule(values, datasets, chosen["parameter"], chosen["half"], chosen["midpoint"])
    details = {**common, "selection_file_sha": sha(selection_file), "rule": info,
               "bootstrap_maps": BOOTSTRAP, "rng": RNG_SEED,
               "delta_game_pp": 100 * games.mean(), "delta_game_pp_ci95": paired_interval(games, 50),
               "delta_match_pp": 100 * matches.mean() / 3, "delta_match_pp_ci95": paired_interval(matches, 100 / 6)}
    exclusive_json(args.output / "confirmation.json", details)
    print(json.dumps(details, sort_keys=True))


if __name__ == "__main__":
    main()
