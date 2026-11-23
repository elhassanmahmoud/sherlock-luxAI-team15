"""Evaluate one frozen spatial adjustment against the first active relic on the untouched 160 cards."""
import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import torch
from experiments.analysis.relictsuche_20261123.flottenblick.flotte import POWER
from experiments.analysis.relictsuche_20261123.flottenblick.vorhersage import arrays, load as fleet
from experiments.analysis.relictsuche_20261123.nebelstruktur.modell import (
    HEAD, HERE, inputs, load, predictions, route_scores,
)
from experiments.analysis.relictsuche_20261123.ortundflotte.richtung import score_options, take
from experiments.analysis.relictsuche_20261123.sensorpaare.modell import estimate, learned
from experiments.analysis.relictsuche_20261123.zeitlicher_flottenblick.lernen import samples
from experiments.analysis.relictsuche_20261123.vergleich.spielen import sha
from experiments.analysis.relictsuche_20261123.zielschaetzer.lernen import labels
from scripts.experiment import limit_threads


def actual(slots):
    import jax
    from luxai_s3.wrappers import LuxAIS3GymEnv
    result = {}
    batch = jax.jit(jax.vmap(labels))
    for seeds in np.array_split(np.asarray(slots, np.int32), 5):
        pos, mir, _, spawn = map(np.asarray, batch(seeds))
        for seed, a, b, tick in zip(seeds, pos, mir, spawn, strict=True):
            result[int(seed)] = ([int(p[0])*24 + int(p[1]) for p in (a, b)], int(tick))
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        for seed in (slots[0], slots[-1]):
            env.reset(seed=seed)
            targets = [int(p[0])*24+int(p[1]) for p in np.asarray(env.state.relic_nodes)[[0, 3]]]
            assert result[seed] == (targets, int(env.state.relic_spawn_schedule[0]))
    finally:
        env.close()
    return result


def calibrated(probs, mask, truth):
    return [float(np.mean((p[mask] - truth[mask])**2)) if mask.any() else None for p in probs]


def mean_map(rows, name):
    vals = [r[name] for r in rows if r[name][0] is not None]
    return np.mean(vals, axis=0).tolist() if vals else None


def case(q, rest, x, t, paths, last, targets, spawn, net, table):
    center, surrounds, old = inputs(x, q, last, t)
    p0, p1 = predictions(net, center, surrounds)
    fog = x[18].astype(bool)
    energy = x[19].astype(np.float32)*20
    start = int(x[12].argmax())
    old_edge = np.broadcast_to(np.where(fog.ravel(), .25, 1.), p0.shape)
    edge = np.clip(old_edge + (p1-p0)*old.ravel()[None], 0., 1.)
    reference = score_options(q, paths, last, fog, energy, start)[2]
    same = route_scores(old_edge, q, paths, last, fog, energy, start)
    assert np.allclose(reference, same, rtol=2e-5, atol=2e-5) and take(reference) == take(same)
    route_values = route_scores(edge, q, paths, last, fog, energy, start)
    picks = [take(reference), take(route_values)]
    routes = np.vstack((paths, np.full((1, 8), start, dtype=np.int16)))
    indices, inside = arrays(routes)
    reachable = np.zeros((8, 576), bool)
    ticks = np.broadcast_to(np.arange(8)[None, :, None], indices.shape)
    ok = inside & ~HEAD[None, None, :]
    reachable[ticks[ok], indices[ok]] = True
    r = rest.reshape(8, 576)
    eligible = reachable & old.ravel()[None] & (r <= 0)
    never = eligible & (last.ravel()[None] < 0)
    _, (_, tab) = estimate(q, last, fog, table)
    truth = r == 0
    probs = (old_edge, tab, p0, p1, edge)
    sight = ((r[:, targets] + POWER[routes[:, :, None], targets]) > 0).any(2)
    sight &= t + np.arange(1, 9) >= spawn+1
    times = np.where(sight.any(1), sight.argmax(1) + 1, 9)
    return {"t": t, "picks": picks, "sight": times[picks].tolist(), "routes": len(routes),
            "oracle": int(times.min()), "target": targets, "spawn": spawn,
            "edges": int(eligible.sum()), "never_edges": int(never.sum()),
            "brier": calibrated(probs, eligible, truth), "never_brier": calibrated(probs, never, truth),
            "attenuated": int((eligible & ~truth).sum()),
            "old_signal_magnitude": float(np.abs(p1[eligible]-p0[eligible]).mean()) if eligible.any() else None}


def main(folder):
    limit_threads()
    torch.set_num_threads(1)
    train = json.loads((HERE / "fit.json").read_bytes())
    assert train["weights"] == sha(HERE / "gewichte.npz")
    for file, digest in train["source"].items():
        assert sha(HERE.parent / file) == digest
    files = sorted((folder / "valid").glob("*.npz"))
    seeds = [int(f.stem) for f in files]
    assert len(seeds) == 160 and set(seeds).isdisjoint(int(f.stem) for f in (folder / "train").glob("*.npz"))
    source = HERE.parent / "ortundflotte/valid_karten.jsonl.gz"
    nominee = {r["seed"]:r["situations"] for r in
               [json.loads(line) for line in gzip.decompress(source.read_bytes()).splitlines()]}
    assert set(nominee) == set(seeds)
    locations = actual(seeds)
    original, net, table = fleet(), load(), learned()
    records = []
    for file in files:
        seed = int(file.stem)
        targets, spawn = locations[seed]
        observations = []
        for q, _, remaining, x, t, paths, last, _ in samples(file, original):
            out = case(q, remaining, x, t, paths, last, targets, spawn, net, table)
            observations.append(out)
        for old, new in zip(nominee[seed], observations, strict=True):
            assert [old["t"], old["picks"][2], old["sight"][2], old["oracle"]] == [
                new["t"], new["picks"][0], new["sight"][0], new["oracle"]]
        records.append({"seed": seed, "cases": observations})
    data = gzip.compress(b"".join((json.dumps(r, separators=(",", ":"))+"\n").encode() for r in records), mtime=0)
    (HERE / "valid_karten.jsonl.gz").write_bytes(data)
    sight = np.asarray([np.mean([v["sight"] for v in e["cases"]], axis=0) if e["cases"] else [0., 0.] for e in records])
    d = sight[:, 0] - sight[:, 1]
    rows = [v for e in records for v in e["cases"]]
    results = {}
    rng = np.random.default_rng(16496002)
    for key in ("brier", "never_brier"):
        values = [mean_map(e["cases"], key) for e in records]
        arr = np.asarray([l for l in values if l is not None])
        diff = arr[:, 2] - arr[:, 3]
        draws = rng.integers(len(diff), size=(20000, len(diff)))
        results[key] = {"maps": len(diff), "scores": arr.mean(0).tolist(),
                        "diff_central_spatial": float(diff.mean()),
                        "ci": np.quantile(diff[draws].mean(1), [.025, .975]).tolist()}
    draw = rng.integers(160, size=(20000, 160))
    gates = {"calibration":results["brier"]["diff_central_spatial"] > 0, "earlier":bool(d.mean()>0),
             "three_maps":int((d>0).sum())>=3, "ahead_of_losses":int((d>0).sum())>int((d<0).sum())}
    results.update(maps=160, samples=len(rows), nonempty_cards=sum(bool(x["cases"]) for x in records),
                   changed=sum(r["picks"][0]!=r["picks"][1] for r in rows),
                   changed_cards=sum(any(r["picks"][0]!=r["picks"][1] for r in x["cases"]) for x in records),
                   edges=sum(r["edges"] for r in rows), attenuated=sum(r["attenuated"] for r in rows),
                   never_edges=sum(r["never_edges"] for r in rows),
                   earlier=float(d.mean()), interval=np.quantile(d[draw].mean(1), [.025, .975]).tolist(),
                   advanced=int((d>0).sum()), delayed=int((d<0).sum()), gates=gates, passed=all(gates.values()),
                   weights=train["weights"], archive_sha=sha(HERE / "valid_karten.jsonl.gz"),
                   nominee_sha=sha(source), comparator_sha=sha(HERE.parent / "sensorpaare/tabellen.npz"))
    (HERE / "valid.json").write_text(json.dumps(results, indent=2)+"\n")
    print(results, flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder", type=Path)
    main(p.parse_args().folder)
