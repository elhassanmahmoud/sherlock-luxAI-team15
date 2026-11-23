"""Measure how long the first field probe produces physical points, relative to V16 on the same map."""
import argparse
import gzip
import json
from pathlib import Path

import numpy as np

from experiments.analysis.relictsuche_20261123.feldbindung.beobachten import HERE, archive, identity, jobs
from experiments.analysis.relictsuche_20261123.vergleich.spielen import write_once


def first_when(trace, name):
    return next((i for i, tick in enumerate(trace) if tick[name]), None)


def score_event(seed, side, opponent, event, candidate, control):
    assert len(candidate) == len(control) == 101 - event["t"] % 101
    assert [r["t"] for r in candidate] == [r["t"] for r in control]
    uid = event["u"]
    initial = uid in candidate[0]["own_units"] and bool(candidate[0]["own_point"])
    assert initial == bool(event["scored"])
    follow = candidate[1] if len(candidate) > 1 else None
    leaves = bool(follow and follow["here"] and 1 <= follow["act"] <= 4)
    eligible = bool(initial and leaves and not follow["known"] and follow["energy"] >= 30
                    and follow["enemy_dist"] > follow["sap_range"])
    data = dict(seed=seed, side=side, opponent=opponent, start=event["t"], target=event["xy"],
                initial=initial, known_at=first_when(candidate, "known"),
                control_known_at=first_when(control, "known"), scout_leaving_next=leaves,
                eligible_to_hold=eligible, remaining=len(candidate), window={})
    for label, steps in (("1", 1), ("4", 4), ("12", 12), ("24", 24), ("end", len(candidate))):
        a, b = candidate[:steps], control[:steps]
        metrics = {key: sum(t[key] for t in a) - sum(t[key] for t in b)
                   for key in ("own_point", "other_point", "own_mirror", "other_mirror")}
        metrics["own_net"] = metrics["own_point"] + metrics["own_mirror"]
        metrics["score_net"] = metrics["own_net"] - metrics["other_point"] - metrics["other_mirror"]
        data["window"][label] = metrics
    data["scout_first4"] = bool(len(candidate) >= 4 and all(uid in q["own_units"] for q in candidate[:4]))
    data["replacement12"] = any(q["own_point"] and uid not in q["own_units"] for q in candidate[:12])
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    idx = archive()
    keys = jobs(idx)
    fingerprint = identity()
    archive_rows = {}
    for key in keys:
        row = json.loads((args.folder / "spiele" / ("_".join(map(str, key)) + ".json")).read_text())
        assert tuple(row["key"]) == key and row["source"] == fingerprint
        if key in idx:
            assert row["hash"] == idx[key]["hash"] and row["matches"] == idx[key]["matches"]
        archive_rows[key] = row
    cases = []
    for (s, t, arm, opp), row in sorted(archive_rows.items()):
        if arm != "probe":
            continue
        control = archive_rows[s, t if opp == "solution92" else 0, "reference", opp]
        cases.append(score_event(s, t, opp, idx[s, t, arm, opp]["event"],
                                 row["readings"][str(t)], control["readings"][str(t)]))
    assert len(cases) == 56 and len({(r["seed"], r["side"], r["opponent"]) for r in cases}) == 56
    all_seeds = sorted({k[0] for k in idx})
    assert len(all_seeds) == 48
    draws = np.random.default_rng(231123).integers(0, len(all_seeds), (20000, len(all_seeds)))
    result = {}
    for opp in ("solution92", "v16"):
        selected = [r for r in cases if r["opponent"] == opp]
        assert len(selected) == 28
        profile = {}
        for window in selected[0]["window"]:
            profile[window] = {}
            for feature in selected[0]["window"][window]:
                paired = np.array([sum(r["window"][window][feature] for r in selected if r["seed"] == s) / 2
                                   for s in all_seeds])
                profile[window][feature] = dict(total=int(2 * paired.sum()), per_seat=float(paired.mean()),
                               ci95=np.percentile(paired[draws].mean(1), [2.5, 97.5]).tolist())
        result[opp] = dict(initial=sum(r["initial"] for r in selected),
                           scorer_stayed_first_four=sum(r["scout_first4"] for r in selected if r["initial"]),
                           takeover_within_twelve=sum(r["replacement12"] for r in selected if r["initial"]),
                           eligible=sum(r["eligible_to_hold"] for r in selected),
                           affected_cards=len({r["seed"] for r in selected}), window=profile)
    eligible = sum(r["eligible_to_hold"] for r in cases)
    outcome = dict(verified_games=len(keys), cards=48, affected=56, source=fingerprint,
                   groups=result, eligible=eligible, holding_gate=eligible >= 8)
    write_once(HERE / "ergebnis.json", outcome)
    payload = "\n".join(json.dumps(r, separators=(",", ":")) for r in cases) + "\n"
    (HERE / "fenster.jsonl.gz").write_bytes(gzip.compress(payload.encode(), mtime=0))
    print(json.dumps(outcome, indent=2))


if __name__ == "__main__":
    main()
