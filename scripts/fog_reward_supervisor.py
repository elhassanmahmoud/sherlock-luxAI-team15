"""Single-use paired Fog reward supervisor: two owned workers, no automatic retry.

The shared integrity, usage, process ownership and shutdown helpers are reused.
Each pair's complete prefill is independently compared before gradient games.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

from scripts.early_curriculum_study import hashes, require, source_identity
from scripts.ensemble_diversity_eval_supervisor import check_usage
from scripts.ensemble_diversity_supervisor import (
    compute_lock, group_alive, request_stop, shutdown_owned, spawn_owned,
)
from scripts.final_training_supervisor import read_power, safe_path, save_state, foreign_jobs

ROOT = Path(__file__).resolve().parents[1]
ARMS = ('control41','neutral41','control42','neutral42')
PAIRS = (ARMS[:2],ARMS[2:])
SOURCE_SHA = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
STOP_FILE = Path('/tmp/sherlock-fog-reward-20261108/STOP')
PLANS = [ROOT / f'docs/superpowers/{kind}/2026-11-08-fog-reward.md' for kind in ('specs','plans')]
CHECK_INTERVAL = 10


def foreign_processes(snapshot, *, owner_pid, owned_pgids):
    jobs = set(foreign_jobs(snapshot,owner_pid=owner_pid,owned_pgids=set(owned_pgids)))
    for line in snapshot.splitlines():
        fields=line.strip().split(None,2)
        if len(fields)!=3: continue
        pid,pgid,command=int(fields[0]),int(fields[1]),fields[2]
        if pid==owner_pid or pgid in owned_pgids: continue
        module=re.search(r'(?:-m\s+scripts\.|scripts/)([A-Za-z0-9_]+)',command)
        if ('python' in Path(command.split()[0]).name.lower() and module and
                any(word in module[1] for word in ('train','eval','study','supervisor','probe','distill','experiment'))):
            jobs.add(pid)
    return sorted(jobs)


def check_model_processes(state, owned):
    groups={child['pgid'] for child in owned.values()}
    # A worker may exempt only the supervisor's explicitly registered live jobs.
    for arm in state.get('active',[]):
        job=state['jobs'][arm]
        require(job['owner_pid']==state['owner_pid'] and job['pgid']==job['pid'],
                'Unowned worker record')
        groups.add(job['pgid'])
    snapshot=subprocess.check_output(['ps','-axo','pid=,pgid=,args='],text=True,timeout=5)
    jobs=foreign_processes(snapshot,owner_pid=state.get('owner_pid',os.getpid()),owned_pgids=groups)
    require(not jobs,f'Foreign model/test processes active: {jobs}')


def guard(state, owned):
    require(not Path(state['stop_file']).exists(),'External STOP requested')
    usage=check_usage(state['usage_file'],now=time.time(),max_used_percent=100)
    power=read_power()
    require(power.get('ac') is True,'AC power required')
    require(source_identity(ROOT,state['python'],state['plans'])==state['source'],'Frozen source/HEAD/plans changed')
    require(hashes(state['inputs'])==state['inputs'] and hashes(state['protected'])==state['protected'],
            'Prepared input/V14/ZIP hash changed')
    check_model_processes(state,owned)
    state.update(last_guard_at=time.time(),last_power=power,last_usage=usage)


def run_name(arm):
    require(arm in ARMS,'Unknown fixed arm')
    return f'20261108_fog_reward_{arm}'


def training_command(state,arm):
    return [state['python'],'-B','-m','scripts.fog_reward_study','run',
        '--prepared',state['prepared'],'--arm',arm,'--name',run_name(arm),
        '--supervisor-state',str(Path(state['out'])/'state.json')]


def worker_guard(state_path,arm,name,prepared):
    state=json.loads(safe_path(state_path).read_text())
    require(arm in ARMS and name==run_name(arm),'Worker role/name differs')
    job=state.get('jobs',{}).get(arm,{})
    require(state.get('status')=='running' and arm in state['active']
            and job.get('pid')==os.getpid() and job.get('pgid')==os.getpgrp()
            and job.get('owner_pid')==state['owner_pid']
            and job.get('argv')==training_command(state,arm),'Worker lacks exact owned supervisor launch')
    require(Path(state['prepared']).resolve()==Path(prepared).resolve(),
            'Worker prepared path differs from launch')
    os.kill(state['owner_pid'],0)  # existence check only; never signal a foreign process
    guard(state,{})


def build_state(prepared,out,python,expected_head,*,usage_file,stop_file=STOP_FILE):
    from scripts import fog_reward_study as study
    require(Path.cwd().resolve()==ROOT,'Use the intended worktree')
    require(re.fullmatch('[0-9a-f]{40}',expected_head) is not None,'Expected HEAD must be full')
    prepared,out=map(safe_path,(prepared,out))
    require(not out.exists() and prepared.is_dir(),'Missing prepared/new exclusive output')
    require(out!=ROOT and ROOT/'agents' not in out.parents and out!=prepared
            and prepared not in out.parents,'Unsafe supervisor output')
    python=Path(python).absolute()
    require(python.is_file() and os.access(python,os.X_OK),'Python unavailable')
    manifest=None
    for arm in ARMS:
        manifest,_,_=study.check_prepared(prepared,arm)
    require(not manifest['smoke'],'Smoke cannot launch the production study')
    require(not (prepared/'supervisor_launch.json').exists()
            and not (prepared/'run_records').exists(),'Study already launched; no resume')
    require(all(not (ROOT/'experiments/runs'/run_name(arm)).exists() for arm in ARMS),
            'Fixed run already exists; no restart')
    source=source_identity(ROOT,python,PLANS)
    require(source['head']==expected_head,'Expected HEAD changed')
    protected=manifest['pins']['protected']
    require(all(protected.get(str(ROOT/f'agents/sherlock/weights/agent_p{i}.pth'))==SOURCE_SHA for i in (0,1)),
            'Protected V14 weights differ')
    require(str(ROOT/'Gruppe15.zip') in protected,'Submission ZIP not protected')
    state=dict(schema_version=1,status='prepared',root=str(ROOT),prepared=str(prepared),out=str(out),
        python=str(python),expected_head=expected_head,plans=[str(p) for p in PLANS],source=source,
        protected=protected,inputs=hashes(p for p in prepared.rglob('*') if p.is_file()),
        usage_file=str(safe_path(usage_file)),stop_file=str(safe_path(stop_file)),owner_pid=os.getpid(),
        jobs={},active=[],paired_prefill={},receipts={},queue=list(ARMS))
    guard(state,{})
    return state


def compare_pair(state,pair):
    """Read each frozen prefill bundle, never later scores/checkpoint outcomes."""
    from scripts import fog_reward_study as study
    proofs=[]
    for arm in pair:
        directory=ROOT/'experiments/runs'/run_name(arm)
        proof=study.validate_prefill_bundle(directory,state['prepared'],arm)
        proofs.append(proof)
    seed=study.ARMS[pair[0]][0]
    result=study.compare_prefill_proofs(*proofs,seed)
    result['proof_sha256']={arm:hashes([ROOT/'experiments/runs'/run_name(arm)/'prefill_proof.json']) for arm in pair}
    from scripts.student_reward_train import _write
    _write(Path(state['out'])/f'paired_prefill_{seed}.json',result)
    state['paired_prefill'][str(seed)]=result
    save_state(state)


def run_queue(state):
    owned={}
    state.update(status='running',started_at=time.time())
    save_state(state)
    try:
        for pair in PAIRS:
            require(not owned,'Previous pair still active')
            guard(state,owned)
            # Counterparts first: do not start another RNG family in either slot.
            for arm in pair:
                spawn_owned(state,arm,training_command(state,arm),owned)
                state['queue'].remove(arm)
                save_state(state)
            paired=False
            while owned:
                guard(state,owned)
                if not paired and all((ROOT/'experiments/runs'/run_name(arm)/'prefill_proof.json').exists() for arm in pair):
                    compare_pair(state,pair)
                    paired=True
                for arm,child in list(owned.items()):
                    code=child['process'].poll()
                    if code is None: continue
                    state['jobs'][arm].update(returncode=code,finished_at=time.time())
                    require(code==0,f'Arm {arm} failed; no further starts')
                    require(paired,f'Arm {arm} exited without admitted paired prefill')
                    require(not group_alive(child['pgid']),'Worker left descendants')
                    del owned[arm]
                    state['active']=list(owned)
                    save_state(state)
                if owned: time.sleep(CHECK_INTERVAL)
            # Tensor audit only after both model children ended.
            from scripts.fog_reward_study import validate_final_receipt
            for arm in pair:
                path=ROOT/'experiments/runs'/run_name(arm)/'final_receipt.json'
                validate_final_receipt(path,arm=arm)
                state['receipts'][arm]=hashes([path])
            guard(state,owned)
        require(len(state['receipts'])==4 and len(state['paired_prefill'])==2,'Incomplete fixed study')
        state.update(status='done',finished_at=time.time(),eligible=False,
            note='Complete technical training only; no strength/promotion decision')
        save_state(state)
        return state
    except BaseException as exc:
        request_stop(state['stop_file'])
        state.update(status='incomplete',eligible=False,error=f'{type(exc).__name__}: {exc}')
        save_state(state)
        raise
    finally:
        shutdown_owned(owned)
        state['active']=[]
        save_state(state)


def run_supervisor(prepared,out,python,expected_head,*,usage_file,stop_file=STOP_FILE):
    signals=(signal.SIGINT,signal.SIGTERM,signal.SIGHUP)
    handlers={sig:signal.getsignal(sig) for sig in signals}
    state=None;wake=None
    try:
        for sig in signals: signal.signal(sig,lambda *_:request_stop(stop_file))
        with compute_lock(ROOT):
            state=build_state(prepared,out,python,expected_head,usage_file=usage_file,stop_file=stop_file)
            Path(state['out']).parent.mkdir(parents=True,exist_ok=True)
            Path(state['out']).mkdir()
            with (Path(state['prepared'])/'supervisor_launch.json').open('x') as stream:
                json.dump(dict(owner_pid=os.getpid(),out=state['out'],started_at=time.time()),stream)
                stream.flush();os.fsync(stream.fileno())
            state['inputs'].update(hashes([Path(state['prepared'])/'supervisor_launch.json']))
            command=['/usr/bin/caffeinate','-i','-w',str(os.getpid())]
            wake=subprocess.Popen(command,start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            state['wake']=dict(pid=wake.pid,pgid=wake.pid,owner_pid=os.getpid(),argv=command)
            save_state(state)
            return run_queue(state)
    finally:
        if wake is not None:
            if wake.poll() is None:
                wake.terminate()
                try: wake.wait(timeout=5)
                except subprocess.TimeoutExpired: wake.kill();wake.wait(timeout=5)
            if state is not None:
                state['wake']['returncode']=wake.returncode
                save_state(state)
        for sig,handler in handlers.items(): signal.signal(sig,handler)


def main():
    parser=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands=parser.add_subparsers(dest='command',required=True)
    start=commands.add_parser('start')
    for name in ('prepared','out','python','expected-head','usage-file'):
        start.add_argument('--'+name,required=True)
    start.add_argument('--stop-file',type=Path,default=STOP_FILE)
    commands.add_parser('stop').add_argument('--stop-file',type=Path,default=STOP_FILE)
    args=parser.parse_args()
    if args.command=='stop': request_stop(args.stop_file)
    else:
        state=run_supervisor(args.prepared,args.out,args.python,args.expected_head,
            usage_file=args.usage_file,stop_file=args.stop_file)
        print(json.dumps(dict(status=state['status'],out=state['out'])))


if __name__=='__main__': main()
