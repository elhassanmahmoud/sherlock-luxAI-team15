"""Synthetic exposure-comparison contracts; no real archives, games or processes."""
import copy
from contextlib import nullcontext
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pandas as pd
import pytest
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.model import QNet
from scripts import frozen_v14_exposure_compare as s
from scripts import frozen_v14_exposure_compare_owner as owner
from scripts.early_curriculum_study import digest, require
from scripts.experiment import state_sha256
from scripts.final_training_supervisor import save_state


@pytest.fixture(autouse=True)
def forbid_real_work(monkeypatch):
    def forbidden(*_args,**_kwargs):
        raise AssertionError('No actual archive, simulator, game or subprocess in synthetic tests')
    from scripts import common
    monkeypatch.setattr(torch,'load',forbidden)
    monkeypatch.setattr(common,'play_game',forbidden)
    monkeypatch.setattr(subprocess,'Popen',forbidden)
    monkeypatch.setitem(sys.modules,'luxai_s3.wrappers',SimpleNamespace(LuxAIS3GymEnv=forbidden))


def save(a,path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    s.write(path,value); a['inputs'][str(path)] = digest(path)
    return str(path)


@pytest.fixture
def admitted(tmp_path,monkeypatch):
    monkeypatch.setattr(s,'ROOT',tmp_path)
    executable = tmp_path/'synthetic-python'; executable.write_text('not executable')
    runtime = tmp_path/'synthetic-core.py'; runtime.write_text('# synthetic historical runtime')
    source = dict(head='new-head',python=sys.executable,executable=str(executable),
                  executable_sha256=digest(executable),files={str(runtime):digest(runtime)})
    a = dict(profile=s.PROFILE,stage='performance',root=str(tmp_path),python=sys.executable,plans=[],
        out=str(tmp_path/'experiments/analysis'/s.PROFILE/'performance_v1'),
        source=source,protected={},inputs={},stop_file=str(tmp_path/'STOP'),allow_battery=True,
        models={r:str(tmp_path/(r+'.pth')) for r in s.ROLES},cohorts={})
    for k,rows in s.COHORTS.items(): a['cohorts'][k] = save(a,tmp_path/(k+'.json'),rows)
    return a


def closed_training(a,tmp_path,fault=None):
    """A complete synthetic hash chain; never import/invoke a historical admission."""
    origin = dict(a['source'],head='historical-training-head')
    out = tmp_path/'historical-training'
    tech = save(a,tmp_path/'original-technical.json',dict(profile=s.TRAINING_PROFILE,status='complete',stage='technical',
        source=origin,games=[dict(key={'seed':831006})]*4))
    approval = save(a,tmp_path/'original-technical-acceptance.json',dict(status='PASS',
        profile=s.TRAINING_PROFILE,source=origin,technical_receipt_sha256=digest(tech),original_processes_ended=True))
    train = dict(profile=s.TRAINING_PROFILE,stage='training',starts=[48,49],root=a['root'],python=a['python'],
        source=origin,protected=a['protected'],inputs={tech:digest(tech),approval:digest(approval)},
        technical_receipt=tech,technical_acceptance=approval,out=str(out),config=dict(w_match=2,lr=.00005))
    train_path = save(a,tmp_path/'historical-admission.json',train); sha = digest(train_path)
    game_rows={role:[dict(key={'seed':9960000+(int(role[-2:])-48)*1000+i//2}) for i in range(440)]
               for role in ('e48','e49')}
    prefills={}
    for role in ('e48','e49'):
        initial=dict(q='initial-q',target='initial-q',optimizer='initial-opt')
        prefills[role]=save(a,out/role/'prefill.json',dict(profile=s.TRAINING_PROFILE,status='prefill_ready',
            role=role,start=int(role[-2:]),admission_sha256=sha,source=origin,config=train['config'],
            games=40,learn_steps=0,initial=initial,current=initial,rows=game_rows[role][:40]))
    pins={r:digest(p) for r,p in prefills.items()}
    review = save(a,out/'root-review.json',dict(status='PASS',profile=s.TRAINING_PROFILE,source=origin,
                                              admission_sha256=sha,prefill_sha256=pins))
    release = save(a,out/'release.json',dict(status='approved',profile=s.TRAINING_PROFILE,
        source=origin,starts=[48,49],roles=['e48','e49'],admission_sha256=sha,
        root_review=review,root_review_sha256=digest(review),prefill_sha256=pins))
    state = dict(profile=s.TRAINING_PROFILE,stage='training',starts=[48,49],source=origin,
        status='complete',active=[],protected=a['protected'],inputs={**train['inputs'],train_path:sha},
        admission_sha256=sha,jobs={},receipts={},final_checks={},release_sha256=digest(release),prefill_ready=pins)
    models = {}; files = {p:digest(p) for p in (train_path,tech,approval,release,review,*prefills.values())}
    for role in ('e48','e49'):
        start = int(role[-2:]); command = ['synthetic-worker',role]
        final = save(a,out/role/'final.pth',dict(synthetic_final=role))
        receipt = dict(status='complete',profile=s.TRAINING_PROFILE,stage='training',role=role,start=start,
            starts=[48,49],behavior='ensemble',opponent_policy='original_solution_else_frozen_v14',
            source=origin,config=train['config'],admission_sha256=sha,
            command=command,games=copy.deepcopy(game_rows[role]),release_sha256=digest(release),
            files={final:digest(final),prefills[role]:pins[role]},
            final_identity=dict(q=role+'-q',target=role+'-target',optimizer=role+'-adam'))
        if role == 'e49':
            if fault == 'incomplete': receipt['status'] = 'incomplete'
            if fault == 'wrong_start': receipt['start'] = 48
            if fault == 'wrong_role': receipt['role'] = 'control'
            if fault == 'wrong_metadata': receipt['behavior'] = 'single'
            if fault == 'short_training': receipt['games'].pop()
            if fault == 'wrong_release': receipt['release_sha256'] = 'other'
            if fault == 'wrong_opponent_policy': receipt['opponent_policy']='historical_four_opponents'
        receipt_path = save(a,out/role/'receipt.json',receipt)
        state['jobs'][role] = dict(returncode=0,argv=command)
        state['receipts'][role] = dict(path=receipt_path,sha256=digest(receipt_path))
        state['final_checks'][role] = dict(status='PASS',role=role,start=start,games=440,learn_steps=60000,
                                          receipt_sha256=digest(receipt_path))
        models[role] = dict(path=final,sha256=digest(final),receipt=receipt_path,receipt_sha256=digest(receipt_path))
        files.update({p:digest(p) for p in (final,receipt_path)})
    if fault == 'failed_job': state['jobs']['e49']['returncode'] = 1
    if fault == 'unfinished_job': state['jobs']['e49']['returncode'] = None
    if fault == 'missing_job': del state['jobs']['e49']
    if fault == 'running_owner': state.update(status='running',active=['e49'])
    if fault == 'missing_validation': del state['final_checks']['e49']
    if fault == 'wrong_prefill_pin': state['prefill_ready']={**pins,'e49':'wrong'}
    state_path = save(a,out/'state.json',state); files[state_path] = digest(state_path)
    closure = dict(profile=s.TRAINING_PROFILE,status='COMPLETE_TRAINING_NO_STRENGTH_CLAIM',source=origin,
        original_processes_ended=True,source_and_input_bindings_valid=True,protected=a['protected'],
        actual=dict(technical_games=4,prefill_games=80,learning_games=800,optimizer_updates=120000),
        admission=train_path,admission_sha256=sha,state=state_path,state_sha256=digest(state_path),
        technical_acceptance=approval,models=models,files=files)
    if fault == 'missing_start': del closure['models']['e49']
    if fault == 'wrong_updates': closure['actual']['optimizer_updates'] -= 1
    if fault == 'unended': closure['original_processes_ended'] = False
    if fault == 'omitted_evidence': del closure['files'][models['e49']['receipt']]
    a['training_completion'] = save(a,tmp_path/'training-closure.json',closure)
    a['training_completion_sha256'] = digest(a['training_completion'])
    if fault == 'changed_final': Path(models['e49']['path']).write_text('changed bytes')
    if fault == 'missing_final': Path(models['e49']['path']).unlink()
    return closure


def test_closed_both_starts_are_consumed_without_readmitting_old_head(admitted,tmp_path):
    closed_training(admitted,tmp_path)
    records = s.accepted_training(admitted)
    assert [r['role'] for r in records] == ['e48','e49']
    assert [r['start'] for r in records] == [48,49]
    assert all(r['source']['head'] != admitted['source']['head'] for r in records)
    assert all(r['path'].name == 'final.pth' and r['config']['w_match'] == 2 for r in records)


@pytest.mark.parametrize('fault',['incomplete','wrong_start','wrong_role','wrong_metadata','short_training',
    'wrong_release','failed_job','unfinished_job','missing_job','running_owner','missing_validation',
    'missing_start','wrong_updates','unended','omitted_evidence','changed_final','missing_final',
    'wrong_opponent_policy','wrong_prefill_pin'])
def test_unaccepted_or_changed_training_is_rejected(admitted,tmp_path,fault):
    closed_training(admitted,tmp_path,fault)
    with pytest.raises((ValueError,FileNotFoundError)): s.accepted_training(admitted)


def test_historical_source_allows_new_head_but_no_changed_or_missing_old_byte(admitted,tmp_path):
    old = copy.deepcopy(admitted); old['source']['head'] = 'accepted-old-head'
    s.historical_bindings(admitted,old)
    key = next(iter(old['source']['files']))
    admitted['source']['files'][key] = 'different'
    with pytest.raises(ValueError,match='runtime'): s.historical_bindings(admitted,old)
    admitted['source']['files'][key] = old['source']['files'][key]
    missing = next(iter(old['inputs'])); del admitted['inputs'][missing]
    with pytest.raises(ValueError,match='runtime'): s.historical_bindings(admitted,old)


@pytest.mark.parametrize('fault',[None,'selected_card','missing_game','changed_card','missing_limitations'])
def test_fixed_cohorts_check_only_884_intervening_actual_rows(admitted,tmp_path,fault):
    a=admitted; closure=closed_training(a,tmp_path)
    proof=dict(profile=s.TRAINING_PROFILE,status='PASS',cohorts=copy.deepcopy(s.COHORTS),
               no_observed_conflicts=True,limitations=['Bounded historical scan only'],
               files={p:digest(p) for p in a['cohorts'].values()})
    if fault=='missing_limitations': proof['limitations']=[]
    a['seed_acceptance']=save(a,tmp_path/'seed-acceptance.json',proof)
    if fault in ('selected_card','missing_game'):
        path=closure['models']['e49']['receipt']; receipt=json.loads(Path(path).read_text())
        if fault=='selected_card': receipt['games'][-1]['key']['seed']=s.COHORTS['direct_behavior'][0]
        else: receipt['games'].pop()
        Path(path).write_text(json.dumps(receipt)); a['inputs'][path]=digest(path)
    if fault=='changed_card':
        values=list(s.COHORTS['solution']); values[0]+=1000
        path=a['cohorts']['solution']; Path(path).write_text(json.dumps(values)); a['inputs'][path]=digest(path)
    if fault:
        with pytest.raises(ValueError): s.fixed_cohorts(a)
    else: assert s.fixed_cohorts(a)==s.COHORTS


def original_reference(a,tmp_path,monkeypatch,fault=None):
    original_members = ['original-'+str(i) for i in range(36)]
    controls = [dict(start=start,identity={'q':f'on{start}-q'},config={'w_match':2}) for start in (48,49)]
    out = tmp_path/'reference-technical'
    models = {}
    for role in ('v14','behavior'):
        path = save(a,out/(role+'.pth'),dict(synthetic_eval=role))
        members = original_members + ([] if role == 'v14' else ['on48-q','on49-q'])
        models[role] = dict(path=path,sha256=digest(path),members=len(members),member_sha256=members,
                            loader_pass=True,batches=[1,8,16])
    approval=save(a,tmp_path/'old-root-acceptance.json',dict(status='PASS',profile=s.prior.PROFILE))
    old=dict(profile=s.prior.PROFILE,stage='performance',root=a['root'],python=a['python'],protected=a['protected'],
        source=dict(a['source'],head='old-assembly-head'),out=str(out),inputs=dict(a['inputs']),technical_acceptance=approval)
    if fault=='profile': old['profile']='foreign'
    if fault=='stage': old['stage']='technical'
    a['reference_performance_admission']=save(a,tmp_path/'old-performance-admission.json',old)
    receipt=dict(models=models)
    monkeypatch.setattr(s,'REFERENCE_ACCEPTANCE_SHA',digest(approval) if fault!='acceptance_hash' else 'wrong')
    monkeypatch.setattr(s,'REFERENCE_SHA',{r:models[r]['sha256'] for r in ('v14','behavior')})
    def original_view(view):
        assert view['source']==old['source'] and view['profile']==s.prior.PROFILE
        assert view['inputs']==a['inputs']
    def assembly(view): original_view(view); return receipt
    def training(view): original_view(view); return controls
    monkeypatch.setattr(s.prior,'accepted_references',original_view)
    monkeypatch.setattr(s.prior,'accepted_assembly',assembly)
    monkeypatch.setattr(s.prior,'accepted_training',training)
    monkeypatch.setattr(s.prior,'admission',lambda *args:pytest.fail('No historical admission under new HEAD'))
    if fault=='append_order': models['behavior']['member_sha256'][-2:]=['on49-q','on48-q']
    if fault=='changed_copy': Path(models['behavior']['path']).write_text('different copy')
    if fault=='runtime': a['source']['files']={}
    return receipt


@pytest.mark.parametrize('fault',[None,'profile','stage','acceptance_hash','append_order','changed_copy','runtime'])
def test_reference_copies_bind_original_root_admission_owner_and_control_finals(admitted,tmp_path,monkeypatch,fault):
    expected = original_reference(admitted,tmp_path,monkeypatch,fault)
    if fault:
        with pytest.raises(ValueError): s.accepted_references(admitted)
    else:
        receipt, records = s.accepted_references(admitted)
        assert receipt == expected and [r['start'] for r in records] == [48,49]


@pytest.fixture
def tensors():
    base = QNet(79,6,hidden=256,dueling=True).state_dict(); members = []
    for i in range(38):
        sd = dict(base); sd['body.0.bias'] = torch.full_like(base['body.0.bias'],i/38); members.append(sd)
    source = dict(q=members[0],target_q=members[0],ensemble=members[1:36],ensemble_dims=[79]*35,
        feature_dim=79,n_actions=6,cfg=AgentConfig(buffer_capacity=8,frozen=True).to_dict())
    finals = [dict(q=members[i],cfg={'lr':999,'w_match':20}) for i in (36,37)]
    return source,finals,members


def test_mount_and_stock_loader_reuse_original_36_plus_both_finals_without_training_cfg(tensors,tmp_path,monkeypatch):
    source,finals,members = tensors; cp = s.mount(source,finals)
    assert s.mount is s.legacy.mount and s.validate_and_load is s.legacy.validate_and_load
    assert s.state_equal([cp['q'],*cp['ensemble']],members) and len(cp['ensemble']) == 37
    assert s.state_equal(cp['ensemble'][17],members[18])  # original index 18 remains in eval
    assert cp['cfg'] == dict(AgentConfig.from_dict(source['cfg']).to_dict(),frozen=False)
    assert cp['cfg']['lr'] != 999 and cp['cfg']['w_match'] == source['cfg']['w_match']
    path = tmp_path/'synthetic.pth'; path.write_text('in-memory witness only')
    monkeypatch.setattr(torch,'load',lambda *_a,**_k:copy.deepcopy(cp))
    agent = s.validate_and_load(path,cp,members)
    assert len(agent.extra_q) == 37 and not agent.training and agent.cfg.to_dict() == cp['cfg']


@pytest.mark.parametrize('fault',['wrong_start','incomplete','old_metadata','wrong_q','wrong_cfg','short_updates','wrong_opponent'])
def test_exposure_final_metadata_not_historical_behavior_metadata(tensors,tmp_path,monkeypatch,fault):
    source,finals,_ = tensors
    cp = dict(q=finals[0]['q'],target_q=finals[0]['q'],opt={},cfg=source['cfg'],feature_dim=79,n_actions=6,
        ensemble=[],ensemble_dims=[],env_steps=193320,learn_steps=60000,
        exposure=dict(profile=s.TRAINING_PROFILE,status='complete',role='e48',start=48,
                      source={'head':'training'},completed_games=440,component_index=18,opponent_sha256=s.REFERENCE_SHA['v14']))
    r = dict(path=tmp_path/'final.pth',config=cp['cfg'],role='e48',start=48,source={'head':'training'},
        identity={k:state_sha256(cp[v]) for k,v in [('q','q'),('target','target_q'),('optimizer','opt')]})
    monkeypatch.setattr(torch,'load',lambda *_a,**_k:cp)
    assert s.load_final(r) is cp
    if fault == 'wrong_start': cp['exposure']['start'] = 49
    if fault == 'incomplete': cp['exposure']['status'] = 'incomplete'
    if fault == 'old_metadata': cp['behavior'] = cp.pop('exposure')
    if fault == 'wrong_opponent': cp['exposure']['opponent_sha256']='other'
    if fault == 'wrong_q': cp['q'] = finals[1]['q']
    if fault == 'wrong_cfg': cp['cfg'] = {'w_match':20}
    if fault == 'short_updates': cp['learn_steps'] = 59999
    with pytest.raises(ValueError,match='accepted final'): s.load_final(r)


def test_null_game_phase_reuses_reference_bytes_and_serializes_only_exposure(admitted,tensors,tmp_path,monkeypatch):
    from scripts import ensemble_diversity_train
    source,finals,members = tensors; a = admitted
    a.update(stage='technical',out=str(tmp_path/'experiments/analysis'/s.PROFILE/'technical_v1'))
    out = s.output_dir(a); out.mkdir(parents=True)
    a['v14_source'] = save(a,tmp_path/'source.pth',dict(synthetic=True))
    a['training_completion'] = save(a,tmp_path/'closure.json',dict(synthetic=True))
    a['reference_performance_admission'] = save(a,tmp_path/'reference.json',dict(synthetic=True))
    references = {}; payloads = {}; saved = []; loaded = []
    for role,additions in (('v14',[]),('behavior',finals)):
        path = save(a,tmp_path/(role+'.pth'),dict(synthetic_eval=role))
        cp = s.mount(source,additions); payloads[path] = cp; expected = [cp['q'],*cp['ensemble']]
        references[role] = dict(path=path,sha256=digest(path),members=len(expected),
            member_sha256=[state_sha256(sd) for sd in expected],loader_pass=True,batches=[1,8,16])
    original_hashes = {p:digest(p) for p in payloads}
    monkeypatch.setattr(s,'accepted_references',lambda _a:({'models':references},[]))
    monkeypatch.setattr(s,'accepted_training',lambda _a:finals)
    monkeypatch.setattr(s,'load_final',lambda r:r)
    monkeypatch.setattr(s,'check_owned',lambda *_a:None)
    monkeypatch.setattr(ensemble_diversity_train,'_source',lambda _p:(source,members[:36],source['cfg']))
    def store(cp,handle):
        saved.append(str(handle.name)); payloads[str(handle.name)] = copy.deepcopy(cp); handle.write(b'synthetic')
    monkeypatch.setattr(torch,'save',store)
    monkeypatch.setattr(torch,'load',lambda p,**_k:copy.deepcopy(payloads[str(p)]))
    real_loader = s.validate_and_load
    def loader(p,cp,expected):
        loaded.append((Path(p).stem,len(expected))); return real_loader(p,cp,expected)
    monkeypatch.setattr(s,'validate_and_load',loader)
    s.run_technical(a,tmp_path/'admission.json','sha',out/'state.json')
    receipt = json.loads((out/'technical-receipt.json').read_text()); s.check_technical(receipt)
    assert receipt['games'] == 0 and loaded == [('v14',36),('behavior',38),('exposure',38)]
    assert saved == [str(out/'exposure.pth')] and {p:digest(p) for p in original_hashes} == original_hashes
    assert not list(out.glob('*.csv')) and not (out/'summary.json').exists()


def rows(a,name,wins=23,draws=17):
    spec = s.job_spec(a,name); results = [1.]*wins+[.5]*draws+[0.]*(40-wins-draws)
    data = []
    keys = [(seed,side) for seed in s.COHORTS[spec['cohort']] for side in ('player_0','player_1')]
    for (seed,side),result in zip(keys,results):
        own,opp = (2,1) if result == 1 else (1,1) if result == .5 else (1,2)
        data.append(dict(seed=seed,side=side,opponent=spec['opponent'],result=result,game_win=int(result==1),
            point_win=result,steps=303,point_counting_version=2,our_wins=own,opp_wins=opp,
            our_points=own*10,opp_points=opp*10))
    return pd.DataFrame(data)


def test_exact_five_jobs_existing_par_eval_and_no_training_override(admitted):
    assert s.JOBS == ('v14_solution','behavior_solution','exposure_solution','exposure_v14','exposure_behavior')
    assert s.COHORTS == dict(solution=list(range(10010000,10010020)),
        direct_v14=list(range(10010100,10010120)),direct_behavior=list(range(10010200,10010220)))
    for name in s.JOBS:
        spec = s.job_spec(admitted,name); argv = s.performance_command(admitted,name)
        assert argv[:4] == [sys.executable,'-B','-m','scripts.par_eval']
        assert argv[argv.index('--weights')+1] == admitted['models'][spec['role']]
        assert argv[argv.index('--seed-list')+1] == admitted['cohorts'][spec['cohort']]
        assert argv[argv.index('--workers')+1] == '1' and '--set' not in argv
    for role in ('v14','behavior'):
        assert s.job_spec(admitted,'exposure_'+role)['opponent'] == 'self:'+admitted['models'][role]


@pytest.mark.parametrize('fault',[None,'duplicate','missing_side','foreign_seed','foreign_opponent','short_game',
    'old_points','inconsistent_result','draw_counted_win','wrong_point_win','too_many_match_wins'])
def test_exact_csv_keys_and_result_arithmetic(admitted,monkeypatch,fault):
    name = 'exposure_v14'; df = rows(admitted,name)
    if fault == 'duplicate': df.loc[1,['seed','side']] = df.loc[0,['seed','side']]
    if fault == 'missing_side': df = df.iloc[:-1]
    if fault == 'foreign_seed': df.loc[:1,'seed'] = 99
    if fault == 'foreign_opponent': df.loc[:1,'opponent'] = 'default'
    if fault == 'short_game': df.loc[0,'steps'] = 302
    if fault == 'old_points': df.loc[0,'point_counting_version'] = 1
    if fault == 'inconsistent_result': df.loc[0,'result'] = 0.
    if fault == 'draw_counted_win': df.loc[39,'game_win'] = 1
    if fault == 'wrong_point_win': df.loc[0,'point_win'] = 0.
    if fault == 'too_many_match_wins': df.loc[0,['our_wins','opp_wins']] = [3,1]
    monkeypatch.setattr(pd,'read_csv',lambda _p:df)
    if fault:
        with pytest.raises(ValueError): s.validate_csv(admitted,name)
    else: assert len(s.validate_csv(admitted,name)) == 40


def test_four_gates_count_24_actual_wins_not_23_plus_draws(admitted,tmp_path):
    out = s.output_dir(admitted); out.mkdir(parents=True)
    for name in s.JOBS: rows(admitted,name).to_csv(s.job_spec(admitted,name)['csv'],index=False)
    result = s.analyze(admitted)
    assert result['counts']['exposure_v14'] == dict(wins=23,draws=17,losses=0)
    assert result['gates'] == dict(solution_v14=True,solution_behavior=True,direct_v14=False,direct_behavior=False)
    assert result['nominated'] is False and result['solution']['v14'][0]['degenerate_interval'] is True
    for name in ('exposure_v14','exposure_behavior'):
        rows(admitted,name,24,16).to_csv(s.job_spec(admitted,name)['csv'],index=False)
    result = s.analyze(admitted); assert result['nominated'] is True and result['games'] == 200
    assert result['files'] == {s.job_spec(admitted,n)['csv']:digest(s.job_spec(admitted,n)['csv']) for n in s.JOBS}
    for reference in ('v14','behavior'):
        name = reference+'_solution'; path = s.job_spec(admitted,name)['csv']
        rows(admitted,name,24,16).to_csv(path,index=False)
        assert s.analyze(admitted)['gates']['solution_'+reference] is False
        rows(admitted,name).to_csv(path,index=False)
    for name in s.JOBS:
        path = s.job_spec(admitted,name)['csv']; pd.read_csv(path).iloc[::-1].to_csv(path,index=False)
    assert s.analyze(admitted)['direct'] == result['direct']
    assert s.analyze(admitted)['solution'] == result['solution']
    # A broken fifth CSV cannot be hidden behind four valid jobs or intersected statistics.
    path = s.job_spec(admitted,s.JOBS[-1])['csv']; pd.read_csv(path).iloc[:-1].to_csv(path,index=False)
    with pytest.raises(ValueError): s.analyze(admitted)


@pytest.mark.parametrize('fault',[None,'pending_root','failed_owner','wrong_final_order','changed_model'])
def test_performance_requires_bound_new_root_assembly_acceptance(admitted,tmp_path,monkeypatch,fault):
    a = admitted; original = ['original-'+str(i) for i in range(36)]; references = {}
    for role in ('v14','behavior'):
        path = save(a,tmp_path/(role+'.pth'),dict(synthetic_eval=role))
        members = original + ([] if role == 'v14' else ['on48-q','on49-q'])
        references[role] = dict(path=path,sha256=digest(path),members=len(members),member_sha256=members,
                               loader_pass=True,batches=[1,8,16])
    a['reference_performance_admission'] = save(a,tmp_path/'reference-performance-admission.json',dict(synthetic=True))
    a['training_completion'] = save(a,tmp_path/'completion.json',dict(synthetic=True))
    a['training_completion_sha256'] = digest(a['training_completion'])
    technical_out = tmp_path/'experiments/analysis'/s.PROFILE/'technical_v1'
    old = dict(a,stage='technical',out=str(technical_out),inputs=dict(a['inputs']))
    a['technical_admission'] = save(a,tmp_path/'technical-admission.json',old); sha = digest(a['technical_admission'])
    path = save(a,technical_out/'exposure.pth',dict(synthetic_exposure=True))
    records = {**references,'exposure':dict(path=path,sha256=digest(path),members=38,
        member_sha256=original+['e48-q','e49-q'],loader_pass=True,batches=[1,8,16])}
    if fault == 'wrong_final_order': records['exposure']['member_sha256'][-2:] = ['e49-q','e48-q']
    command = ['synthetic-technical-worker']
    receipt = dict(profile=s.PROFILE,status='complete',source=a['source'],admission_sha256=sha,
        training_completion_sha256=digest(a['training_completion']),
        reference_performance_admission_sha256=digest(a['reference_performance_admission']),
        models=records,games=0,no_strength_claim=True,command=command)
    a['technical_receipt'] = save(a,technical_out/'technical-receipt.json',receipt)
    receipt_sha = digest(a['technical_receipt'])
    state = dict(profile=s.PROFILE,stage='technical',status='complete',active=[],source=a['source'],inputs=old['inputs'],
        protected=a['protected'],admission_sha256=sha,jobs={'technical':dict(returncode=0,argv=command)},
        receipts={'technical':dict(path=a['technical_receipt'],sha256=receipt_sha)})
    if fault == 'failed_owner': state['jobs']['technical']['returncode'] = 1
    a['technical_state'] = save(a,technical_out/'state.json',state)
    approval = dict(profile=s.PROFILE,status='PASS',source=a['source'],admission_sha256=sha,
        technical_receipt_sha256=receipt_sha,owner_state_sha256=digest(a['technical_state']),
        actual_assembly_and_stock_loader_pass=True,original_processes_ended=True)
    if fault == 'pending_root': approval['status'] = 'pending'
    a['technical_acceptance'] = save(a,tmp_path/'technical-acceptance.json',approval)
    a['models'] = {r:records[r]['path'] for r in s.ROLES}
    if fault == 'changed_model': Path(a['models']['exposure']).write_text('changed')
    monkeypatch.setattr(s,'accepted_references',lambda _a:({'models':references},[]))
    monkeypatch.setattr(s,'accepted_training',lambda _a:[dict(identity={'q':'e48-q'}),dict(identity={'q':'e49-q'})])
    if fault:
        with pytest.raises(ValueError): s.accepted_assembly(a)
    else: assert s.accepted_assembly(a) == receipt


def test_phase_admission_rejects_wrong_phase_and_unbound_root_closure(admitted,tmp_path,monkeypatch):
    a = admitted; monkeypatch.chdir(tmp_path)
    a.update(schema_version=1,start_authorized=True)
    path = tmp_path/'admission.json'; s.write(path,a)
    with pytest.raises(ValueError,match='separate phase'): s.admission(path,digest(path),'technical')
    a['protected'] = {str(tmp_path/f'agents/sherlock/weights/agent_p{i}.pth'):s.V14_SHA for i in (0,1)}
    a['protected'][str(tmp_path/'Gruppe15.zip')] = s.ZIP_SHA
    a['training_completion'] = save(a,tmp_path/'closure.json',dict(synthetic=True))
    a['training_completion_sha256'] = 'wrong-root-hash'
    path = tmp_path/'second-admission.json'; s.write(path,a)
    monkeypatch.setattr(s,'source_identity',lambda *_a:a['source'])
    monkeypatch.setattr(s,'hashes',lambda mapping:dict(mapping))
    with pytest.raises(ValueError,match='Root training completion hash'): s.admission(path,digest(path),'performance')


@pytest.fixture
def owner_harness(tmp_path,monkeypatch):
    """Narrow adaptation of existing match_weight_compare owner fixtures; no processes."""
    from scripts import ensemble_diversity_supervisor as lifecycle
    from scripts import fog_reward_supervisor as supervisor
    import scripts
    out = tmp_path/'phase'; admission_path = tmp_path/'admission.json'
    usage = tmp_path/'usage.json'; usage.write_text('{}')
    config = dict(root=str(tmp_path),out=str(out),python=sys.executable,plans=[],source={'head':'fixed'},
        protected={},inputs={},stop_file=str(tmp_path/'STOP'),allow_battery=True)
    h = SimpleNamespace(out=out,launches=[],widths=[],returncodes={},fault=None,cleanup=[],children={},analysis=0)
    fake = SimpleNamespace(PROFILE=s.PROFILE,JOBS=s.JOBS,require=require,digest=digest,write=s.write,
        output_dir=lambda _a:out,bound=lambda _a,p:Path(p))
    def admit(path,sha,stage):
        require(digest(path) == sha and json.loads(path.read_text())['stage'] == stage,'Wrong independent admission')
        return copy.deepcopy(config)
    fake.admission = admit
    fake.technical_command = lambda _a,p,sha:[sys.executable,'-B','-m','scripts.frozen_v14_exposure_compare','technical']
    fake.performance_command = lambda _a,name:[sys.executable,'-B','-m','scripts.par_eval',name]
    fake.job_spec = lambda _a,name:dict(csv=str(out/(name+'.csv')))
    def validate(_a,name): require(h.fault != 'csv','Invalid actual CSV')
    fake.validate_csv = validate
    fake.check_technical = lambda r:require(r['games'] == 0,'Unexpected technical games')
    def analyze(_a): h.analysis += 1; return dict(games=200)
    fake.analyze = analyze
    monkeypatch.setitem(sys.modules,'scripts.frozen_v14_exposure_compare',fake)
    monkeypatch.setattr(scripts,'frozen_v14_exposure_compare',fake)
    def guard(state,owned,*,allow_battery):
        assert allow_battery and state['inputs'] == config['inputs']
        require(not Path(state['stop_file']).exists(),'External STOP')
        require(h.fault != 'quota','Quota reached 100%')
    monkeypatch.setattr(supervisor,'guard',guard)
    monkeypatch.setattr(lifecycle,'compute_lock',lambda _root:nullcontext())
    monkeypatch.setattr(lifecycle,'group_alive',lambda _pgid:False)
    monkeypatch.setattr(lifecycle,'request_stop',lambda path:Path(path).touch(exist_ok=True))
    class Child:
        def __init__(self,name,pid): self.name,self.pid = name,pid
        def poll(self): return h.returncodes.get(self.name,0)
    def spawn(state,name,argv,owned):
        assert len(owned) < 2 and name not in h.children
        child = Child(name,90000+len(h.launches)); h.children[name] = child
        h.launches.append(name); owned[name] = dict(process=child,pgid=child.pid,owner_pid=state['owner_pid'])
        h.widths.append(len(owned)); state['active'] = list(owned)
        state['jobs'][name] = dict(pid=child.pid,pgid=child.pid,owner_pid=state['owner_pid'],argv=argv)
        save_state(state)
        if name == 'technical':
            receipt = dict(status='complete',source=config['source'],admission_sha256=digest(admission_path),
                           command=argv,games=0)
            if h.fault == 'receipt': receipt['source'] = {'head':'wrong'}
            s.write(out/'technical-receipt.json',receipt)
        else: (out/(name+'.csv')).write_text('synthetic complete CSV')
        if h.fault == 'stop_after_spawn': Path(config['stop_file']).touch()
        if h.fault == 'admission_after_spawn': admission_path.write_text('changed')
    monkeypatch.setattr(lifecycle,'spawn_owned',spawn)
    def cleanup(owned):
        assert set(owned) <= set(h.children)
        h.cleanup.append(tuple(owned))
        if h.fault == 'cleanup': raise RuntimeError('owned group cleanup failed')
    monkeypatch.setattr(lifecycle,'shutdown_owned',cleanup)
    def run(stage):
        config['stage'] = stage; admission_path.write_text(json.dumps(config))
        monkeypatch.setattr(sys,'argv',['owner',stage,'--admission',str(admission_path),
            '--admission-sha',digest(admission_path),'--usage-file',str(usage)])
        return owner.main()
    h.run = run
    return h


@pytest.mark.parametrize('stage',['technical','performance'])
def test_owner_exact_phase_and_waves_without_automatic_transition_or_resume(owner_harness,stage):
    h = owner_harness; h.run(stage)
    state = json.loads((h.out/'state.json').read_text())
    expected = ['technical'] if stage == 'technical' else list(s.JOBS)
    assert h.launches == expected and state['status'] == 'complete' and state['active'] == []
    assert h.widths == ([1] if stage == 'technical' else [1,2,1,2,1])
    assert h.analysis == (0 if stage == 'technical' else 1) and state['promotion'] is False
    assert (h.out/'summary.json').exists() == (stage == 'performance')
    with pytest.raises(ValueError,match='no resume'): h.run(stage)
    assert h.launches == expected


@pytest.mark.parametrize('fault',['exit','csv','stop_after_spawn','admission_after_spawn'])
def test_owner_failure_cleans_only_owned_children_and_never_starts_later_wave(owner_harness,fault):
    h = owner_harness
    if fault == 'exit': h.returncodes[s.JOBS[0]] = 1
    else: h.fault = fault
    with pytest.raises(ValueError): h.run('performance')
    state = json.loads((h.out/'state.json').read_text())
    assert state['status'] == 'failed' and state['active'] == [] and h.cleanup
    assert h.launches == (list(s.JOBS[:1]) if fault in ('stop_after_spawn','admission_after_spawn') else list(s.JOBS[:2]))
    assert h.analysis == 0 and not (h.out/'summary.json').exists()


def test_quota_and_invalid_technical_receipt_cannot_launch_performance(owner_harness):
    h = owner_harness; h.fault = 'quota'
    with pytest.raises(ValueError,match='Quota'): h.run('technical')
    assert not h.launches and not h.out.exists()
    h.fault = 'receipt'
    with pytest.raises(ValueError,match='receipt differs'): h.run('technical')
    assert h.launches == ['technical'] and h.analysis == 0 and h.cleanup


def test_cleanup_failure_preserves_owned_active_record(owner_harness):
    h = owner_harness; h.fault = 'cleanup'; h.returncodes[s.JOBS[0]] = 1
    with pytest.raises(RuntimeError,match='cleanup failed'): h.run('performance')
    state = json.loads((h.out/'state.json').read_text())
    assert state['status'] == 'failed' and state['active'] == list(s.JOBS[:2])
    assert state['cleanup_error'] and h.analysis == 0
