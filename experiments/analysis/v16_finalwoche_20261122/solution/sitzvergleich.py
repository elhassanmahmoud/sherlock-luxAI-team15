"""Reconcile the V16 and R3 Solution results from confirmation panels 3 and 5."""
import argparse
import csv
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE.parents[1]
SEATS = ("player_0", "player_1")
OUTCOMES = {(1, 1): "both_won", (1, 0): "v16_only", (0, 1): "r3_only", (0, 0): "both_lost"}
SOURCES = {
    3: (7261000, {
        "v16": ("devf_20261117/bestaetigung3_kandidat.csv", "e9d6946d7894ebd4e3d0abb41341a66b95df68d0c897c486139dca00a2ee6cef"),
        "r3": ("devf_20261117/bestaetigung3_r3.csv", "9f86eba32322768154b7874b0fe8a9f45995cee2cbfda9b812d3078b15e748a8"),
    }),
    5: (7267000, {
        "v16": ("devh_20261117/bestaetigung5_k.csv", "94e7f359be85323561dbfefc4a43668a2b82bee06a8315e82ca33367ee8a9e04"),
        "r3": ("devh_20261117/bestaetigung5_r3.csv", "ec51094fb13472ee36eeb79deb0032fdd4e0c4754ae8e41c4a6e2e7df71b8672"),
    }),
}


def solution_rows(path, digest, first_seed):
    if sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError(f"Unexpected source version in {path}")
    rows = {}
    with path.open(newline="") as stream:
        for row in csv.DictReader(stream):
            if row["opponent"] != "solution92":
                continue
            key = int(row["seed"]), row["side"]
            matches = int(row["our_wins"])
            won = int(row["game_win"])
            if (key in rows or int(row["steps"]) != 303 or int(row["point_counting_version"]) != 2
                    or not 0 <= matches <= 3 or matches + int(row["opp_wins"]) != 3
                    or won != int(matches >= 2)):
                raise ValueError(f"Invalid game in {path} at {key}")
            rows[key] = {"win": won, "matches": matches, "points": int(row["our_points"]),
                         "opponent_points": int(row["opp_points"])}
    expected = {(s, p) for s in range(first_seed, first_seed + 400) for p in SEATS}
    if rows.keys() != expected:
        raise ValueError(f"Unexpected or missing Solution seats in {path}")
    return rows


def compare():
    panels, differences = {}, []
    for panel, (first_seed, files) in SOURCES.items():
        games = {agent: solution_rows(ANALYSIS / filename, digest, first_seed)
                 for agent, (filename, digest) in files.items()}
        outcomes = Counter()
        match_pairs = Counter()
        for (seed, side), v16 in sorted(games["v16"].items()):
            r3 = games["r3"][seed, side]
            outcome = OUTCOMES[v16["win"], r3["win"]]
            outcomes[outcome] += 1
            if v16["win"] == r3["win"]:
                continue
            match_pairs[f'{outcome}:V16={v16["matches"]},R3={r3["matches"]}'] += 1
            differences.append({"panel": panel, "seed": seed, "side": side, "outcome": outcome,
                                **{f"v16_{k}": v for k, v in v16.items()}, **{f"r3_{k}": v for k, v in r3.items()}})
        panels[panel] = {"games_per_agent": len(games["v16"]), "outcomes": dict(outcomes),
                         "v16_wins": sum(v["win"] for v in games["v16"].values()),
                         "r3_wins": sum(v["win"] for v in games["r3"].values()),
                         "discordant_match_win_pairs": dict(sorted(match_pairs.items()))}
    return panels, differences


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    panels, differences = compare()
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "ergebnis.json").write_text(json.dumps(panels, indent=2) + "\n")
    with (args.out / "unterschiedliche_sitze.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(differences[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(differences)
