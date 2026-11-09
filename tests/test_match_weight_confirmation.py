"""Synthetic confirmation contracts; no production archives, processes or games."""
import copy
from contextlib import nullcontext
import importlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from scripts.early_curriculum_study import digest
from scripts.final_training_supervisor import save_state


@pytest.fixture
def s(monkeypatch):
    assert importlib.util.find_spec('scripts.match_weight_confirmation'), 'Confirmation contract missing'
    module = importlib.import_module('scripts.match_weight_confirmation')
    import torch
    from scripts import common
    def forbidden(*_a, **_k):
        pytest.fail('No production archive, game or simulator in confirmation tests')
    monkeypatch.setattr(torch, 'load', forbidden)
    monkeypatch.setattr(common, 'play_game', forbidden)
    monkeypatch.setitem(sys.modules, 'luxai_s3.wrappers', SimpleNamespace(LuxAIS3GymEnv=forbidden))
    return module


def config(s, tmp_path, monkeypatch):
    monkeypatch.setattr(s, 'ROOT', tmp_path)
    return dict(profile=s.PROFILE, stage='confirmation', root=str(tmp_path), python=sys.executable,
        out=str(tmp_path/'experiments/analysis'/s.PROFILE/'confirmation_v1'), inputs={}, protected={},
        source={}, models={}, cohorts={}, plans=[], stop_file=str(tmp_path/'STOP'), allow_battery=True,
        schema_version=1, start_authorized=True)


def history(s, tmp_path, monkeypatch, fault=None):
    a = config(s, tmp_path, monkeypatch)
    def save(name, value):
        path = tmp_path/name; path.parent.mkdir(parents=True, exist_ok=True)
        s.write(path, value); a['inputs'][str(path)] = digest(path)
        return str(path)
    runtime = save('old-runtime.py', {'synthetic': 'runtime'})
    executable = save('python', {'synthetic': 'executable'})
    old_source = dict(head='closed-selection', files={runtime:digest(runtime)},
                      python=sys.executable, executable=executable, executable_sha256=digest(executable))
    a['source'] = dict(old_source, head='new-confirmation', files=dict(old_source['files']))
    old_models = {r:save(r+'.pth', {'synthetic':r}) for r in ('v14','control','match')}
    a['models'] = {r:old_models[r] for r in ('v14','match')}
    monkeypatch.setattr(s, 'MODEL_SHA', {r:digest(p) for r,p in a['models'].items()})
    original = ['original-'+str(i) for i in range(36)]
    tech_models = {r:dict(path=p,sha256=digest(p),members=36 if r=='v14' else 38,
        member_sha256=original+([] if r=='v14' else [r+'48',r+'49']),loader_pass=True,batches=[1,8,16])
        for r,p in old_models.items()}
    tech = dict(profile=s.SELECTION_PROFILE,status='complete',source=old_source,games=0,
                models=tech_models,no_strength_claim=True)
    tech_path = save('technical-receipt.json',tech)
    accept = save('technical-acceptance.json',dict(status='PASS',profile=s.SELECTION_PROFILE,
        source=old_source,technical_receipt_sha256=digest(tech_path),actual_assembly_and_stock_loader_pass=True))
    old = dict(profile=s.SELECTION_PROFILE,stage='performance',root=a['root'],python=a['python'],
        source=old_source,protected=a['protected'],inputs=dict(a['inputs']),models=old_models,
        out=str(tmp_path/'old-performance'),technical_receipt=tech_path,technical_acceptance=accept)
    a['selection_admission'] = save('old-admission.json', old)
    old_sha = digest(a['selection_admission'])
    files = {save('old-performance/'+name+'.csv',{'synthetic':name}):None for name in s.selection.JOBS}
    files = {p:digest(p) for p in files}
    gates = {k:True for k in ('solution_v14','solution_control','direct_v14','direct_control')}
    counts = {n:dict(wins=24,draws=0,losses=16) for n in s.selection.JOBS}
    summary = dict(profile=s.SELECTION_PROFILE,source=old_source,admission_sha256=old_sha,games=200,
                   nominated=True,gates=gates,counts=counts,files=files)
    if fault=='not_nominated': summary['nominated']=False
    if fault=='gate': summary['gates']=dict(gates,direct_v14=False)
    a['selection_summary'] = save('old-performance/summary.json',summary)
    owner = dict(profile=s.SELECTION_PROFILE,stage='performance',status='complete',active=[],source=old_source,
        admission_sha256=old_sha,inputs=old['inputs'],protected=a['protected'],
        jobs={n:dict(returncode=0) for n in s.selection.JOBS},
        receipts={n:dict(path=str(tmp_path/'old-performance'/(n+'.csv')),
            sha256=files[str(tmp_path/'old-performance'/(n+'.csv'))],games=40) for n in s.selection.JOBS})
    if fault=='owner_running': owner.update(status='running',active=['match_v14'])
    if fault=='failed_job': owner['jobs']['match_v14']['returncode']=1
    if fault=='missing_job': del owner['jobs']['match_v14']
    a['selection_state'] = save('old-performance/state.json',owner)
    audit = dict(summary,status='PASS',summary_sha256=digest(a['selection_summary']))
    if fault=='audit': audit['status']='FAIL'
    a['selection_audit'] = save('audit.json',audit)
    a['selection_review'] = save('review.md',{'review':'verified'})
    closure = dict(summary,status='COMPLETE_RESULT_VERIFIED',original_processes_ended=True,
        source_and_input_bindings_valid=True,protected=a['protected'],
        summary_sha256=digest(a['selection_summary']),owner_state_sha256=digest(a['selection_state']),
        independent_results_sha256=digest(a['selection_audit']),
        independent_review_sha256=digest(a['selection_review']))
    if fault=='incomplete': closure['status']='incomplete'
    if fault=='unbound_process': closure['original_processes_ended']=False
    a['selection_closure'] = save('closure.json',closure)
    monkeypatch.setattr(s,'SELECTION_CLOSURE_SHA',digest(a['selection_closure']))
    if fault=='changed_closure': Path(a['selection_closure']).write_text('{}')
    if fault=='changed_model': Path(a['models']['match']).write_text('changed')
    if fault=='runtime': Path(runtime).write_text('changed')
    if fault=='runtime_mapping': a['source']['files'][runtime]='different'
    if fault=='executable': a['source']['executable_sha256']='different'
    if fault=='missing_input': del a['inputs'][old_models['control']]
    if fault=='changed_summary': Path(a['selection_summary']).write_text('{}')
    return a


def test_historical_selection_is_closed_nominated_and_keeps_old_runtime(s,tmp_path,monkeypatch):
    a=history(s,tmp_path,monkeypatch)
    monkeypatch.setattr(s.selection,'admission',lambda *_a:pytest.fail('No old admission against new HEAD'))
    s.accepted_selection(a)


@pytest.mark.parametrize('fault',['not_nominated','gate','owner_running','failed_job','missing_job','audit',
    'incomplete','unbound_process','changed_closure','changed_model','runtime','runtime_mapping',
    'executable','missing_input','changed_summary'])
def test_bad_historical_or_runtime_binding_rejected(s,tmp_path,monkeypatch,fault):
    with pytest.raises((ValueError,KeyError)): s.accepted_selection(history(s,tmp_path,monkeypatch,fault))


def frame(s,name,seeds=None,opponents=None):
    seeds=seeds or s.COHORTS['direct' if name=='match_v14' else 'panel']
    opponents=opponents or (['self:old-v14'] if name=='match_v14' else s.PANEL)
    rows=[]
    for opp in opponents:
        for seed in seeds:
            for side in ('player_0','player_1'):
                rows.append(dict(opponent=opp,seed=seed,side=side,result=1.,our_wins=2,opp_wins=1,
                    our_points=200,opp_points=150,point_win=1.,game_win=1,steps=303,point_counting_version=2))
    return pd.DataFrame(rows)


def test_exact_jobs_and_existing_par_eval_commands(s,tmp_path,monkeypatch):
    a=config(s,tmp_path,monkeypatch); a['models']={'v14':'old-v14','match':'old-match'}
    a['cohorts']={'panel':'panel.json','direct':'direct.json'}
    assert s.JOBS==('v14_panel','match_panel','match_v14')
    assert [s.job_spec(a,n)['games'] for n in s.JOBS]==[160,160,120]
    for name in s.JOBS:
        argv=s.performance_command(a,name)
        assert argv[:4]==[sys.executable,'-B','-m','scripts.par_eval']
        assert argv[argv.index('--workers')+1]=='1' and '--set' not in argv
        assert argv[argv.index('--opponents')+1]==('self:old-v14' if name=='match_v14' else ','.join(s.PANEL))


@pytest.mark.parametrize('name', ['v14_panel','match_v14'])
@pytest.mark.parametrize('fault',[None,'duplicate','side','seed','opponent','steps','version','score','draw_win','point'])
def test_csv_requires_exact_160_or_120_keys_and_metrics(s,tmp_path,monkeypatch,name,fault):
    a=config(s,tmp_path,monkeypatch);a['models']={'v14':'old-v14','match':'old-match'}
    a['cohorts']={'panel':'panel.json','direct':'direct.json'}
    df=frame(s,name)
    if fault=='duplicate': df.loc[1,['seed','side']]=df.loc[0,['seed','side']]
    if fault=='side': df=df.iloc[:-1]
    if fault=='seed': df.loc[0,'seed']=-1
    if fault=='opponent': df.loc[0,'opponent']='foreign'
    if fault=='steps': df.loc[0,'steps']=302
    if fault=='version': df.loc[0,'point_counting_version']=1
    if fault=='score': df.loc[0,'result']=0
    if fault=='draw_win': df.loc[0,['result','our_wins','opp_wins']]=[.5,1,1]
    if fault=='point': df.loc[0,'point_win']=0
    monkeypatch.setattr(pd,'read_csv',lambda _p:df)
    if fault:
        with pytest.raises(ValueError): s.validate_csv(a,name)
    else: assert len(s.validate_csv(a,name))==s.job_spec(a,name)['games']


def test_exact_gate_boundaries_count_wins_not_scores(s):
    counts={r:{o:dict(wins=30,draws=10,losses=0) for o in s.PANEL} for r in ('v14','match')}
    counts['direct']=dict(wins=72,draws=48,losses=0)
    p=dict(delta=-.5e-12,low=-.025-.5e-12); d=dict(low=.5+2e-12)
    assert all(s.gate_checks(counts,p,d).values())
    for key,stats,value in [('direct_wins',counts['direct'],71),('solution_wins',counts['match']['solution92'],29),
                            ('default_wins',counts['match']['default'],29),('square_wins',counts['match']['sol92_sq'],27),
                            ('rush_wins',counts['match']['rush'],27)]:
        previous=stats['wins']; stats['wins']=value
        assert not s.gate_checks(counts,p,d)[key]
        stats['wins']=previous
    counts['match']['sol92_sq']['wins']=28
    assert s.gate_checks(counts,p,d)['square_wins']
    assert not s.gate_checks(counts,dict(delta=-2e-12,low=0),d)['panel_mean']
    assert not s.gate_checks(counts,dict(delta=0,low=-.025-2e-12),d)['panel_low']
    assert not s.gate_checks(counts,p,dict(low=.5+1e-12))['direct_low']


def test_analysis_marks_degenerate_panel_and_resamples_whole_maps(s,tmp_path,monkeypatch):
    a=config(s,tmp_path,monkeypatch);a['models']={'v14':'old-v14','match':'old-match'}
    frames={n:frame(s,n) for n in s.JOBS}
    # Exactly 36 fully won direct maps, 24 fully lost maps: 72 real wins.
    direct=frames['match_v14']; direct.loc[72:,['result','our_wins','opp_wins','game_win']]=[0.,1,2,0]
    monkeypatch.setattr(s,'validate_csv',lambda _a,n:frames[n])
    monkeypatch.setattr(s,'digest',lambda _p:'synthetic')
    result=s.analyze(a)
    rng=np.random.default_rng(0)
    expected=np.percentile(rng.choice(np.r_[np.ones(36),np.zeros(24)],size=(5000,60)).mean(1),[2.5,97.5])
    assert (result['direct']['low'],result['direct']['high'])==tuple(expected)
    assert result['panel']['maps']==20 and result['direct']['maps']==60 and result['games']==440
    assert result['degenerate']['panel'] is True and result['degenerate']['direct'] is False
    assert result['panel']['low']==result['panel']['high']==0
    assert 'empirical' in result['interpretation'].lower() and not result['promotion_authorized']
    assert result['counts']['direct']==dict(wins=72,draws=0,losses=48)
    original=copy.deepcopy(result)
    for n in frames: frames[n]=frames[n].iloc[::-1]
    assert s.analyze(a)==original


def test_fresh_admission_and_fixed_seed_proof(s,tmp_path,monkeypatch):
    a=history(s,tmp_path,monkeypatch);monkeypatch.chdir(tmp_path)
    for key,values in s.COHORTS.items():
        p=tmp_path/(key+'.json'); s.write(p,values);a['cohorts'][key]=str(p);a['inputs'][str(p)]=digest(p)
    evidence=tmp_path/'scan.json';s.write(evidence,{'historical_scan':True});a['inputs'][str(evidence)]=digest(evidence)
    proof=tmp_path/'seed-proof.json';s.write(proof,dict(status='PASS',profile=s.PROFILE,cohorts=s.COHORTS,
        no_observed_conflicts=True,limitations=['local only'],files={str(evidence):digest(evidence)}))
    a['seed_acceptance']=str(proof);a['inputs'][str(proof)]=digest(proof)
    a['protected']={str(tmp_path/f'agents/sherlock/weights/agent_p{i}.pth'):s.V14_SHA for i in (0,1)}
    a['protected'][str(tmp_path/'Gruppe15.zip')]=s.ZIP_SHA
    monkeypatch.setattr(s,'source_identity',lambda *_a:a['source'])
    monkeypatch.setattr(s,'hashes',lambda paths:dict(paths))
    monkeypatch.setattr(s,'accepted_selection',lambda _a:None)
    path=tmp_path/'admission.json';s.write(path,a)
    assert s.admission(path,digest(path))==a
    a['stage']='performance';path.write_text(json.dumps(a))
    with pytest.raises(ValueError): s.admission(path,digest(path))
    a['stage']='confirmation';Path(a['cohorts']['panel']).write_text(json.dumps([True]+s.COHORTS['panel'][1:]))
    a['inputs'][a['cohorts']['panel']]=digest(a['cohorts']['panel']);path.write_text(json.dumps(a))
    with pytest.raises(ValueError): s.admission(path,digest(path))


@pytest.fixture
def owner_harness(s,tmp_path,monkeypatch):
    assert importlib.util.find_spec('scripts.match_weight_confirmation_owner'), 'Confirmation owner missing'
    owner=importlib.import_module('scripts.match_weight_confirmation_owner')
    from scripts import ensemble_diversity_supervisor as life
    from scripts import fog_reward_supervisor as supervisor
    out=tmp_path/'phase'; path=tmp_path/'admission.json'; usage=tmp_path/'usage.json';usage.write_text('{}')
    a=dict(root=str(tmp_path),out=str(out),python=sys.executable,plans=[],source={'head':'fixed'},
        protected={},inputs={},stop_file=str(tmp_path/'STOP'),allow_battery=True,stage='confirmation')
    h=SimpleNamespace(out=out,launches=[],widths=[],codes={},fault=None,cleanups=[],analyses=0)
    def admit(p,sha):
        assert digest(p)==sha
        return copy.deepcopy(a)
    fake=SimpleNamespace(PROFILE=s.PROFILE,JOBS=s.JOBS,require=s.require,digest=digest,write=s.write,
        admission=admit,bound=lambda _a,p:Path(p),output_dir=lambda _a:out,
        job_spec=lambda _a,n:dict(csv=str(out/(n+'.csv')),games=120 if n=='match_v14' else 160),
        performance_command=lambda _a,n:[sys.executable,'-B','-m','scripts.par_eval',n])
    def validate(_a,n):
        if h.fault=='csv': raise ValueError('Invalid CSV')
        return [None]*(120 if n=='match_v14' else 160)
    fake.validate_csv=validate
    def analyze(_a): h.analyses+=1; return dict(games=440,passed=False)
    fake.analyze=analyze
    monkeypatch.setitem(sys.modules,'scripts.match_weight_confirmation',fake)
    import scripts
    monkeypatch.setattr(scripts,'match_weight_confirmation',fake)
    def guard(state,owned,*,allow_battery):
        assert allow_battery and state['inputs']==a['inputs']
        if h.fault=='quota': raise ValueError('Quota')
        s.require(not Path(state['stop_file']).exists(),'STOP')
    monkeypatch.setattr(supervisor,'guard',guard)
    monkeypatch.setattr(life,'compute_lock',lambda _root:nullcontext())
    monkeypatch.setattr(life,'group_alive',lambda _pg:False)
    monkeypatch.setattr(life,'request_stop',lambda p:Path(p).touch(exist_ok=True))
    class Child:
        def __init__(self,n): self.name=n;self.pid=80000+len(h.launches)
        def poll(self): return h.codes.get(self.name,0)
    def spawn(state,n,argv,owned):
        assert len(owned)<2
        child=Child(n);h.launches.append(n)
        owned[n]=dict(process=child,pgid=child.pid,owner_pid=state['owner_pid'])
        state['jobs'][n]=dict(pid=child.pid,pgid=child.pid,argv=argv,owner_pid=state['owner_pid'])
        state['active']=list(owned);save_state(state);h.widths.append(len(owned))
        (out/(n+'.csv')).write_text('synthetic CSV')
        if h.fault=='stop': Path(a['stop_file']).touch()
    monkeypatch.setattr(life,'spawn_owned',spawn)
    monkeypatch.setattr(life,'shutdown_owned',lambda owned:h.cleanups.append(tuple(owned)))
    def run():
        path.write_text(json.dumps(a))
        monkeypatch.setattr(sys,'argv',['owner','--admission',str(path),'--admission-sha',digest(path),
                                      '--usage-file',str(usage)])
        owner.main()
    h.run=run
    return h


def test_owner_exact_two_plus_one_waves_receipt_sizes_and_no_restart(owner_harness):
    h=owner_harness;h.run();state=json.loads((h.out/'state.json').read_text())
    assert h.launches==['v14_panel','match_panel','match_v14'] and h.widths==[1,2,1]
    assert [state['receipts'][n]['games'] for n in h.launches]==[160,160,120]
    assert state['status']=='complete' and state['active']==[] and h.analyses==1
    assert all(j['returncode']==0 for j in state['jobs'].values())
    with pytest.raises(ValueError,match='no resume'): h.run()
    assert len(h.launches)==3


@pytest.mark.parametrize('fault',['exit','csv','stop','quota'])
def test_owner_stops_only_owned_jobs_without_later_wave_or_summary(owner_harness,fault):
    h=owner_harness
    if fault=='exit': h.codes['v14_panel']=1
    else: h.fault=fault
    with pytest.raises(ValueError): h.run()
    assert h.analyses==0 and 'match_v14' not in h.launches
    if fault=='quota': assert not h.out.exists()
    else:
        state=json.loads((h.out/'state.json').read_text())
        assert state['status']=='failed' and state['active']==[] and h.cleanups
        assert not (h.out/'summary.json').exists()
