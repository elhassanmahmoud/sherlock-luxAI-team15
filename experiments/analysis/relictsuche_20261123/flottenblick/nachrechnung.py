"""Recompute the held-out forecast contrast from recorded decisions, verify original labels and file identities."""
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RAW = Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/flottenblick")


def run():
    fitted = json.loads((HERE/"fit.json").read_text())
    valid = json.loads((HERE/"pruefung.json").read_text())
    if any(sha256((HERE/n).read_bytes()).hexdigest() != h for n,h in fitted["fit_sources"].items()):
        raise ValueError("Frozen training/ranking source differs")
    if sha256((HERE/"flottengewichte.npz").read_bytes()).hexdigest() != valid["weights_sha256"]:
        raise ValueError("Frozen CNN differs")
    logs = [json.loads(l) for l in gzip.decompress((HERE/"vorhersagen.jsonl.gz").read_bytes()).splitlines()]
    all_seeds = set()
    engine_checks = datasets = 0
    for split, meta in (("train",fitted),("valid",valid)):
        if any(sha256((HERE.parents[3]/p).read_bytes()).hexdigest() != h for p,h in meta["source"].items()):
            raise ValueError("A frozen source differs")
        n, checks = 0, 0
        for seed_s, expected in meta["maps_sha256"].items():
            seed = int(seed_s)
            p = RAW/split/f"{seed}.npz"
            if sha256(p.read_bytes()).hexdigest() != expected or seed in all_seeds:
                raise ValueError("Repeated or modified map")
            all_seeds.add(seed)
            datasets += 1
            with np.load(p,allow_pickle=False) as d:
                count, check = len(d["turn"]), int(d["checks"])
                power = d["remaining"]
                if power.shape != (count,8,24,24) or (count and check < 2):
                    raise ValueError("Incomplete ground-truth horizon")
                if np.any(np.any(power>0,axis=1) & ~d["full"]):
                    raise ValueError("A removed scout increased actual union visibility")
                n += count
                checks += check
        if n != meta["samples"] or checks != meta["engine_checks"]:
            raise ValueError("Sample or check count differs")
        engine_checks += checks
    ref = valid["reference"]
    by_map = {}
    for r in logs:
        diff = np.array(r["methods"][ref]["values"][0]) - r["methods"]["cnn"]["values"][0]
        by_map.setdefault(r["seed"],[]).append(float(diff))
    vector = np.array([np.mean(v) for v in by_map.values()])
    if len(vector) != valid["active_maps"] or len(logs) != valid["samples"]:
        raise ValueError("Different validation denominator")
    reported = valid["cnn_improvement"][ref]["near_brier"]
    delta = float(vector.mean())
    rng = np.random.default_rng(2311234)
    ci = np.percentile(vector[rng.integers(len(vector),size=(4000,len(vector)))].mean(1), (2.5,97.5))
    if abs(delta - reported["mean"]) > 1e-9 or not np.allclose(ci,reported["ci95"],atol=1e-9,rtol=0):
        raise ValueError("Different forecast effect")
    result = dict(verified_map_files=datasets, separate_seeds=len(all_seeds), engine_checks=engine_checks,
                  validated_forecast_records=len(logs), near_brier_gain=delta, ci95=ci.tolist())
    if (HERE/"spielprobe.json").exists():
        records = [json.loads(l) for l in gzip.decompress((HERE/"spielzuege.jsonl.gz").read_bytes()).splitlines()]
        live_sources = [HERE/n for n in ("AUSWERTUNGSPLAN.md","flotte.py","kandidat.py","vorhersage.py",
                                          "modell.json","flottengewichte.npz","spielprobe.py")]
        signature = sha256(b"".join(f.read_bytes() for f in live_sources)).hexdigest()
        if any(r["source"] != signature for r in records):
            raise ValueError("Changed real-game sources")
        lookup = {(r["seed"],r["team"],r["arm"]):r for r in records}
        real_maps = sorted({r["seed"] for r in records})
        if len(real_maps) != 64 or len(lookup) != 384 or all_seeds.intersection(real_maps):
            raise ValueError("Real sensor trial selection changed")
        gains = []
        for seed in real_maps:
            per_side = []
            for team in (0,1):
                arms = [lookup[seed,team,v] for v in ("original","simple","cnn")]
                if (len({a["prefix"] for a in arms}) != 1 or arms[0]["changes"]
                        or any(len({e[1] for e in a["changes"]}) > 1 for a in arms)):
                    raise ValueError("Real prefix or unit constraint differs")
                per_side.append(arms[2]["exclusive_pairs"]-arms[1]["exclusive_pairs"])
            gains.append(float(np.mean(per_side)))
        actual = float(np.mean(gains))
        measured = json.loads((HERE/"spielprobe.json").read_text())
        if actual != measured["cnn_gain"]["simple"]["exclusive_pairs"]["mean"]:
            raise ValueError("Different incremental real scout information")
        result.update(real_prefixes=len(records), real_pairs_gain=actual)
    (HERE/"nachrechnung.json").write_text(json.dumps(result,indent=2)+"\n")
    print(result)


if __name__ == "__main__":
    run()
