"""Fixed, two-stage match-end counterfactual pilot. No resume or training."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import random
import signal
import subprocess
import sys
import time
import numpy as np

from scripts.early_curriculum_study import digest, hashes, require, source_identity, resource_lock
from scripts.holder_rollout_probe import protected_inputs, foreign_processes, write_json, V14_SHA
from scripts.ensemble_diversity_eval_supervisor import check_usage
from scripts.final_training_supervisor import read_power

ROOT=Path(__file__).resolve().parents[1]
MAPS=(11011000,11011001,11011002,11011004,11011007,11011011,11011013,11011017)
FIRST=((11011017,'player_0'),(11011000,'player_0'))
KEYS=FIRST+tuple((s,p) for s in MAPS for p in ('player_0','player_1') if (s,p) not in FIRST)
PLANS=[ROOT/'docs/superpowers/specs/2026-11-10-match-outcome-selector-design.md',
       ROOT/'docs/superpowers/plans/2026-11-10-match-outcome-selector.md']
LIMITS={'reference_steps':16*303,'instrumented_steps':16*303,'diagnostic_steps':5856,
        'technical_extra_steps':976,'completed_pairs':48,'started_games':32,'completed_games':32}


def phase_keys(phase):
    require(phase in ('technical','remaining'),'Unknown phase')
    return list(KEYS[:2] if phase=='technical' else KEYS[2:])


def summarize_pairs(rows):
    keys=[(r['seed'],r['side'],r['candidate']['match']) for r in rows]
    require(len(keys)==len(set(keys)),'Duplicate opportunity')
    require(all(r['live_verified'] and r['delta_win'] in (-1,0,1) for r in rows),'Invalid/unverified pair')
    require(all(r['effective'] or (r['delta_win']==r['delta_points']==r['delta_h12']==0) for r in rows),
            'Ineffective pair has nonzero label')
    effective=[r for r in rows if r['effective']]
    positive=[r for r in rows if r['delta_win']>0]
    em=len({r['seed'] for r in effective});pm=len({r['seed'] for r in positive})
    b=len(effective)>=24 and em>=6;c=len(positive)>=3 and pm>=3
    return dict(cases=len(rows),effective_pairs=len(effective),effective_maps=em,
                positive_flips=len(positive),positive_maps=pm,
                negative_flips=sum(r['delta_win']<0 for r in rows),zero_flips=sum(r['delta_win']==0 for r in rows),
                delta_points_sum=sum(r['delta_points'] for r in rows),
                h12_end_sign_reversals=sum(r['delta_h12']*r['delta_points']<0 for r in rows),
                influence_gate=b,label_gate=c,passed=b and c)


class Guard:
    def __init__(self,state):self.state=state;self.last_check=0.
    def __call__(self,force=False):
        s=self.state;now=time.time()
        require(not Path(s['stop_file']).exists(),'STOP requested')
        if not force and now-self.last_check<10:return
        used=check_usage(s['usage_file'],now=now,max_used_percent=95)
        require(source_identity(ROOT,sys.executable,PLANS)==s['source'],'Frozen source changed')
        require(hashes(s['inputs'])==s['inputs'] and hashes(s['protected'])==s['protected'],'Input/protected file changed')
        snapshot=subprocess.check_output(['ps','-axo','pid=,pgid=,args='],text=True,timeout=5)
        require(not foreign_processes(snapshot,owner=os.getpid()),'Other model/test process active')
        power=read_power()
        require(type(power['ac']) is bool and type(power['percent']) is int,'Unknown power state')
        # User explicitly supervises battery operation; do not invent a new AC gate.
        s.update(last_guard_at=now,last_usage=used,last_power=power);self.last_check=now


def play(seed,side,weights,*,instrumented,out,guard,progress,verify_map):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from agents.sherlock.main import Agent_x
    from agents.Solution_92_Kaggle.base import Global
    from scripts.common import make_opponent
    from scripts.par_eval import build_cfg
    from scripts.holder_rollout import Snapshot,exact_digest,module_fingerprint
    from scripts.match_outcome_rollout import MatchOutcomeAgent,step_frame,paired_match_outcome
    import torch
    cls=MatchOutcomeAgent if instrumented else Agent_x
    agent=cls('player_0',agent_path=str(weights),cfg=build_cfg(str(weights),[]),train=False,seed=0)
    agent.set_to_eval_mode();agent.autosave_on_terminate=False
    for net in [agent.q,agent.target_q,*agent.extra_q]:net.eval().requires_grad_(False)
    before_modules=module_fingerprint(agent)
    other=f'player_{1-int(side[-1])}';opponent=make_opponent('solution92',other)
    agent.new_game(side);random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    env=LuxAIS3GymEnv(numpy_output=True)
    name=f'{seed}_{side}_'+('collector' if instrumented else 'reference')
    frame_path=out/(name+'.frames.jsonl.gz');pair_path=out/(name+'.pairs.jsonl.gz')
    pairs=[];pending=None;steps=0;resets=0;matches=[];totals=np.zeros(2,np.int64)
    trajectory=hashlib.sha256();verified=False
    def append(stream,row):stream.write(json.dumps(row,allow_nan=False,separators=(',',':'))+'\n');stream.flush()
    try:
        obs,info=env.reset(seed=seed)
        agent.set_env_cfg(info['params']);opponent.set_env_cfg(info['params'])
        require(int(info['params']['max_steps_in_match'])==100,'Unexpected match length')
        with gzip.open(frame_path,'xt',encoding='utf-8') as frames,gzip.open(pair_path,'xt',encoding='utf-8') as evidence:
            while True:
                guard();before=exact_digest(env.state),exact_digest(obs)
                ms=int(np.asarray(obs[side]['match_steps']));match=steps//101
                can_select=instrumented and pending is None and 40<=ms<=70 and match not in agent.used_matches
                if instrumented:agent.collect=can_select
                snapshot=Snapshot.capture(env,agent,opponent,obs,Global) if can_select else None
                actions={side:agent.act(steps,obs[side]),other:opponent.act(steps,obs[other])}
                require(not agent.caught_errors,'Caught live agent error')
                if can_select and agent.candidate is not None:
                    pair=paired_match_outcome(snapshot,side,agent.candidate,verify=verify_map and not verified,
                        guard=guard,on_step=lambda:progress('diagnostic_steps'),
                        on_technical_step=lambda:progress('technical_extra_steps'))
                    pair.update(seed=seed,side=side,pair_id=len(pairs),status='pending_live_verification')
                    append(evidence,pair)
                    brief={k:pair[k] for k in ('seed','side','pair_id','candidate','effective','delta_win','delta_points','delta_h12','reverse_repeat')}
                    brief.update(baseline_outcome=pair['baseline']['outcome'],alternative_outcome=pair['alternative']['outcome'])
                    pairs.append(brief);pending=pair;progress('completed_pairs')
                    if pair['reverse_repeat'] is not None:verified=True
                following,frame=step_frame(env,agent,opponent,obs,side,steps,actions=actions,before=before,
                        on_env_step=lambda:progress('instrumented_steps' if instrumented else 'reference_steps'))
                if pending is not None:
                    offset=steps-pending['candidate']['step']
                    require(frame==pending['baseline']['frames'][offset],'Baseline differs from actual live future')
                    if frame['terminal'] is not None:
                        pairs[-1]['live_verified']=True
                        append(evidence,dict(pair_id=pending['pair_id'],status='live_verified',baseline_sha256=pending['baseline']['sha256']))
                        pending=None
                append(frames,frame);trajectory.update(bytes.fromhex(frame['sha256']))
                totals+=frame['points'];resets+=int(ms==0)
                if frame['terminal'] is not None:matches.append(frame['terminal'])
                obs=following;steps+=1
                if frame['done']:break
        require(pending is None and steps==303 and resets==3 and len(matches)==3,'Incomplete match/game')
        require(module_fingerprint(agent)==before_modules,'Frozen modules changed')
        return dict(seed=seed,side=side,steps=steps,resets=resets,matches=matches,
                    wins=np.asarray(obs[side]['team_wins']).tolist(),points=totals.tolist(),
                    trajectory_sha256=trajectory.hexdigest(),pairs=pairs,verified_map=verified,
                    artifacts=hashes([frame_path,pair_path]))
    finally:env.close()


def load_technical(previous,acceptance,source):
    previous,acceptance=Path(previous),Path(acceptance)
    prior=json.loads(previous.read_text());accepted=json.loads(acceptance.read_text())
    require(prior['status']=='complete' and prior['phase']=='technical'
            and prior['counters']['completed_games']==prior['counters']['started_games']==4,'Incomplete technical phase')
    require(accepted['status']=='accepted' and accepted['manifest_sha256']==digest(previous),'Unbound technical acceptance')
    require(prior['source']==source and prior['keys']==[list(k) for k in FIRST],'Technical source/keys differ')
    require([(g['key']['seed'],g['key']['side']) for g in prior['games']]==list(FIRST),'Technical game keys differ')
    inputs=[previous,acceptance]
    for game in prior['games']:
        require(game['passivity'] and all(game['passivity'].values()),'Technical passivity missing')
        for role in ('reference','collector'):
            artifacts=game[role]['artifacts']
            require(len(artifacts)==2,'Missing technical artifacts')
            for filename,expected in artifacts.items():
                path=Path(filename)
                require(path.resolve().is_relative_to(previous.parent.resolve())
                        and path.is_file() and digest(path)==expected,'Technical artifact altered or missing')
                inputs.append(path)
    return prior,inputs


def run_probe(out,*,phase,weights,usage_file,stop_file,expected_head,previous=None,acceptance=None):
    out=Path(out).absolute();weights=Path(weights).absolute()
    require(not out.exists(),'No resume or overwrite')
    source=source_identity(ROOT,sys.executable,PLANS)
    prior=None;inputs=[weights];prior_counts={k:0 for k in LIMITS}
    if phase=='remaining':
        require(previous is not None and acceptance is not None,'Actual technical acceptance required')
        prior,technical_inputs=load_technical(previous,acceptance,source)
        prior_counts=prior['counters'];inputs.extend(technical_inputs)
    require(source['head']==expected_head,'Wrong HEAD')
    require(digest(weights)==V14_SHA,'Only frozen V14 supported')
    if prior:require(prior['source']==source,'Technical source differs')
    state=dict(schema_version=1,phase=phase,status='running',pid=os.getpid(),started_at=time.time(),
               source=source,inputs=hashes(inputs),protected=hashes(protected_inputs(ROOT)),
               usage_file=str(Path(usage_file).absolute()),stop_file=str(Path(stop_file).absolute()),
               keys=phase_keys(phase),counters={k:0 for k in LIMITS},prior_counters=prior_counts,games=[])
    guard=Guard(state);guard(True)
    require(state['last_usage']['usedPercent']<92,'No new phase above closure threshold')
    out.mkdir(parents=True,exist_ok=False)
    manifest=out/'manifest.json'
    def save():write_json(manifest,state)
    def progress(counter):
        state['counters'][counter]+=1
        require(state['counters'][counter]+prior_counts[counter]<=LIMITS[counter],'Fixed execution limit exceeded')
        if not counter.endswith('steps') or state['counters'][counter]%50==0:save()
    def stop(*_):raise KeyboardInterrupt('Termination requested')
    signal.signal(signal.SIGTERM,stop);save()
    verified_maps={g['key']['seed'] for g in prior['games'] if g['collector']['verified_map']} if prior else set()
    try:
        from scripts.experiment import limit_threads
        limit_threads()
        with resource_lock(ROOT):
            for seed,side in phase_keys(phase):
                record={'key':dict(seed=seed,side=side)};state['games'].append(record);save()
                for instrumented in (False,True):
                    guard(True);progress('started_games')
                    result=play(seed,side,weights,instrumented=instrumented,out=out,guard=guard,
                                progress=progress,verify_map=seed not in verified_maps)
                    record['collector' if instrumented else 'reference']=result
                    progress('completed_games')
                    if result['verified_map']:verified_maps.add(seed)
                ref,col=record['reference'],record['collector']
                record['passivity']={k:ref[k]==col[k] for k in ('seed','side','steps','resets','matches','wins','points','trajectory_sha256')}
                require(all(record['passivity'].values()),'Passivity mismatch');save()
            guard(True)
        all_games=(prior['games'] if prior else [])+state['games']
        rows=[r for g in all_games for r in g['collector']['pairs']]
        state['summary']=summarize_pairs(rows)
        state.update(status='complete',finished_at=time.time());save()
    except BaseException as exc:
        state.update(status='failed',error=f'{type(exc).__name__}: {exc}',finished_at=time.time());save();raise
    return state


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('out','weights','usage-file','stop-file'):parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--phase',choices=('technical','remaining'),required=True)
    parser.add_argument('--expected-head',required=True)
    parser.add_argument('--previous',type=Path);parser.add_argument('--acceptance',type=Path)
    args=vars(parser.parse_args());run_probe(**args)


if __name__=='__main__':main()
