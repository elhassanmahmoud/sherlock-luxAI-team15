"""Estimate the relationship between the first and second public-generator relic pairs."""
import argparse
from hashlib import sha256
import inspect
import json
from pathlib import Path

import jax
import jax.numpy as jnp
import numpy as np
from luxai_s3 import state

HERE = Path(__file__).resolve().parent
SIZE = 24
COORDS = np.array([(x, y) for x in range(SIZE) for y in range(SIZE) if x + y < SIZE], dtype=np.int16)
LOOKUP = np.empty(SIZE * SIZE, dtype=np.int16)
for idx, (x, y) in enumerate(COORDS):
    LOOKUP[x * SIZE + y] = idx
    LOOKUP[(23-y) * SIZE + 23-x] = idx


def pair(key):
    noise = state.generate_perlin_noise_2d(key, (24, 24), (4, 4))
    return jnp.argsort(noise.ravel())[-3:-1]


def sample(salt, count):
    key = jax.random.key(salt)
    @jax.jit
    def block(indices):
        keys = jax.vmap(lambda i: jax.random.fold_in(key, i))(indices)
        return jax.vmap(pair)(keys)
    output = []
    for start in range(0, count, 256):
        output.append(np.asarray(block(jnp.arange(start, start+256, dtype=jnp.int32))))
    return LOOKUP[np.concatenate(output)[:count]]


def estimate(train):
    n = len(COORDS)
    joint = np.zeros((n, n), np.int32)
    np.add.at(joint, (train[:, 0], train[:, 1]), 1)
    marginal = (joint.sum(0) + 0.5) / (len(train) + n/2)
    # Both members of a matched, mirrored pair need only one representative.
    opposite = 23 - COORDS[:, ::-1]
    dist = np.minimum(np.abs(COORDS[:, None] - COORDS).max(-1),
                      np.abs(COORDS[:, None] - opposite).max(-1))
    rings = np.bincount(dist[train[:, 0], train[:, 1]], minlength=int(dist.max())+1).astype(float) + 0.5
    ring_model = np.zeros((n, n))
    for i in range(n):
        for radius in np.unique(dist[i]):
            mask = dist[i] == radius
            ring_model[i, mask] = rings[radius] * marginal[mask] / marginal[mask].sum()
    ring_model /= ring_model.sum(1, keepdims=True)
    conditional = joint + 32 * marginal
    conditional /= conditional.sum(1, keepdims=True)
    return joint, dist, {"overall": np.broadcast_to(marginal, (n, n)), "distance": ring_model,
                         "conditional": conditional}


def assess(test, dist, models, far):
    retained = dist[test[:, 0],test[:, 1]] > 2 if far else np.ones(len(test), bool)
    ids = test[retained]
    measures = {}
    for name, probabilities in models.items():
        crossentropy = top10 = top25 = 0.0
        for i in np.unique(ids[:, 0]):
            actual = ids[ids[:, 0] == i, 1]
            possible = dist[i] > 2 if far else np.ones(len(COORDS), bool)
            p = probabilities[i] * possible
            p = p / p.sum()
            crossentropy -= np.log(p[actual]).sum()
            # Give equal-probability locations fractional credit when the cutoff splits ties.
            higher = ((p[:, None] > p) & possible[:, None]).sum(0)
            equal = ((p[:, None] == p) & possible[:, None]).sum(0)
            for fraction in (0.1, 0.25):
                k = int(np.ceil(possible.sum() * fraction))
                credit = np.clip((k - higher[actual]) / equal[actual], 0, 1).sum()
                if fraction == 0.1:
                    top10 += credit
                else:
                    top25 += credit
        measures[name] = {"logloss": float(crossentropy/len(ids)), "top10": float(top10/len(ids)),
                          "top25": float(top25/len(ids))}
    return dict(n=len(ids), measures=measures)


def run(out):
    train = sample(362013, 131072)
    test = sample(562017, 8192)
    counts, dist, models = estimate(train)
    complete = assess(test, dist, models, False)
    far = assess(test, dist, models, True)
    q = far["measures"]
    gate = (far["n"] >= 200 and q["conditional"]["logloss"] < min(q["overall"]["logloss"], q["distance"]["logloss"])
            and q["conditional"]["top25"] >= q["overall"]["top25"] + 0.03)
    np.savez_compressed(out / "paarhaeufigkeiten.npz", coords=COORDS, counts=counts)
    engine = Path(inspect.getfile(state))
    report = dict(engine_sha256=sha256(engine.read_bytes()).hexdigest(), training_fields=len(train),
                  test_fields=len(test), source="synthetic independent public-generator noise fields",
                  pairs=len(COORDS), complete=complete, outside_first_zone=far, qualifies_for_game_diagnosis=gate)
    (out / "ergebnis.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("out",type=Path)
    run(cli.parse_args().out)
