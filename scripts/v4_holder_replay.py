"""Fixed v4 holder replays. Record private post-step scoring only after each command was returned."""
import argparse
from collections import Counter
import csv
import fcntl
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from agents.sherlock.hybrid_agent import HybridAgent
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.final_battle_compare import ROOT,WEIGHTS,contract,digest
from scripts.par_eval import build_cfg,require_no_agent_errors
from scripts.points_hybrid_screen import environment
from scripts.protocol import SIDES
from scripts.scoring import match_points_after_step
from scripts.train_combat_advice import publish_json
from scripts.v4_sole_holder import ObservedHybrid,occupancy

STUDENT=ROOT/"experiments/candidates/umbau_20261115/student_v4.pth"
V4="0e8b280cb2173c4efd0d0c94e38119bf2f570dd5af06f52e1b5a7c9743ad7b7f"
V14="98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
CSV_SHA={"mixed":"dab8ad9200433eb46b311992ef940e8110aeaf520ef4b1995b81b7403b80381c",
         "points":"0dba9a914e11564a1f767182fe0230ee4e92bfe88fdafd9419e93cc3d3da7189"}
TARGETS=((7150003,1),(7150010,0),(7150011,1),(7150026,0),(7150039,0),(7150054,1),
         (7150068,0),(7150068,1),(7150074,1),(7150083,1))
MODE={"mixed":"mixed","points":"points","native_mixed":"mixed","native_points":"points","guard":"mixed"}


def plan(stage):
    if stage=="tech":
        return [(7150068,f"player_{s}","solution92",arm) for arm in ("mixed","points","native_mixed","native_points")
                for s in ((1,) if arm.startswith("native_") else (0,1))]
    if stage=="directed":
        return [(seed,f"player_{s}","solution92",arm) for seed,s in TARGETS for arm in ("mixed","guard")]
    if stage=="screen":
        return [(seed,side,foe,arm) for seed in range(7170200,7170216) for side in SIDES
                for arm,foes in (("mixed",("solution92","kaggle3")),("guard",("solution92","kaggle3","mixed"))) for foe in foes]
    raise ValueError(stage)


def canonical_sha(data):
    return sha256(json.dumps(data,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def binding():
    m=contract(SimpleNamespace(candidate="v14",model=None,opponents="kaggle3,solution92",first=7170200,maps=16))
    src=m["sources"]
    for f in ("v4_sole_holder.py","v4_holder_replay.py","points_hybrid_screen.py","r3_solution_retrace.py",
              "protocol.py","variants.py","fetch_kaggle3.py","train_combat_advice.py"):
        src["scripts/"+f]=digest(Path(__file__).with_name(f))
    for p in (ROOT/"lux").glob("*.py"):
        src[str(p.relative_to(ROOT))]=digest(p)
    if digest(STUDENT)!=V4 or m["weights"]!=V14:
        raise ValueError("Original registered v4 and V14 are required")
    history={}
    for arm,h in CSV_SHA.items():
        p=ROOT/f"experiments/analysis/kaggle3_20261115/student_hyb_v4_{arm}.csv"
        if digest(p)!=h:
            raise ValueError("Different original Dev A reference")
        with p.open() as f:
            subset=[r for r in csv.DictReader(f) if r["opponent"]=="solution92"]
        rows={(int(r["seed"]),r["side"]):{k:int(r[k]) for k in ("our_wins","opp_wins","our_points",
              "opp_points","steps","game_win","point_counting_version")} for r in subset}
        if len(rows)!=200 or len(rows)!=len(subset):
            raise ValueError("Incomplete historical reference")
        history[arm]=rows
    if tuple(sorted((s,int(t[-1])) for (s,t),r in history["mixed"].items()
                    if r["game_win"]!=history["points"][s,t]["game_win"]))!=TARGETS:
        raise ValueError("Registered directed known seats changed")
    stamp=dict(student=V4,v14=V14,sources=canonical_sha(src),environment=environment(),csv=CSV_SHA,
        plan=digest(ROOT/"experiments/analysis/v4_sole_holder_20261115/PLAN.md"),stay_bias=1.5,unstack=True,radius=5)
    return stamp,history


def hybrid(arm,side):
    cfg=build_cfg(str(STUDENT),["imit_stay_bias=1.5","imit_unstack=true"])
    args=(side,str(WEIGHTS),str(STUDENT))
    kw=dict(mode=MODE[arm],combat_radius=5,student_cfg=cfg)
    if arm.startswith("native_"):
        return HybridAgent(*args,**kw)
    return ObservedHybrid(*args,guard=(arm=="guard"),**kw)


class Monitor:
    def __init__(self,env,actor,side):
        self.env,self.actor,self.side=env,actor,side
        self.team=int(side[-1])
        self.frames=[]
        self.events=[]
        self.snapshots=[]
        self.orders=[sha256(),sha256()]

    def reset(self,**kw):
        obs,info=self.env.reset(**kw)
        self.previous=obs[self.side]
        return obs,info

    def step(self,commands):
        before=self.previous
        n=int(before["steps"])
        for seat,h in zip(SIDES,self.orders):
            cmds=np.asarray(commands[seat],dtype="<i2")
            if cmds.shape!=(16,3):
                raise ValueError("Unexpected actual command matrix")
            h.update(cmds.tobytes(order="C"))
        result=self.env.step(commands)
        observations,_,_,_,info=result
        after=observations[self.side]
        score=match_points_after_step(before,after,info)
        match_step=int(before["match_steps"])
        over=int(after["match_steps"])==0
        frame=dict(step=n,match=n//101+1,match_step=match_step,points=score.tolist())
        if over:
            diff=np.asarray(after["team_wins"])-np.asarray(before["team_wins"])
            if sorted(diff.tolist())!=[0,1]:
                raise ValueError("Invalid match winner")
            frame["winner"]=int(diff.argmax())
        self.frames.append(frame)
        pos,_,ids=occupancy(after,self.team)
        self.snapshots.append(None if over else Counter(tuple(map(int,pos[u])) for u in ids))
        for e in getattr(self.actor,"events",()):
            self.events.append(dict(step=n,match=n//101+1,match_step=match_step,**e))
        self.previous=after
        return result

    def closeout(self,row):
        if len(self.frames)!=303 or [f["step"] for f in self.frames]!=list(range(303)):
            raise ValueError("Not a complete game")
        matches=[]
        for m in range(3):
            segment=self.frames[101*m:101*(m+1)]
            if [r["match_step"] for r in segment]!=list(range(101)) or sum("winner" in r for r in segment)!=1:
                raise ValueError("Invalid match boundaries")
            finish=segment[-1]
            matches.append(dict(match=m+1,our_points=int(finish["points"][self.team]),
                                opp_points=int(finish["points"][1-self.team]),won=int(finish["winner"]==self.team)))
        if (sum(r["won"] for r in matches)!=row["our_wins"] or
                any(sum(m[k] for m in matches)!=row[k] for k in ("our_points","opp_points"))):
            raise ValueError("Observed match scores differ from course scorer")
        for e in self.events:
            t=e["step"]
            xy=tuple(e["world"])
            e["observed_count_after"]=None if self.snapshots[t] is None else self.snapshots[t][xy]
            end=(t//101+1)*101-1
            until=next((i for i in range(t,end) if self.snapshots[i][xy]),end)
            e["observed_empty_step_ends"]=until-t
            e["censored_at_match_boundary"]=until==end
            e["points_after"]=self.frames[t]["points"]
            e["points_before"]=self.frames[t-1]["points"] if t%101 else [0,0]
        return dict(matches=matches,orders_sha256=[h.hexdigest() for h in self.orders],events=self.events)


def filename(out,stage,key):
    seed,side,foe,arm=key
    if stage=="directed" and seed==7150068 and arm=="mixed":
        stage="tech"
    return out/stage/f"{seed}_{side}_{foe}_{arm}.json"


def run_one(env,key):
    seed,side,foe,arm=key
    agent=hybrid(arm,side)
    other=SIDES[1-int(side[-1])]
    opp=hybrid("native_mixed",other) if foe=="mixed" else make_opponent(foe,other)
    observer=Monitor(env,agent,side)
    game=play_game(observer,agent,opp,seed,side,False)
    for actor in (agent,opp):
        require_no_agent_errors(actor,actor)
        if isinstance(actor,HybridAgent):
            require_no_agent_errors(actor.v14,actor.student)
    row={k:int(game[k]) for k in ("our_wins","opp_wins","our_points","opp_points","steps","game_win","point_counting_version")}
    return dict(seed=seed,side=side,opponent=foe,arm=arm,game=row,**observer.closeout(row))


def play(a):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    import torch
    limit_threads()
    torch.manual_seed(0)
    stamp,history=binding()
    out=a.out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    if a.stage!="tech":
        from scripts.v4_holder_assess import require_predecessor
        require_predecessor(out,a.stage)
    env=None
    try:
        lockpath=out/(a.stage+".lock")
        with lockpath.open("a") as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            for key in plan(a.stage):
                p=filename(out,a.stage,key)
                p.parent.mkdir(parents=True,exist_ok=True)
                if p.exists():
                    existing=json.loads(p.read_bytes())
                    if (existing["source"]!=stamp or existing["reproduces_archive"] is False
                            or tuple(existing[k] for k in ("seed","side","opponent","arm"))!=key):
                        raise ValueError("Changed previous run")
                    continue
                if env is None:
                    env=LuxAIS3GymEnv(numpy_output=True)
                r=run_one(env,key)
                mode=MODE[key[3]]
                historic=history[mode].get((key[0],key[1]))
                r["reproduces_archive"]=r["game"]==historic if historic and key[3]!="guard" else None
                r["source"]=stamp
                publish_json(p,r)
                print(key,r["game"],r["reproduces_archive"],flush=True)
                if r["reproduces_archive"] is False:
                    raise ValueError("Original v4 result differs from recorded Dev A; comparison halted")
            if binding()[0]!=stamp:
                raise ValueError("Sources changed during run")
    finally:
        if env is not None:
            env.close()


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage",choices=("tech","directed","screen"))
    p.add_argument("--out",type=Path,required=True)
    play(p.parse_args())
