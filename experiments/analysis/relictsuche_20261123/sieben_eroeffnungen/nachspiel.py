"""Reproduce all seven changed seats while allowing a bounded number of real scout overrides."""
import argparse
import gzip
import json
from pathlib import Path

from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.abschlusspruefung.vergleich import make
from experiments.analysis.relictsuche_20261123.vergleich.spielen import Monitor, sha, write_once
from scripts.common import play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors


HERE = Path(__file__).resolve().parent
SERIES = HERE.parent / "sicht1_wiederholung"
CAPS = (0, 1, 3, 8)


class LimitedScout:
    def __init__(self, side, cap):
        self.scout = make("ortundflotte", side)
        self.cap = cap
        self.overrides = []

    def __getattr__(self, name):
        return getattr(self.scout, name)

    def act(self, step, obs):
        if self.scout.changes >= self.cap:
            self.scout.done = True
        before = self.scout.changes
        actions = self.scout.act(step, obs)
        if self.scout.changes > before:
            self.overrides.append([step, int(self.scout.uid), int(actions[self.scout.uid, 0])])
        return actions


def play(env, seed, team, cap):
    own = f"player_{team}"
    scout = LimitedScout(own, cap)
    opponent = make("solution92", f"player_{1 - team}")
    monitor = Monitor(env, team, "discovery")
    result = play_game(monitor, scout, opponent, seed, own, False)
    require_no_agent_errors(scout.scout.base, opponent)
    assert monitor.turn == result["steps"] == 303 and len(scout.overrides) <= cap
    return dict(seed=seed, team=team, cap=cap, overrides=scout.overrides, matches=monitor.matches,
                sight=monitor.first_sight, credit=monitor.first_credit,
                win=result["game_win"], digest=monitor.digest.hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scratch", type=Path)
    parser.add_argument("operation", choices=("play", "score"))
    parser.add_argument("lane", type=int, nargs="?", default=0)
    args = parser.parse_args()
    limit_threads()
    frozen = json.loads((SERIES / "ergebnis.json").read_bytes())
    cases = [(s["seed"], s["team"]) for s in frozen["seats"] if s["gain"]]
    assert len(cases) == 7 and sha(SERIES / "partien.jsonl.gz") == frozen["archive"]
    keys = [(s, t, cap) for s, t in cases for cap in CAPS]
    def target(s, t, cap):
        return args.scratch / f"{s}_{t}_{cap}.json"
    if args.operation == "play":
        args.scratch.mkdir(parents=True, exist_ok=True)
        env = LuxAIS3GymEnv(numpy_output=True)
        try:
            for seed, team, cap in keys[args.lane::4]:
                write_once(target(seed, team, cap), play(env, seed, team, cap))
        finally:
            env.close()
        return
    with gzip.open(SERIES / "partien.jsonl.gz", "rt") as stream:
        anchors = {tuple(row["key"]): row for row in map(json.loads, stream) if tuple(row["key"][:2]) in cases}
    records = []
    for seed, team, cap in keys:
        row = json.loads(target(seed, team, cap).read_bytes())
        assert (row["seed"], row["team"], row["cap"]) == (seed, team, cap)
        if cap in (0, 8):
            archive = anchors[seed, team, "v16" if cap == 0 else "ortundflotte", "solution92"]
            assert all(archive[k] == row[k] for k in ("sight", "credit", "digest", "matches", "win"))
        records.append(row)
    write_once(HERE / "ergebnis.json", dict(source=frozen["archive"], rows=records))


if __name__ == "__main__":
    main()
