"""Reconstruct public game parameters and compare two fixed, archived paired panels."""
import json
from pathlib import Path
import sys

import jax
import jax.numpy as jnp
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "solution"))
from sitzvergleich import ANALYSIS, SOURCES, solution_rows
from luxai_s3.params import env_params_ranges
from luxai_s3.wrappers import LuxAIS3GymEnv

CUTS = {"unit_sensor_range": 2, "unit_move_cost": 2, "unit_sap_cost": 40, "unit_sap_range": 5}


def generate(seed):
    key, _ = jax.random.split(jax.random.key(seed))
    public = {}
    for field, choices in env_params_ranges.items():
        key, subkey = jax.random.split(key)
        if field in CUTS:
            public[field] = jax.random.choice(subkey, jnp.asarray(choices))
    return jnp.asarray([public[field] for field in CUTS])


def stats(maps):
    seats = 2 * len(maps)
    return dict(maps=len(maps), seats=seats, v16_losses=sum(r["v16_losses"] for r in maps),
                r3_losses=sum(r["r3_losses"] for r in maps), only_r3=sum(r["only_r3"] for r in maps),
                only_v16=sum(r["only_v16"] for r in maps))


def analyze(maps):
    groups = {}
    for field, cut in CUTS.items():
        low = [m for m in maps if m[field] <= cut]
        high = [m for m in maps if m[field] > cut]
        entry = {"low": stats(low), "high": stats(high), "cut": cut}
        if field == "unit_sensor_range":
            rng = np.random.default_rng(231123)
            samples = []
            means = []
            for group in (low, high):
                data = np.asarray([m["v16_losses"] / 2 for m in group])
                means.append(data.mean())
                samples.append(data[rng.integers(len(data), size=(10000, len(data)))].mean(1))
            entry["low_minus_high_pp"] = float(100 * (means[0] - means[1]))
            entry["ci95_pp"] = (100 * np.percentile(samples[0] - samples[1], [2.5, 97.5])).tolist()
        groups[field] = entry
    return groups


def run():
    maps = []
    for panel, (start, sources) in SOURCES.items():
        old = solution_rows(ANALYSIS / sources["r3"][0], sources["r3"][1], start)
        current = solution_rows(ANALYSIS / sources["v16"][0], sources["v16"][1], start)
        seeds = np.arange(start, start + 400, dtype=np.int32)
        parameters = np.asarray(jax.jit(jax.vmap(generate))(seeds))
        env = LuxAIS3GymEnv(numpy_output=True)
        try:
            for position in (0, 99, 200, 399):
                _, info = env.reset(seed=int(seeds[position]))
                assert [info["params"][key] for key in CUTS] == parameters[position].tolist()
        finally:
            env.close()
        for i, seed in enumerate(seeds.tolist()):
            pair = [(current[seed, side]["win"], old[seed, side]["win"]) for side in ("player_0", "player_1")]
            maps.append(dict(seed=seed, panel=panel, **dict(zip(CUTS, parameters[i].tolist(), strict=True)),
                             v16_losses=sum(1 - v for v, _ in pair), r3_losses=sum(1 - r for _, r in pair),
                             only_v16=pair.count((1, 0)), only_r3=pair.count((0, 1))))
    groups = {str(panel): analyze([m for m in maps if m["panel"] == panel]) for panel in SOURCES}
    groups["both"] = analyze(maps)
    delta = lambda key: groups[key]["unit_sensor_range"]["low_minus_high_pp"]
    report = dict(public_values_checked_with_real_resets=8, groups=groups, maps=maps,
                  supports_low_vision_focus=delta("3") > 0 and delta("5") > 0 and delta("both") >= 2)
    target = HERE / "ergebnis.json"
    target.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v["unit_sensor_range"] for k, v in groups.items()}, indent=2))


if __name__ == "__main__":
    run()
