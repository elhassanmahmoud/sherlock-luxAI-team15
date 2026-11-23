"""Independent whole-game evaluation of the trained two-network veto on 64 new low-vision maps."""
import argparse
from datetime import datetime
import gzip
import json
import os
from pathlib import Path
import sys

import numpy as np

from experiments.analysis.relictsuche_20261123.netzvertrauen.erheben import HERE, frozen
from experiments.analysis.relictsuche_20261123.netzvertrauen.kandidat import create
from experiments.analysis.relictsuche_20261123.netzvertrauen.lernen import utility
from experiments.analysis.relictsuche_20261123.vergleich.panel import sensor
from experiments.analysis.relictsuche_20261123.vergleich.spielen import CUTOFF, THREADS, play, sha, stamp, validate, write_once
from scripts.experiment import limit_threads

sys.path.insert(0, str(HERE.parent / "spielwert"))
from pruefspiele import dual


def schedule():
    import jax
    pool = np.arange(162960000, 162961024, dtype=np.int32)
    seeds = list(map(int, pool[np.asarray(jax.jit(jax.vmap(sensor))(pool)) == 1][:64]))
    assert len(set(seeds)) == 64
    return [(s, t, arm, opp) for s in seeds for t, arm, opp in
            [(-1, "self", "v16"), *((side, a, o) for side in (0, 1) for a, o in
              (("reference", "solution92"), ("select", "solution92"), ("select", "v16")))]]


def evaluate(rows):
    seeds = sorted({k[0] for k in rows})
    sample = np.random.default_rng(231123).integers(0, len(seeds), (20000, len(seeds)))
    def estimate(v):
        return dict(mean=float(v.mean()), ci95=np.percentile(v[sample].mean(1), [2.5, 97.5]).tolist())
    opponents = {}
    combined = []
    for opp in ("solution92", "v16"):
        maps = []
        accepted = denied = 0
        for s in seeds:
            seats = []
            for t in (0, 1):
                b, a = [rows[s, t, arm, opp] for arm in ("reference", "select")]
                if a["decision"] is True:
                    accepted += 1
                    assert a["events"] and a["events"][0][0] == a["first_proposal"]
                    assert len({e[1] for e in a["events"]}) == 1
                else:
                    denied += a["decision"] is False
                    assert not a["events"] and a["action_hash"] == b["action_hash"]
                seats.append((a["win"], b["win"], b["sight"] - a["sight"],
                              b["credit"] - a["credit"], utility(a, b)))
            maps.append(np.mean(seats, axis=0))
        v = np.array(maps)
        combined.append(v)
        opponents[opp] = dict(wins=int(v[:, 0].sum()*2), base_wins=int(v[:, 1].sum()*2),
                              accepted=accepted, vetoed=denied,
                              gain=estimate(v[:, 0]-v[:, 1]), win=estimate(v[:, 0]),
                              sight=estimate(v[:, 2]), credit=estimate(v[:, 3]), utility=estimate(v[:, 4]))
    equal = np.mean(combined, axis=0)
    external, direct = (opponents[n] for n in ("solution92", "v16"))
    gates = dict(solution=external["wins"] >= external["base_wins"], direct=direct["wins"] >= 64,
                 earlier=bool(equal[:, 2].mean() > 0), utility=bool(equal[:, 4].mean() > 0))
    return dict(cards=len(seeds), games=len(seeds)*7, groups=opponents, sight=estimate(equal[:, 2]),
                utility=estimate(equal[:, 4]), gates=gates, passed=all(gates.values()))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder", type=Path)
    p.add_argument("stage", choices=("play", "score"))
    p.add_argument("lane", type=int, nargs="?", default=0)
    p.add_argument("stride", type=int, nargs="?", default=1)
    a = p.parse_args()
    gate = json.loads((HERE / "ergebnis.json").read_text())
    assert gate["passed"] and gate["model_sha"] == sha(HERE / "modell.json")
    tech = json.loads((HERE / "technik.json").read_text())
    assert len(tech) == 8 and all(r["turns"] == 303 for r in tech)
    assert 0 <= a.lane < a.stride and os.getenv("PYTHONHASHSEED") == "0" and all(os.getenv(k)=="1" for k in THREADS)
    files = [HERE / n for n in ("technik.json", "ergebnis.json", "modell.json", "lernen.py", "pruefen.py", "kandidat.py")]
    files.append(HERE.parent / "spielwert/pruefspiele.py")
    token = stamp(dict(study=frozen(), files={str(f.relative_to(HERE.parent)): sha(f) for f in files}))
    jobs = schedule()
    assert len(jobs) == len(set(jobs)) == 448
    def output(k):
        return a.folder / "frisch" / ("_".join(map(str, k))+".json")
    if a.stage == "play":
        from luxai_s3.wrappers import LuxAIS3GymEnv
        limit_threads()
        env = LuxAIS3GymEnv(numpy_output=True)
        try:
            for k in jobs[a.lane::a.stride]:
                if datetime.now(CUTOFF.tzinfo) >= CUTOFF:
                    break
                dest = output(k)
                if dest.exists():
                    assert json.loads(dest.read_text())["source"] == token
                    continue
                s, t, arm, opp = k
                if arm == "self":
                    row = dual(env, s, token)
                else:
                    actors = []
                    def factory(side):
                        agent = create(side)
                        actors.append(agent)
                        return agent
                    row = play(env, ("test", *k), token, factory if arm == "select" else None)
                    if actors:
                        row.update(decision=actors[0].decision, first_proposal=actors[0].at)
                write_once(dest, row)
        finally:
            env.close()
        return
    rows, packed = {}, []
    for k in jobs:
        data = json.loads(output(k).read_text())
        assert data["source"] == token
        packed.append(data)
        for r in data.get("views", [data]):
            key = (r["seed"], r["team"], r["id"], r["opponent"])
            validate(r, ("test", *key), token)
            assert key not in rows
            rows[key] = r
    assert len(rows) == 512
    result = evaluate(rows)
    write_once(HERE / "duelle.json", result)
    data = "\n".join(json.dumps(r, separators=(",", ":")) for r in packed)+"\n"
    (HERE / "duelle.jsonl.gz").write_bytes(gzip.compress(data.encode(), mtime=0))
    print(result)


if __name__ == "__main__":
    main()
