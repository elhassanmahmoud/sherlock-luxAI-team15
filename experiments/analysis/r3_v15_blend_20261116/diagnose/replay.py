"""Passively record all twelve archived R3 losses against Solution for each original policy."""
import argparse
import csv
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import sys

import numpy as np

SHARED = Path("experiments/analysis/movement_soft_20261115/shared_400")
R3_TABLE = SHARED/"measured/r3/games.jsonl"
V15_TABLE = Path("experiments/analysis/umbau_20261115/confirm/v15_candidate.csv")
PINS = {R3_TABLE:"6154c21e78a3abfccfba9a50a1f73efa767c909eaa3aaf5e472347edb3e6b649",
        V15_TABLE:"1cc603732dafff379e57f236be4fc37a0bdd7dfcfa35fcc0e7ce78c95387c4cd"}
FIELDS = ("result","wins","losses","points","opp_points","steps")
NATIVE = ("game_win","our_wins","opp_wins","our_points","opp_points","steps")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(test, why):
    if not test:
        raise ValueError(why)


def originals(repo):
    tables = {}
    for path, pin in PINS.items():
        require(digest(repo/path)==pin, str(path))
        with (repo/path).open() as f:
            rows = csv.DictReader(f) if path==V15_TABLE else map(json.loads,f)
            result = {}
            for r in rows:
                if r["opponent"] != "solution92":
                    continue
                key = int(r["seed"]),r["side"]
                require(key not in result, "Duplicate key")
                result[key] = [int(r[k]) for k in (NATIVE if path==V15_TABLE else FIELDS)]
            tables["v15" if path==V15_TABLE else "r3"] = result
    keys = {(s,p) for s in range(7158000,7158400) for p in ("player_0","player_1")}
    require(all(set(r)==keys for r in tables.values()), "Incomplete table")
    cases = sorted(k for k,r in tables["r3"].items() if not r[0])
    require(len(cases)==12 and sum(tables["v15"][k][0] for k in cases)==9, "Different sample")
    return cases,tables


class Observer:
    def __init__(self,env,agent,arm,side):
        self.env,self.agent,self.arm,self.side = env,agent,arm,side
        self.team = int(side[-1])
        self.frames = []
        self.commands = {k:hashlib.sha256() for k in ("player_0","player_1")}

    def reset(self,**kw):
        obs,info = self.env.reset(**kw)
        self.obs = obs
        self.radius = int(info["params"]["unit_sap_range"])
        return obs,info

    def step(self,actions):
        from scripts.scoring import match_points_after_step
        side,t = self.side,self.team
        before = self.obs[side]
        n = len(self.frames)
        require(int(before["steps"])==n and int(before["match_steps"])==n%101, "Clock")
        def units(team):
            energy = np.asarray(before["units"]["energy"])[team].reshape(16)
            pos = np.asarray(before["units"]["position"])[team]
            live = np.asarray(before["units_mask"])[team] & (energy>=0)
            return [[int(u),int(pos[u,0]),int(pos[u,1]),int(energy[u])] for u in np.flatnonzero(live)]
        own,visible = units(t),units(1-t)
        belief = (self.agent if self.arm=="r3" else self.agent._imitation.v14).belief
        known = np.argwhere(belief.point_tiles)
        if belief.mirrored:
            known = 23-known[:,::-1]
        # At the restart, both own observations may still display outgoing match units.
        # Keep the raw evidence, distinguishing step zero in the summaries.
        commands = {}
        for player,mat in actions.items():
            m = np.asarray(mat)
            require(m.shape==(16,3) and m.dtype.kind in "iu","Bad world actions")
            self.commands[player].update(m.astype("<i8").tobytes())
            commands[player] = m.tolist()
        after,rew,term,trunc,info = self.env.step(actions)
        exact = match_points_after_step(before,after[side],info)
        def relative(value):
            return [int(value[t]),int(value[1-t])]
        self.frames.append(dict(step=n, own=own,visible=visible,confirmed=known.tolist(),
            own_orders=commands[side],opp_orders=commands["player_"+str(1-t)],
            before=relative(before["team_points"]),after=relative(exact),
            next_public_points=relative(after[side]["team_points"]),
            next_wins=relative(after[side]["team_wins"])))
        self.obs=after
        return after,rew,term,trunc,info


def start(arm,source,model,repo):
    from scripts.experiment import limit_threads
    limit_threads()
    import torch
    from scripts import common
    from agents.sherlock.main import Agent_x
    if arm=="r3":
        from scripts import final_battle_compare as b
        manifest = json.loads((repo/SHARED/"measured/r3/manifest.json").read_bytes())
        for name,h in manifest["sources"].items():
            require(digest(source/name)==h, f"Different original R3 source {name}")
        require(digest(model)==manifest["model"] and digest(b.WEIGHTS)==manifest["weights"], "R3 weights")
        from importlib.util import find_spec
        engine=Path(find_spec("luxai_s3").origin).parent
        for name,h in manifest["engine"].items():
            require(digest(engine/name)==h,"R3 engine")
        b.init_worker("selective_movement",str(model))
        return b.evaluate.agent,b.evaluate.env,manifest
    from scripts.v15_style_panel import contract
    from scripts.check_candidate_runner import verify_loaded
    from luxai_s3.wrappers import LuxAIS3GymEnv
    pin = contract(model)
    torch.manual_seed(0)
    agent = Agent_x("player_0",agent_path=str(model),train=False,seed=0)
    verify_loaded(agent,torch.load(model,map_location="cpu",weights_only=False))
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    h = agent._imitation
    require(h.mode=="mixed" and h.combat_radius==5 and h.student.cfg.imit_stay_bias==1.5 and h.student.cfg.imit_unstack, "V15 mode")
    return agent,LuxAIS3GymEnv(numpy_output=True),pin


def main(a):
    keys,tables = originals(a.repo)
    sys.path.insert(0,str(a.source))
    os.chdir(a.source)
    from scripts.common import make_opponent,play_game
    from scripts.par_eval import require_no_agent_errors
    agent,env,pin = start(a.arm,a.source,a.model,a.repo)
    a.out.mkdir(parents=True,exist_ok=True)
    with (a.out/(a.arm+"-manifest.json")).open("x") as f:
        json.dump(dict(arm=a.arm,model_sha256=digest(a.model),source_pin=pin,table_sha256={str(p):h for p,h in PINS.items()},
                  recorder_sha256=digest(Path(__file__)),keys=keys),f,indent=1)
    for seed,side in keys:
        observer = Observer(env,agent,a.arm,side)
        other = "player_"+str(1-int(side[-1]))
        rival = make_opponent("solution92",other)
        row = play_game(observer,agent,rival,seed,side,train=False)
        require_no_agent_errors(agent,rival)
        got = [int(row[k]) for k in NATIVE]
        expected = tables[a.arm][seed,side]
        data=dict(arm=a.arm,seed=seed,side=side,expected=expected,actual=got,radius=observer.radius,
                  command_sha256={k:h.hexdigest() for k,h in observer.commands.items()},frames=observer.frames)
        dest=a.out/f"{a.arm}-{seed}-{side}.json.gz"
        with dest.open("xb") as f:
            f.write(gzip.compress(json.dumps(data,separators=(",",":")).encode(),mtime=0))
        require(len(observer.frames)==303 and got==expected, f"Reproduction failed {seed}/{side}: {got} != {expected}")
        print(a.arm,seed,side,got,flush=True)
    env.close()


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arm",choices=("r3","v15"))
    for k in ("repo","source","model","out"):
        parser.add_argument("--"+k,type=lambda p:Path(p).resolve(),required=True)
    main(parser.parse_args())
