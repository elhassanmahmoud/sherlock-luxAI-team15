"""Compare frozen scout routes, weighting earlier actual sightings by verified original-course field income."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.nutzbarer_fund.ertrag import HERE,COORD,PAIR_END,XY,value_weights
from experiments.analysis.relictsuche_20261123.ortundflotte.richtung import score_options,take
from experiments.analysis.relictsuche_20261123.flottenblick.flotte import PAIR,POWER,paint
from experiments.analysis.relictsuche_20261123.flottenblick.vorhersage import arrays,OFFSETS,load,predict
from experiments.analysis.relictsuche_20261123.zielschaetzer.kandidat import parameters
from experiments.analysis.relictsuche_20261123.vergleich.spielen import CUTOFF,sha,stamp,write_once
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
sys.path.insert(0,str(HERE.parent/"flottenblick"))
from sammeln import initialize


def route_scores(q,paths,last,fog,energy,origin,value):
    patterns=np.vstack((paths,np.full((1,8),origin)))
    cells,inside=arrays(patterns)
    vision=np.where(fog.ravel()[cells]&~np.all(OFFSETS==0,axis=1),.25,1)*inside*(.97**np.arange(1,9))[None,:,None]
    footprint=np.zeros((len(patterns),576),np.float32)
    np.maximum.at(footprint,(np.arange(len(patterns))[:,None,None],PAIR[cells]),vision)
    mirror=(23-XY[:,1])*24+23-XY[:,0]
    seen=np.maximum(last.ravel(),last.ravel()[mirror])
    fresh=np.where(seen<0,1.,.55*np.maximum(0,1-seen/50))
    q=q.ravel()
    other=np.where(np.arange(576)==mirror,q,1-(1-q)*(1-q[mirror]))
    mass=np.zeros(576);prior,_=parameters();mass[24*COORD[:,0]+COORD[:,1]]=prior/prior.mean()*value
    cost=.08*np.sum(fog.ravel()[patterns],axis=1)+.025*np.maximum(0.,-energy.ravel()[patterns]).mean(1)
    return footprint@(mass*fresh*(1-other))-cost


def trace(env,path,model):
    rec=json.loads(path.with_suffix(".json").read_text());seed=rec["seed"]
    assert sha(path)==rec["sha256"]
    with np.load(path,allow_pickle=False) as src:
        ts,x,dist,offset,paths,last,remaining,uids=[src[k] for k in ("turn","x","projections","offsets","paths","last","remaining","uid")]
    if not len(ts):return dict(seed=seed,cases=[],played=0)
    n,side,other,_,actor,rival,obs=initialize(env,seed,rec["index"])
    aims=[x*24+y for x,y in np.asarray(env.state.relic_nodes)[[0,3]].astype(int)]
    spawn=int(env.state.relic_spawn_schedule[0])
    score=[];cases=[]
    end=int(ts[-1])+24;assert end<=100
    lookup={int(t):j for j,t in enumerate(ts)}
    for t in range(end+1):
        public=obs[side]
        score.append(int(public["team_points"][n]))
        if t in lookup:
            j=lookup[t];live=np.asarray(public["units_mask"][n])&(np.asarray(public["units"]["energy"][n]).reshape(-1)>=0)
            uid=int(uids[j]);assert live[uid]
            loc=np.asarray(public["units"]["position"][n],int).copy()
            if n:loc=23-loc[:,::-1]
            assert np.argmax(x[j,12])==24*loc[uid,0]+loc[uid,1]
            assert np.allclose(x[j,0],paint(loc[live & (np.arange(16)!=uid)]),atol=.001)
            p=paths[offset[j]:offset[j+1]]
            board=x[j].astype(np.float32);q=predict(*model,board,dist[j])
            origin=int(np.argmax(board[12]));fog=board[18].astype(bool);energy=board[19]*20
            v=value_weights(loc[live],board[17].astype(bool))
            before=score_options(q,p,last[j],fog,energy,origin)[2]
            check=route_scores(q,p,last[j],fog,energy,origin,np.ones(len(v)))
            assert np.allclose(before,check,rtol=1e-5,atol=5e-6) and take(before)==take(check)
            selected=[take(before),take(route_scores(q,p,last[j],fog,energy,origin,v))]
            choices=np.vstack((p,np.full((1,8),origin)))
            seen=((remaining[j].reshape(8,576)[:,aims]+POWER[choices[:,:,None],aims])>0).any(2)&(t+np.arange(1,9)>=spawn+1)
            sight=np.where(seen.any(1),seen.argmax(1)+1,9)
            cases.append(dict(t=t,choice=selected,sight=sight[selected].tolist()))
        if t<end:
            cmds={side:actor.act(t,public),other:rival.act(t,obs[other])}
            obs=env.step(cmds)[0]
    require_no_agent_errors(actor,rival)
    for c in cases:c["credits"]=score[c["t"]+24]-score[c["t"]]
    return dict(seed=seed,cases=cases,played=end)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("raw",type=Path);p.add_argument("folder",type=Path)
    p.add_argument("stage",choices=("play","score"));p.add_argument("lane",nargs="?",type=int,default=0);p.add_argument("stride",nargs="?",type=int,default=1)
    a=p.parse_args();limit_threads()
    assert json.loads((HERE/"valid.json").read_bytes())["passed"]
    files=sorted((a.raw/"valid").glob("*.npz"));assert len(files)==160
    token=stamp({p.name:sha(p) for p in (HERE/"PLAN.md",HERE/"ertrag.py",HERE/"modell.json",HERE/"valid.json",Path(__file__))})
    def dest(f):return a.folder/(f.stem+".json")
    if a.stage=="play":
        env=LuxAIS3GymEnv(numpy_output=True);model=load()
        try:
            for f in files[a.lane::a.stride]:
                if datetime.now(CUTOFF.tzinfo)>=CUTOFF:break
                if dest(f).exists():assert json.loads(dest(f).read_text())["source"]==token
                else:write_once(dest(f),dict(source=token,**trace(env,f,model)))
        finally:env.close()
        return
    rows=[json.loads(dest(f).read_text()) for f in files]
    assert len({r["seed"] for r in rows})==160 and all(r["source"]==token for r in rows)
    def per(r):
        z=r["cases"]
        if not z:return [0,0]
        gain=np.array([v["sight"][0]-v["sight"][1] for v in z]);credits=np.array([v["credits"]/24 for v in z])
        return [gain.mean(),(gain*credits).mean()]
    vals=np.array([per(r) for r in rows]);mean=vals.mean(0)
    draws=np.random.default_rng(231123).integers(0,160,(20000,160))
    write_once(HERE/"routen.json",dict(source=token,passed=bool(mean[0]>=0 and mean[1]>0),means=mean.tolist(),
            ci=np.quantile(vals[draws].mean(1),[.025,.975],axis=0).T.tolist(),situations=sum(len(r["cases"]) for r in rows),cards=rows))


if __name__=="__main__":main()
