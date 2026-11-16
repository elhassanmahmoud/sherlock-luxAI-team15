"""Summarize verified one-step forks in the selected candidate games."""
from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
from pathlib import Path
import json


def evaluate(source, selected):
    by_seat = {}
    total = Counter()
    blob = source.read_bytes()
    lines = blob.splitlines()
    seal = json.loads(source.with_name("complete.json").read_bytes())
    if seal != {"n": len(lines), "sha256": sha256(blob).hexdigest()}:
        raise ValueError("Invalid repetition seal")
    for line in lines:
        row = json.loads(line)
        key = row["seed"], row["seat"]
        if (row["arm"], row["opponent"]) != ("defense", "solution") or key not in selected:
            continue
        if key in by_seat or row["steps"] != 303:
            raise ValueError(f"Duplicate/incomplete case {key}")
        counts = Counter(steps=0, units=0, own_points_added=0, enemy_points_denied=0,
                         turns_enemy_scored_less=0, turns_enemy_scored_more=0,
                         enemy_energy_removed=0, own_energy_spent=0, previous_own_fields_saved_net=0,
                         previous_enemy_fields_denied_net=0)
        observed = set()
        for event in row["forks"]:
            t = event["step"]
            if t in observed or not 0 <= t < 303 or not event["units"]:
                raise ValueError(f"Duplicate/invalid intervention {key} {t}")
            observed.add(t)
            own, enemy = event["actual_gain"]
            own_base, enemy_base = event["r3_gain"]
            added, denied = own - own_base, enemy_base - enemy
            if (added != len(event["own_fields_gained"]) - len(event["own_fields_lost"])
                    or denied != len(event["enemy_fields_denied"]) - len(event["enemy_fields_conceded"])):
                raise ValueError(f"Field attribution failed for {key} {t}")
            own_energy, enemy_energy = event["energy_actual_minus_r3"]
            counts.update(steps=1, units=len(event["units"]), own_points_added=added,
                          enemy_points_denied=denied, turns_enemy_scored_less=int(denied > 0),
                          turns_enemy_scored_more=int(denied < 0), enemy_energy_removed=-enemy_energy,
                          own_energy_spent=-own_energy,
                          previous_own_fields_saved_net=len(event["previous_own_fields_saved"])
                              - len(event["previous_own_fields_abandoned"]),
                          previous_enemy_fields_denied_net=len(event["previous_enemy_fields_denied"])
                              - len(event["previous_enemy_fields_conceded"]))
        if (counts["steps"] != row["routing"].get("changed_turns", 0)
                or counts["units"] != row["routing"].get("changed_unit_actions", 0)):
            raise ValueError(f"Policy counts disagree with world commands in {key}")
        total.update(counts)
        by_seat[f"{key[0]}/{key[1]}"] = dict(counts)
    if len(by_seat) != len(selected):
        raise ValueError("Missing candidate games with one-step probes")
    return {"by_seat": by_seat, "total": dict(total)}


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("games", type=Path)
    args = parser.parse_args()
    study = Path(__file__).resolve().parents[2]
    archive = json.loads((study / "unit_handoff_20261116/archiv.json").read_bytes())
    selected = set(map(tuple, archive["vs_v15"]["lost"]))
    print(json.dumps(evaluate(args.games, selected), indent=2))
