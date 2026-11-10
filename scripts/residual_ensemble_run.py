"""Single-use fixed pilot launcher; reuses the existing ownership/lock guards.

Each phase requires a new explicit root invocation. Training workers wait for
root acceptance of their real prefill bundles; no automatic retry or promotion.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time
from contextlib import contextmanager

import numpy as np
import torch

from agents.sherlock.main import Agent_x
from agents.sherlock.residual import ResidualActor, V14_SHA, file_sha
from scripts.early_curriculum_study import hashes, require, source_identity
from scripts.ensemble_diversity_supervisor import compute_lock, spawn_owned, shutdown_owned
from scripts.ensemble_diversity_supervisor import request_stop
from scripts.ensemble_diversity_eval_supervisor import check_usage
from scripts.final_training_supervisor import save_state, safe_path
from scripts.fog_reward_supervisor import guard
from scripts.residual_ensemble_compare import fixed_jobs, summarize
from scripts.residual_ensemble_train import ResidualLearner
from scripts.student_reward_train import _write
from scripts.threat_warmstart import TraceEnv, state_sha256

ROOT=Path(__file__).resolve().parents[1]
PRIMARY=Path('/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15')
OUT=ROOT/'experiments/analysis/residual_ensemble_20261110'
BASE=ROOT/'agents/sherlock/weights/agent_p0.pth'
BASE_EVAL=ROOT/'experiments/analysis/match_weight_compare_20261109/technical_v1/v14.pth'
V13=ROOT/'experiments/releases/20261101_v13_neb/agent_p0.pth'
ORIGINAL=Path('/private/tmp/residual-v14-original-20261110')
ZIP_SHA='88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6'
PLANS=[ROOT/f'docs/superpowers/{kind}/2026-11-10-residual-ensemble{suffix}.md'
       for kind,suffix in [('plans',''),('specs','-design')]]


def read_json(path):
    return json.loads(Path(path).read_text())


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def append(path,row):
    with Path(path).open('a') as stream:
        stream.write(json.dumps(row,allow_nan=False)+'\n')
        stream.flush()
        os.fsync(stream.fileno())


def phase_jobs(phase,nominee=None):
    if phase=='technical': return [dict(name='parity')]
    if phase=='training': return [dict(name=f'R{s}',seed=s) for s in (61,62)]
    return fixed_jobs(phase,nominee)


def accepted_previous(directory):
    receipt=directory/'accepted.json'
    require(receipt.is_file(),'Previous phase has no root acceptance')
    completion=directory/'completion.json'
    require(read_json(receipt)['completion_sha256']==file_sha(completion),
            'Previous acceptance does not bind completion')
    accepted=read_json(completion)
    # Bind actual tensors/data across phase boundaries, not just the receipt.
    # In confirmation this also checks the selected model in selection.inputs.
    require(hashes(accepted['inputs'])==accepted['inputs'] and
            hashes(accepted['outputs'])==accepted['outputs'],
            'Accepted input/output bytes changed between phases')
    return accepted


@contextmanager
def stop_signals(path):
    signals=(signal.SIGINT,signal.SIGTERM,signal.SIGHUP)
    previous={sig:signal.getsignal(sig) for sig in signals}
    try:
        for sig in signals:
            signal.signal(sig,lambda *_:request_stop(path))
        yield
    finally:
        for sig,handler in previous.items(): signal.signal(sig,handler)


def command(state,name):
    return [state['python'],'-B','-m','scripts.residual_ensemble_run','worker',
            '--phase',state['phase'],'--job',name]


def worker_check(state,name):
    live=read_json(Path(state['out'])/'state.json')
    job=live['jobs'].get(name,{})
    require(live['status']=='running' and name in live['active']
            and job.get('pid')==os.getpid() and job.get('pgid')==os.getpgrp()
            and job.get('argv')==command(live,name),'Unowned or mismatched worker')
    os.kill(live['owner_pid'],0)
    require(not Path(live['stop_file']).exists(),'STOP requested')
    check_usage(live['usage_file'],now=time.time(),max_used_percent=92)


def protected():
    paths=[base/f'agents/sherlock/weights/agent_p{i}.pth' for base in (ROOT,PRIMARY) for i in (0,1)]
    paths += [base/'Gruppe15.zip' for base in (ROOT,PRIMARY)]
    result=hashes(paths)
    require(all(value==(ZIP_SHA if path.endswith('.zip') else V14_SHA) for path,value in result.items()),
            'Protected release changed')
    return result


def launch(phase,nominee=None):
    require(Path.cwd().resolve()==ROOT,'Wrong worktree')
    require(phase in ('technical','training','selection','confirmation'),'Invalid phase')
    out=OUT/phase
    require(not out.exists(),'This fixed phase already exists; no retry')
    inputs=[BASE,BASE_EVAL,V13,OUT/'seed_audit.json']
    require(file_sha(BASE_EVAL)=='817e565f8628a3a860c3dcb84e69e9d68c5f0954f791fbd06e0f115bf6cf95d2'
            and file_sha(V13)=='6d00b6c52366a613eed3b7b5b6f9c3c088802716a85c30fe192c46c57bdd8e62',
            'Comparison input hashes differ')
    inputs += list((ORIGINAL/'original_sherlock').rglob('*.py'))
    require(inputs and (ORIGINAL/'original_sherlock/main.py').is_file(),'Original source snapshot missing')
    if phase!='technical':
        previous={'training':'technical','selection':'training','confirmation':'selection'}[phase]
        receipt=OUT/previous/'accepted.json'
        accepted_previous(OUT/previous)
        inputs += [receipt, OUT/previous/'completion.json']
    if phase in ('selection','confirmation'):
        inputs += [OUT/'training'/a/'final.pth' for a in ('R61','R62')]
    if phase=='confirmation':
        prior=read_json(OUT/'selection/completion.json')['analysis']
        require(prior['nominee']==nominee and nominee is not None,'Nominee differs from fixed selection')
    state=dict(root=str(ROOT),out=str(out),python=sys.executable,phase=phase,
               plans=[str(p) for p in PLANS],source=source_identity(ROOT,sys.executable,PLANS),
               inputs=hashes(inputs),protected=protected(),owner_pid=os.getpid(),
               usage_file='/private/tmp/sherlock-residual-usage.json',stop_file=str(OUT/'STOP'),
               jobs={},active=[],status='prepared',fixed_jobs=phase_jobs(phase,nominee))
    # Admission is fresh, source pinned and quota known before creating workers.
    check_usage(state['usage_file'],now=time.time(),max_used_percent=92)
    guard(state,{},allow_battery=True)
    out.mkdir(parents=True,exist_ok=False)
    owned={}
    with stop_signals(Path(state['stop_file'])), compute_lock(ROOT):
        try:
            state.update(status='running',started_at=time.time())
            save_state(state)
            queue=list(state['fixed_jobs'])
            while queue or owned:
                guard(state,owned,allow_battery=True)
                check_usage(state['usage_file'],now=time.time(),max_used_percent=92)
                while queue and len(owned)<2:
                    j=queue.pop(0)
                    spawn_owned(state,j['name'],command(state,j['name']),owned)
                for name,child in list(owned.items()):
                    rc=child['process'].poll()
                    if rc is None: continue
                    state['jobs'][name].update(returncode=rc,ended_at=time.time())
                    del owned[name]
                    state['active']=list(owned)
                    save_state(state)
                    require(rc==0,f'Worker failed: {name} ({rc}); no retry')
                save_state(state)
                if owned: time.sleep(5)
            guard(state,{},allow_battery=True)
            completion=dict(phase=phase,source=state['source'],inputs=state['inputs'],
                            protected=protected(),ended_at=time.time(),jobs=state['jobs'])
            if phase in ('selection','confirmation'):
                data={j['name']:read_rows(out/j['name']/'games.jsonl') for j in state['fixed_jobs']}
                completion['analysis']=summarize(phase,state['fixed_jobs'],data)
            else:
                completion['proofs']={j['name']:read_json(out/j['name']/'proof.json') for j in state['fixed_jobs']}
            completion['outputs']=hashes(p for p in out.rglob('*') if p.is_file()
                                         and p.name not in ('state.json',) and p.suffix!='.log')
            _write(out/'completion.json',completion)
            state['status']='complete'
        except BaseException as exc:
            state.update(status='failed',error=f'{type(exc).__name__}: {exc}')
            raise
        finally:
            shutdown_owned(owned,grace=30)
            state['active']=[]
            state['ended_at']=time.time()
            save_state(state)


def original_actor(side):
    sys.path.insert(0,str(ORIGINAL))
    from original_sherlock.main import Agent_x as Original
    cfg=Original._cfg_from_checkpoint(str(BASE));cfg.frozen=False
    return Original(side,str(BASE),cfg=cfg,train=False,seed=0)


def actual_game(agent,key,opponent,env,*,collect=False):
    from scripts.common import make_opponent, play_game
    other='player_1' if key['side']=='player_0' else 'player_0'
    opp=make_opponent('self' if opponent=='v13' else opponent,other,
                      self_play_path=str(V13 if opponent=='v13' else BASE_EVAL))
    if hasattr(opp,'cfg'): opp.cfg.frozen=False
    traced=TraceEnv(env)
    row=play_game(traced,agent,opp,key['seed'],key['side'],train=collect)
    row.update(native_sha256=traced.native.hexdigest(),trajectory_sha256=traced.trajectory.hexdigest(),
               caught_errors=int(agent.caught_errors)+int(getattr(opp,'caught_errors',0)))
    require(row['steps']==303 and row['point_counting_version']==2 and row['caught_errors']==0,
            'Incomplete or failed game')
    return row


def cache_audit(agent):
    batch=agent.replay.sample(min(256,len(agent.replay)),np.random.default_rng(991))
    with torch.no_grad():
        errors=[]
        for s,b in (('s','base_s'),('ns','base_ns')):
            direct=agent.policy.baseline(torch.as_tensor(batch[s])).numpy()
            require(np.allclose(direct,batch[b],rtol=1e-5,atol=2e-5),'Cached baseline differs')
            errors.append(float(np.max(np.abs(direct-batch[b]))))
    return dict(max_abs_errors=errors,rows=len(batch['a']),writes=agent.replay.writes,size=len(agent.replay))


def worker(phase,name):
    state=read_json(OUT/phase/'state.json')
    worker_check(state,name)
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    from luxai_s3.wrappers import LuxAIS3GymEnv
    env=LuxAIS3GymEnv(numpy_output=True)
    out=OUT/phase/name
    out.mkdir(exist_ok=False)
    t0=time.monotonic()
    if phase=='technical':
        proofs=[]
        for key in [dict(seed=9946007,side='player_0'),dict(seed=831006,side='player_1')]:
            for opponent in ('solution92','self'):
                worker_check(state,name)
                stock=original_actor(key['side'])
                stock_tensors=state_sha256([m.state_dict() for m in [stock.q]+stock.extra_q])
                row=actual_game(stock,key,opponent,env)
                row.update(role='original',opponent=opponent)
                append(out/'games.jsonl',row)
                del stock
                candidate=ResidualLearner(key['side'],BASE,seed=61,exploration=0)
                require(state_sha256([m.state_dict() for m in candidate.policy.bases])==stock_tensors,
                        'Original 36 tensors/order differ')
                before=state_sha256(candidate.policy.bases.state_dict())
                other=actual_game(candidate,key,opponent,env,collect=True)
                other.update(role='zero_residual_collector',opponent=opponent)
                append(out/'games.jsonl',other)
                for k in ('native_sha256','trajectory_sha256','result','our_points','opp_points','our_wins','opp_wins'):
                    require(row[k]==other[k],f'Zero residual parity failed: {key}/{opponent}/{k}')
                require(candidate.updates==0 and not candidate.optimizer.state
                        and candidate.pending is None and candidate.eligible_steps==300
                        and state_sha256(candidate.policy.bases.state_dict())==before,'Technical learning/state drift')
                audit=cache_audit(candidate)
                proofs.append(dict(key=key,opponent=opponent,parity=True,cache=audit,
                                   original_tensor_hash=stock_tensors,
                                   stock_secs=row['secs'],candidate_secs=other['secs']))
                del candidate
        _write(out/'proof.json',dict(games=8,pairs=proofs,elapsed=time.monotonic()-t0,
                                    peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        return
    if phase=='training':
        seed=next(j['seed'] for j in state['fixed_jobs'] if j['name']==name)
        torch.manual_seed(seed)
        agent=ResidualLearner('player_0',BASE,seed=seed)
        original=state_sha256(agent.policy.bases.state_dict())
        initial=state_sha256(agent.policy.residual.state_dict())
        learning_start=None
        for i in range(120):
            worker_check(state,name)
            card=i//2
            key=dict(seed=11010000+card,side=f'player_{i%2}')
            opponent='solution92' if card%5<3 else 'self'
            before=agent.updates
            row=actual_game(agent,key,opponent,env,collect=True)
            require(agent.pending is None and agent.updates-before==(150 if i>=40 else 0),
                    'Unexpected updates or unfinished transition')
            row.update(index=i,opponent=opponent,updates=agent.updates,rows=agent.replay.writes,
                       phase='learning' if i>=40 else 'prefill')
            append(out/'games.jsonl',row)
            _write(out/'progress.json',dict(completed=i+1,updates=agent.updates,rows=agent.replay.writes,
                                          elapsed=time.monotonic()-t0))
            if i==39:
                require(agent.updates==0 and not agent.optimizer.state and
                        state_sha256(agent.policy.residual.state_dict())==initial,'Prefill changed residual')
                require(state_sha256(agent.policy.bases.state_dict())==original,'Prefill changed bases')
                torch.save(agent.learning_checkpoint(),out/'prefill.pth')
                agent.replay.save(out/'prefill_replay.npz')
                proof=dict(games=40,updates=0,baseline_hash=original,residual_hash=initial,
                           cache=cache_audit(agent),files=hashes([out/'prefill.pth',out/'prefill_replay.npz']))
                _write(out/'prefill_proof.json',proof)
                while not (out/'prefill_accepted.json').exists():
                    worker_check(state,name)
                    time.sleep(5)
                accepted=read_json(out/'prefill_accepted.json')
                require(accepted['proof_sha256']==file_sha(out/'prefill_proof.json'),'Invalid prefill acceptance')
                agent.learn_enabled=True
                learning_start=time.monotonic()
        require(agent.updates==12000 and agent.eligible_steps==36000
                and state_sha256(agent.policy.bases.state_dict())==original
                and state_sha256(agent.policy.residual.state_dict())!=initial,'Final training contract failed')
        torch.save(agent.learning_checkpoint(),out/'final.pth')
        agent.replay.save(out/'final_replay.npz')
        losses=np.asarray(agent.losses)
        np.save(out/'losses.npy',losses,allow_pickle=False)
        _write(out/'proof.json',dict(games=120,learning_games=80,updates=agent.updates,
              baseline_hash=original,initial_residual_hash=initial,
              final_residual_hash=state_sha256(agent.policy.residual.state_dict()),cache=cache_audit(agent),
              loss_first100=float(losses[:100,0].mean()),loss_last100=float(losses[-100:,0].mean()),
              diagnostics=agent.residual_diagnostics,elapsed=time.monotonic()-t0,
              learning_secs=time.monotonic()-learning_start,
              peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        return
    job=next(j for j in state['fixed_jobs'] if j['name']==name)
    if job['agent']=='V14':
        agent=Agent_x('player_0',str(BASE_EVAL),train=False,seed=0)
    else:
        agent=ResidualActor('player_0',BASE,OUT/'training'/job['agent']/'final.pth',seed=0)
    for i,key in enumerate(job['keys']):
        worker_check(state,name)
        row=actual_game(agent,key,job['opponent'],env)
        append(out/'games.jsonl',row)
        _write(out/'progress.json',dict(completed=i+1,elapsed=time.monotonic()-t0))
    _write(out/'proof.json',dict(games=len(job['keys']),elapsed=time.monotonic()-t0,
                               peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                               diagnostics=getattr(agent,'residual_diagnostics',{})))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['launch','worker'])
    parser.add_argument('--phase',required=True,choices=['technical','training','selection','confirmation'])
    parser.add_argument('--job')
    parser.add_argument('--nominee',choices=['R61','R62'])
    args=parser.parse_args()
    if args.mode=='launch': launch(args.phase,args.nominee)
    else: worker(args.phase,args.job)


if __name__=='__main__': main()
