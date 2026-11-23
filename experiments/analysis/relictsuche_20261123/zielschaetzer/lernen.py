"""Estimate first-pair and scoring-cell probabilities from independent official map resets."""
from hashlib import sha256
import inspect
import json
from pathlib import Path

import jax
import jax.numpy as jnp
import numpy as np
from luxai_s3 import state, wrappers
from luxai_s3.params import EnvParams

HERE = Path(__file__).resolve().parent
TRAIN = (161100000, 49152)
VALID = (161150000, 8192)
COORD = np.asarray([(x, y) for x in range(24) for y in range(24) if x+y < 24])
LOOKUP = np.empty((24, 24), np.int16)
LOOKUP[tuple(COORD.T)] = np.arange(len(COORD))
LOOKUP[tuple((23-COORD[:, ::-1]).T)] = np.arange(len(COORD))


def labels(seed):
    _, reset_key = jax.random.split(jax.random.key(seed))
    m = state.gen_map(reset_key, EnvParams(), 1, 24, 24, 6, 6, 5)
    return m["relic_nodes"][0], m["relic_nodes"][3], m["relic_node_configs"][0].sum(), m["relic_spawn_schedule"][0]


def collect(seed, count):
    batch = jax.jit(jax.vmap(labels))
    pos, density = [], []
    for start in range(seed, seed+count, 256):
        p, q, d, s = [np.asarray(a) for a in batch(jnp.arange(start, start+256, dtype=jnp.int32))]
        if not np.array_equal(q, 23-p[:, ::-1]) or not np.all((s >= 0) & (s < 50)):
            raise ValueError("Unexpected first-pair geometry or activation")
        pos.append(LOOKUP[p[:, 0], p[:, 1]])
        density.append(d)
    return np.concatenate(pos), np.concatenate(density)


def verify_labels():
    env = wrappers.LuxAIS3GymEnv(numpy_output=True)
    verified = []
    try:
        for seed in (TRAIN[0], TRAIN[0]+471, VALID[0], VALID[0]+274):
            env.reset(seed=seed)
            exact = labels(seed)
            arrays = (env.state.relic_nodes[0], env.state.relic_nodes[3], env.state.relic_node_configs[0].sum(),
                      env.state.relic_spawn_schedule[0])
            if not all(np.array_equal(a, b) for a, b in zip(exact, arrays)):
                raise ValueError("Generator labels differ from official reset")
            verified.append(seed)
    finally:
        env.close()
    return verified


def quality(p, labels):
    high = (p[:, None] > p).sum(0)
    equal = (p[:, None] == p).sum(0)
    credit = np.clip((75-high)/equal, 0., 1.)
    return {"logloss": float(-np.log(p[labels]).mean()), "top_quarter": float(credit[labels].mean())}


def main():
    resets = verify_labels()
    train, scored = collect(*TRAIN)
    counts = np.bincount(train, minlength=300)
    test, _ = collect(*VALID)
    prob = (counts+.5)/(len(train)+150.)
    uniform = np.where(COORD.sum(1) == 23, 1., 2.)/576
    qa = {name: quality(v, test) for name, v in (("learned", prob), ("flat_cell", uniform))}
    eligible = qa["learned"]["logloss"] < qa["flat_cell"]["logloss"] and qa["learned"]["top_quarter"] > qa["flat_cell"]["top_quarter"]
    result = dict(train=TRAIN, valid=VALID, reset_agreement=resets, counts=counts.tolist(),
                  point_bit_density=float(scored.sum()/(25*len(train))), quality=qa, eligible=eligible,
                  sha256={p.name: sha256(p.read_bytes()).hexdigest() for p in (
                      Path(inspect.getfile(state)), Path(inspect.getfile(wrappers)), Path(__file__), HERE/"PLAN.md")})
    (HERE/"ort.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({k: result[k] for k in ("quality", "eligible", "point_bit_density")}), flush=True)


if __name__ == "__main__":
    main()
