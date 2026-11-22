"""Reproducible public teacher labels, referee-only loss diagnosis, and a single matched continuation."""
from __future__ import annotations
import argparse
from collections import defaultdict
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT))
from regel import DIR, ReturnPolicy
from scripts.experiment import limit_threads
from scripts.fetch_kaggle3 import verify
from scripts.r3_package import r3_package_agent
from scripts.scoring import match_points_after_step,point_tile_map
from scripts.common import make_opponent
from scripts.par_eval import require_no_agent_errors
from scripts.kaggle3_opponent import Kaggle3Opponent

PACKAGE=ROOT/'experiments/releases/20261117_sherlock_v16/agent.zip'
DIGEST='0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099'
spec=importlib.util.spec_from_file_location('referee_diagnosis',ROOT/'experiments/analysis/r3_kaggle_20261117/diagnose.py')
diag=importlib.util.module_from_spec(spec)
spec.loader.exec_module(diag)


class IndependentRNG:
    # The shadow runs on its own RNG streams, including initialization.
    def __init__(self,seed):
        import torch
        self.state=(random.Random(seed).getstate(),np.random.RandomState(seed).get_state(),
                    torch.Generator().manual_seed(seed).get_state())

    @contextmanager
    def active(self):
        import torch
        def read(): return (random.getstate(),np.random.get_state(),torch.get_rng_state())
        def restore(s):
            random.setstate(s[0]); np.random.set_state(s[1]); torch.set_rng_state(s[2])
        real=read()
        restore(self.state)
        try:
            yield
        finally:
            self.state=read()
            restore(real)


def write(path,payload):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists(): raise FileExistsError(path)
    temp=path.with_suffix('.partial')
    temp.write_text(json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n')
    temp.replace(path)


def state_hash(state):
    import jax
    h=hashlib.sha256()
    for leaf in jax.tree_util.tree_leaves(state):
        arr=np.asarray(leaf)
        h.update(str((arr.dtype,arr.shape)).encode())
        h.update(arr.tobytes())
    return h.hexdigest()


def lost_causes(s,post,acts,p,group,losses):
    assessment=diag.account(s,acts,p)
    alive_after=np.asarray(post.units_mask,dtype=bool)&(np.asarray(post.units.energy)[...,0]>=0)
    next_pos=np.asarray(post.units.position)
    result={}
    for tile in losses:
        uids=[int(u) for u in np.flatnonzero(assessment['alive'][group]) if tuple(s['pos'][group,u])==tile]
        types=[]
        for u in uids:
            if alive_after[group,u] and tuple(next_pos[group,u])!=tile and acts[group,u,0] in (1,2,3,4):
                types.append('bewegung_ueberlebt')
            elif assessment['collided'][group,u]:
                types.append('kollision')
            elif not alive_after[group,u]:
                sap=sum(assessment['fl'][k][group,u] for k in ('sap_direct_in','sap_splash_in'))
                void=assessment['fl']['void_in'][group,u]
                types.append('sap_und_sog' if sap and void else 'sap_beteiligt' if sap else 'sog_beteiligt' if void
                             else 'energie_oder_andere_ursache')
            else:
                types.append('anderer_uebergang')
        result[tile]='+'.join(sorted(set(types))) or 'keine_lebende_voreinheit'
    return result


def run_one(seed,side_id,folder,fork=None):
    limit_threads()
    import torch
    from luxai_s3.wrappers import LuxAIS3GymEnv
    team=int(side_id)
    side,other=f'player_{team}',f'player_{1-team}'
    path=folder/f'{seed}_{team}.json'
    if fork is None:
        dest=path
        target=None
    else:
        base_data=json.loads(path.read_text())
        target=base_data['selected'][fork]
        dest=folder/f'{seed}_{team}_m{target["match"]}.json'
    if dest.exists(): raise FileExistsError(dest)
    if hashlib.sha256(PACKAGE.read_bytes()).hexdigest()!=DIGEST or not verify(): raise ValueError('Source')
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    me=r3_package_agent(side,PACKAGE)
    enemy=make_opponent('kaggle3',other)
    adapter=ReturnPolicy(me)
    stream=IndependentRNG(seed)
    # Branches omit the teacher entirely. Prefix/decision equality also tests that
    # the shadow did not affect the two players or the environment.
    teacher=None
    if target is None:
        with stream.active():
            teacher=Kaggle3Opponent(side)
    env=LuxAIS3GymEnv(numpy_output=True)
    for agent,which in ((me,side),(enemy,other)):
        if hasattr(agent,'new_game'): agent.new_game(which)
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    obs,info=env.reset(seed=seed)
    parameters={k:info['full_params'][k] for k in ('unit_sap_cost','unit_sap_range','unit_sap_dropoff_factor','unit_energy_void_factor','unit_move_cost')}
    for agent in (me,enemy): agent.set_env_cfg(info['params'])
    if teacher is not None:
        with stream.active(): teacher.set_env_cfg(info['params'])
    losses=[];selected=[];events=[];frames=[];barriers={}
    steps=0; prefix=hashlib.sha256()
    end=target['step']+8 if target is not None else 303
    for step in range(end):
        m,ms=divmod(step,101)
        if ms==0: 
            early=set()
            previous=set()
            gaps={}
        s=diag.snap(env.state) if fork is None and ms>=70 else None
        original=np.asarray(me.act(step,obs[side]))
        other_act=np.asarray(enemy.act(step,obs[other]))
        options,vacant=adapter.options(obs[side],original)
        if fork is None and 71<=ms<=94:
            from barrieren import count
            count(adapter,obs[side],original,early,previous,options,barriers)
        if teacher is not None:
            with stream.active():
                label=teacher.act(step,obs[side])
        score=np.stack((original,other_act) if team==0 else (other_act,original)).astype(np.int16)
        prefix.update(score.tobytes())
        chosen=options[0] if options else None
        adjusted=original
        if chosen is not None and (fork is None or step==target['step']):
            item=dict(**chosen,step=step,match=m+1,ms=ms,n_options=len(options))
            if fork is None:
                item['teacher']=int(label[chosen['uid'],0])
                events.append(item)
                if not any(x['match']==m+1 for x in selected):
                    selected.append(dict(**item,prefix=prefix.hexdigest(),state=state_hash(env.state)))
            elif (target['prefix']!=prefix.hexdigest() or target['state']!=state_hash(env.state)
                    or any(target[k]!=v for k,v in item.items())):
                raise ValueError(f'Divergent branch state, proposed commands or teacher {target}')
            else:
                adjusted=adapter.apply(original,chosen)
                uid=chosen['uid']
                loc=np.asarray(obs[side]['units']['position'])[team,uid]
                expected_world=loc+np.asarray(DIR[int(adjusted[uid,0])])
                if (not np.array_equal(expected_world,chosen['world']) or
                        np.count_nonzero(np.any(original!=adjusted,axis=1))!=1):
                    raise ValueError('Seat transformation or single-unit intervention')
        if target is not None and step==target['step'] and adjusted is original:
            raise ValueError('Target never intervened')
        if target is not None and step<target['step']:
            expected=base_data['frames'][step]
        if teacher is not None:
            with stream.active():
                teacher.remember_played_actions(adjusted)
        next_obs,_,term,trunc,info=env.step({side:adjusted,other:other_act})
        terminal=bool(term[side]) or bool(trunc[side])
        if terminal!=(step==302): raise ValueError('Game length')
        gain=(match_points_after_step(obs[side],next_obs[side],info)-np.asarray(obs[side]['team_points'])).astype(int)
        post=info['final_state']
        actual=point_tile_map(post)
        pos=np.asarray(post.units.position)
        live=np.asarray(post.units_mask,dtype=bool)&(np.asarray(post.units.energy)[...,0]>=0)
        fields=[{tuple(map(int,xy)) for xy in pos[t,live[t]] if actual[tuple(xy)]} for t in (0,1)]
        if gain.tolist()!=list(map(len,fields)): raise ValueError('Score accounting')
        own,op=fields[team],fields[1-team]
        frame=dict(step=step,own=sorted(map(list,own)),gain=[int(gain[team]),int(gain[1-team])])
        if fork is not None and step<target['step'] and frame!=expected: raise ValueError('Referee trajectory')
        frames.append(frame)
        if ms<=70: early.update(own)
        if fork is None and ms>=70:
            fell=(previous-own)&early
            if fell:
                causes=lost_causes(s,post,score,parameters,team,fell)
                for tile in sorted(fell):
                    row=dict(match=m+1,ms=ms,tile=list(tile),cause=causes[tile],vacant_turns=0,returned=False)
                    losses.append(row)
                    gaps[tile]=row
            for tile in list(gaps):
                if tile in own:
                    gaps.pop(tile)['returned']=True
                else:
                    gaps[tile]['vacant_turns']+=1
        previous=own
        obs=next_obs;steps+=1
    require_no_agent_errors(me,enemy)
    if target is None:
        data=dict(seed=seed,side=team,steps=steps,gameside=side,match_wins=np.asarray(obs[side]['team_wins']).astype(int).tolist(),
                  selected=selected,events=events,losses=losses,frames=frames,barriers=barriers,zip_sha=DIGEST)
    else:
        ix=target['step']; span=slice(ix,ix+8)
        def outcomes(fs):
            delta=np.sum([r['gain'] for r in fs[span]],axis=0).tolist()
            return dict(points=delta,tile_turns=sum(target['world'] in r['own'] for r in fs[span]))
        data=dict(seed=seed,side=team,event=target,steps=steps,original=outcomes(base_data['frames']),
                  alternative=outcomes(frames),zip_sha=DIGEST)
    write(dest,data); env.close()
    print(dest.name,'complete',flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('seed',type=int);a.add_argument('side',type=int,choices=(0,1));a.add_argument('folder',type=Path)
    a.add_argument('--fork',type=int)
    v=a.parse_args()
    run_one(v.seed,v.side,v.folder,v.fork)
