"""Evaluate one safe revision of the current scout route after three real steps."""
import argparse
import gzip
import json
from pathlib import Path
import sys
import jax
import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.ortundflotte.kandidat import create
from experiments.analysis.relictsuche_20261123.ortundflotte.richtung import score_options
from experiments.analysis.relictsuche_20261123.flottenblick.flotte import DX,DY,POWER,DIRECTIONS,flat,inputs,option_frame,support
from experiments.analysis.relictsuche_20261123.flottenblick.vorhersage import predict
from experiments.analysis.relictsuche_20261123.vergleich.panel import sensor
from experiments.analysis.relictsuche_20261123.vergleich.spielen import write_once
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'flottenblick'))
from sammeln import capture,initialize,without
THRESHOLDS=(0.,1.,3.,float('inf'))


def decision(scout,original,state,old,step):
    team=scout.base.team_id
    f=option_frame(state,original,scout.history,team,scout.uid)
    if f is None or len(old)<2 or not f['first'][old[0]]:return None
    start=np.asarray(f['start'])
    previous=start+np.cumsum(np.column_stack((DX[old],DY[old])),axis=0)
    if np.any((previous<0)|(previous>=24)) or not np.all(f['ctx']['passable'][tuple(previous.T)]):return None
    ids,lengths,paths=support(f)
    allowed=(lengths>=len(old))&(DIRECTIONS[ids,0]!=old[0])
    if not allowed.any():return None
    ids=ids[allowed];paths=paths[allowed,:len(old)]
    paths=np.vstack((flat(previous),paths))
    x,dist=inputs(f,scout.history,step)
    q=predict(scout.net,scout.model,x,dist)
    ctx=f['ctx']
    score=score_options(q,paths,scout.history.last_seen,ctx['nebula'],ctx['energy_map'],int(flat(start)))[2,:-1]
    best=1+int(np.argmax(score[1:]))
    return paths[[0,best]],float(score[best]-score[0]),DIRECTIONS[ids[best-1],:len(old)].tolist()


def game(env,seed,index):
    team,side,other,opp,unused,rival,obs=initialize(env,seed,index)
    scout=create(side);scout.new_game(side);scout.set_env_cfg(unused.env_cfg)
    aims=np.asarray(env.state.relic_nodes)[[0,3]];aims=24*aims[:,0]+aims[:,1];spawn=int(env.state.relic_spawn_schedule[0])
    change=None;sensors=[];point=None
    for t in range(85):
        history=scout.history;previous=list(scout.route)
        ready=(not scout.done and scout.event and t==scout.event['step']+3 and len(previous)>=2)
        cmd=scout.act(t,obs[side])
        if ready and not scout.done and not history.finished and len(scout.route)==len(previous)-1:
            # The unaltered proposal for the already bound ship may have been overwritten by the scout.
            # Its native action is recovered below from a per-tick copy captured by the base hook.
            change=decision(scout,captured[0],scout.base._imitation.last_fz,np.array(previous),t)
            if change is not None:point=int(t)
        if t==0:
            captured=[None];native=scout.base.act
            def remember(*args,**kwargs):
                proposed=native(*args,**kwargs);captured[0]=np.asarray(proposed).copy();return proposed
            scout.base.act=remember
        enemy=rival.act(t,obs[other]);obs=env.step({side:cmd,other:enemy})[0]
        if change is not None:
            sensors.append(without(capture(env,team,side,obs),scout.uid).ravel()[aims])
            if len(sensors)==change[0].shape[1]:break
        elif scout.done or history.finished or (scout.event and t>=scout.event['step']+3) or t>76 and scout.uid is None:break
    require_no_agent_errors(scout.base,rival)
    if change is None:return dict(seed=seed,opponent=opp,team=team,turn=None)
    routes,advantage,direction=change
    n=routes.shape[1];assert len(sensors)==n
    sight=((np.array(sensors)+POWER[routes[:,:,None],aims])>0).any(2)&(point+np.arange(1,n+1)>=spawn+1)
    delays=np.where(sight.any(1),sight.argmax(1)+1,n+1)
    return dict(seed=seed,opponent=opp,team=team,turn=point,gain=advantage,delay=delays.tolist(),uid=int(scout.uid),routes=routes.tolist())


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);p.add_argument('stage',choices=('train','valid'))
    p.add_argument('op',choices=('play','score'));p.add_argument('lane',type=int,nargs='?',default=0);p.add_argument('stride',type=int,nargs='?',default=1)
    a=p.parse_args();limit_threads();n,start=(192,165100000) if a.stage=='train' else (80,165110000)
    if a.stage=='valid' and not json.loads((HERE/'train.json').read_bytes())['passed']:return
    pool=np.arange(start,start+2000,dtype=np.int32);seeds=list(map(int,pool[np.asarray(jax.jit(jax.vmap(sensor))(pool))==1][:n]))
    def dest(s):return a.folder/a.stage/f'{s}.json'
    if a.op=='play':
        env=LuxAIS3GymEnv(numpy_output=True)
        try:
            for i in range(a.lane,n,a.stride):
                if not dest(seeds[i]).exists():write_once(dest(seeds[i]),game(env,seeds[i],i))
        finally:env.close()
        return
    rows=[json.loads(dest(s).read_bytes()) for s in seeds]
    diff=np.array([[v['delay'][0]-v['delay'][1] if v['turn'] is not None and v['gain']>h else 0 for h in THRESHOLDS] for v in rows])
    avg=diff.mean(0);idx=int(3-np.argmax(avg[::-1])) if a.stage=='train' else json.loads((HERE/'train.json').read_bytes())['choice']
    selections=sum(v['turn'] is not None and v['gain']>THRESHOLDS[idx] for v in rows)
    rand=np.random.default_rng(231123).integers(0,n,(20000,n));val=diff[:,idx]
    write_once(HERE/(a.stage+'.json'),dict(cards=n,offered=sum(r['turn'] is not None for r in rows),choice=idx,changed=selections,mean=avg.tolist(),
               earlier=int((val>0).sum()),later=int((val<0).sum()),ci=np.quantile(val[rand].mean(1),[.025,.975]).tolist(),
               passed=bool(idx<3 and avg[idx]>0 and (a.stage=='train' or selections>=3))))
    (HERE/(a.stage+'_karten.jsonl.gz')).write_bytes(gzip.compress(b''.join(json.dumps(r,separators=(',',':')).encode()+b'\n' for r in rows),mtime=0))


if __name__=='__main__':main()
