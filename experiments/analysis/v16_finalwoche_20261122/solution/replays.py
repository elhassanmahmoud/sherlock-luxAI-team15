"""Reproduziert die acht vorab ausgewählten, bei R3 und V16 ungleichen Solution-Sitze."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from feldverlauf import DIGEST, PACKAGE, ROOT, Record, measure
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.r3_package import r3_package_agent
from sitzvergleich import compare

PACKAGES = {
    "v16": (PACKAGE, DIGEST),
    "r3": (ROOT / "experiments/releases/20261116_r3_finale/agent.zip",
           "8aabdc732143a1e3f5babdd6edb6272e166b54671ee397e50e02083261c4a64d"),
}


class MatchRecord(Record):
    def reset(self, **kwargs):
        self.match_winners = []
        return super().reset(**kwargs)

    def step(self, actions):
        wins_before = np.asarray(self.previous["team_wins"])
        result = super().step(actions)
        if len(self.frames) % 101 == 0:
            wins = np.asarray(self.previous["team_wins"]) - wins_before
            if wins.shape != (2,) or sorted(wins.tolist()) != [0, 1]:
                raise ValueError(f"Unerwarteter Matchabschluss: {wins}")
            self.match_winners.append(int(np.argmax(wins)))
        return result


def play(agent_name, out):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads()
    path, digest = PACKAGES[agent_name]
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError("Falsches Kurspaket")
    _, archive_rows = compare()
    with (HERE / "unterschiedliche_sitze.csv").open() as src:
        differences = list(csv.DictReader(src))
    if [{k: str(v) for k, v in r.items()} for r in archive_rows] != differences:
        raise ValueError("Abweichung der Quelllisten")
    sampled = {}
    for row in sorted(archive_rows, key=lambda r: r["seed"]):
        sampled.setdefault((row["panel"], row["outcome"], row["side"]), row)
    if len(sampled) != 8:
        raise ValueError("Eine Schicht fehlt")
    results = []
    env = MatchRecord(LuxAIS3GymEnv(numpy_output=True))
    for (panel, outcome, side), row in sorted(sampled.items()):
        seed = row["seed"]
        t = int(side[-1])
        opponent = make_opponent("solution92", f"player_{1-t}")
        agent = r3_package_agent(side, path)
        actual = play_game(env, agent, opponent, seed, side, train=False)
        fields = {"our_wins": "matches", "our_points": "points", "opp_points": "opponent_points", "game_win": "win"}
        expected = {k: row[f"{agent_name}_{v}"] for k, v in fields.items()}
        actual = {k: actual[k] for k in fields}
        verified = expected == actual and len(env.frames) == 303
        if len(env.match_winners) != 3 or env.match_winners.count(t) != actual["our_wins"]:
            raise ValueError("Nicht plausible Matchsieger")
        matches = []
        for idx, start in enumerate((0, 101, 202)):
            frames = env.frames[start:start + 101]
            def score(slice_, team):
                return sum(len(f[team]) for f in frames[slice_])
            match = {"win": int(env.match_winners[idx] == t)}
            for name, team in (("sherlock", t), ("solution", 1 - t)):
                match[name] = {**measure(frames, team),
                               "points_0_70": score(slice(0, 71), team),
                               "points_71_80": score(slice(71, 81), team),
                               "points_81_100": score(slice(81, 101), team)}
            matches.append(match)
        for key, who in (("our_points", "sherlock"), ("opp_points", "solution")):
            if sum(m[who]["points"] for m in matches) != actual[key]:
                raise ValueError("Abweichender Gesamtstand")
        results.append({"panel": panel, "expected_outcome_group": outcome, "side": side, "seed": seed,
                        "verified": verified, "actual": actual, "expected": expected, "matches": matches})
        print(agent_name, seed, side, "OK" if verified else f"abweichend {actual} / {expected}", flush=True)
    out.write_text(json.dumps(results) + "\n")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--arm", choices=PACKAGES)
    p.add_argument("--out", type=Path, default=HERE / "replays.json")
    args = p.parse_args()
    if args.arm:
        return play(args.arm, args.out)
    # Kurspakete verwenden denselben Modulnamen. Die Unterprozesse laufen nacheinander.
    with tempfile.TemporaryDirectory() as tmp:
        pair = {}
        for arm in PACKAGES:
            path = Path(tmp) / (arm + ".json")
            subprocess.run([sys.executable, __file__, "--arm", arm, "--out", str(path)], check=True)
            pair[arm] = json.loads(path.read_text())
    args.out.write_text(json.dumps({"sha256": {k: v[1] for k, v in PACKAGES.items()}, "arms": pair}, indent=2) + "\n")


if __name__ == "__main__":
    main()
