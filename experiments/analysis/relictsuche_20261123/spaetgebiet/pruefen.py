"""Recount public bounds from replay frames without calling the primary evaluator."""
import argparse
from collections import Counter, defaultdict
import gzip
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def evidence():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    report = json.loads((HERE / "ergebnis.json").read_text())
    hashes = {item["path"]: item["sha256"] for item in report["inputs"]}
    counts = defaultdict(Counter)
    leads = defaultdict(list)
    unique = defaultdict(set)
    triggers = defaultdict(dict)
    frames_checked = 0
    raw_lines = []
    for name, digest in sorted(hashes.items()):
        data = (args.source / name).read_bytes()
        assert sha256(data).hexdigest() == digest
        game = json.loads(gzip.decompress(data))
        raw_lines.append(json.dumps(game, separators=(",", ":")))
        for match in (2, 3):
            rr = [f for f in game["frames"] if f["match"] == match]
            assert [f["turn"] for f in rr] == list(range(1, 101))
            # The 101st decision resets the public scoreboard. Its points are counted
            # by the referee in the match total and generate no next-turn alarm.
            for team in (0, 1):
                last_gain = game["matches"][match - 1][team] - sum(f["gains"][team] for f in rr)
                assert 0 <= last_gain <= 16
            frames_checked += len(rr)
            for rule in ("region", "possible", "old_joint"):
                key = game["group"], rule
                c = counts[key]
                c["complete_matches"] += 1
                alarms = []
                for index, f in enumerate(rr):
                    if rule != "old_joint":
                        measured = any(n > limit for n, limit in zip(f["gains"], f["limits"][rule], strict=True))
                        assert measured == f["alarms"][rule]
                    if f["known"] and 10 <= f["turn"] <= 80 and f["alarms"][rule]:
                        hidden = set(map(tuple, f["missing"]))
                        c["false_alarm_turns"] += int(not hidden)
                        c["unexplained_in_region_turns"] += int(sum(f["outside"]) == 0)
                        discover = next((q["turn"] for q in rr[index + 1:] if hidden & set(map(tuple, q["known"]))), 101)
                        if hidden and sum(f["outside"]) and discover - f["turn"] >= 5:
                            alarms.append((f["turn"], discover - f["turn"]))
                c["alarmed_matches"] += any(f["known"] and 10 <= f["turn"] <= 80 and f["alarms"][rule] for f in rr)
                if alarms:
                    seat = game["seed"], game["team"]
                    margin = game["matches"][match - 1][0] - game["matches"][match - 1][1]
                    triggers[key][(*seat, match)] = alarms[0][0]
                    c["actionable_matches"] += 1
                    leads[key].append(alarms[0][1])
                    unique[key, "maps"].add(seat[0])
                    c["actionable_score_losses"] += int(margin < 0)
                    c["tied_among_actionable"] += int(margin == 0)
                    if margin < 0:
                        unique[key, "loss_seats"].add(seat)
    assert len(raw_lines) == 88 and frames_checked == 17600
    for (group, rule), c in counts.items():
        key = group, rule
        target = report["groups"][group][rule]
        for field, value in c.items():
            assert target[field] == value, (key, field)
        assert target["actionable_maps"] == len(unique[key, "maps"])
        assert target["actionable_loss_seats"] == len(unique[key, "loss_seats"])
        assert abs(target["mean_lead"] - sum(leads[key]) / len(leads[key])) < 1e-8
    new = triggers["new", "region"]
    old = triggers["new", "old_joint"]
    contrast = dict(new_only=len(new.keys() - old.keys()), old_only=len(old.keys() - new.keys()),
                    both=len(new.keys() & old.keys()),
                    earlier_on_both=sum(new[k] < old[k] for k in new.keys() & old.keys()))
    (HERE / "spielzuege.jsonl.gz").write_bytes(gzip.compress(("\n".join(raw_lines) + "\n").encode(), mtime=0))
    print(dict(games=len(raw_lines), checked_turns=frames_checked, fresh_late_matches=contrast))


if __name__ == "__main__":
    evidence()
