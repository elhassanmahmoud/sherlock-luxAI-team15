"""Compare the same learned search route for all idle, free units at the first real decision."""
from pathlib import Path
import argparse
import gzip
import json
import sys
import jax
import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.flottenblick.flotte import DIRECTIONS,History,POWER,flat,inputs,option_frame,support
from experiments.analysis.relictsuche_20261123.flottenblick.vorhersage import load,predict
from experiments.analysis.relictsuche_20261123.ortundflotte.richtung import take,score_options
from experiments.analysis.relictsuche_20261123.vergleich.panel import sensor
from experiments.analysis.relictsuche_20261123.vergleich.spielen import sha,write_once
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'flottenblick'))
from sammeln import capture,initialize,without
THRESHOLDS=(0.,1.,3.,float('inf'))


def proposals(state,original,history,team,step,net):
    first=option_frame(state,original,history,team)
    if first is None:return []
    peak=[]
    ids=state[1]
    ordered=[first['uid']]+[int(i) for i in ids if i!=first['uid'] and original[i,0]==0 and history.stays[i]>=4]
    for i,uid in enumerate(ordered):
        f=first if i==0 else option_frame(state,original,history,team,fixed=uid)
        if f is None:continue
        codes,lengths,paths=support(f)
        if len(np.unique(DIRECTIONS[codes,0]))<2:
            if i==0:return []
            continue
        x,dist=inputs(f,history,step)
        q=predict(*net,x,dist);ctx=f['ctx'];start=int(flat(f['start']))
        vals=score_options(q,paths,history.last_seen,ctx['nebula'],ctx['energy_map'],start)[2]
        pick=take(vals)
        route=np.full(8,start) if pick==len(paths) else paths[pick]
        peak.append(dict(uid=uid,margin=float(vals[:-1].max()-vals[-1]),route=route,frame=f,
                         code=None if pick==len(paths) else int(codes[pick]),length=0 if pick==len(paths) else int(lengths[pick])))
    return peak


def choose(rows,tolerance):
    best=max(range(len(rows)),key=lambda i:rows[i]['margin'])
    return best if best and rows[best]['code'] is not None and rows[best]['margin']>rows[0]['margin']+tolerance else 0


def game(env,seed,index,net):
    team,side,other,opp,actor,rival,obs=initialize(env,seed,index)
    h=History();decision=[];t0=None;future=[]
    aims=np.asarray(env.state.relic_nodes)[[0,3]]
    aims=24*aims[:,0]+aims[:,1]
    birth=int(env.state.relic_spawn_schedule[0])
    for t in range(85):
        public=obs[side];h.observe(t,public,team)
        if not decision and (h.finished or t>76):break
        original=actor.act(t,public);state=actor._imitation.last_fz
        h.proposals(state,original,team)
        if not decision and t>=16:
            decision=proposals(state,original,h,team,t,net)
            if decision:t0=t
        enemy=rival.act(t,obs[other])
        obs=env.step({side:original,other:enemy})[0]
        if decision:
            future.append(capture(env,team,side,obs))
            if len(future)==8:break
    require_no_agent_errors(actor,rival)
    rows=[]
    for r in decision:
        power=np.stack([without(v,r['uid']).ravel()[aims] for v in future])
        assert power.shape==(8,2)
        view=((power+POWER[r['route'][:,None],aims])>0).any(1)&(t0+np.arange(1,9)>=birth+1)
        delay=int(view.argmax()+1 if view.any() else 9)
        rows.append(dict(uid=int(r['uid']),margin=r['margin'],code=r['code'],sight=delay))
    picks=[choose(rows,limit) if rows else 0 for limit in THRESHOLDS]
    return dict(seed=seed,team=team,opponent=opp,turn=t0,options=rows,picks=picks)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder',type=Path);p.add_argument('stage',choices=('train','valid'));p.add_argument('op',choices=('play','score'))
    p.add_argument('lane',type=int,nargs='?',default=0);p.add_argument('stride',type=int,nargs='?',default=1)
    a=p.parse_args();limit_threads()
    n,start=(160,165010000) if a.stage=='train' else (80,165020000)
    if a.stage=='valid' and not json.loads((HERE/'train.json').read_bytes())['passed']:return
    pool=np.arange(start,start+2000,dtype=np.int32);seeds=list(map(int,pool[np.asarray(jax.jit(jax.vmap(sensor))(pool))==1][:n]))
    def target(s):return a.folder/a.stage/f'{s}.json'
    if a.op=='play':
        env=LuxAIS3GymEnv(numpy_output=True);net=load()
        try:
            for i in range(a.lane,n,a.stride):
                if not target(seeds[i]).exists():write_once(target(seeds[i]),game(env,seeds[i],i,net))
        finally:env.close()
        return
    rows=[json.loads(target(s).read_bytes()) for s in seeds]
    result=np.array([[0 if not r['options'] else r['options'][0]['sight']-r['options'][k]['sight'] for k in r['picks']] for r in rows])
    av=result.mean(0)
    j=int(3-np.argmax(av[::-1])) if a.stage=='train' else json.loads((HERE/'train.json').read_bytes())['chosen']
    diff=result[:,j];changed=sum(r['picks'][j]>0 for r in rows)
    draw=np.random.default_rng(231123).integers(0,n,(20000,n))
    write_once(HERE/(a.stage+'.json'),dict(cards=n,any_route=sum(bool(r['options']) for r in rows),multiple=sum(len(r['options'])>1 for r in rows),
               chosen=j,alternatives=av.tolist(),changed=changed,earlier=int((diff>0).sum()),later=int((diff<0).sum()),
               ci=np.quantile(diff[draw].mean(1),[.025,.975]).tolist(),passed=bool(j<3 and av[j]>0 and (a.stage=='train' or changed>=3))))
    (HERE/(a.stage+'_karten.jsonl.gz')).write_bytes(gzip.compress(b''.join(json.dumps(v,separators=(',',':')).encode()+b'\n' for v in rows),mtime=0))


if __name__=='__main__':main()
