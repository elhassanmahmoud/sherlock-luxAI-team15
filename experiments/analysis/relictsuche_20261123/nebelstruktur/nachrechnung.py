"""Recompute first-relic timing from physical distance and audit propagation of learned edge weights."""
import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import torch
from scipy.signal import correlate2d
from scipy.special import expit
from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.flottenblick.vorhersage import load as fleet
from experiments.analysis.relictsuche_20261123.nebelstruktur.modell import HERE, inputs, load, predictions, route_scores
from experiments.analysis.relictsuche_20261123.ortundflotte.richtung import take
from experiments.analysis.relictsuche_20261123.zeitlicher_flottenblick.lernen import samples
from experiments.analysis.relictsuche_20261123.vergleich.spielen import sha
from scripts.experiment import limit_threads


def convolution(planes, weights):
    outs = []
    for kernel in weights:
        outs.append(sum(correlate2d(p, w, mode="same", boundary="fill") for p, w in zip(planes, kernel, strict=True)))
    return np.stack(outs)


def independently_predict(weights, point, surroundings):
    basic = np.einsum("oi,ixy->oxy", weights["point.0.weight"][:, :, 0, 0], point)
    basic = np.maximum(basic + weights["point.0.bias"][:, None, None], 0)
    basic = np.einsum("oi,ixy->oxy", weights["point.2.weight"][:, :, 0, 0], basic)
    basic += weights["point.2.bias"][:, None, None]
    first = weights["first.weight"].copy()
    first[:, :, 1, 1] = 0.
    near = np.maximum(0., convolution(surroundings, first))
    dilated = np.zeros((10, 10, 5, 5), np.float32)
    dilated[:, :, ::2, ::2] = weights["second.weight"]
    ring = np.maximum(0., convolution(near, dilated))
    change = np.einsum("oi,ixy->oxy", weights["horizon.weight"][:, :, 0, 0], ring)
    return expit(basic).reshape(8, 576), expit(basic+change).reshape(8, 576)


def describe(x):
    return {"mean": float(np.mean(x)), "median": float(np.median(x)), "p95": float(np.quantile(x, .95)),
            "max": float(np.max(x))}


def main(folder):
    limit_threads()
    torch.set_num_threads(1)
    rep = json.loads((HERE / "valid.json").read_bytes())
    arch = HERE / "valid_karten.jsonl.gz"
    assert sha(arch) == rep["archive_sha"]
    data = [json.loads(s) for s in gzip.decompress(arch.read_bytes()).splitlines()]
    vals = {r["seed"]: r["cases"] for r in data}
    normal, net = fleet(), load()
    with np.load(HERE / "gewichte.npz") as z:
        weights = dict(z)
    samples_total = maps = computed = changed = affected_scores = rank_changes = reties = 0
    errors = []
    max_raw = []
    max_played = []
    max_scores = []
    best_margins = []
    fractions = []
    gate_dist = []
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        for file in sorted((folder / "valid").glob("*.npz")):
            seed = int(file.stem)
            env.reset(seed=seed)
            maps += 1
            targets = np.asarray(env.state.relic_nodes)[[0, 3]]
            spawn = int(env.state.relic_spawn_schedule[0])
            cells = targets[:, 0]*24 + targets[:, 1]
            for source, recorded in zip(samples(file, normal), vals[seed], strict=True):
                q, _, rest, x, step, opts, last, _ = source
                assert cells.tolist() == recorded["target"] and step == recorded["t"] and spawn == recorded["spawn"]
                start = int(x[12].argmax())
                routes = np.vstack((opts, np.full((1, 8), start)))
                xy = np.stack(np.divmod(routes, 24), axis=-1)
                dist = np.abs(xy[:, :, None, :] - targets[None, None, :, :]).max(-1)
                gains = np.where(dist == 0, 12, np.where(dist == 1, 1, 0))
                visible = ((rest.reshape(8, 576)[:, cells] + gains) > 0).any(2)
                visible &= np.arange(step+1, step+9) > spawn
                delay = np.min(np.where(visible, np.arange(1, 9), 9), axis=1)
                assert recorded["sight"] == delay[recorded["picks"]].tolist() and recorded["oracle"] == delay.min()
                point, scenery, old = inputs(x, q, last, step)
                base, spatial = predictions(net, point, scenery)
                if samples_total % 29 == 0:
                    sc0, sc1 = independently_predict(weights, point, scenery)
                    errors.append(max(np.abs(sc0-base).max(), np.abs(sc1-spatial).max()))
                    assert errors[-1] < 4e-6
                    computed += 1
                old_weight = np.broadcast_to(np.where(x[18].ravel()>0, .25, 1.), (8, 576))
                correction = (spatial - base)*old.ravel()[None]
                adjusted = np.clip(old_weight+correction, 0, 1)
                max_raw.append(np.abs(correction).max())
                max_played.append(np.abs(adjusted-old_weight).max())
                fractions.append(float(np.mean(adjusted!=old_weight)))
                comparison = [route_scores(h, q, opts, last, x[18].astype(bool), x[19]*20, start)
                              for h in (old_weight, adjusted)]
                picks = [take(scores) for scores in comparison]
                assert picks == recorded["picks"]
                difference = np.abs(comparison[0]-comparison[1])
                max_scores.append(difference.max())
                affected_scores += difference.max() > 1.e-5
                rank_changes += comparison[0][:-1].argmax() != comparison[1][:-1].argmax()
                top = np.sort(comparison[0][:-1])
                best_margins.append(top[-1]-top[-2])
                reties += abs(top[-1]-top[-2]) < 1.e-7
                gate_dist.append(abs(top[-1] - comparison[0][-1] - 1.))
                changed += picks[0] != picks[1]
                samples_total += 1
    finally:
        env.close()
    assert maps == 160 and samples_total == rep["samples"] and changed == rep["changed"]
    result = {"engine_maps": maps, "physical_route_sets": samples_total, "scipy_model_checks": computed,
              "max_scipy_error": float(max(errors)), "sets_with_changed_route_scores": int(affected_scores),
              "best_moving_route_changed": int(rank_changes), "selected_changed": int(changed), "initial_ties": int(reties),
              "maximum_spatial_probability_change_by_set": describe(max_raw),
              "maximum_applied_weight_change_by_set": describe(max_played),
              "fraction_applied_whole_map": describe(fractions),
              "maximum_route_score_change_by_set": describe(max_scores),
              "original_two_best_moving_margin": describe(best_margins), "original_wait_gate_distance": describe(gate_dist),
              "archive_sha": rep["archive_sha"]}
    (HERE / "nachrechnung.json").write_text(json.dumps(result, indent=2)+"\n")
    print(result, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("folder", type=Path)
    main(ap.parse_args().folder)
