"""Attribute actual scoring squares to the information Sherlock had before that turn."""
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "solution"))
from feldverlauf import DIGEST, PACKAGE
from replays import MatchRecord
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from luxai_s3.wrappers import LuxAIS3GymEnv


class PublicMap:
    def __init__(self, base):
        self.base = base
        self.before = []

    def __getattr__(self, name):
        return getattr(self.base, name)

    def act(self, step, obs):
        actions = self.base.act(step, obs)
        memory = self.base._imitation.belief
        zone = memory.relic_zone
        category = np.where(memory.point_tiles, 2, np.where(zone, 1, 0)).astype(np.int8)
        if memory.mirrored:
            from sherlock.geometry import mirror_map
            category = mirror_map(category)
        self.before.append((category, np.array(obs["sensor_mask"], dtype=bool, copy=True)))
        return actions


def summarize(frames, maps, winners, team):
    matches = []
    for index, winner in enumerate(winners):
        phases = [dict(our=Counter(), enemy=Counter(), prior_visible_enemy=0) for _ in range(4)]
        for turn in range(101):
            t = 101 * index + turn
            category, visible = maps[t]
            phase = phases[max(0,(turn-1)//25)]
            for seat, key in ((team, "our"), (1-team, "enemy")):
                for tile in frames[t][seat]:
                    name = ("outside_known_zone", "unconfirmed_inside", "confirmed")[category[tile]]
                    phase[key][name] += 1
                    if key == "enemy":
                        phase["prior_visible_enemy"] += int(visible[tile])
        ours = sum(sum(p["our"].values()) for p in phases)
        theirs = sum(sum(p["enemy"].values()) for p in phases)
        matches.append(dict(number=index+1, own=ours, opponent=theirs, win=int(team==winner), phases=phases))
    return matches


def run():
    if sha256(PACKAGE.read_bytes()).hexdigest()!=DIGEST or os.environ.get("PYTHONHASHSEED")!="0":
        raise ValueError("Wrong original policy or runtime")
    limit_threads()
    root = HERE.parent / "signalstudie" / "haupt"
    filenames = [root / f"worker_{i}.jsonl" for i in range(2)]
    rows = [json.loads(line) for p in filenames for line in p.read_text().splitlines()]
    losing = {(r["seed"],r["side"]) for r in rows if r["arm"]=="signal" and r["opponent"]=="solution92" and not r["game_win"]}
    seeds = {s for s,_ in losing}
    pairs = {(r["seed"],r["side"]):r for r in rows if r["arm"]=="signal" and r["opponent"]=="solution92" and r["seed"] in seeds}
    if len(rows)!=900 or len(seeds)!=4 or len(losing)!=4 or len(pairs)!=8 or any(r["changes"] for r in pairs.values()):
        raise ValueError("The eight controls changed")
    engine = LuxAIS3GymEnv(numpy_output=True)
    env = MatchRecord(engine)
    games = []
    try:
        for (seed, side), original in sorted(pairs.items()):
            team = int(side[-1])
            actor = PublicMap(r3_package_agent(side, PACKAGE))
            opponent = make_opponent("solution92",f"player_{1-team}")
            score = play_game(env, actor, opponent, seed, side, train=False)
            require_no_agent_errors(actor.base, opponent)
            columns = ("steps","our_points","opp_points","our_wins","opp_wins","game_win")
            if (any(score[k]!=original[k] for k in columns) or env.match_winners!=original["match_winners"]
                    or len(env.frames)!=303 or len(actor.before)!=303):
                raise ValueError("Not the same game as the original trial")
            matches=summarize(env.frames, actor.before, env.match_winners, team)
            if (sum(m["own"] for m in matches)!=score["our_points"]
                    or sum(m["opponent"] for m in matches)!=score["opp_points"]):
                raise ValueError("Field-point accounting does not add up")
            games.append(dict(seed=seed, side=side, result=score["game_win"], matches=matches))
            print(seed,side,"verified",flush=True)
    finally:
        engine.close()
    output=dict(games=games,release=DIGEST,source={p.name:sha256(p.read_bytes()).hexdigest() for p in filenames})
    (HERE/"spielverlaeufe.json").write_text(json.dumps(output,sort_keys=True,separators=(",",":"))+"\n")


if __name__=="__main__":
    run()
