"""Festes V16-Panel. Die öffentliche Inferenz und der externe Wahrheitsprüfer sind getrennt."""
import argparse
from hashlib import sha256
from importlib.metadata import distribution
import json
import os
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE.parent / "paarhinweis"))
from obergrenze import inspect, ENV_SHA, STATE_SHA
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.r3_package import r3_package_agent

PACKAGE = ROOT / "experiments/releases/20261117_sherlock_v16/agent.zip"
DIGEST = "0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"
SEEDS = range(160343000, 160343048)
SCORES = ("steps", "game_win", "our_wins", "opp_wins", "our_points", "opp_points")


class Recorder:
    """Die Policy kennt nur ihre Teambeobachtung. Aufzeichnung nach ihrer Originalaktion."""
    def __init__(self, side):
        self.base = r3_package_agent(side, PACKAGE)
        self.side = side
        self.frames = []

    def __getattr__(self, name):
        return getattr(self.base, name)

    def act(self, step, obs):
        action = self.base.act(step, obs)
        if 101 <= step <= 201:
            belief = self.base._imitation.belief
            turn = step - 101
            if (int(obs["match_steps"]) != turn or (belief.match_idx,belief.match_step) != (1,turn)):
                raise ValueError(f"Alter Gedächtnisstand bei {step}")
            scores = list(map(int, obs["team_points"]))
            if self.side == "player_1":
                scores.reverse()
            self.frames.append(dict(match=2,turn=turn,
                remembered_relic=sorted([list(map(int,xy)) for xy in belief.relic_positions]),
                pairs=int(belief.known_pairs()),known=sorted(map(int,belief._point)),candidate_n=int(belief.candidate.sum()),
                public_points=scores))
        return action


class GroundTruth:
    """Nur der Auswerter sieht aktive Paare. Nichts aus dem Spielzustand fließt in Aktionen."""
    def __init__(self, env):
        self.env = env
        self.active_pairs = []
        self.match_winners = []
        self.wins = np.zeros(2, dtype=int)

    def reset(self, **options):
        self.steps = 0
        return self.env.reset(**options)

    def step(self, actions):
        if 101 <= self.steps <= 201:
            mask=np.asarray(self.env.state.relic_nodes_mask)
            count=int(mask.sum())
            if count % 2:
                raise ValueError("Unerwartete Zahl aktiver Relikte")
            self.active_pairs.append(count//2)
        self.steps += 1
        result = self.env.step(actions)
        wins = np.asarray(result[0]["player_0"]["team_wins"], dtype=int)
        if np.any(wins != self.wins):
            delta = wins - self.wins
            if delta.sum()!=1 or delta.min()<0: raise ValueError("Ungültige Matchentscheidung")
            self.match_winners.append(int(np.argmax(delta)))
            self.wins = wins.copy()
        return result


def measure(frames, active):
    if len(frames)!=101 or len(active)!=101 or any(a>b for a,b in zip(active,active[1:])):
        raise ValueError("Unvollständiges Match oder verlorenes Reliktpaar")
    seen = next((r["turn"] for r in frames if r["pairs"]>=2),None)
    spawn = next((t for t,n in enumerate(active) if n>=2),None)
    # confirmed relative mirror pair: diagonal co-located relics can collapse a pair in Belief;
    # inspect applies only to exactly two mirror positions. Record a separate quality flag.
    pair = frames[0]["remembered_relic"]
    mirrored_open = len(pair)==2 and pair[1] == [23-pair[0][1],23-pair[0][0]]
    values = inspect(frames) if mirrored_open else dict(eligible=0,joint_turns=[],joint_first=None)
    signals = values["joint_turns"]
    first = signals[0] if signals else None
    end = seen if seen is not None else 100
    start = max(50, spawn) if spawn is not None else None
    opportunity = start is not None and start<=79 and end-start>=5
    early = first is not None and first<=79 and end-first>=5 and active[first]>=2
    result = dict(true_second_spawn=spawn,known_second=seen,opening_remembered=len(pair),
        opening_pair=mirrored_open,opportunity=opportunity,eligible_turns=values["eligible"],
        joint_turns=signals,first=values["joint_first"],false_turns=[t for t in signals if active[t]<2],
        early=early, public_lead=end-first if first is not None else None,
        state_50=dict(known=len(frames[50]["known"]),unresolved=frames[50]["candidate_n"],
                      remembered=len(frames[50]["remembered_relic"])),
        match2_our_score=frames[-1]["public_points"][0],match2_opp_score=frames[-1]["public_points"][1])
    if seen is not None and (spawn is None or seen<spawn):
        result["knowledge_precedes_truth"]=True
    return result


def source_hashes():
    engine = distribution("luxai-s3")
    if engine.version!="0.2.1":
        raise ValueError("Falsche Engine")
    files=[HERE/"PLAN.md", Path(__file__), HERE.parent/"paarhinweis"/"obergrenze.py",
           *(ROOT/"agents"/"Solution_92_Kaggle").glob("*.py"),
           *(ROOT/"scripts"/name for name in ("common.py","experiment.py","metrics.py","r3_package.py")),
           PACKAGE]
    info={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
    if info[str(PACKAGE.relative_to(ROOT))]!=DIGEST:
        raise ValueError("V16-ZIP stimmt nicht")
    for name, digest in (("env.py",ENV_SHA),("state.py",STATE_SHA)):
        actual=sha256(Path(engine.locate_file("luxai_s3/"+name)).read_bytes()).hexdigest()
        if actual!=digest:
            raise ValueError("Falsche Kurs-Engine")
        info["luxai_s3/"+name]=actual
    return info


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("shard", choices=[0,1],type=int)
    args=ap.parse_args()
    hashes=source_hashes()
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv
    env = LuxAIS3GymEnv(numpy_output=True)
    directory=HERE/"beobachtung"
    directory.mkdir(exist_ok=True)
    expected=directory/f"quellen_{args.shard}.json"
    if expected.exists() and json.loads(expected.read_bytes())!=hashes:
        raise ValueError("Quellstand seit der letzten Aufnahme abweichend")
    expected.write_text(json.dumps(hashes,sort_keys=True,indent=2)+"\n")
    out=directory/f"worker_{args.shard}.jsonl"
    keys=[(seed,side) for seed in SEEDS if seed%2==args.shard for side in ("player_0","player_1")]
    done=[(r["seed"],r["side"]) for r in (map(json.loads,out.read_text().splitlines()) if out.exists() else [])]
    if done!=keys[:len(done)]:
        raise ValueError("Fehlende, doppelte oder fremde Teilergebnisse")
    for seed,side in keys[len(done):]:
        enemy_side="player_1" if side=="player_0" else "player_0"
        agent=Recorder(side)
        trace=GroundTruth(env)
        metrics=play_game(trace,agent,make_opponent("solution92",enemy_side),seed,side,False)
        if metrics["steps"]!=303 or agent.base.caught_errors or getattr(agent.base._imitation,"caught_errors",0):
            raise ValueError("Unvollständiger Agentenlauf")
        team = int(side[-1])
        if len(trace.match_winners)!=3 or trace.match_winners.count(team)!=metrics["our_wins"]:
            raise ValueError("Fehlende Matchausgänge")
        row=dict(seed=seed,side=side,match_winners=trace.match_winners,match2_win=trace.match_winners[1]==team,**{k:metrics[k] for k in SCORES},**measure(agent.frames,trace.active_pairs))
        with out.open("a") as sink:
            sink.write(json.dumps(row,separators=(",",":"))+"\n")
            sink.flush()
            os.fsync(sink.fileno())
        print(seed,side,flush=True)
    if source_hashes()!=hashes:
        raise ValueError("Unbeabsichtigter Quellwechsel")


if __name__=="__main__":
    main()
