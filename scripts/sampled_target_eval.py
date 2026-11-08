"""Fixed 400-game pilot executor and complete receipt-bound analysis.

Execution requires sealed training evidence and the fixed admitted plan.
The shared owned queue is reused with two scoped adapter callbacks; production
agent behavior, historical supervisor files and existing comparison profiles stay unchanged.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr,redirect_stdout
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import time

from scripts import ensemble_diversity_compare as C
from scripts import ensemble_diversity_eval_supervisor as S
from scripts import sampled_target_compare as F
from scripts.early_curriculum_study import read_rows
from scripts.fog_reward_supervisor import foreign_processes

ROOT=F.ROOT
PROFILE=F.PROFILE
STOP_FILE=Path('/tmp').resolve()/'sherlock-sampled-performance-20261108'/'STOP'
_shared_guard=S.guard
require=C.require

def checked_stop(path):
    path=S.helpers().safe_path(Path(path).absolute())
    require(path==STOP_FILE,'Use the canonical Sampled performance STOP path');return path

def guard(state,owned):
    power=_shared_guard(state,owned);require(power.get('ac') is True,'AC power required')
    require(len(owned)<=2 and len(state.get('active',[]))<=2,'Maximum two evaluation jobs')
    snapshot=subprocess.check_output(['ps','-axo','pid=,pgid=,args='],text=True,timeout=5)
    jobs=foreign_processes(snapshot,owner_pid=os.getpid(),owned_pgids={child['pgid'] for child in owned.values()})
    require(not jobs,f'Foreign model/test processes active: {jobs}');return power

def validate_job_csv(path,job,seeds):
    """Reuse the strict course CSV reader; permit only this fixed direct-path extension."""
    seeds=C._seeds(seeds)
    require(type(job.get('expected_games')) is int and job['expected_games']==2*len(seeds)==40
        and job.get('opponent') in (*F.PANEL,F.direct_label(45),F.direct_label(46)),'Unexpected fixed job')
    expected={(job['opponent'],seed,side) for seed in seeds for side in F.SIDES};seen=set();normalized=[]
    for row in read_rows(path):
        numbers={key:float(value) for key,value in row.items() if key not in ('opponent','side')}
        require(all(math.isfinite(v) for v in numbers.values()) and numbers['seed'].is_integer(),'Nonfinite/noninteger game data')
        key=(row['opponent'],int(numbers['seed']),row['side'])
        require(key in expected and key not in seen,'Unexpected/duplicate game key');seen.add(key)
        require(numbers['steps']==303 and numbers['point_counting_version']==2 and numbers['secs']>=0,
            'Wrong game length/counting version/runtime')
        for name in ('sap_attempts','sap_hits','relics_found','relics_seen','known_point_tiles',
                     'belief_contradictions','unit_steps','our_points','opp_points'):
            require(numbers[name].is_integer() and numbers[name]>=0,f'Invalid {name}')
        for name in ('wait_frac','invalid_frac','greedy_masked_frac','stack_frac'):
            require(0<=numbers[name]<=1,f'Invalid {name}')
        normalized.append({**row,**numbers,'seed':key[1]})
    require(seen==expected and len(normalized)==40,'Incomplete CSV game keys');return normalized

def build_state(jobs,admission,out,python,expected_head,*,usage_file,stop_file=STOP_FILE):
    h=S.helpers();require(Path.cwd().resolve()==ROOT,'Use intended evaluation worktree')
    require(isinstance(expected_head,str) and re.fullmatch('[0-9a-f]{40}',expected_head),'Expected HEAD must be full')
    jobs_path,admission_path,out=map(h.safe_path,(jobs,admission,out));base=h.safe_path(ROOT/F.ANALYSIS)
    require(out!=base and out.is_relative_to(base) and not out.exists(),'Use a fresh fixed analysis output')
    reservation=base/'performance_launch.json';require(not reservation.exists(),'Performance already launched; no retry')
    python=Path(python).absolute();require(python.is_file() and os.access(python,os.X_OK),'Python unavailable')
    admitted,bindings=F.validate_admission(admission_path,root=ROOT)
    plan=C._load_json(jobs_path);job_list=F.validate_plan(plan,ROOT,admitted)
    models={r:admitted['roles'][r]['sha256'] for r in F.ARMS}
    paths=[jobs_path,admission_path,*map(Path,bindings),*(S.repo_path(ROOT,p) for p in plan['roles'].values()),
        *(S.repo_path(ROOT,j['seed_list']) for j in job_list)]
    plans=[str(S.repo_path(ROOT,p)) for p in (F.SPEC,F.PROTOCOL)];paths.extend(map(Path,plans))
    source=h.source_identity(ROOT,python,plans);require(source['head']==expected_head,'Expected evaluation HEAD changed')
    protected=h.hashes([S.repo_path(ROOT,f'agents/sherlock/weights/agent_p{i}.pth') for i in (0,1)])
    require(set(protected.values())=={F.SOURCE_SHA},'Protected V14 changed')
    protected.update(h.hashes([S.repo_path(ROOT,'Gruppe15.zip')]))
    require(all(out!=p and out not in p.parents for p in paths),'Inputs overlap output')
    provenance=dict(profile=PROFILE,phase='performance',model_sha256=models,source_identity=source,
        acceptance_sha256=F.ACCEPTANCE_SHA256,historical_source=admitted['historical_source'],
        study_kind='fixed_submitted_successor_method_pilot',inference_config=admitted['inference_config'])
    return dict(schema_version=1,profile=PROFILE,phase='performance',root=str(ROOT),out=str(out),python=str(python),
        jobs_path=str(jobs_path),expected_head=expected_head,source=source,plans=plans,protected=protected,
        inputs=h.hashes(paths),admission_path=str(admission_path),admission_sha256=C.digest(admission_path),
        acceptance_sha256=F.ACCEPTANCE_SHA256,model_sha256=models,opponent_sha256=plan['opponent_sha256'],
        provenance=provenance,usage_file=str(h.safe_path(usage_file)),max_used_percent=100,
        stop_file=str(checked_stop(stop_file)),reservation=str(reservation),expected_games=400,
        job_plan={j['name']:j for j in job_list},queue=[j['name'] for j in job_list],jobs={},active=[],receipts={},
        status='prepared',owner_pid=os.getpid())

def validate_receipt(receipt,job,csv_path,root,plan,frozen):
    expected=dict(profile=PROFILE,status='complete',returncode=0,job_name=job['name'],phase='performance',
        role=job['role'],opponent=job['opponent'],weights=job['weights'],model_sha256=frozen['model_sha256'][job['role']],
        seed_list_sha256=C.digest(root/job['seed_list']),csv_sha256=C.digest(csv_path),rows=40,
        source_identity=frozen['source_identity'],opponent_sha256=plan['opponent_sha256'])
    require(isinstance(receipt,dict) and all(receipt.get(k)==v for k,v in expected.items())
        and type(receipt.get('returncode')) is int and type(receipt.get('rows')) is int,'Unbound execution receipt')
    command=[frozen['source_identity']['python'],'-B','-m','scripts.par_eval','--weights',str(root/job['weights']),
        '--seed-list',str(root/job['seed_list']),'--workers','1','--opponents',job['opponent'],'--out',str(csv_path)]
    require(receipt.get('command')==command,'Execution command differs; no unilateral config overrides')
    return expected['csv_sha256']

def analyze(jobs_json,result_dir,*,root=ROOT,provenance=None):
    """Nothing is aggregated before all400 records and every source/model/receipt bind."""
    import pandas as pd
    h=S.helpers();root=h.safe_path(root);result_dir=h.safe_path(result_dir);jobs_json=h.safe_path(jobs_json)
    require(result_dir!=root/F.ANALYSIS and result_dir.is_relative_to(root/F.ANALYSIS),'Wrong performance output')
    require(provenance is not None and h.safe_path(provenance)==result_dir/'provenance.json','Frozen provenance required')
    frozen=C._load_json(provenance);state=C._load_json(result_dir/'state.json')
    reservation=root/F.ANALYSIS/'performance_launch.json';launch=C._load_json(reservation)
    require(all(r.get('profile')==PROFILE and r.get('phase')=='performance' for r in (state,launch,frozen))
        and state.get('status')=='complete' and state.get('completed_games')==state.get('expected_games')==400
        and not state.get('queue') and not state.get('active') and type(state.get('wake',{}).get('returncode')) is int,
        'Performance is not completely closed')
    require(state.get('root')==str(root) and state.get('out')==str(result_dir) and launch.get('out')==str(result_dir)
        and state.get('jobs_path')==launch.get('jobs_path')==str(jobs_json) and state.get('reservation')==str(reservation),
        'State/launch/plan paths differ')
    source=frozen.get('source_identity')
    require(isinstance(source,dict) and C._hex(source.get('head'),40) and bool(source.get('files'))
        and state.get('source')==source==launch.get('source_identity') and state.get('expected_head')==source['head']
        and state.get('python')==source.get('python') and state.get('provenance')==frozen,'Evaluation source/HEAD differs')
    require(frozen.get('study_kind')=='fixed_submitted_successor_method_pilot'
        and state.get('acceptance_sha256')==frozen.get('acceptance_sha256')==F.ACCEPTANCE_SHA256,
        'Historical acceptance binding differs')
    admission=h.safe_path(state['admission_path']);admitted,bindings=F.validate_admission(admission,root=root)
    plan=C._load_json(jobs_json);jobs=F.validate_plan(plan,root,admitted)
    models={r:admitted['roles'][r]['sha256'] for r in F.ARMS}
    require(state.get('model_sha256')==frozen.get('model_sha256')==models and state['admission_sha256']==C.digest(admission)
        and state.get('opponent_sha256')==plan['opponent_sha256']
        and frozen.get('inference_config')==admitted['inference_config']
        and frozen.get('historical_source')==admitted['historical_source'],'Inference/model/historical identity differs')
    protected={str(root/f'agents/sherlock/weights/agent_p{i}.pth'):F.SOURCE_SHA for i in (0,1)}
    protected[str(root/'Gruppe15.zip')]=C.digest(S.repo_path(root,'Gruppe15.zip'))
    require(state.get('protected')==protected,'Protected V14/ZIP binding differs');S.check_inputs(state)
    bound=[jobs_json,Path(provenance),reservation,admission,*map(Path,bindings),
        *(S.repo_path(root,p) for p in plan['roles'].values()),*(S.repo_path(root,j['seed_list']) for j in jobs),
        S.repo_path(root,F.SPEC),S.repo_path(root,F.PROTOCOL)]
    require(all(state['inputs'].get(str(p))==C.digest(p) for p in bound),'Missing frozen input binding')
    names={j['name'] for j in jobs}
    require(state.get('job_plan')=={j['name']:j for j in jobs} and set(state.get('jobs',{}))==names
        and set(state.get('receipts',{}))==names and {p.stem for p in result_dir.glob('*.csv')}==names
        and {p.stem for p in (result_dir/'receipts').glob('*.json')}==names,'Missing/extra CSVs/jobs/receipts')
    rows={};csv_hashes={};receipt_hashes={}
    for job in jobs:
        name=job['name'];csv_path=h.safe_path(result_dir/f'{name}.csv')
        receipt_path=h.safe_path(result_dir/'receipts'/f'{name}.json');receipt=C._load_json(receipt_path)
        csv_hashes[name]=validate_receipt(receipt,job,csv_path,root,plan,frozen);receipt_hashes[name]=C.digest(receipt_path)
        require(state['receipts'][name]==dict(path=str(receipt_path),sha256=receipt_hashes[name],rows=40)
            and type(state['jobs'][name].get('returncode')) is int and state['jobs'][name]['returncode']==0
            and state['jobs'][name].get('argv')==receipt['command'],'Process receipt/command differs')
        require(all(state['inputs'].get(str(p))==C.digest(p) for p in (csv_path,receipt_path)),'Unbound raw result')
        rows[name]=validate_job_csv(csv_path,job,job['seeds'])
    panels={r:pd.DataFrame([row for j in jobs if j['role']==r and j['kind']=='panel' for row in rows[j['name']]]) for r in F.ARMS}
    direct={str(seed):pd.DataFrame(rows[f'sampled{seed}_direct']) for seed in (45,46)}
    result=F.validate_performance(panels,direct)
    return dict(schema_version=1,status='complete',profile=PROFILE,phase='performance',jobs=10,**result,
        input_sha256=dict(plan=C.digest(jobs_json),provenance=C.digest(provenance),state=C.digest(result_dir/'state.json'),
            reservation=C.digest(reservation),admission=C.digest(admission),historical_acceptance=F.ACCEPTANCE_SHA256,
            csv=csv_hashes,receipts=receipt_hashes))

def run_supervisor(jobs,admission,out,python,expected_head,*,usage_file,stop_file=STOP_FILE):
    h=S.helpers();stop_file=checked_stop(stop_file)
    if stop_file.exists():raise S.StopRequested('Existing STOP inhibits start')
    handlers={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP)}
    prior_guard,prior_csv=S.guard,S.validate_job_csv;state=wake=None
    try:
        for sig in handlers:signal.signal(sig,lambda *_:S.request_stop(stop_file))
        # Scoped controller callbacks only, restored even on failure. No Agent/RNG/factory changes.
        S.guard,S.validate_job_csv=guard,validate_job_csv
        with h.compute_lock(ROOT):
            h.check_model_processes({})
            state=build_state(jobs,admission,out,python,expected_head,usage_file=usage_file,stop_file=stop_file)
            guard(state,{})
            target=h.safe_path(state['out']);target.mkdir(parents=True);(target/'receipts').mkdir()
            with (target/'controller.log').open('x',buffering=1) as log,redirect_stdout(log),redirect_stderr(log):
                try:
                    S.reserve_launch(state);guard(state,{})
                    command=['/usr/bin/caffeinate','-i','-w',str(os.getpid())]
                    wake=subprocess.Popen(command,start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                    state['wake']=dict(pid=wake.pid,pgid=wake.pid,argv=command,owner_pid=os.getpid());h.save_state(state)
                    return S.run_queue(state)
                except BaseException as exc:
                    state.update(status='stopped' if isinstance(exc,S.StopRequested) else 'failed',
                        error=f'{type(exc).__name__}: {exc}',finished_at=time.time());h.save_state(state);raise
    finally:
        try:
            if wake is not None:
                if wake.poll() is None:
                    wake.terminate()
                    try:wake.wait(timeout=5)
                    except subprocess.TimeoutExpired:wake.kill();wake.wait(timeout=5)
                if state is not None:state['wake']['returncode']=wake.returncode;h.save_state(state)
        except BaseException as exc:
            S.request_stop(stop_file)
            if state is not None:
                state.update(status='failed',cleanup_error=f'{type(exc).__name__}: {exc}');h.save_state(state)
            raise
        finally:
            S.guard,S.validate_job_csv=prior_guard,prior_csv
            for sig,handler in handlers.items():signal.signal(sig,handler)

def main():
    parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True)
    start=commands.add_parser('start')
    for key in ('jobs','admission','out','python','expected-head','usage-file'):start.add_argument('--'+key,required=True)
    start.add_argument('--stop-file',type=Path,default=STOP_FILE)
    analysis=commands.add_parser('analyze')
    for key in ('jobs','results','out'):analysis.add_argument('--'+key,type=Path,required=True)
    stop=commands.add_parser('stop');stop.add_argument('--stop-file',type=Path,default=STOP_FILE)
    args=parser.parse_args()
    if args.command=='stop':S.request_stop(checked_stop(args.stop_file))
    elif args.command=='analyze':S.exclusive_json(args.out,analyze(args.jobs,args.results,provenance=args.results/'provenance.json'))
    else:
        result=run_supervisor(args.jobs,args.admission,args.out,args.python,args.expected_head,usage_file=args.usage_file,stop_file=args.stop_file)
        print(json.dumps(dict(status=result['status'],out=result['out'])))

if __name__=='__main__':main()
