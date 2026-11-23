"""Fit a single point-opportunity weight on real course trajectories and hold it fixed on other maps."""
import argparse
from datetime import datetime
import gzip
import json
from pathlib import Path
import sys
import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.suche_nach_punkten.richtung import options,WEIGHTS
from experiments.analysis.relictsuche_20261123.ortundflotte.richtung import take,score_options
from experiments.analysis.relictsuche_20261123.flottenblick.flotte import POWER,paint
from experiments.analysis.relictsuche_20261123.flottenblick.vorhersage import load,predict
from experiments.analysis.relictsuche_20261123.vergleich.spielen import CUTOFF,common_source,write_once,stamp,sha
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.scoring import point_tile_map

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"flottenblick"))
from sammeln import initialize


def trace(env,path,net):
    rec=json.loads(path.with_suffix(".json").read_text());seed=rec["seed"]
    assert sha(path)==rec["sha256"]
    with np.load(path,allow_pickle=False) as src:
        ts,x,dist,offset,paths,last,remaining,uids=[src[k] for k in ("turn","x","projections","offsets","paths","last","remaining","uid")]
    if not len(ts):return dict(seed=seed,situations=[],played=0)
    team,side,other,_,actor,rival,obs=initialize(env,seed,rec["index"])
    pos=[];live=[];active=[]
    aims=np.asarray(env.state.relic_nodes)[[0,3]];aims=24*aims[:,0]+aims[:,1]
    spawn=int(env.state.relic_spawn_schedule[0])
    end=int(ts[-1])+8;score=0
    for tick in range(end+1):
        public=obs[side];state=env.state
        xy=np.asarray(state.units.position[team],int)
        ok=np.asarray(state.units_mask[team],bool)&(np.asarray(state.units.energy[team]).reshape(-1)>=0)
        assert np.array_equal(np.asarray(public['units']['position'][team])[ok],xy[ok])
        points=point_tile_map(state)
        count=sum(points[p] for p in {tuple(c) for c in xy[ok]})
        total=int(public["team_points"][team]);assert tick==0 or total-score==count
        score=total
        if team:xy=23-xy[:,::-1];points=points[::-1,::-1].T
        pos.append(xy);live.append(ok);active.append(points.ravel())
        if tick<end:
            cmds={side:actor.act(tick,public),other:rival.act(tick,obs[other])}
            obs=env.step(cmds)[0]
    require_no_agent_errors(actor,rival);rows=[]
    for i,t in enumerate(ts):
        t=int(t);uid=int(uids[i]);board=x[i].astype(np.float32);origin=int(board[12].argmax())
        assert origin==24*pos[t][uid,0]+pos[t][uid,1] and np.allclose(board[0],paint(pos[t][live[t]&(np.arange(16)!=uid)]),atol=.001)
        p=paths[offset[i]:offset[i+1]]
        q=predict(*net,board,dist[i]);fog=board[18].astype(bool);energy=board[19]*20
        weighted=options(q,p,last[i],fog,energy,origin,(board[0]>0)|(board[1]>0))
        base=score_options(q,p,last[i],fog,energy,origin)[2]
        assert np.array_equal(weighted[0],base)
        choice=np.array([take(row) for row in weighted])
        routes=np.vstack((p,np.full((1,8),origin)))[choice]
        visual=((remaining[i].reshape(8,576)[:,aims]+POWER[routes[:,:,None],aims])>0).any(2)&(t+np.arange(1,9)>=spawn+1)
        possible=np.zeros((len(WEIGHTS),8),bool);team_paid=np.zeros(8,bool)
        for j in range(8):
            k=t+1+j;rest=pos[k][live[k]&(np.arange(16)!=uid)]
            occupied=24*rest[:,0]+rest[:,1];tile=routes[:,j]
            possible[:,j]=np.asarray(active[k])[tile]&~np.isin(tile,occupied)
            team_paid[j]=np.any(np.asarray(active[k])[occupied])
        def first(mask):return np.where(mask.any(1),mask.argmax(1)+1,9)
        sight=first(visual);info=first(visual|possible|team_paid);new=np.array([len(np.unique(r[m])) for r,m in zip(routes,possible,strict=True)])
        rows.append(dict(t=t,choice=choice.tolist(),sight=sight.tolist(),info=info.tolist(),fields=new.tolist()))
    return dict(seed=seed,situations=rows,played=end)


def score(rows,stage,signature):
    by=[]
    for r in rows:
        v=[]
        for e in r["situations"]:
            s,info,f=[np.asarray(e[k]) for k in ("sight","info","fields")]
            v.append([s[0]-s,info[0]-info,(info[0]-info)+.25*(f-f[0])])
        by.append(np.mean(v,axis=0) if v else np.zeros((3,len(WEIGHTS))))
    a=np.array(by)
    j=int(np.argmax(a.mean(0)[2])) if stage=="train" else json.loads((HERE/"train.json").read_bytes())["selected"]
    val=a[:,:,j];means=val.mean(0);n=len(rows)
    draw=np.random.default_rng(231123).integers(0,n,(20000,n))
    ahead=int(sum(val[:,2]>0));passed=j>0 and means[2]>0 and (stage=="train" or (means[0]>=-.05 and ahead>=4))
    write_once(HERE/(stage+".json"),dict(cards=n,situations=sum(len(r["situations"]) for r in rows),props=a.mean(0).tolist(),source=signature,
                 selected=j,weight=float(WEIGHTS[j]),benefit=means.tolist(),ci=np.quantile(val[draw].mean(1),[.025,.975],axis=0).T.tolist(),
                 advanced=ahead,delayed=int(sum(val[:,2]<0)),passed=bool(passed)))
    (HERE/f"{stage}_situationen.jsonl.gz").write_bytes(gzip.compress(b"".join(json.dumps(r,separators=(",",":")).encode()+b"\n" for r in rows),mtime=0))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("raw",type=Path);p.add_argument("folder",type=Path)
    p.add_argument("stage",choices=("train","valid"));p.add_argument("op",choices=("play","score"))
    p.add_argument("lane",type=int,nargs="?",default=0);p.add_argument("stride",type=int,nargs="?",default=1);a=p.parse_args();limit_threads()
    files=sorted((a.raw/a.stage).glob("*.npz"));assert len(files)==(480 if a.stage=="train" else 160)
    source=stamp(dict(base=common_source(),inputs={str(f.relative_to(HERE.parent)):sha(f) for f in [HERE/"PLAN.md",HERE/"richtung.py",Path(__file__),HERE.parent/"nutzbarer_fund/ertrag.py",HERE.parent/"ortundflotte/richtung.py"]}))
    if a.stage=="valid":
        fit=json.loads((HERE/"train.json").read_bytes());assert fit["passed"] and fit["source"]==source
    def dest(f):return a.folder/a.stage/(f.stem+".json")
    if a.op=="play":
        env=LuxAIS3GymEnv(numpy_output=True);net=load()
        try:
            for f in files[a.lane::a.stride]:
                if datetime.now(CUTOFF.tzinfo)>=CUTOFF:break
                if dest(f).exists():assert json.loads(dest(f).read_bytes())["source"]==source
                else:write_once(dest(f),dict(source=source,**trace(env,f,net)))
        finally:env.close()
    else:
        rows=[json.loads(dest(f).read_bytes()) for f in files];assert all(r["source"]==source for r in rows)
        score(rows,a.stage,source)


if __name__=="__main__":main()
