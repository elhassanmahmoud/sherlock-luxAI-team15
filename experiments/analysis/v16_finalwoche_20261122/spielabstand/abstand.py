"""Reconstruct the exact match deficits of every historical V16 loss to Solution."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "solution"))
sys.path.insert(0, str(HERE.parent))
from feldverlauf import DIGEST, PACKAGE, ROOT
from replays import MatchRecord
from sitzvergleich import ANALYSIS, SOURCES, solution_rows
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from luxai_s3.wrappers import LuxAIS3GymEnv


class SavedCommands:
    def __init__(self, path, expected, side):
        metadata = json.loads(path.with_suffix(".json").read_text())
        if (metadata["package"] != DIGEST or metadata["sha256"] != sha256(path.read_bytes()).hexdigest()
                or metadata["actual"] != expected or metadata["seat"]["side"] != side):
            raise ValueError("Wrong recorded policy or result")
        with np.load(path, allow_pickle=False) as stored:
            self.rows = {key: stored[key] for key in ("commands", "team_points", "team_wins", "match_steps", "sensor_mask")}

    def act(self, step, obs):
        for key in ("team_points", "team_wins", "match_steps", "sensor_mask"):
            if not np.array_equal(obs[key], self.rows[key][step]):
                raise ValueError(f"Public replay mismatch in {key} at step {step}")
        return self.rows["commands"][step].copy()


def run(archive, out):
    limit_threads()
    if os.environ.get("PYTHONHASHSEED") != "0" or sha256(PACKAGE.read_bytes()).hexdigest() != DIGEST:
        raise ValueError("Wrong runtime or release")
    games = []
    engine = LuxAIS3GymEnv(numpy_output=True)
    env = MatchRecord(engine)
    try:
        for panel, (start, sources) in SOURCES.items():
            file, digest = sources["v16"]
            originals = solution_rows(ANALYSIS / file, digest, start)
            for (seed, side), expected in sorted(originals.items()):
                if expected["win"]:
                    continue
                record = archive / f"v16_{seed}_{side}.npz"
                actor = SavedCommands(record, expected, side) if record.exists() else r3_package_agent(side, PACKAGE)
                team = int(side[-1])
                opponent = make_opponent("solution92", f"player_{1-team}")
                result = play_game(env, actor, opponent, seed, side, train=False)
                require_no_agent_errors(actor, opponent)
                if (result["steps"] != 303 or result["point_counting_version"] != 2
                        or result["our_wins"] != expected["matches"] or result["our_points"] != expected["points"]
                        or result["opp_points"] != expected["opponent_points"] or result["game_win"] != 0):
                    raise ValueError(f"Course result differs at {seed}/{side}")
                matches = []
                for index, winner in enumerate(env.match_winners):
                    frames = env.frames[101*index:101*(index+1)]
                    increments = np.array([[len(s[team]), len(s[1-team])] for s in frames])
                    scores = increments.cumsum(axis=0)
                    ours, theirs = map(int, scores[-1])
                    won = int(winner == team)
                    if (won and ours < theirs) or (not won and ours > theirs):
                        raise ValueError("Match winner inconsistent with score")
                    checks = {turn: int(scores[turn,0]-scores[turn,1]) for turn in (25,50,75,90,100)}
                    matches.append(dict(number=index+1, own=ours, opposition=theirs, win=won, margin=checks,
                                        safe=0 if won else theirs-ours+1, tie=0 if won else max(1,theirs-ours)))
                if (len(matches) != 3 or sum(v["own"] for v in matches) != expected["points"]
                        or sum(v["opposition"] for v in matches) != expected["opponent_points"]
                        or sum(v["win"] for v in matches) != expected["matches"]):
                    raise ValueError("Match-level accounting mismatch")
                needed = sorted((m for m in matches if not m["win"]), key=lambda m: (m["safe"], m["number"]))[:2-expected["matches"]]
                game = dict(panel=panel, seed=seed, side=side, commands="saved" if record.exists() else "release",
                            matches=matches, needed=[m["number"] for m in needed],
                            safe=sorted(m["safe"] for m in matches)[1], tie=sorted(m["tie"] for m in matches)[1])
                games.append(game)
                print(seed, side, "verified", flush=True)
    finally:
        engine.close()
    if len(games) != 35 or len({(g["seed"],g["side"]) for g in games}) != 35:
        raise ValueError("Expected exactly all 35 losses")
    thresholds = {points: {kind: sum(g[kind] <= points for g in games) for kind in ("safe","tie")}
                  for points in (1,3,5,10,25,50)}
    critical = [m for g in games for m in g["matches"] if m["number"] in g["needed"]]
    gaps = {turn: {key: float(value) for key,value in zip(("q25","median","q75"),np.percentile(
        [m["margin"][turn] for m in critical],[25,50,75]))} for turn in (25,50,75,90,100)}
    output = dict(release=DIGEST, lost_seats=len(games), cards=len({g["seed"] for g in games}),
                  sources={p:v[1]["v16"] for p,v in SOURCES.items()}, thresholds=thresholds,
                  median_safe=float(np.median([g["safe"] for g in games])), critical_matches=len(critical),
                  deficit_checkpoints=gaps, games=games)
    out.write_text(json.dumps(output, separators=(",",":"), allow_nan=False)+"\n")


if __name__ == "__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("historical_commands", type=Path)
    cli.add_argument("--out",type=Path,default=HERE/"spielabstand.json")
    args=cli.parse_args()
    run(args.historical_commands,args.out)
