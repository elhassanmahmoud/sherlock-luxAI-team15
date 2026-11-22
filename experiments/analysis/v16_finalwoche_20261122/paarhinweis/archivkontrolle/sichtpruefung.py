"""Vergleicht die Archiveingabe des Belief mit der Original-Beobachtungsfunktion."""
from pathlib import Path
from types import SimpleNamespace
import gzip
import json

import jax.numpy as jnp
import numpy as np
from luxai_s3.env import LuxAIS3Env
from pruefen import SEEDS, SOURCES, project


def adapted_state(row):
    # Der Serializer speichert zunächst die aktiven Originale und dann ihre Spiegel.
    active = np.asarray(row["relic_nodes"], dtype=int).reshape(-1, 2)
    half = len(active) // 2
    positions = np.zeros((6, 2), dtype=int)
    mask = np.zeros(6, dtype=bool)
    for index in range(half):
        for offset, source in ((0, index), (3, index + half)):
            positions[index + offset] = active[source]
            mask[index + offset] = True
    def block(values):
        return SimpleNamespace(**{key: jnp.asarray(v) for key, v in values.items()})
    return SimpleNamespace(
        units=block(row["units"]), units_mask=jnp.array(row["units_mask"]),
        sensor_mask=jnp.array(row["vision_power_map"]) > 0,
        relic_nodes=jnp.asarray(positions), relic_nodes_mask=jnp.asarray(mask),
        map_features=block(row["map_features"]), team_points=jnp.array(row["team_points"]),
        team_wins=jnp.array(row["team_wins"]), steps=row["steps"], match_steps=row["match_steps"],
    )


def main():
    config = SimpleNamespace(fixed_env_params=SimpleNamespace(num_teams=2))
    checked = 0
    for seed in SEEDS:
        replay = json.loads(gzip.decompress((SOURCES / str(seed) / "episode.json.gz").read_bytes()))
        for step in (0, 149, 201):
            row = replay["observations"][step]
            reference = LuxAIS3Env.get_obs(config, adapted_state(row))
            for team in (0, 1):
                obs = reference[f"player_{team}"]
                for key, value in project(row, team).items():
                    if isinstance(value, dict):
                        for key2, value2 in value.items():
                            np.testing.assert_array_equal(value2, getattr(getattr(obs, key), key2))
                    else:
                        np.testing.assert_array_equal(value, getattr(obs, key))
                checked += 1
    print(f"{checked} öffentliche Sichten feldweise mit LuxAIS3Env.get_obs identisch")


if __name__ == "__main__":
    main()
