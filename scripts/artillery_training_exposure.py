"""Offline artillery helper exposure on two fixed archived targeting traces.

Uses archived evaluation booleans and only a reconstructed training-mode helper.
No Agent construction, model forward, environment, game or action modification.
"""
from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

import numpy as np

from agents.sherlock.config import AgentConfig
from agents.sherlock.main import Agent_x
from scripts import holder_rollout_probe as probe
from scripts.early_curriculum_study import digest, hashes, require, resource_lock, source_identity
from scripts.final_training_supervisor import safe_path
from scripts.holder_rollout import exact_digest

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'docs/superpowers/plans/2026-11-08-artillery-training-exposure.md'
TRACES=ROOT/'experiments/analysis/continuation_20261102/targeting'
OUT=ROOT/'experiments/analysis/artillery_training_exposure_20261108/run_v1'
STOP=Path('/tmp').resolve()/'sherlock-artillery-training-exposure-20261108'/'STOP'
CFG_KEYS=('art_surplus','art_min_hits','art_safe','art_splash','splash_min_drop','art_splash_hits',
          'splash_safe_below','sap_reserve_k','art_reserve','art_safe_cheb')


class UnavailableEstimator:
    """Archived posterior is absent; training must never query this sentinel."""
    def __init__(self): self.posterior='not serialized; never queried'
    def dropoff(self,*args,**kwargs): raise RuntimeError('Historical estimator posterior unavailable')


def state_hashes(agent,ctx,sap):
    cfg=agent.cfg.to_dict() if hasattr(agent.cfg,'to_dict') else vars(agent.cfg)
    return dict(cfg=exact_digest(cfg),param_est=exact_digest(agent.param_est.__dict__),
        belief=exact_digest(vars(agent.belief)),ctx=exact_digest(ctx),sap=exact_digest(sap))


def observe_training(agent,original,ctx,uid,sap,*,archived_eval,step,append):
    """Call training only; restore state and return the recorded eval answer."""
    require(agent.training is False and type(archived_eval) is bool,'Inference baseline/archived boolean required')
    before=state_hashes(agent,ctx,sap)
    try:
        agent.training=True
        counter=original(agent,ctx,uid,sap)
        require(type(counter) in (bool,np.bool_),'Training helper must return a boolean')
    finally:
        agent.training=False
        after=state_hashes(agent,ctx,sap)
        require(agent.training is False and before==after,'Training callback mutated config/estimator/belief/context/arguments')
    append(dict(step=int(step),uid=int(uid),estimated_hits=int(sap[2]),eval_verdict=archived_eval,
        eval_source='archived event; not recomputed',training_verdict=bool(counter),
        training_min_hits=int(agent.cfg.art_min_hits),eval_dropoff=None,
        eval_dropoff_status='historical estimator posterior unavailable',training_dropoff=0.0,
        before=before,after=after))
    return archived_eval


def helper_ast(source):
    nodes=[n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.FunctionDef) and n.name=='_artillery_ok']
    require(len(nodes)==1,'Missing/ambiguous artillery helper source')
    return ast.dump(nodes[0],include_attributes=False)


def verify_history(manifest):
    old=manifest['git_head'];relative='agents/sherlock/main.py'
    historical=subprocess.check_output(['git','-C',str(ROOT),'show',f'{old}:{relative}'])
    expected=[sha for path,sha in manifest['sources'].items() if path.endswith('/'+relative)]
    require(len(expected)==1 and hashlib.sha256(historical).hexdigest()==expected[0],
            'Archived agent Git blob differs from trace manifest')
    current=(ROOT/relative).read_bytes()
    require(helper_ast(historical.decode())==helper_ast(current.decode()),'Artillery helper code changed since archived trace')
    require(manifest.get('status')=='complete' and manifest['weights']['sha256']==probe.V14_SHA,'Wrong/incomplete V14 trace provenance')
    return dict(historical_head=old,historical_main_sha256=expected[0],current_main_sha256=hashlib.sha256(current).hexdigest(),
        helper_ast_sha256=hashlib.sha256(helper_ast(current.decode()).encode()).hexdigest(),helper_code_identical=True,
        full_agent_source_identical=historical==current,config_rule='normalized full trace config equals normalized historical game config')


def reconstruct(public,event,historical_cfg):
    cfg=AgentConfig.from_dict(public['config'])
    require(cfg.to_dict()==AgentConfig.from_dict(historical_cfg).to_dict(),'Trace/game normalized configuration differs')
    require(all(k in public['config'] for k in CFG_KEYS),'Missing archived helper configuration')
    ctx={k:public[k] for k in ('W','H','sap_cost','sap_range')}
    ctx.update(ally_pos=np.asarray(public['ally_pos'],dtype=np.int64),ally_ene=np.asarray(public['ally_ene'],dtype=np.float64),
        enemy_coords=np.asarray(public['enemy_coords'],dtype=np.int64).reshape(-1,2),
        enemy_energies=np.asarray(public['enemy_energies'],dtype=np.float64),
        assigned={int(u):tuple(p) for u,p in public['assigned'].items()},
        first_on_tile={tuple(item['position']):int(item['uid']) for item in public['first_on_tile']})
    points=np.asarray(public['point_tiles'],dtype=bool)
    require(points.shape==(ctx['W'],ctx['H']) and np.isfinite(ctx['ally_ene']).all()
        and np.isfinite(ctx['enemy_energies']).all(),'Invalid archived helper context')
    uid=event['uid'];unit=event['unit_context']
    require(type(uid) is int and 0<=uid<len(ctx['ally_pos']) and list(ctx['ally_pos'][uid])==unit['position']
        and float(ctx['ally_ene'][uid])==unit['energy']
        and ctx['assigned'].get(uid)==(tuple(unit['target']) if unit['target'] is not None else None),
        'Event-time unit context differs from saved public context')
    require(event['return_status']=='returned' and type(event['return']) is bool
        and event['arguments']==event['arguments_after'] and set(event['arguments'])=={'sap'},
        'Missing/failed/mutated archived helper event')
    sap=tuple(event['arguments']['sap'])
    require(len(sap)==3 and all(type(n) is int for n in sap),'Invalid archived SAP tuple')
    agent=SimpleNamespace(training=False,cfg=cfg,belief=SimpleNamespace(point_tiles=points),param_est=UnavailableEstimator())
    return agent,ctx,uid,sap


def run(expected_head,usage_file):
    out=safe_path(OUT);stop=safe_path(STOP);require(not out.exists(),'Fresh fixed output required; no resume/overwrite')
    manifest_path=safe_path(TRACES/'manifest.json');manifest=json.loads(manifest_path.read_text())
    keys=[dict(seed=s,side=p) for s,p in probe.SMOKE_KEYS]
    paths=[safe_path(TRACES/f"{k['seed']}_{k['side']}.jsonl.gz") for k in keys]
    source=source_identity(ROOT,sys.executable,[PLAN]);require(len(expected_head)==40 and source['head']==expected_head,'Expected full HEAD differs')
    state=dict(schema_version=1,status='running',source=source,source_plans=[str(PLAN)],
        inputs=hashes([manifest_path,PLAN,*paths]),protected=hashes(probe.protected_inputs(ROOT)),
        usage_file=str(safe_path(usage_file)),stop_file=str(stop),pid=os.getpid(),pgid=os.getpgrp(),argv=sys.argv,
        games=0,training_updates=0,model_forwards=0,trace_reports=[],started_at=time.time(),
        limits='Archived helper exposure only, selected states; historical evaluation boolean not recomputed. '
            'No historical estimator posterior, hidden-frame reproduction, final-action-change, quality or strength claim.')
    base_guard=probe.Guard(state);requested=[];reserved=False
    def guard(*,force=False):
        require(not requested,'Signal requested stop');base_guard(force=force)
    handlers={s:signal.getsignal(s) for s in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP)}
    with resource_lock(ROOT):
        try:
            for sig in handlers: signal.signal(sig,lambda *_:requested.append(True))
            guard(force=True);state['history']=verify_history(manifest)
            out.parent.mkdir(parents=True,exist_ok=True);out.mkdir();reserved=True
            probe.write_json(out/'manifest.json',state)
            for key,path in zip(keys,paths):
                guard(force=True)
                game=next(g for g in manifest['games'] if all(g['key'][k]==key[k] for k in key))
                require(game['trace']['path']==path.name and digest(path)==game['trace']['sha256'],'Trace bytes differ from manifest')
                rows=[];trace_count=0;decisions=0;native=hashlib.sha256()
                output=out/(path.name.removesuffix('.jsonl.gz')+'.helper_calls.jsonl')
                with gzip.open(path,'rt') as stream,output.open('x') as sink:
                    for index,line in enumerate(stream):
                        guard();record=json.loads(line);trace_count+=1
                        require(all(record['key'][k]==key[k] for k in key) and record['key']['obs_step']==index,'Unexpected trace row/key ordering')
                        before_record=exact_digest(record);native.update(exact_digest(record['native_actions']).encode())
                        decisions+=record['status']=='decision'
                        for event in record.get('events',[]):
                            if event['method']!='_artillery_ok': continue
                            agent,ctx,uid,sap=reconstruct(record['public'],event,game['observed']['config'])
                            def append(row):
                                row.update(seed=key['seed'],side=key['side'],event_order=event['order'])
                                rows.append(row);sink.write(json.dumps(row,allow_nan=False)+'\n');sink.flush()
                            result=observe_training(agent,Agent_x._artillery_ok,ctx,uid,sap,
                                archived_eval=event['return'],step=record['key']['obs_step'],append=append)
                            require(result is event['return'],'Archived evaluation answer was replaced')
                        require(exact_digest(record)==before_record,'Archived record/context/actions mutated')
                require(trace_count==303 and decisions==300,'Incomplete known trace')
                changed=[r for r in rows if r['eval_verdict']!=r['training_verdict']]
                state['trace_reports'].append(dict(key=key,trace_rows=trace_count,decision_rows=decisions,
                    helper_calls=len(rows),unique_step_uid=len({(r['step'],r['uid']) for r in rows}),
                    verdict_combinations={f'{str(e).lower()}_{str(t).lower()}':sum(
                        r['eval_verdict'] is e and r['training_verdict'] is t for r in rows)
                        for e in (False,True) for t in (False,True)},
                    differing_helper_calls=len(changed),differing_unique_step_uid=len({(r['step'],r['uid']) for r in changed}),
                    archived_native_actions_digest=native.hexdigest(),actions_unchanged_in_memory=True,artifacts=hashes([output])))
                probe.write_json(out/'manifest.json',state)
            guard(force=True);state.update(status='complete',finished_at=time.time());probe.write_json(out/'manifest.json',state)
            return state
        except BaseException as exc:
            state.update(status='failed',error=f'{type(exc).__name__}: {exc}')
            if reserved: probe.write_json(out/'manifest.json',state)
            raise
        finally:
            for sig,handler in handlers.items(): signal.signal(sig,handler)


def main():
    parser=argparse.ArgumentParser(description=__doc__.splitlines()[0]);parser.add_argument('--expected-head',required=True)
    parser.add_argument('--usage-file',type=Path,required=True)
    args=parser.parse_args();result=run(args.expected_head,args.usage_file)
    print(json.dumps(dict(status=result['status'],traces=len(result['trace_reports']),games=0)))


if __name__=='__main__': main()
