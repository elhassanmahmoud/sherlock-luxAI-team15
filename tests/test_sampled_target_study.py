"""Synthetic Task3 specifications. Authored first as text; execution UNRUN."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest

BASE = Path(__file__).resolve().parents[1]

def load(name):
    spec = importlib.util.spec_from_file_location('scripts.' + name, BASE/'scripts'/f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

S = load('sampled_target_study')
V = load('sampled_target_supervisor')

def test_exact_four_arms_and_six_disjoint_cohorts():
    assert tuple(S.ARMS) == ('control45', 'sampled45', 'control46', 'sampled46')
    assert [len(v) for v in S.COHORTS.values()] == [20, 80, 20, 80, 20, 20]
    values = [seed for block in S.COHORTS.values() for seed in block]
    assert len(values) == len(set(values)) == 240
    assert 4242 not in values

@pytest.mark.parametrize('seed', [45, 46])
def test_rollouts_fixed_paired_and_complete(seed):
    control, sampled = (S.rollout_plan(f'{role}{seed}') for role in ('control', 'sampled'))
    assert control == sampled and len(control) == 200
    for phase, count, block in [('prefill', 40, 'prefill'), ('train', 160, 'train')]:
        rows = [r for r in control if r['phase'] == phase]
        assert len(rows) == count
        assert [(r['seed'], r['side']) for r in rows] == [
            (seed, side) for seed in S.COHORTS[f'{block}{seed}'] for side in S.SIDES]
        assert [r['game'] for r in rows] == list(range(count))
        assert all(r['opponent'] in S.MIX for r in rows)

def test_unknown_arm_and_missing_external_admission_fail_closed(tmp_path):
    with pytest.raises(ValueError): S.rollout_plan('sampled47')
    with pytest.raises(ValueError): S.validate_admission(tmp_path/'absent.json', None, 'study')
    assert S.ADMISSION_SHA256 is None

def test_training_config_has_only_fixed_overrides():
    cfg = dict(hidden=256, gamma=.99, batch_size=256, buffer_capacity=300000,
        canonical=True, double_dqn=True, use_sap=True, eps_end=.05, eps_decay_steps=60000,
        learn_start=5000, train_every=2, target_update_every=500, guided_prob=.7,
        lr=.0003, frozen=True, rules_in_training=False, rules_in_training_all=False,
        rescue_in_training=False, fog_unknown_reward_neutral=False, art_splash_in_training=False)
    out = S.training_config(cfg)
    assert out == dict(cfg, lr=5e-5, frozen=False, rules_in_training=True,
        rules_in_training_all=True, rescue_in_training=True)

def proof(role='control', seed=45):
    shared = dict(config_sha256='c'*64, schedule_sha256='s'*64,
        initial=dict(q='q'*64, target='q'*64, optimizer='o'*64, agent_rng='a'*64,
            global_rng='g'*64, env_steps=60000, learn_steps=0, replay_size=0),
        end=dict(q='q'*64,target='q'*64,optimizer='o'*64,agent_rng='b'*64,
            global_rng='h'*64,env_steps=72120,learn_steps=0,replay_size=6000),
        replay_sha256='r'*64, events_semantic_sha256='e'*64, trajectory_sha256='t'*64,
        rows_semantic_sha256='w'*64, captured=6000, committed=6000, terminal=100,
        nonterminal=5900, frames=12120, confirmed=12120,
        diagnosis=dict(rows=6000,nonterminal=5900,different_index=3,different_target=2,
            outside_mask=1,positive=1,negative=1,delta_sum=0.,readonly=True))
    return dict(schema_version=1,status='prefill_ready',profile=S.PROFILE,
        arm=f'{role}{seed}',run_seed=seed,bootstrap_mode=S.ARMS[f'{role}{seed}'][1],
        games=40,shared=shared)

def test_pair_compares_semantics_not_arm_or_mode():
    result = S.compare_prefill_proofs(proof(), proof('sampled'), 45)
    assert result['status'] == 'matched' and result['eligible'] is False
    assert result['run_seed'] == 45

@pytest.mark.parametrize('fault', ['mode', 'seed', 'rng', 'replay', 'events', 'rows',
    'missing', 'updates', 'no_index_intervention', 'no_target_intervention'])
def test_pair_rejects_corruption_or_null_intervention(fault):
    a, b = proof(), proof('sampled')
    if fault == 'mode': b['bootstrap_mode'] = 'double_dqn'
    elif fault == 'seed': b['run_seed'] = 46
    elif fault == 'rng': b['shared']['end']['agent_rng'] = 'z'*64
    elif fault in ('replay','events','rows'):
        key = {'replay':'replay_sha256','events':'events_semantic_sha256','rows':'rows_semantic_sha256'}[fault]
        b['shared'][key] = 'z'*64
    elif fault == 'missing': b['shared']['committed'] -= 1
    elif fault == 'updates': b['shared']['end']['learn_steps'] = 1
    else:
        key = 'different_index' if fault == 'no_index_intervention' else 'different_target'
        a['shared']['diagnosis'][key] = b['shared']['diagnosis'][key] = 0
    with pytest.raises(ValueError): S.compare_prefill_proofs(a, b, 45)

def episode_events():
    f = 'f'*64; m = 'm'*64
    return [
        dict(event='episode',episode_id=0,seed=4242,side='player_0',phase='prefill',game=0,opponent='default'),
        dict(event='frame',key=[0,0,0],env_steps=60000,observation_sha256='o'*64,native=[[0,0,0]]*16,
             units=[dict(uid=0,action=0,features_sha256=f,mask_sha256=m)]),
        dict(event='capture',identity=[0,0,0],match_idx=0,action=0,done=1.,s_sha256=f,ns_sha256=f,mask_sha256=m,reward=0.),
        dict(event='commit',identity=[0,0,0],successor_key=None,action=0,done=1.,next_action=-1,next_action_env_steps=-1,ordinal=1),
        dict(event='confirmed',key=[0,0,0],native_sha256=S.experiment.state_sha256(np.zeros((16,3),dtype=int))),
    ]

def test_streamed_events_need_confirmed_frames_and_exact_commits():
    tracker = S.EventValidator(initial_ordinal=0)
    for event in episode_events(): tracker.add(event)
    tracker.boundary(expected_steps=1)
    assert tracker.counts['captured'] == tracker.counts['committed'] == 1
    assert tracker.counts['frames'] == tracker.counts['confirmed'] == 1

@pytest.mark.parametrize('fault',['unconfirmed','duplicate','wrong_label','wrong_ordinal'])
def test_streamed_evidence_rejects_incomplete_or_false_events(fault):
    events = episode_events()
    if fault == 'unconfirmed': events.pop()
    elif fault == 'duplicate': events.insert(4, copy.deepcopy(events[3]))
    elif fault == 'wrong_label': events[3]['next_action'] = 0
    else: events[3]['ordinal'] = 2
    tracker = S.EventValidator(initial_ordinal=0)
    with pytest.raises(ValueError):
        for event in events: tracker.add(event)
        tracker.boundary(expected_steps=1)

def test_semantic_rows_ignore_elapsed_time_only():
    a = [dict(seed=1,side='player_0',result=1,secs=2.)]
    b = [dict(seed=1,side='player_0',result=1,secs=99.)]
    assert S.semantic_rows(a) == S.semantic_rows(b)
    b[0]['result'] = 0
    assert S.semantic_rows(a) != S.semantic_rows(b)

def test_technical_plan_is_exact_four_known_games():
    jobs = S.technical_plan()
    assert len(jobs) == 4
    assert {(j['bootstrap_mode'],j['side']) for j in jobs} == {
        (mode,side) for mode in S.MODES for side in S.SIDES}
    assert all(j['seed']==4242 and j['run_seed']==45 and j['opponent']=='default' for j in jobs)

def test_no_old_factory_or_immediate_action_audit_in_local_learner():
    text = (BASE/'scripts/sampled_target_study.py').read_text()
    assert 'VARIANTS[' not in text and 'action_audit(' not in text
    assert 'class PilotLearners(experiment.Learners)' in text

def test_supervisor_pairs_and_commands_are_fixed():
    assert V.PAIRS == (('control45','sampled45'),('control46','sampled46'))
    state = dict(python='/x/python',prepared='/p',out='/o',stage='study')
    command = V.training_command(state,'sampled45')
    assert command[command.index('--arm')+1] == 'sampled45'
    assert command[command.index('--supervisor-state')+1] == '/o/state.json'
    assert 'scripts.sampled_target_study' in command

def test_supervisor_guard_checks_all_existing_primitives(monkeypatch,tmp_path):
    calls=[]
    monkeypatch.setattr(V,'check_usage',lambda *a,**k:calls.append('quota') or {'used_percent':1})
    monkeypatch.setattr(V,'read_power',lambda:calls.append('power') or {'ac':True})
    monkeypatch.setattr(V,'source_identity',lambda *a:calls.append('source') or {'head':'x'})
    monkeypatch.setattr(V,'hashes',lambda x:x)
    monkeypatch.setattr(V,'check_model_processes',lambda *a:calls.append('processes'))
    state=dict(profile=V.PROFILE,stage='study',stop_file=str(tmp_path/'STOP'),usage_file='usage',python='py',plans=[],
        source={'head':'x'},inputs={},protected={},active=[])
    V.guard(state,{})
    assert calls == ['quota','power','source','processes']
    state['active'] = ['a','b','c']
    with pytest.raises(ValueError):V.guard(state,{})

def test_study_does_not_implement_task4():
    assert not hasattr(S,'performance_plan') and not hasattr(S,'validate_performance')

def two_step_evidence():
    data={'s':np.stack([np.zeros(79,dtype='float32'),np.ones(79,dtype='float32')]),
        'ns':np.stack([np.ones(79,dtype='float32'),np.ones(79,dtype='float32')*2]),
        'a':np.array([1,5],dtype='int64'),'r':np.array([.1,2],dtype='float32'),
        'done':np.array([0,1],dtype='float32'),'mask':np.array([[1,0,0,0,0,0]]*2,dtype=bool),
        'next_action':np.array([5,-1],dtype='int8'),'episode_id':np.array([0,0],dtype='int32'),
        'source_step':np.array([0,1],dtype='int16'),'match_idx':np.array([0,0],dtype='int8'),
        'uid':np.array([0,0],dtype='int8'),'next_action_env_steps':np.array([60001,-1],dtype='int64')}
    events=[episode_events()[0]]
    for i in range(2):
        native=np.zeros((16,3),dtype=int);native[0,0]=int(data['a'][i])
        events.append(dict(event='frame',key=[0,0,i],env_steps=60000+i,observation_sha256='o'*64,native=native.tolist(),
            units=[dict(uid=0,action=int(data['a'][i]),features_sha256=S.experiment.state_sha256(data['s'][i]),
                mask_sha256=S.experiment.state_sha256(data['mask'][i]))]))
        if i==1:
            events.append(dict(event='commit',identity=[0,0,0],successor_key=[0,0,1],action=1,done=0.,
                next_action=5,next_action_env_steps=60001,ordinal=1))
        events.append(dict(event='capture',identity=[0,i,0],match_idx=0,action=int(data['a'][i]),done=float(data['done'][i]),
            s_sha256=S.experiment.state_sha256(data['s'][i]),ns_sha256=S.experiment.state_sha256(data['ns'][i]),
            mask_sha256=S.experiment.state_sha256(data['mask'][i]),reward=float(data['r'][i])))
        if i==1:
            events.append(dict(event='commit',identity=[0,1,0],successor_key=None,action=5,done=1.,
                next_action=-1,next_action_env_steps=-1,ordinal=2))
        events.append(dict(event='confirmed',key=[0,0,i],native_sha256=S.experiment.state_sha256(native)))
    return events,data

def test_actual_later_frame_label_outside_mask_and_saved_arrays_join():
    events,data=two_step_evidence();tracker=S.EventValidator(data=data,total_committed=2)
    for event in events[:4]:tracker.add(event)
    assert tracker.ordinal==0 and len(tracker.pending)==1
    for event in events[4:]:tracker.add(event)
    tracker.boundary(expected_steps=2)
    assert tracker.checked_replay==2 and tracker.counts['nonterminal']==1

@pytest.mark.parametrize('fault',['next_action','next_action_env_steps','a','r','s','ns','mask','uid'])
def test_replay_evidence_detects_wrong_source_successor_or_reward(fault):
    events,data=two_step_evidence()
    if fault in ('s','ns'):data[fault][0,0]+=1
    elif fault=='mask':data[fault][0,1]=True
    else:data[fault][0]+=1
    with pytest.raises(ValueError):
        tracker=S.EventValidator(data=data,total_committed=2)
        for event in events:tracker.add(event)

@pytest.mark.parametrize('fault',['float_native','bad_uid','bad_action','bad_match','bad_clock'])
def test_frame_rejects_invalid_integer_domains(fault):
    events=episode_events();frame=events[1]
    if fault=='float_native':frame['native'][0]=[.5,0,0]
    elif fault=='bad_uid':frame['units'][0]['uid']=16
    elif fault=='bad_action':frame['units'][0]['action']=6
    elif fault=='bad_match':frame['key'][1]=3
    else:frame['env_steps']=-1
    tracker=S.EventValidator();tracker.add(events[0])
    with pytest.raises(ValueError):tracker.add(frame)

def test_replay_npz_schema_hash_matches_live_and_rejects_partial(tmp_path):
    _,data=two_step_evidence();path=tmp_path/'b.npz'
    np.savez(path,schema_version=np.array(1,dtype='int64'),**data)
    checked=S.load_replay_data(path)
    from types import SimpleNamespace
    live=SimpleNamespace(size=2,capacity=300000,obs_dim=79,pos=2,**checked)
    assert S.replay_hash(live)==S.replay_data_hash(checked)
    data.pop('next_action');np.savez(path,schema_version=np.array(1,dtype='int64'),**data)
    with pytest.raises(ValueError):S.load_replay_data(path)

def admission_fixture(tmp_path,monkeypatch):
    monkeypatch.setattr(S,'ROOT',tmp_path)
    approved=dict(source={'head':'f'*40},protected={'weight':'a'*64})
    monkeypatch.setattr(S,'pins',lambda:approved)
    def artifact(name,value):
        p=tmp_path/name;p.write_text(json.dumps(value));return {'path':name,'sha256':S.file_sha256(p)}
    raw=artifact('raw.json',{'scan':'raw'})
    audit=artifact('audit.json',dict(status='PASS',no_observed_conflicts=True,limitations=['external data unknown'],
        raw_audit=raw,files={'raw.json':raw['sha256']}))
    seed=artifact('seed.json',dict(schema_version=1,status='PASS',profile=S.PROFILE,cohorts=S.COHORTS,audit=audit))
    review=artifact('review.json',{'status':'PASS'})
    admit=dict(schema_version=1,status='PASS',profile=S.PROFILE,stage='technical',pins=approved,
        review=dict(review,path=str(tmp_path/review['path'])),seed_acceptance=dict(seed,path=str(tmp_path/seed['path'])),
        technical_acceptance=None)
    path=tmp_path/'admission.json';path.write_text(json.dumps(admit))
    return path,admit

def test_admission_binds_explicit_hash_seed_artifacts_and_current_source(tmp_path,monkeypatch):
    path,admit=admission_fixture(tmp_path,monkeypatch)
    value,bound=S.validate_admission(path,S.file_sha256(path),'technical')
    assert value==admit and len(bound)==5
    (tmp_path/'raw.json').write_text('{}')
    with pytest.raises(ValueError):S.validate_admission(path,S.file_sha256(path),'technical')

@pytest.mark.parametrize('fault',['wrong_sha','different_source','empty_inventory','missing_limit','wrong_cohort','no_technical_acceptance'])
def test_admission_rejects_incomplete_or_unreviewed_binding(tmp_path,monkeypatch,fault):
    path,admit=admission_fixture(tmp_path,monkeypatch)
    if fault=='wrong_sha':
        with pytest.raises(ValueError):S.validate_admission(path,'0'*64,'technical')
        return
    if fault=='different_source':monkeypatch.setattr(S,'pins',lambda:{})
    elif fault=='no_technical_acceptance':admit['stage']='study'
    else:
        seedpath=tmp_path/'seed.json';seed=json.loads(seedpath.read_text())
        if fault=='wrong_cohort':seed['cohorts']['prefill45'][0]=4242
        else:
            auditpath=tmp_path/'audit.json';audit=json.loads(auditpath.read_text())
            if fault=='empty_inventory':audit['files']={}
            else:audit['limitations']=[]
            auditpath.write_text(json.dumps(audit));seed['audit']['sha256']=S.file_sha256(auditpath)
        seedpath.write_text(json.dumps(seed));admit['seed_acceptance']['sha256']=S.file_sha256(seedpath)
    path.write_text(json.dumps(admit))
    with pytest.raises(ValueError):S.validate_admission(path,S.file_sha256(path),admit['stage'])

def test_readonly_target_diagnosis_uses_existing_networks_no_rng(monkeypatch):
    import torch
    from types import SimpleNamespace
    _,data=two_step_evidence()
    class Buffer(SimpleNamespace):
        def __len__(self):return self.size
    buf=Buffer(size=2,capacity=300000,obs_dim=79,pos=2,**data)
    class Net:
        def __call__(self,ns):return torch.tensor([[3.,2.,1.,0.,-1.,-2.]]*len(ns))
    agent=SimpleNamespace(buffer=buf,device='cpu',q=Net(),target_q=Net(),cfg=SimpleNamespace(gamma=.99))
    monkeypatch.setattr(S,'learning_identity',lambda agent:{'stable':True})
    rng=torch.get_rng_state().clone();result=S.diagnose_targets(agent)
    assert torch.equal(rng,torch.get_rng_state())
    assert result['rows']==2 and result['nonterminal']==result['different_index']==result['different_target']==1
    assert result['outside_mask']==result['negative']==1 and result.get('positive',0)==0
    assert result['readonly'] is True

def technical_receipt(role):
    shared=proof(role)['shared'];shared.pop('diagnosis')
    shared['end'].update(env_steps=60303,replay_size=10)
    shared.update(captured=10,committed=10,terminal=1,nonterminal=9,frames=303,confirmed=303)
    return dict(job=f'technical_{role}_p0',arm=f'{role}45',bootstrap_mode=S.ARMS[f'{role}45'][1],side='player_0',shared=shared)

def test_technical_pair_requires_real_nonterminal_label_exposure():
    control,sampled=technical_receipt('control'),technical_receipt('sampled')
    assert S.compare_technical_receipts(control,sampled,'player_0')['status']=='matched'
    for r in (control,sampled):
        r['shared'].update(captured=0,committed=0,terminal=0,nonterminal=0)
        r['shared']['end']['replay_size']=0
    with pytest.raises(ValueError):S.compare_technical_receipts(control,sampled,'player_0')

@pytest.mark.parametrize('field,value',[('games',199),('games',201),('updates',23999),('env_steps',120599),
    ('train_games',159),('prefill_games',39),('arm','sampled46'),('eligible',True)])
def test_final_receipt_rejects_missing_extra_or_wrong_progress(tmp_path,monkeypatch,field,value):
    entry=dict(run_seed=45,bootstrap_mode='double_dqn')
    manifest={'pins':{'source':'fixture'}}
    monkeypatch.setattr(S,'check_prepared',lambda *a:(manifest,entry,None))
    monkeypatch.setattr(S,'file_sha256',lambda p:'a'*64)
    receipt=dict(schema_version=1,status='done',profile=S.PROFILE,eligible=False,arm='control45',run_seed=45,
        bootstrap_mode='double_dqn',games=200,prefill_games=40,train_games=160,updates=24000,env_steps=120600,
        pins=manifest['pins'],manifest_sha256='a'*64,prepared='/fixture')
    receipt[field]=value;path=tmp_path/'final.json';path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError):S.validate_final_receipt(path,arm='control45')

def test_local_learners_constructs_exactly_one_shared_base(monkeypatch,tmp_path):
    from types import SimpleNamespace
    calls=[]
    def construct(*args,**kwargs):
        calls.append((args,kwargs));return SimpleNamespace(set_to_train_mode=lambda:None)
    monkeypatch.setattr(S,'SampledTargetAgent',construct)
    entry=dict(config={},run_seed=45,bootstrap_mode='sampled_successor')
    learners=S.PilotLearners(entry,tmp_path/'initial.pth',tmp_path/'run')
    assert len(calls)==1 and learners.agents['player_0'] is learners.agents['player_1']
    assert len(learners.unique())==1 and calls[0][1]['seed']==4500
    assert calls[0][1]['bootstrap_mode']=='sampled_successor'

def test_real_stream_writer_and_reader_bind_full_game_and_saved_arrays(tmp_path):
    from types import SimpleNamespace
    events,data=two_step_evidence()
    for step in range(2,303):
        events.extend([dict(event='frame',key=[0,min(step//101,2),step],env_steps=60000+step,
            observation_sha256='a'*64,native=[[0,0,0]]*16,units=[]),
            dict(event='confirmed',key=[0,min(step//101,2),step],native_sha256=S.experiment.state_sha256(np.zeros((16,3),dtype=int)))])
    fake=SimpleNamespace(buffer=SimpleNamespace(counts={'committed':0},_capture=None))
    path=tmp_path/'phase/provenance.jsonl.gz';writer=S.EventStream(path,fake)
    for event in events:
        if event['event']=='capture':
            ep,step,uid=event['identity']
            fake.buffer._capture={'rows':[dict(episode_id=ep,source_step=step,uid=uid,r=event['reward'])]}
        writer(event)
    game=writer.game_summary();summary=writer.close()
    plan=[{k:events[0][k] for k in S.PLAN_KEYS}]
    reread,games,checked=S.validate_stream(path,plan,data=data,total_committed=2)
    assert reread==summary and games==[game] and checked==2
    with pytest.raises(ValueError):S.validate_stream(path,plan,episode_start=1)

def test_exclusive_readiness_never_exposes_partial_json_and_never_overwrites(tmp_path):
    path=tmp_path/'ready.json'
    with pytest.raises(ValueError):S.write(path,{'invalid':float('nan')},exclusive=True)
    assert not path.exists()
    S.write(path,{'ready':True},exclusive=True)
    with pytest.raises(FileExistsError):S.write(path,{'ready':False},exclusive=True)
    assert json.loads(path.read_text())=={'ready':True}

def test_supervisor_technical_stage_never_launches_training_command():
    state=dict(stage='technical',python='/py',prepared='/prepared',out='/out')
    assert len(V.TECHNICAL_ARMS)==4
    for job in V.TECHNICAL_ARMS:
        command=V.training_command(state,job)
        assert command[4]=='technical' and command[command.index('--arm')+1]==job
    with pytest.raises(ValueError):V.training_command(state,'control45')

@pytest.mark.parametrize('fault',[None,'exit_failure','cleanup_failure'])
def test_supervisor_owned_queue_cleanup_and_no_automatic_next_stage(tmp_path,monkeypatch,fault):
    from types import SimpleNamespace
    trace=[];state=dict(stage='technical',status='prepared',out=str(tmp_path),stop_file=str(tmp_path/'STOP'),
        python='/python',prepared='/prepared',queue=list(V.TECHNICAL_ARMS),jobs={},active=[],receipts={},
        paired_prefill={},technical_pairs={})
    def spawn(state,job,command,owned):
        trace.append(('spawn',job));owned[job]={'pgid':100+len(trace),'process':SimpleNamespace(
            poll=lambda:7 if fault=='exit_failure' else 0)}
        state['jobs'][job]={'argv':command};state['active']=list(owned)
    def collect(state,pair):
        trace.append(('collect',pair));state['technical_pairs'][f'player_{pair[0][-1]}']={'status':'matched'}
        for job in pair:state['receipts'][job]={'fixture':'hash'}
    def cleanup(owned):
        trace.append(('cleanup',len(owned)))
        if fault=='cleanup_failure':raise ValueError('fixture cleanup failure')
    monkeypatch.setattr(V,'spawn_owned',spawn);monkeypatch.setattr(V,'collect_pair',collect)
    monkeypatch.setattr(V,'shutdown_owned',cleanup);monkeypatch.setattr(V,'group_alive',lambda *a:False)
    monkeypatch.setattr(V,'guard',lambda state,owned:None);monkeypatch.setattr(V,'save_state',lambda state:None)
    monkeypatch.setattr(V,'request_stop',lambda path:trace.append(('stop',str(path))))
    if fault:
        with pytest.raises(ValueError):V.run_queue(state)
        assert state['status']=='incomplete'
    else:
        assert V.run_queue(state)['status']=='done' and state['eligible'] is False and state['active']==[]
        assert [e for e in trace if e[0]=='spawn']==[('spawn',j) for j in V.TECHNICAL_ARMS]
        assert trace.index(('collect',V.TECHNICAL_PAIRS[0]))<trace.index(('spawn',V.TECHNICAL_ARMS[2]))
    if fault=='exit_failure':assert len([e for e in trace if e[0]=='spawn'])==2
    assert any(e[0]=='cleanup' for e in trace)

@pytest.mark.parametrize('fault',[None,'framework_argv0','wrong_executable','wrong_pid','wrong_command','peer_timeout'])
def test_worker_ownership_registration_is_bounded_and_exact(tmp_path,monkeypatch,fault):
    state=dict(profile=V.PROFILE,status='running',stage='study',root=str(V.ROOT),prepared=str(tmp_path/'prepared'),
        out=str(tmp_path),python='/python',stop_file=str(tmp_path/'STOP'),owner_pid=9,active=['control45','sampled45'],jobs={})
    command=V.training_command(state,'control45')
    state['jobs']['control45']=dict(pid=10,pgid=10,owner_pid=9,argv=command)
    state['jobs']['sampled45']={}
    if fault=='wrong_pid':state['jobs']['control45']['pid']=11
    elif fault=='wrong_command':state['jobs']['control45']['argv']=['bad']
    elif fault=='peer_timeout':state['jobs'].pop('sampled45')
    path=tmp_path/'state.json';path.write_text(json.dumps(state));calls=[]
    monkeypatch.setattr(V.os,'getpid',lambda:10);monkeypatch.setattr(V.os,'getpgrp',lambda:10)
    monkeypatch.setattr(V.os,'getppid',lambda:9);monkeypatch.setattr(V.os,'kill',lambda pid,sig:calls.append((pid,sig)))
    actual=command.copy()
    if fault=='framework_argv0':
        actual[0]='/Library/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python'
    monkeypatch.setattr(V.sys,'orig_argv',actual)
    monkeypatch.setattr(V.sys,'executable','/wrong/python' if fault=='wrong_executable' else state['python'])
    monkeypatch.setattr(V,'guard',lambda *a:calls.append('guard'))
    clock=iter([0,16]);monkeypatch.setattr(V.time,'monotonic',lambda:next(clock))
    if fault not in (None,'framework_argv0'):
        with pytest.raises(ValueError):V.worker_guard(path,'control45',V.run_name('control45'),state['prepared'],startup=True)
        assert 'guard' not in calls
    else:
        assert V.worker_guard(path,'control45',V.run_name('control45'),state['prepared'],startup=True)==state
        assert calls==[(9,0),'guard']
