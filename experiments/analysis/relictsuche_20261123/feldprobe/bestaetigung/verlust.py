"""Reproduce both full trajectories of the single newly lost confirmation seat without changing play."""
import gzip
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch

from spielen import HERE, FIELD, PACKAGE, CurrentMonitor, check, create, decode, limit_threads, make_opponent, play_game, require_no_agent_errors, r3_package_agent, sha, write_once
from scripts.scoring import point_tile_map

OUTPUT=HERE/"verlust"
SEED=162800176


def cells(grid):
    return np.flatnonzero(np.asarray(grid).ravel()).tolist()


def visible_public(obs):
    return [list(map(int,p)) for p in np.asarray(obs["relic_nodes"])[np.asarray(obs["relic_nodes_mask"],bool)]]


class Trace(CurrentMonitor):
    def __init__(self,env,base,actor):
        super().__init__(env,0,actor,"confirm")
        self.base_for_review=base
        self.trace=[]

    def step(self,actual):
        t=self.turn
        b=self.base_for_review._imitation.belief
        obs=self.old
        e=self.probe.event if self.probe else None
        snapshot=dict(t=t,known=cells(b.point_tiles),dead=cells(b.dead_tiles),zone=cells(b.relic_zone),
                      before_positions=np.asarray(obs["units"]["position"][0],int).tolist(),
                      before_alive=np.asarray(obs["units_mask"][0],int).tolist(),
                      before_energy=np.asarray(obs["units"]["energy"][0],int).reshape(-1).tolist(),
                      known_relic_observations=visible_public(obs),official=np.asarray(actual["player_0"] if self.original is None else self.original,int).tolist(),
                      own_cmd=np.asarray(actual["player_0"],int).tolist(),opp_cmd=np.asarray(actual["player_1"],int).tolist(),
                      own_sight=cells(obs["sensor_mask"]))
        if e and e["t"]==t:
            from experiments.analysis.relictsuche_20261123.feldprobe.signalmodell import options,pick,proba,HISTORY,STATIC
            from experiments.analysis.relictsuche_20261123.feldprobe.kandidat import columns
            fz=self.probe.base._imitation.last_fz
            ids=np.asarray(fz[1],int); feat=fz[2]; masks=fz[3]
            allowed=np.zeros((16,5),bool);allowed[ids]=masks[:,:5]
            busy=np.ones(16,bool);pts,sap=columns()
            busy[ids]=(feat[:,pts].max(axis=1)>0)|(feat[:,sap]>0)
            positions=np.array(snapshot["before_positions"]);ene=np.array(snapshot["before_energy"])
            live=np.array(snapshot["before_alive"],bool)&(ene>=0)
            opt=options(self.probe.history,t%101,t//101+1,0,positions,ene,live,b.point_tiles,b.tile_type,
                        self.original,allowed,busy,self.probe.base.env_cfg["unit_move_cost"])
            chosen=opt[pick(opt,self.probe.model)]
            check(chosen[0]==e["u"] and chosen[1]==e["d"],"Public diagnostic decision differs")
            snapshot["decision"]={"scores":proba(self.probe.model,[chosen[4],chosen[5]]).tolist(),
                "features_new":dict(zip(STATIC+HISTORY,map(float,chosen[4]),strict=True)),
                "features_original":dict(zip(STATIC+HISTORY,map(float,chosen[5]),strict=True))}
        result=super().step(actual)
        st=result[4]["final_state"]
        truth=point_tile_map(st)
        pos=np.asarray(st.units.position,int)
        alive=np.asarray(st.units_mask,bool)&(np.asarray(st.units.energy)[...,0]>=0)
        energy=np.asarray(st.units.energy,int)[...,0]
        point_cells=[]
        occupancy=[]
        for team in (0,1):
            alive_cells=np.unique(pos[team][alive[team]],axis=0)
            scored=[int(x)*24+int(y) for x,y in alive_cells if truth[x,y]]
            point_cells.append(sorted(scored))
            occupancy.append([[int(uid),*list(map(int,pos[team,uid])),int(energy[team,uid])] for uid in np.flatnonzero(alive[team])])
        check([len(g) for g in point_cells]==self.profile[-1],"Occupancy not equal to game points")
        snapshot.update(truth=cells(truth),points=point_cells,occupancy=occupancy,credit=self.profile[-1])
        self.trace.append(snapshot)
        return result


def main():
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads()
    root=HERE/"sicht1"
    original_rows=decode(root/"partien.jsonl.gz")
    index={r["arm"]:r for r in original_rows if r["seed"]==SEED and r["team"]==0 and r["opponent"]=="solution92"}
    env=LuxAIS3GymEnv(numpy_output=True)
    records=[]
    try:
        for arm in ("reference","probe"):
            random.seed(SEED);torch.manual_seed(SEED);np.random.seed(SEED)
            own=create("player_0") if arm=="probe" else r3_package_agent("player_0",PACKAGE)
            other=make_opponent("solution92","player_1")
            base=own.base if arm=="probe" else own
            mon=Trace(env,base,own if arm=="probe" else None)
            result=play_game(mon,own,other,SEED,"player_0",False)
            require_no_agent_errors(base,other)
            old=index[arm]
            check(mon.digest.hexdigest()==old["hash"] and mon.matches==old["matches"] and mon.profile==old["profile"] and
                  mon.detail==old["event"] and len(mon.trace)==303 and result["game_win"]==old["win"],"Unfaithful archived trajectory")
            records.append(dict(arm=arm,archived_commands=old["hash"],trace=mon.trace))
    finally:env.close()
    r,c=[x["trace"] for x in records]
    tick=index["probe"]["event"]["t"]
    check(r[:tick]==c[:tick],"History differs before intervention")
    check(r[tick]["own_cmd"]==c[tick]["official"] and r[tick]["opp_cmd"]==c[tick]["opp_cmd"] and sum(
        a!=b for a,b in zip(r[tick]["own_cmd"],c[tick]["own_cmd"]))==1,"Wrong difference at switch")
    OUTPUT.mkdir(parents=True,exist_ok=True)
    archive=OUTPUT/"zuege.jsonl.gz"
    binary=b"".join(json.dumps(x,sort_keys=True,separators=(",",":")).encode()+b"\n" for x in records)
    if not archive.exists():archive.write_bytes(gzip.compress(binary,mtime=0))
    check(gzip.decompress(archive.read_bytes())==binary,"Existing raw differs")
    write_once(OUTPUT/"reproduktion.json",dict(seed=SEED,side=0,changed_tick=tick,arm_action_sha256={a:index[a]["hash"] for a in index},
                  total_reproduced_commands=2*303*2*16,exact_preturn_steps=tick,source_archive_sha256=sha(root/"partien.jsonl.gz"),
                  trace_sha256=sha(archive),event=index["probe"]["event"]))
    print(SEED,tick,sha(archive),flush=True)


if __name__=="__main__":
    main()
