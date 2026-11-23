"""Paired opening outcomes and map bootstrap, without using the active game screen."""
import gzip
from hashlib import sha256
import json

import numpy as np

from routes import HERE


def paired():
    with gzip.open(HERE / "eroeffnungen.jsonl.gz", "rt") as f:
        rows = [json.loads(line) for line in f]
    lookup = {(r["seed"], r["side"], r["arm"]): r for r in rows}
    seeds = sorted({r["seed"] for r in rows})
    if len(seeds) != 32 or len(rows) != len(lookup) or len(rows) != 128:
        raise ValueError("Incomplete paired openings")
    def measures(r):
        return np.array([r["first"], r["first_credit"], r["after_70"][0] - r["after_70"][1],
                         r["final"][0] - r["final"][1], r["won"]])
    original, learned = (np.asarray([[measures(lookup[s, t, a]) for t in (0, 1)] for s in seeds], float)
                         for a in ("original", "learned"))
    delta = (learned - original).mean(1)
    rng = np.random.default_rng(231123)
    boot = delta[rng.integers(len(seeds), size=(8000, len(seeds)))].mean(1)
    val = {}
    for k, key in enumerate(("first_sight", "first_credit", "score_margin70", "final_margin", "opening_win")):
        val[key] = dict(original=original[..., k].mean(), learned=learned[..., k].mean(),
                        difference=delta[:, k].mean(), ci95=np.percentile(boot[:, k], (2.5, 97.5)).tolist(),
                        less=int((learned[..., k] < original[..., k]).sum()),
                        equal=int((learned[..., k] == original[..., k]).sum()),
                        greater=int((learned[..., k] > original[..., k]).sum()))
    candidates = [r for r in rows if r["arm"] == "learned"]
    changes = sum(r["changes"] for r in candidates)
    if any(r["commands"] != 101 * 16 or r["range"] != 1 for r in rows) or any(
            len(r["events"]) != r["changes"] or len({e[1] for e in r["events"]}) > 1 for r in candidates):
        raise ValueError("Bad activity count")
    result = dict(maps=len(seeds), openings=len(rows), opening_turns=101*len(rows),
                  opened_seats=len(candidates), first_to_101_if_missing=True,
                  interventions=changes, affected_seats=sum(r["changes"] > 0 for r in candidates),
                  affected_maps=sum(bool(lookup[s, 0, "learned"]["changes"] or lookup[s, 1, "learned"]["changes"])
                                    for s in seeds),
                  candidate_wins=int(learned[..., -1].sum()), original_wins=int(original[..., -1].sum()),
                  metrics=val, raw_sha256=sha256((HERE / "eroeffnungen.jsonl.gz").read_bytes()).hexdigest())
    (HERE / "eroeffnung_ergebnis.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    paired()
