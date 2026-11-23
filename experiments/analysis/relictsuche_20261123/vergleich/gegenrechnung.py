"""Separate calculation from the portable archive, using no benchmark or scorer imports."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def verify(phase, directory):
    result = json.loads((directory / "ergebnis.json").read_text())
    provenance = json.loads((directory / "herkunft.json").read_text())
    rosters = json.loads((HERE / "karten.json").read_text())
    cards = rosters[phase]
    names = sorted(result["candidates"])
    archive = directory / "partien.jsonl.gz"
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == provenance["archive_sha256"]
    with gzip.open(archive, "rt") as f:
        rows = [json.loads(x) for x in f]
    key = lambda r: (r["seed"], r["team"], r["id"], r["opponent"])
    index = {key(r): r for r in rows}
    games = {(s, t, who, opp) for s in cards for t in (0, 1) for who in ["reference", *names]
             for opp in (("solution92",) if who == "reference" else ("solution92", "v16"))}
    assert len(index) == len(rows) == result["games"] == len(games) and set(index) == games
    assert len(set(cards)) == result["maps"]
    for r in rows:
        assert r["phase"] == phase and r["caught_errors"] == [0, 0] and r["steps"] == 303
        assert r["actions_checked"] == [303, 303] and r["point_counting_version"] == 2
        assert r["sensor"] == 1 or phase == "general"
        assert sum(m["win"] for m in r["matches"]) == r["wins"] and (r["wins"] > 1) == r["win"]
        assert [sum(m["points"][i] for m in r["matches"]) for i in range(2)] == r["points"]
        assert len({e[1] for e in r["events"]}) <= 1
        assert len({e[0] for e in r["events"]}) == len(r["events"])
        assert all(e[3] in range(1, 5) and e[2] in range(5) and e[2] != e[3] for e in r["events"])
        assert (r["credit"] == 101) == (not r["matches"][0]["points"][0])
        assert r["source"] == result["identities"][r["id"]]
    indices = np.random.Generator(np.random.PCG64(231123)).choice(len(cards), size=(20000, len(cards)), replace=True)

    def stats(card_values, reported):
        avg = np.mean(card_values)
        lo, hi = np.percentile(np.mean(np.take(card_values, indices), axis=1), [2.5, 97.5])
        assert np.allclose([avg, lo, hi], [reported["mean"], *reported["ci95"]], rtol=0, atol=1e-12)
        return float(avg), float(lo)

    def vector(r):
        m = r["matches"][0]
        a, b = r["after_70"]
        c, d = m["points"]
        return [-r["sight"], -r["credit"], a, b, a-b, c, d, c-d, m["win"], r["win"], r["wins"]]

    eligible = []
    checked = {}
    for name in names:
        state = result["candidates"][name]
        direct = [sum(index[s, t, name, "v16"]["win"] for t in (0, 1)) / 2 for s in cards]
        probability, direct_lo = stats(direct, state["direct_rate"])
        matrix = []
        seats = []
        for s in cards:
            seat_changes = []
            for t in (0, 1):
                b, a = index[s, t, "reference", "solution92"], index[s, t, name, "solution92"]
                if not a["events"]:
                    assert a["action_hash"] == b["action_hash"] and vector(a) == vector(b)
                seat_changes.append(np.subtract(vector(a), vector(b)))
            seats.extend(seat_changes)
            matrix.append(np.mean(seat_changes, axis=0))
        values = {}
        labels = "sight credit own70 opp70 margin70 match1points match1opp match1margin match1win whole all_match_wins".split()
        for j, field in enumerate(labels):
            values[field] = stats(np.array(matrix)[:, j], state["paired"][field])
            v = np.array(seats)[:, j]
            assert np.allclose(state["paired"][field]["by_seat"], [v[::2].mean(), v[1::2].mean()])
            assert [sum(v > 0), sum(v == 0), sum(v < 0)] == [state["paired"][field][f] for f in ("positive_seats", "equal_seats", "negative_seats")]
        for opp, title in (("v16", "direct"), ("solution92", "solution")):
            relevant = [r for r in rows if r["id"] == name and r["opponent"] == opp]
            for t in (0, 1, None):
                rr = [r for r in relevant if t is None or r["team"] == t]
                sub = state[title]["all"] if t is None else state[title]["by_seat"][str(t)]
                assert (sub["games"], sub["wins"], sub["match1wins"], sub["changes"], sub["changed_maps"]) == (
                    len(rr), sum(r["win"] for r in rr), sum(r["matches"][0]["win"] for r in rr),
                    sum(len(r["events"]) for r in rr), len({r["seed"] for r in rr if r["events"]}))
        if phase == "general":
            win_lo = values["whole"][1]
            qualified = (win_lo > 0 and probability >= .5 and direct_lo >= .45) or (direct_lo > .5 and win_lo >= -.01)
        else:
            qualified = values["sight"][0] >= 1 and all(values[k][0] >= 0 for k in ("credit", "margin70", "match1win", "whole"))
            if phase == "discovery":
                qualified &= probability >= .5 and state["solution"]["all"]["changed_maps"] >= 8
            else:
                qualified &= values["sight"][1] > 0
        assert bool(qualified) == state["passed"]
        if qualified:
            eligible.append((-values["sight"][0], -values["match1margin"][0], -state["solution"]["all"]["wins"], name))
        checked[name] = {"direct_wins": int(round(probability * 2 * len(cards))), "paired_outcomes": len(values),
                         "both_seats": True, "eligibility_reproduced": True}
    nominated = min(eligible)[-1] if eligible else None
    assert nominated == result["nominee"]
    print(json.dumps({"games": len(rows), "maps": len(cards), "nominee": nominated, "candidates": checked}, indent=2))
    return nominated


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("phase", choices=("discovery", "confirm", "general"))
    p.add_argument("--dir", type=Path)
    a = p.parse_args()
    verify(a.phase, a.dir or HERE / a.phase)
