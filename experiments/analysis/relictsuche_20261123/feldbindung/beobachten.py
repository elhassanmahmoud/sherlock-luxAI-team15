"""Replay the first field-probe choices, checking complete outcomes and attributing scores at its target."""
import argparse
from datetime import datetime
import gzip
import json
from pathlib import Path
import torch
import numpy as np
from experiments.analysis.relictsuche_20261123.feldprobe.kandidat import create,PACKAGE
from experiments.analysis.relictsuche_20261123.vergleich.spielen import Monitor,CUTOFF,write_once,common_source,stamp,sha
from scripts.r3_package import r3_package_agent
from scripts.common import make_opponent,play_game
from scripts.par_eval import require_no_agent_errors
from scripts.experiment import limit_threads
from scripts.scoring import point_tile_map

HERE=Path(__file__).resolve().parent
PACK=HERE.parent/"feldprobe/ganze_partien.jsonl.gz"
DX=np.array([(0,0),(0,-1),(1,0),(0,1),(-1,0),(0,0)])


def archive():
    with gzip.open(PACK,"rt") as f:
        rows=list(map(json.loads,f))
    assert len(rows)==288
    return {(r["seed"],r["team"],r["arm"],r["opponent"]):r for r in rows}


def jobs(idx):
    tasks={}
    for r in idx.values():
        e=r["event"]
        if not e:continue
        s,t,opp=r["seed"],r["team"],r["opponent"]
        tasks[s,t,"probe",opp]=[(t,e)]
        if opp=="solution92":
            tasks[s,t,"reference",opp]=[(t,e)]
        else:
            tasks.setdefault((s,0,"reference","v16"),[]).append((t,e))
    assert sum(k[2]=="probe" for k in tasks)==56
    return tasks


def identity():
    return stamp(dict(base=common_source(),inputs={p.name:sha(p) for p in (PACK,HERE/"beobachten.py",HERE/"PLAN.md",HERE.parent/"feldprobe/kandidat.py",HERE.parent/"feldprobe/modell.json",HERE.parent/"feldprobe/signalmodell.py")}))


class Watch(Monitor):
    def __init__(self,env,team,brains,events):
        super().__init__(env,team,"discovery")
        self.brains=brains
        self.events_by_side=events
        self.readings={t:[] for t,_ in events}

    def step(self,cmd):
        tick=self.turn
        current={}
        for side,e in self.events_by_side:
            t=e["t"]
            if not t<=tick<(t//101+1)*101:continue
            player=self.brains[side]
            b=player._imitation.belief
            xy=tuple(e["xy"])
            mirror=(23-xy[1],23-xy[0])
            coord=mirror if b.mirrored else xy
            u=e["u"]
            # self.old is from this game's designated team. In the shared selfgame, use the correct side's own observation.
            obs=self.world_obs[f"player_{side}"]
            positions=np.asarray(obs["units"]["position"][side])
            opp=np.asarray(obs["units"]["position"][1-side])
            em=np.asarray(obs["units_mask"][1-side],bool)
            ene=int(np.asarray(obs["units"]["energy"][side,u]).item())
            cur=tuple(map(int,positions[u]))
            is_here=bool(obs["units_mask"][side,u] and ene>=0 and cur==xy)
            enemy_dist=int(np.abs(opp[em]-positions[u]).sum(1).min()) if em.any() else 99
            current[side]=dict(t=tick,known=bool(b.point_tiles[coord]),empty=bool(b.dead_tiles[coord]),here=is_here,
                energy=ene,enemy_dist=enemy_dist,sap_range=int(player.env_cfg["unit_sap_range"]),
                act=int(cmd[f"player_{side}"][u,0]))
        out=super().step(cmd)
        self.world_obs=out[0]
        if current:
            s=out[4]["final_state"]
            truth=point_tile_map(s)
            pos=np.asarray(s.units.position)
            live=np.asarray(s.units_mask)&(np.asarray(s.units.energy)[:,:,0]>=0)
            for side,e in self.events_by_side:
                if side not in current:continue
                target=tuple(e["xy"])
                mirror=(23-target[1],23-target[0])
                r=current[side]
                for who,n in ((side,"own"),(1-side,"other")):
                    direct=np.flatnonzero(live[who] & np.all(pos[who]==target,axis=1)).tolist()
                    sym=np.flatnonzero(live[who] & np.all(pos[who]==mirror,axis=1)).tolist() if mirror!=target else []
                    r[n+"_units"]=direct
                    r[n+"_point"]=int(bool(direct) and truth[target])
                    r[n+"_mirror"]=int(bool(sym) and truth[mirror])
                self.readings[side].append(r)
        return out

    def reset(self,**kw):
        r=super().reset(**kw)
        self.world_obs=r[0]
        return r


def one(env,k,events,idx,identity):
    s,t,version,opp=k
    torch.manual_seed(s)
    side=f"player_{t}";other=f"player_{1-t}"
    ours=create(side) if version=="probe" else r3_package_agent(side,PACKAGE)
    rival=make_opponent("solution92",other) if opp=="solution92" else r3_package_agent(other,PACKAGE)
    p=Watch(env,t,{t:ours,1-t:rival},events)
    result=play_game(p,ours,rival,s,side,False)
    require_no_agent_errors(ours.base if version=="probe" else ours,rival)
    assert p.turn==303 and result["game_win"]==int(sum(m["win"] for m in p.matches)>=2)
    if k in idx:
        anchor=idx[k]
        assert p.digest.hexdigest()==anchor["hash"] and p.matches==anchor["matches"]
    for n,e in events:
        trace=p.readings[n]
        assert len(trace)==101-e["t"]%101 and trace[0]["t"]==e["t"]
        if version=="probe":
            assert all(ours.event[k]==e[k] for k in ("t","xy","ref","u","old","d"))
            assert bool(e["scored"])==bool(trace[0]["own_point"] and e["u"] in trace[0]["own_units"])
    return dict(key=k,source=identity,hash=p.digest.hexdigest(),matches=p.matches,readings=p.readings)


def main():
    from luxai_s3.wrappers import LuxAIS3GymEnv
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path);p.add_argument("lane",type=int);p.add_argument("stride",type=int)
    a=p.parse_args()
    limit_threads()
    ident=identity()
    idx=archive();tasks=jobs(idx)
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for k in sorted(tasks)[a.lane::a.stride]:
            if datetime.now(CUTOFF.tzinfo)>=CUTOFF:break
            f=a.folder/"spiele"/("_".join(map(str,k))+".json")
            if f.exists():
                assert json.loads(f.read_text())["source"]==ident
                continue
            write_once(f,one(env,k,tasks[k],idx,ident))
    finally:
        env.close()
    assert identity()==ident


if __name__=="__main__":
    main()
