"""Synthetic coverage for fixed pilot evaluation, loading and evidence contracts."""
import copy
import csv
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

BASE=Path(__file__).resolve().parents[1]

def load(name):
    spec=importlib.util.spec_from_file_location('scripts.'+name,BASE/'scripts'/f'{name}.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module

F=load('sampled_target_compare')
E=load('sampled_target_eval')

def frame(opponents,seeds,result=.5):
    return pd.DataFrame([dict(opponent=o,seed=s,side=side,result=result,game_win=int(result==1))
        for o in opponents for s in seeds for side in F.SIDES])

def matrices():
    panels={r:frame(F.PANEL,F.COHORTS['panel']) for r in F.ARMS}
    direct={str(seed):frame((F.direct_label(seed),),F.COHORTS['direct']) for seed in (45,46)}
    for seed in (45,46):
        panels[f'sampled{seed}'].loc[:7,['result','game_win']]=[1.,1]
    direct['46'].loc[0,['result','game_win']]=[1.,1]
    return panels,direct

def test_integer_boundary_exact16_and_direct81():
    panels,direct=matrices();result=F.validate_performance(panels,direct)
    assert result['passed'] and result['panel_half_win_gain_sum']==16
    assert result['direct_half_win_sum']==81 and result['promoted'] is False
    assert result['games']==400 and result['maps_per_cohort']==20
    panels['sampled46'].loc[0,['result','game_win']]=[.5,0]
    result=F.validate_performance(panels,direct)
    assert not result['passed'] and result['panel_half_win_gain_sum']==15

def test_one_nonpositive_start_and_exact80_direct_fail():
    panels,direct=matrices();panels['sampled45']=panels['control45'].copy()
    panels['sampled46'].loc[:31,['result','game_win']]=[1.,1]
    assert not F.validate_performance(panels,direct)['passed']
    panels,direct=matrices();direct['46'].loc[0,['result','game_win']]=[.5,0]
    out=F.validate_performance(panels,direct)
    assert out['direct_half_win_sum']==80 and not out['passed']
    direct['45'].loc[0,['result','game_win']]=[0.,0]
    direct['46'].loc[:2,['result','game_win']]=[1.,1]
    assert not F.validate_performance(panels,direct)['passed']

@pytest.mark.parametrize('fault',['missing','duplicate','unknown_role','unknown_seed','unknown_side','unknown_opponent','strict','wrong_direct_path'])
def test_incomplete_or_invalid_matrices_fail(fault):
    panels,direct=matrices()
    if fault=='missing':panels['sampled45']=panels['sampled45'].iloc[:-1]
    elif fault=='duplicate':panels['sampled45']=pd.concat([panels['sampled45'],panels['sampled45'].iloc[:1]])
    elif fault=='unknown_role':panels['V14']=panels['control45'].copy()
    elif fault=='unknown_seed':panels['sampled45'].loc[0,'seed']=4242
    elif fault=='unknown_side':panels['sampled45'].loc[0,'side']='player_2'
    elif fault=='unknown_opponent':panels['sampled45'].loc[0,'opponent']='default'
    elif fault=='strict':panels['sampled45'].loc[0,'game_win']=0
    else:direct['45']['opponent']='self:experiments/runs/training/final/agent.pth'
    with pytest.raises(ValueError):F.validate_performance(panels,direct)

def test_mean_interval_keeps_same_map_cluster_across_both_starts_and_opponents():
    panels,direct=matrices()
    # Strongly correlated map effects: resampling160 independent rows would narrow this interval.
    for role,panel in panels.items():
        sampled=role.startswith('sampled')
        panel['result']=[(1. if s<9930010 else 0.) if sampled else .5 for s in panel['seed']]
        panel['game_win']=(panel.result==1.).astype(int)
    out=F.validate_performance(panels,direct)['descriptive_mean_panel']
    values=np.array([.5]*10+[-.5]*10)
    rng=np.random.Generator(np.random.PCG64(0))
    sample=values[rng.integers(0,20,size=(5000,20))].mean(axis=1)
    assert out['delta']==0 and [out['low'],out['high']]==list(np.percentile(sample,[2.5,97.5]))
    assert out['maps']==20 and out['fixed_starts']==2

def admitted():
    return dict(roles={role:dict(path=path,sha256=str(i+1)*64) for i,(role,path) in enumerate(F.ROLE_PATHS.items())})

def test_plan_has_only_exact400_games_and_inference_direct_paths():
    plan=F.performance_plan(admitted())
    assert plan['total_games']==400 and len(plan['jobs'])==10
    assert sum(job['expected_games'] for job in plan['jobs'])==400
    assert {j['role'] for j in plan['jobs']}==set(F.ARMS) and 'V14' not in plan['roles']
    assert all(j['workers']==1 and j['expected_games']==40 for j in plan['jobs'])
    assert {j['opponent'] for j in plan['jobs'] if j['kind']=='direct'}=={F.direct_label(45),F.direct_label(46)}
    assert plan['opponent_sha256']=={F.ROLE_PATHS[f'control{s}']:admitted()['roles'][f'control{s}']['sha256'] for s in (45,46)}

def test_unpinned_historical_acceptance_cannot_start(tmp_path,monkeypatch):
    monkeypatch.setattr(F,'ACCEPTANCE_SHA256',None)
    with pytest.raises(ValueError):F.historical_acceptance(tmp_path)

@pytest.mark.parametrize('fault',['extra_job','wrong_seed','training_direct','override','wrong_hash','wrong_count','bool_count'])
def test_plan_rejects_scope_or_model_drift(tmp_path,fault):
    admission=admitted();plan=F.performance_plan(admission)
    base=tmp_path/F.PLAN_DIR;base.mkdir(parents=True)
    for name in ('panel','direct'):(base/f'{name}.json').write_text(json.dumps(F.COHORTS[name]))
    if fault=='extra_job':plan['jobs'].append(copy.deepcopy(plan['jobs'][0]))
    elif fault=='wrong_seed':(base/'panel.json').write_text(json.dumps([4242,*F.COHORTS['panel'][1:]]))
    elif fault=='training_direct':plan['jobs'][-1]['opponent']='self:training/agent.pth'
    elif fault=='override':plan['jobs'][0]['set']=['rules_in_training=true']
    elif fault=='wrong_hash':plan['opponent_sha256'][F.ROLE_PATHS['control45']]='f'*64
    elif fault=='wrong_count':plan['jobs'][0]['expected_games']=42
    else:plan['max_simultaneous_model_processes']=True
    with pytest.raises(ValueError):F.validate_plan(plan,tmp_path,admission)

def tiny_checkpoint():
    import torch
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.model import QNet
    cfg=AgentConfig(hidden=8,buffer_capacity=8,frozen=False).to_dict()
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(7);q=QNet(79,6,hidden=cfg['hidden'],dueling=cfg['dueling'])
    cp=dict(q=q.state_dict(),target_q=copy.deepcopy(q.state_dict()),cfg=cfg,feature_dim=79,n_actions=6,
        ensemble=[],ensemble_dims=[],env_steps=120600,learn_steps=24000,opt={},metadata=['keep',1])
    return cp,cfg

def test_inference_copy_retains_every_nonconfig_item_and_rejects_drift():
    source,cfg=tiny_checkpoint();source['cfg']=dict(cfg,lr=5e-5,rules_in_training=True)
    candidate=F.inference_copy(source,cfg)
    assert candidate['cfg']==dict(cfg,frozen=False)
    F.validate_copy(source,candidate,cfg)
    candidate['metadata'][1]=2
    with pytest.raises(ValueError):F.validate_copy(source,candidate,cfg)
    candidate=F.inference_copy(source,cfg);candidate['q'][next(iter(candidate['q']))].add_(1)
    with pytest.raises(ValueError):F.validate_copy(source,candidate,cfg)
    candidate=F.inference_copy(source,cfg);candidate['cfg']['rescue_in_training']=True
    with pytest.raises(ValueError):F.validate_copy(source,candidate,cfg)

def test_actual_primary_and_direct_self_load_exact_same_bound_config(tmp_path):
    import torch
    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent
    from scripts.par_eval import build_cfg
    original,cfg=tiny_checkpoint();original['cfg']=dict(cfg,lr=5e-5,rules_in_training=True,rescue_in_training=True)
    cp=F.inference_copy(original,cfg);path=tmp_path/'inference.pth';torch.save(cp,path)
    primary=Agent_x('player_0',agent_path=str(path),cfg=build_cfg(str(path),[]),train=False,seed=0)
    primary.set_to_eval_mode();opponent=make_opponent('self','player_1',self_play_path=str(path))
    assert type(primary) is type(opponent) is Agent_x
    assert primary.cfg.to_dict()==opponent.cfg.to_dict()==dict(cfg,frozen=False)
    assert not primary.training and not opponent.training

def test_csv_validator_accepts_fixed_direct_path_and_rejects_unknown_rows(tmp_path):
    from scripts.experiment import GAME_FIELDS
    job=next(j for j in F.performance_plan(admitted())['jobs'] if j['name']=='sampled45_direct')
    rows=[]
    for seed in F.COHORTS['direct']:
        for side in F.SIDES:
            row={k:0 for k in GAME_FIELDS};row.update(opponent=job['opponent'],seed=seed,side=side,
                steps=303,point_counting_version=2,result=.5,game_win=0,point_win=.5,our_wins=1,opp_wins=1)
            rows.append(row)
    path=tmp_path/'rows.csv'
    def save():
        with path.open('w') as stream:
            writer=csv.DictWriter(stream,fieldnames=GAME_FIELDS);writer.writeheader();writer.writerows(rows)
    save();assert len(E.validate_job_csv(path,job,F.COHORTS['direct']))==40
    rows[0]['opponent']='self:training/agent.pth';save()
    with pytest.raises(ValueError):E.validate_job_csv(path,job,F.COHORTS['direct'])

def test_receipt_requires_exact_command_model_and_source(tmp_path):
    admission=admitted();plan=F.performance_plan(admission);job=plan['jobs'][0]
    csvpath=tmp_path/'out.csv';csvpath.write_text('fixture')
    seedpath=tmp_path/job['seed_list'];seedpath.parent.mkdir(parents=True);seedpath.write_text(json.dumps(F.COHORTS['panel']))
    frozen={'source_identity':{'python':'/python','head':'a'*40},'model_sha256':{r:e['sha256'] for r,e in admission['roles'].items()}}
    receipt=dict(profile=F.PROFILE,status='complete',returncode=0,job_name=job['name'],phase='performance',
        role=job['role'],opponent=job['opponent'],weights=job['weights'],model_sha256=frozen['model_sha256'][job['role']],
        seed_list_sha256=F.C.digest(seedpath),csv_sha256=F.C.digest(csvpath),rows=40,
        source_identity=frozen['source_identity'],opponent_sha256=plan['opponent_sha256'],
        command=['/python','-B','-m','scripts.par_eval','--weights',str(tmp_path/job['weights']),
            '--seed-list',str(seedpath),'--workers','1','--opponents',job['opponent'],'--out',str(csvpath)])
    assert E.validate_receipt(receipt,job,csvpath,tmp_path,plan,frozen)==F.C.digest(csvpath)
    for key,value in [('model_sha256','0'*64),('source_identity',{}),('rows',39),('command',receipt['command']+['--set','x=true'])]:
        bad=copy.deepcopy(receipt);bad[key]=value
        with pytest.raises(ValueError):E.validate_receipt(bad,job,csvpath,tmp_path,plan,frozen)

def sealed_history(tmp_path,monkeypatch):
    """Tiny byte-only historical contract fixture; never pretends these are real weights."""
    files={};root=tmp_path.resolve();old=str(root);head='a'*40
    def blob(path,text='synthetic artifact'):
        p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);files[str(p)]=F.C.digest(p);return p
    def put(path,value):return blob(path,json.dumps(value))
    def ref(path):return {'path':str(path),'sha256':files[str(path)]}
    weights=blob('agents/sherlock/weights/agent_p0.pth');source_sha=F.C.digest(weights)
    monkeypatch.setattr(F,'SOURCE_SHA',source_sha)
    protected={str(p):F.C.digest(p) for p in (weights,blob('agents/sherlock/weights/agent_p1.pth'),blob('Gruppe15.zip'))}
    source={'head':head,'files':{'old.py':'b'*64}}
    raw=blob('operations/raw.gz');audit=put('operations/seeds_audit.json',dict(status='PASS',no_observed_conflicts=True,
        limitations=['unknown external data'],raw_audit={'path':'operations/raw.gz','sha256':F.C.digest(raw)},
        files={'operations/raw.gz':F.C.digest(raw)}))
    seeds=put('operations/seed_acceptance.json',dict(schema_version=1,status='PASS',profile=F.PROFILE,
        cohorts=F.COHORTS,audit={'path':'operations/seeds_audit.json','sha256':F.C.digest(audit)}))
    tech_receipts={name:ref(put(f'operations/{name}.json',{'synthetic':True}))
        for name in ('technical_control_p0','technical_sampled_p0','technical_control_p1','technical_sampled_p1')}
    technical=put('operations/technical.json',dict(status='PASS',profile=F.PROFILE,games=4,receipts=tech_receipts))
    cfg=dict(frozen=True,fog_unknown_reward_neutral=False,art_splash_in_training=False)
    prepared=root/'prepared';manifest=dict(schema_version=1,profile=F.PROFILE,stage='study',cohorts=F.COHORTS,
        source=str(weights),source_sha256=source_sha,source_config=cfg,pins={'source':source,'protected':protected},
        input_sha256={str(weights):source_sha},arms={})
    for arm in F.ARMS:
        initial=blob(f'prepared/{arm}/initial.pth')
        manifest['arms'][arm]=dict(config=F.expected_training_config(cfg),bootstrap_mode='double_dqn' if arm.startswith('control') else 'sampled_successor',
            run_seed=int(arm[-2:]),component_index=18,weights_sha256=F.C.digest(initial))
    manifest_path=put('prepared/manifest.json',manifest);blob('prepared/supervisor_launch.json')
    arms={};jobs={};receipts={};validation={};receipt_hashes={}
    for arm in F.ARMS:
        artifacts={name:F.C.digest(blob(f'runs/{arm}/{name}')) for name in F.FINAL_FILES}
        receipt=dict(schema_version=1,status='done',profile=F.PROFILE,eligible=False,arm=arm,run_seed=int(arm[-2:]),
            bootstrap_mode=manifest['arms'][arm]['bootstrap_mode'],games=200,prefill_games=40,train_games=160,
            updates=24000,env_steps=120600,pins=manifest['pins'],prepared=str(prepared),
            manifest_sha256=F.C.digest(manifest_path),artifacts=artifacts,command=['synthetic',arm])
        path=put(f'runs/{arm}/final_receipt.json',receipt);sha=F.C.digest(path)
        arms[arm]=dict(receipt_path=str(path),receipt_sha256=sha,checkpoint_path=str(path.parent/'final/agent.pth'),
            checkpoint_sha256=artifacts['final/agent.pth'])
        jobs[arm]=dict(returncode=0,finished_at=1,argv=receipt['command']);receipts[arm]={str(path):sha}
        validation[arm]=dict(status='PASS',receipt_sha256=sha,games=200,updates=24000,env_steps=120600)
        receipt_hashes[arm]=sha
    pairs={};pair_refs={}
    for seed in ('45','46'):
        pairs[seed]=dict(status='matched',eligible=False,run_seed=int(seed),proof_sha256={role+seed:
            files[str(root/f'runs/{role}{seed}/prefill_proof.json')] for role in ('control','sampled')})
        pair_refs[seed]=ref(put(f'operations/pair{seed}.json',pairs[seed]))
    state=put('operations/state.json',dict(status='done',stage='study',profile=F.PROFILE,eligible=False,
        active=[],queue=[],source=source,prepared=str(prepared),protected=protected,jobs=jobs,receipts=receipts,
        technical_pairs={},paired_prefill=pairs,wake={'returncode':-15}))
    original=put('operations/original_validation.json',dict(status='PASS',training_head=head,
        validator='scripts.sampled_target_study.validate_final_receipt',arms=validation))
    independent=put('operations/independent.json',dict(status='PASS',training_head=head,receipt_sha256=receipt_hashes))
    accepted=dict(schema_version=1,status='PASS',profile=F.PROFILE,eligible_for_performance=True,totals=F.TOTALS,
        root=old,training_head=head,source=source,protected=protected,prepared=str(prepared),
        prepared_manifest_sha256=F.C.digest(manifest_path),arms=arms,files=files.copy(),supervisor=ref(state),
        seed_acceptance=ref(seeds),technical_acceptance=ref(technical),original_validation=ref(original),
        independent_audit=ref(independent),paired_prefill=pair_refs)
    path=put(F.ACCEPTANCE,accepted);monkeypatch.setattr(F,'ACCEPTANCE_SHA256',F.C.digest(path))
    return path,accepted

def test_historical_acceptance_is_sealed_old_source_not_current_head(tmp_path,monkeypatch):
    path,accepted=sealed_history(tmp_path,monkeypatch)
    actual,bound=F.historical_acceptance(tmp_path)
    assert actual==accepted and bound[str(path)]==F.C.digest(path)
    assert actual['source']['head']=='a'*40
    checkpoint=Path(accepted['arms']['sampled45']['checkpoint_path']);checkpoint.write_text('changed')
    with pytest.raises(ValueError):F.historical_acceptance(tmp_path)

@pytest.mark.parametrize('fault',['unsealed','incomplete_arm','wrong_head','wrong_budget','missing_artifact','wrong_final_path','unaccepted_audit'])
def test_historical_acceptance_rejects_incomplete_or_changed_evidence(tmp_path,monkeypatch,fault):
    path,accepted=sealed_history(tmp_path,monkeypatch)
    if fault=='unsealed':path.write_text('{}')
    else:
        if fault=='incomplete_arm':accepted['arms'].pop('sampled46')
        elif fault=='wrong_head':accepted['training_head']='c'*40
        elif fault=='wrong_budget':accepted['totals']=dict(F.TOTALS,updates=95999)
        elif fault=='missing_artifact':accepted['files'].pop(accepted['arms']['control45']['checkpoint_path'])
        elif fault=='wrong_final_path':accepted['arms']['control45']['checkpoint_path']=str(tmp_path/'prepared/control45/initial.pth')
        else:
            audit=Path(accepted['independent_audit']['path']);value=json.loads(audit.read_text());value['status']='incomplete'
            audit.write_text(json.dumps(value));sha=F.C.digest(audit)
            accepted['independent_audit']['sha256']=sha;accepted['files'][str(audit)]=sha
        path.write_text(json.dumps(accepted));monkeypatch.setattr(F,'ACCEPTANCE_SHA256',F.C.digest(path))
    with pytest.raises(ValueError):F.historical_acceptance(tmp_path)
