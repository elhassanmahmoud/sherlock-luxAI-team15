"""Recompute the immutable five-arm panel from each 303-turn public score sequence."""
from collections import Counter
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_bytes())


def direct_controls(history, panel):
    """Swapping Hold/Feldprobe leaves two copies of Feldprobe up to the first added stay."""
    details = []
    for seed in panel:
        rows = [history[seed, team, "hold", "probe"] for team in (0, 1)]
        time = [r["events"][1][0] if len(r["events"]) == 2 else 303 for r in rows]
        start = min(time)
        gains = np.array([rows[0]["profile"], np.asarray(rows[1]["profile"])[:, ::-1]])
        same_prefix = rows[0]["prefix"][:start + 1] == rows[1]["prefix"][:start + 1]
        if not same_prefix or not np.array_equal(gains[0, :start], gains[1, :start]):
            details.append({"seed": seed, "unmatched_world_prefix": True, "at": start})
            continue
        if start == 303:
            assert rows[0]["hash"] == rows[1]["hash"] and rows[0]["win"] + rows[1]["win"] == 1
            continue
        if time[0] == time[1]:
            details.append({"seed": seed, "simultaneous": True, "at": start})
            continue
        focal = int(time[1] < time[0])
        stop = max(time)
        delta = gains[focal, start:stop, focal] - gains[1 - focal, start:stop, focal]
        details.append({
            "seed": seed, "simultaneous": False, "at": start, "focal": focal,
            "untreated_other_copy_through": stop - 1,
            "own1": int(delta[0]), "own4": int(delta[:4].sum()) if len(delta) >= 4 else None,
            "whole_win_change": rows[focal]["win"] + rows[1 - focal]["win"] - 1 if stop == 303 else None,
        })
    return details


def main():
    panel = read("karten_leistung.json")
    report = read("leistung.json")
    archive = HERE / "leistung_partien.jsonl.gz"
    assert sha256(archive.read_bytes()).hexdigest() == report["archive_sha"]
    rows = [json.loads(line) for line in gzip.decompress(archive.read_bytes()).splitlines()]
    history = {}
    arm_counts = Counter()
    followups = []
    for row in rows:
        seed, team, arm, rival = k = tuple(row["key"])
        assert k not in history and seed in panel and team in (0, 1)
        assert row["source"] == report["source"] and row["errors"] == [0, 0]
        assert len(row["matches"]) == 3 and len(row["profile"]) == len(row["prefix"]) == row["steps"] == 303
        assert all(len(turn) == 2 and all(0 <= n <= 16 for n in turn) for turn in row["profile"])
        total_match_wins = 0
        for match, sums in enumerate(row["matches"]):
            scores = np.sum(row["profile"][101 * match:101 * (match + 1)], axis=0).tolist()
            assert scores == sums["points"]
            if scores[0] != scores[1]:
                assert sums["win"] == (scores[0] > scores[1])
            total_match_wins += sums["win"]
        assert row["win"] == (total_match_wins >= 2)
        events = row["events"]
        assert len(events) <= {"reference": 0, "probe": 1, "hold": 2}[arm]
        if events:
            first, uid, old, new = events[0]
            assert 0 <= uid < 16 and new != old and new in (1, 2, 3, 4)
            assert [w["t"] for w in row["window"]] == list(range(first, first + 5))
            assert all(w["gain"] == row["profile"][w["t"]] for w in row["window"])
        if len(events) == 2:
            time, unit, move, wait = events[1]
            decision = row["follow"]
            assert arm == "hold" and time == first + 1 and unit == uid and move in (1, 2, 3, 4) and wait == 0
            assert decision["uid"] == uid and decision["eligible"] and decision["selected"]
            assert decision["t"] == time and decision["original"] == move and row["window"][0]["uid"]
            followups.append({
                "seed": seed, "side": team, "opponent": rival, "t": time,
                "original_target_scored": row["window"][0]["scoring"],
                "follow_target_scored": row["window"][1]["scoring"] and row["window"][1]["uid"],
            })
        history[k] = row
        arm_counts[arm, rival] += 1
    assert len(rows) == len(history) == 480 and len(panel) == len(set(panel)) == 48
    assert arm_counts == Counter({("reference", "solution92"): 96, ("probe", "solution92"): 96,
                                 ("hold", "solution92"): 96, ("hold", "v16"): 96, ("hold", "probe"): 96})

    verified = []
    for seed in panel:
        for team in (0, 1):
            ref = history[seed, team, "reference", "solution92"]
            probe = history[seed, team, "probe", "solution92"]
            hold = history[seed, team, "hold", "solution92"]
            if probe["events"]:
                t = probe["events"][0][0]
                assert probe["prefix"][:t + 1] == ref["prefix"][:t + 1]
                assert probe["profile"][:t] == ref["profile"][:t]
            else:
                assert probe["hash"] == ref["hash"] and probe["profile"] == ref["profile"]
            assert hold["events"][:1] == probe["events"][:1]
            used = len(hold["events"]) == 2
            own1 = own4 = 0
            if used:
                t = hold["events"][1][0]
                assert hold["prefix"][:t + 1] == probe["prefix"][:t + 1]
                assert hold["profile"][:t] == probe["profile"][:t]
                assert hold["window"][0] == probe["window"][0]
                delta = np.subtract(hold["profile"][t:t + 4], probe["profile"][t:t + 4])[:, 0]
                own1, own4 = int(delta[0]), int(delta.sum())
            else:
                assert hold["hash"] == probe["hash"] and hold["profile"] == probe["profile"]
            verified.append({
                "seed": seed, "team": team, "base": ref["win"], "probe": probe["win"],
                "hold": hold["win"], "vs_v16": history[seed, team, "hold", "v16"]["win"],
                "vs_probe": history[seed, team, "hold", "probe"]["win"],
                "actual_hold": used, "own1": own1, "own4": own4,
            })
    assert verified == report["pairs"]
    totals = {key: sum(row[key] for row in verified) for key in
              ("base", "probe", "hold", "vs_v16", "vs_probe", "actual_hold", "own1", "own4")}
    gates = {"solution_vs_base": totals["hold"] >= totals["base"],
             "solution_vs_probe": totals["hold"] >= totals["probe"],
             "direct_v16": totals["vs_v16"] >= 48, "direct_probe": totals["vs_probe"] >= 48,
             "immediate": totals["own1"] > 0, "protected": True}
    assert totals == report["totals"] and gates == report["gates"] and all(gates.values()) == report["passed"]
    out = {"games": len(rows), "checked_rounds": 303 * len(rows), "totals": totals,
           "gates": gates, "passed": all(gates.values()), "public_followups": followups,
           "paired_direct_against_feldprobe": direct_controls(history, panel),
           "archive_sha": report["archive_sha"]}
    (HERE / "gegenpruefung_leistung.json").write_text(json.dumps(out, indent=2) + "\n")
    print(totals, gates)


if __name__ == "__main__":
    main()
