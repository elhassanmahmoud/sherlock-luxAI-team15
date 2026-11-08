"""Narrow guarded executor and receipt-bound analysis for the fixed Fog comparison.

Uses the existing two-worker queue and owned cleanup without changing old profiles.
Selection and optional confirmation retain one shared HEAD/source freeze; write
result JSON/Markdown outside bound inputs and keep audit Python outside the repo.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr,redirect_stdout
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

from scripts import ensemble_diversity_compare as C
from scripts import ensemble_diversity_eval_supervisor as S
from scripts import fog_reward_compare as F
from scripts.fog_reward_supervisor import foreign_processes

ROOT=F.ROOT
PROFILE=F.PROFILE
ANALYSIS=F.ANALYSIS
PROTOCOL=F.PROTOCOL
STOP_FILE=Path('/tmp').resolve()/'sherlock-fog-comparison-20261108'/'STOP'
_shared_guard=S.guard
require=C.require


def checked_stop(path):
    # Canonicalize only system tmp at definition; reject child symlink aliases.
    return S.helpers().safe_path(Path(path).absolute())


def guard(state,owned):
    power=_shared_guard(state,owned)
    require(power.get('ac') is True,'AC power required for Fog comparison')
    snapshot=subprocess.check_output(['ps','-axo','pid=,pgid=,args='],text=True,timeout=5)
    groups={child['pgid'] for child in owned.values()}
    jobs=foreign_processes(snapshot,owner_pid=os.getpid(),owned_pgids=groups)
    require(not jobs,f'Foreign model/probe/test processes active: {jobs}')
    return power


def build_state(jobs, admission, out, python, expected_head, *, usage_file,
                phase="selection", nominee=None, selection_acceptance=None,
                max_used_percent=100, stop_file=STOP_FILE):
    """Adapt only the admission boundary; execution stays in the shared supervisor."""
    require(max_used_percent==100, 'Fixed strict quota ceiling must be100')
    h = S.helpers()
    require(Path.cwd().resolve() == ROOT, 'Use the intended checkout')
    require(isinstance(expected_head, str) and re.fullmatch('[0-9a-f]{40}', expected_head), 'Expected HEAD must be full')
    jobs_path, admission_path, out = map(h.safe_path, (jobs, admission, out))
    base = h.safe_path(ROOT / ANALYSIS)
    require(out != base and out.is_relative_to(base) and not out.exists(), 'Use a fresh study analysis output directory')
    reservation = h.safe_path(base / f'{phase}_launch.json')
    require(not reservation.exists(), 'Validation already launched; no automatic restart')
    python = Path(python).absolute()
    require(python.is_file() and os.access(python, os.X_OK), 'Python unavailable')
    admitted, admitted_bindings = F.validate_admission(admission_path,root=ROOT)
    paths = [jobs_path, admission_path, *map(Path,admitted_bindings)]
    plan = C._load_json(jobs_path)
    job_list = F.validate_plan(plan, ROOT, phase=phase, nominee=nominee)
    require(admitted.get('status') == 'admitted', 'Models have not been admitted')
    models = {}
    for role, relative in plan['roles'].items():
        path = S.repo_path(ROOT, relative)
        value = C.digest(path)
        require(admitted['roles'][role]['path']==relative and admitted['roles'][role]['sha256']==value,
            f'Admitted fixed model path/hash differs: {role}')
        models[role] = value
        paths.append(path)
    paths.extend(S.repo_path(ROOT, relative) for relative in plan['opponent_sha256'])
    paths.extend(S.repo_path(ROOT, job['seed_list']) for job in job_list)
    plans = [str(S.repo_path(ROOT, p)) for p in (F.SPEC,F.PROTOCOL)]
    paths.extend(map(Path, plans))
    source = h.source_identity(ROOT, python, plans)
    require(source['head'] == expected_head, 'Expected HEAD changed')
    protected = h.hashes([S.repo_path(ROOT, f'agents/sherlock/weights/agent_p{i}.pth') for i in (0, 1)])
    require(set(protected.values()) == {F.SOURCE_SHA}, 'Protected V14 weights differ')
    protected.update(h.hashes([S.repo_path(ROOT, 'Gruppe15.zip')]))
    if phase=='confirmation':
        selected,selection_paths=selection_evidence(selection_acceptance,root=ROOT)
        require(selected==nominee,'Confirmation differs from accepted single nominee')
        paths.extend(selection_paths)
    require(all(out != path and out not in path.parents for path in paths), 'An input overlaps output')
    provenance = dict(profile=PROFILE, phase=phase, nominee=nominee, model_sha256=models, source_identity=source,
        acceptance_sha256=F.ACCEPTANCE_SHA256, study_kind='fixed_paired_fog_reward_comparison')
    return dict(schema_version=1, profile=PROFILE, root=str(ROOT), out=str(out), python=str(python),
        phase=phase, nominee=nominee, selection_acceptance=(str(h.safe_path(selection_acceptance)) if phase=='confirmation' else None),
        jobs_path=str(jobs_path), expected_head=expected_head,
        source=source, plans=plans, protected=protected, inputs=h.hashes(paths),
        admission_path=str(admission_path), admission_sha256=C.digest(admission_path),
        acceptance_sha256=F.ACCEPTANCE_SHA256, model_sha256=models, opponent_sha256=plan['opponent_sha256'],
        provenance=provenance, usage_file=str(h.safe_path(usage_file)), max_used_percent=max_used_percent,
        stop_file=str(checked_stop(stop_file)), reservation=str(reservation), expected_games=F.TOTALS[phase],
        job_plan={job['name']: job for job in job_list}, queue=[job['name'] for job in job_list],
        jobs={}, active=[], receipts={}, status='prepared', owner_pid=os.getpid())


def selection_evidence(acceptance,*,root=ROOT):
    """Bind exactly one independently audited, deterministically recomputed screen."""
    h=S.helpers();root=h.safe_path(root)
    require(acceptance is not None,'Independent selection acceptance required')
    acceptance=h.safe_path(acceptance)
    launch_path=root/ANALYSIS/'selection_launch.json'
    launch=C._load_json(launch_path)
    out=h.safe_path(launch['out'])
    summary_path=out/'summary.json'
    audit=C._load_json(acceptance)
    expected=dict(status='PASS',profile=PROFILE,summary_sha256=C.digest(summary_path))
    require(all(audit.get(k)==v for k,v in expected.items()) and audit.get('nominee') in F.CANDIDATES,
            'Independent selection acceptance is absent/unbound')
    summary=C._load_json(summary_path)
    recomputed=analyze(launch['jobs_path'],out,root=root,provenance=out/'provenance.json',phase='selection')
    require(summary==recomputed and summary['nominee']==audit['nominee'],
            'Selection summary/nominee differs from complete independently accepted data')
    paths=[acceptance,launch_path,summary_path,out/'state.json',out/'provenance.json',Path(launch['jobs_path'])]
    for name in summary['input_sha256']['csv']:
        paths.extend((out/f'{name}.csv',out/'receipts'/f'{name}.json'))
    return audit['nominee'],paths


def prepare_confirmation(acceptance,*,root=ROOT):
    nominee,_=selection_evidence(acceptance,root=root)
    path=S.repo_path(root,str(ANALYSIS/'plans/confirmation_jobs.json'))
    plan=F.make_plan('confirmation',nominee)
    F.validate_plan(plan,root,phase='confirmation',nominee=nominee)
    S.exclusive_json(path,plan)
    return plan


def _receipt(receipt,job,csv_path,root,plan,frozen):
    expected=dict(profile=PROFILE,status='complete',returncode=0,job_name=job['name'],
        phase=plan['phase'],role=job['role'],opponent=job['opponent'],weights=job['weights'],
        model_sha256=frozen['model_sha256'][job['role']],seed_list_sha256=C.digest(root/job['seed_list']),
        csv_sha256=C.digest(csv_path),rows=job['expected_games'],source_identity=frozen['source_identity'],
        opponent_sha256=plan['opponent_sha256'])
    require(isinstance(receipt,dict) and all(receipt.get(k)==v for k,v in expected.items())
        and type(receipt.get('returncode')) is int and type(receipt.get('rows')) is int,
        f'Invalid/unbound execution receipt: {job["name"]}')
    command=[frozen['source_identity']['python'],'-B','-m','scripts.par_eval',
        '--weights',str(root/job['weights']),'--seed-list',str(root/job['seed_list']),
        '--workers','1','--opponents',job['opponent'],'--out',str(csv_path)]
    require(receipt.get('command')==command,'Execution command differs from fixed single-worker job')
    return expected['csv_sha256']


def analyze(jobs_json,result_dir,*,root=ROOT,provenance=None,phase='selection',nominee=None):
    """Validate complete plan/state/input/source/receipt/CSV matrices before statistics."""
    import pandas as pd
    h=S.helpers();root=h.safe_path(root);result_dir=h.safe_path(result_dir);jobs_json=h.safe_path(jobs_json)
    require(result_dir!=root/ANALYSIS and result_dir.is_relative_to(root/ANALYSIS),'Wrong result directory')
    plan=C._load_json(jobs_json);jobs=F.validate_plan(plan,root,phase=phase,nominee=nominee)
    require(provenance is not None,'Frozen provenance required')
    provenance=h.safe_path(provenance)
    require(provenance==result_dir/'provenance.json','Frozen provenance required')
    frozen=C._load_json(provenance);state=C._load_json(result_dir/'state.json')
    reservation=root/ANALYSIS/f'{phase}_launch.json';launch=C._load_json(reservation)
    total=F.TOTALS[phase]
    require(all(r.get('profile')==PROFILE and r.get('phase')==phase for r in (state,launch,frozen))
        and frozen.get('nominee')==nominee
        and state.get('nominee')==nominee and state.get('status')=='complete'
        and state.get('completed_games')==total and state.get('expected_games')==total
        and not state.get('queue') and not state.get('active'),'Incomplete/wrong phase state')
    require(state.get('root')==str(root) and state.get('out')==str(result_dir)
        and launch.get('out')==str(result_dir) and state.get('jobs_path')==str(jobs_json)
        and launch.get('jobs_path')==str(jobs_json) and state.get('reservation')==str(reservation),
        'State/launch/plan paths differ')
    source=frozen.get('source_identity')
    require(isinstance(source,dict) and C._hex(source.get('head'),40) and bool(source.get('files'))
        and state.get('source')==source and launch.get('source_identity')==source
        and state.get('expected_head')==source['head'] and state.get('python')==source.get('python')
        and state.get('provenance')==frozen,'Frozen source/HEAD/command provenance differs')
    require(state.get('acceptance_sha256')==F.ACCEPTANCE_SHA256
        and frozen.get('acceptance_sha256')==F.ACCEPTANCE_SHA256
        and frozen.get('study_kind')=='fixed_paired_fog_reward_comparison','Historical training binding differs')
    admission=h.safe_path(state['admission_path']);admitted,bindings=F.validate_admission(admission,root=root)
    models={r:admitted['roles'][r]['sha256'] for r in plan['roles']}
    require(state.get('model_sha256')==models and frozen.get('model_sha256')==models
        and state['admission_sha256']==C.digest(admission),'Admitted model/config provenance differs')
    protected={str(root/f'agents/sherlock/weights/agent_p{i}.pth'):F.SOURCE_SHA for i in (0,1)}
    protected[str(root/'Gruppe15.zip')]=C.digest(S.repo_path(root,'Gruppe15.zip'))
    require(state.get('protected')==protected,'Protected V14/ZIP bindings differ')
    S.check_inputs(state)
    bound=[jobs_json,provenance,reservation,admission,*map(Path,bindings),
        *(S.repo_path(root,p) for p in plan['roles'].values()),
        *(S.repo_path(root,p) for p in plan['opponent_sha256']),
        *(S.repo_path(root,j['seed_list']) for j in jobs),
        S.repo_path(root,F.PROTOCOL),S.repo_path(root,F.SPEC)]
    if phase=='confirmation':
        selected,selection_paths=selection_evidence(state.get('selection_acceptance'),root=root)
        require(selected==nominee,'Confirmation is not bound to the accepted selected nominee')
        bound.extend(selection_paths)
    else:
        require(state.get('selection_acceptance') is None,'Selection cannot claim prior selection acceptance')
    require(all(state['inputs'].get(str(p))==C.digest(p) for p in bound),'Missing frozen input binding')
    names={j['name'] for j in jobs}
    require(state.get('job_plan')=={j['name']:j for j in jobs} and set(state.get('jobs',{}))==names
        and set(state.get('receipts',{}))==names,'Incomplete fixed state jobs/receipts')
    require({p.stem for p in result_dir.glob('*.csv')}==names
        and {p.stem for p in (result_dir/'receipts').glob('*.json')}==names,'Missing/extra CSV/receipt jobs')
    rows={};csv_hashes={};receipt_hashes={}
    for job in jobs:
        name=job['name'];csv_path=h.safe_path(result_dir/f'{name}.csv')
        receipt_path=h.safe_path(result_dir/'receipts'/f'{name}.json');receipt=C._load_json(receipt_path)
        csv_hashes[name]=_receipt(receipt,job,csv_path,root,plan,frozen)
        receipt_hashes[name]=C.digest(receipt_path)
        require(state['receipts'][name]==dict(path=str(receipt_path),sha256=receipt_hashes[name],rows=job['expected_games'])
            and state['jobs'][name].get('returncode')==0 and state['jobs'][name].get('argv')==receipt['command'],
            'State process receipt/command differs')
        require(all(state['inputs'].get(str(p))==C.digest(p) for p in (csv_path,receipt_path)),
                'Raw CSV/receipt is not bound to state')
        rows[name]=C.validate_job_csv(csv_path,job,job['seeds'])
    # No aggregate/nominee is computed before every expected artifact passes.
    panels={r:pd.DataFrame([row for j in jobs if j['role']==r and j['kind']=='panel'
                          for row in rows[j['name']]]) for r in plan['roles']}
    results={r:(F.selection_checks if phase=='selection' else F.confirmation_checks)(
        panels['V14'],panels[r],pd.DataFrame(rows[f'{r}_direct']),name=r)
        for r in plan['roles'] if r!='V14'}
    report=dict(schema_version=1,status='complete',profile=PROFILE,phase=phase,jobs=len(jobs),games=total,
        results=results,nominee=F.choose_nominee(results) if phase=='selection' else nominee,
        interpretation='Whole-map paired bootstrap5000 PCG64 seed0,95% unadjusted intervals. '
            'Screening is exploratory. Passing is not promotion. No top-up, successor or second confirmation. '
            'A neutral-vsV14 confirmation does not isolate the reward effect; two starts limit generalization.',
        score_definition='(strict wins +0.5 draws)/games; strict wins reported separately',
        input_sha256=dict(plan=C.digest(jobs_json),provenance=C.digest(provenance),state=C.digest(result_dir/'state.json'),
            reservation=C.digest(reservation),admission=C.digest(admission),historical_acceptance=F.ACCEPTANCE_SHA256,
            csv=csv_hashes,receipts=receipt_hashes))
    if phase=='selection':
        from scripts.league_gates import panel_delta
        report['neutral_minus_control_panel']=C._score_stats(
            panel_delta(panels['NEUTRAL38'],panels['CONTROL38'],panel=F.SCREEN_PANEL),
            F._subset(panels['NEUTRAL38'],F.SCREEN_PANEL),F._subset(panels['CONTROL38'],F.SCREEN_PANEL))
    else: report['passed']=results[nominee]['passed']
    return report


def run_supervisor(jobs,admission,out,python,expected_head,*,usage_file,phase='selection',nominee=None,
                   selection_acceptance=None,stop_file=STOP_FILE):
    h=S.helpers();stop_file=checked_stop(stop_file)
    if stop_file.exists(): raise S.StopRequested('Existing STOP inhibits start')
    handlers={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP)}
    wake=None;state=None;prior_guard=S.guard
    try:
        for sig in handlers: signal.signal(sig,lambda *_:S.request_stop(stop_file))
        S.guard=guard
        with h.compute_lock(ROOT):
            h.check_model_processes({})
            state=build_state(jobs,admission,out,python,expected_head,usage_file=usage_file,
                phase=phase,nominee=nominee,selection_acceptance=selection_acceptance,stop_file=stop_file)
            S.guard(state,{})
            target=h.safe_path(state['out']);target.parent.mkdir(parents=True,exist_ok=True);target.mkdir()
            (target/'receipts').mkdir()
            with (target/'controller.log').open('x',buffering=1) as log,redirect_stdout(log),redirect_stderr(log):
                try:
                    S.reserve_launch(state);S.guard(state,{})
                    command=['/usr/bin/caffeinate','-i','-w',str(os.getpid())]
                    wake=subprocess.Popen(command,start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                    state['wake']=dict(pid=wake.pid,pgid=wake.pid,argv=command,owner_pid=os.getpid())
                    h.save_state(state)
                    return S.run_queue(state)
                except BaseException as exc:
                    state.update(status='stopped' if isinstance(exc,S.StopRequested) else 'failed',
                        error=f'{type(exc).__name__}: {exc}',finished_at=time.time())
                    h.save_state(state);raise
    finally:
        try:
            if wake is not None:
                if wake.poll() is None:
                    wake.terminate()
                    try: wake.wait(timeout=5)
                    except subprocess.TimeoutExpired: wake.kill();wake.wait(timeout=5)
                if state is not None:
                    state['wake']['returncode']=wake.returncode;h.save_state(state)
        finally:
            S.guard=prior_guard
            for sig,handler in handlers.items(): signal.signal(sig,handler)


def main():
    parser=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands=parser.add_subparsers(dest='command',required=True)
    start=commands.add_parser('start')
    for name in ('jobs','admission','out','python','expected-head','usage-file'): start.add_argument('--'+name,required=True)
    start.add_argument('--phase',choices=tuple(F.COHORTS),default='selection')
    start.add_argument('--nominee',choices=F.CANDIDATES)
    start.add_argument('--selection-acceptance',type=Path)
    start.add_argument('--stop-file',type=Path,default=STOP_FILE)
    analyze_cmd=commands.add_parser('analyze')
    for name in ('jobs','results','out'): analyze_cmd.add_argument('--'+name,type=Path,required=True)
    analyze_cmd.add_argument('--phase',choices=tuple(F.COHORTS),default='selection')
    analyze_cmd.add_argument('--nominee',choices=F.CANDIDATES)
    prep=commands.add_parser('prepare-confirmation');prep.add_argument('--selection-acceptance',type=Path,required=True)
    stop=commands.add_parser('stop');stop.add_argument('--stop-file',type=Path,default=STOP_FILE)
    args=parser.parse_args()
    if args.command=='stop': S.request_stop(checked_stop(args.stop_file))
    elif args.command=='prepare-confirmation': print(json.dumps(prepare_confirmation(args.selection_acceptance)))
    elif args.command=='analyze':
        summary=analyze(args.jobs,args.results,provenance=args.results/'provenance.json',phase=args.phase,nominee=args.nominee)
        S.exclusive_json(args.out,summary)
    else:
        state=run_supervisor(args.jobs,args.admission,args.out,args.python,args.expected_head,usage_file=args.usage_file,
            phase=args.phase,nominee=args.nominee,selection_acceptance=args.selection_acceptance,stop_file=args.stop_file)
        print(json.dumps(dict(status=state['status'],out=state['out'])))


if __name__=='__main__': main()
