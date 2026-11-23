"""Fixed course seeds, selected using only the public sensor range."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PANELS = {"discovery": (161200000, 40), "confirm": (161210000, 120), "general": (161220000, 160)}
TECHNICAL = [160394000, 160394018]


def sensor(seed):
    import jax
    import jax.numpy as jnp
    from luxai_s3.params import env_params_ranges

    key, _ = jax.random.split(jax.random.key(seed))
    for field, values in env_params_ranges.items():
        key, sub = jax.random.split(key)
        if field == "unit_sensor_range":
            return jax.random.choice(sub, jnp.asarray(values))
    raise ValueError("Missing public sensor range")


def build():
    import jax
    import numpy as np

    result = {"technical": TECHNICAL}
    for phase, (start, size) in PANELS.items():
        if phase == "general":
            result[phase] = list(range(start, start + size))
            continue
        raw = np.arange(start, start + 1000, dtype=np.int32)
        ranges = np.asarray(jax.jit(jax.vmap(sensor))(raw))
        chosen = raw[ranges == 1][:size].tolist()
        if len(chosen) != size:
            raise ValueError("Insufficient low-vision maps")
        result[phase] = chosen
    union = [seed for panel in result.values() for seed in panel]
    if len(union) != len(set(union)):
        raise ValueError("Panel overlap")
    return result


if __name__ == "__main__":
    output = HERE / "karten.json"
    panels = build()
    if output.exists() and json.loads(output.read_text()) != panels:
        raise ValueError("Frozen map panel changed")
    output.write_text(json.dumps(panels, indent=2) + "\n")
