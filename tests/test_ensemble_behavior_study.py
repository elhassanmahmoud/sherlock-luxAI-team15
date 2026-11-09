"""Synthetic contracts only: production archives and simulator access are forbidden."""
import copy
from contextlib import nullcontext
import importlib
import json
from pathlib import Path
import sys

import numpy as np
import pytest
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.model import QNet
from scripts import match_weight_study as old


@pytest.fixture
def study(monkeypatch):
    if not importlib.util.find_spec('scripts.ensemble_behavior_study'):
        pytest.skip('Behavior contract not implemented yet')
    module = importlib.import_module('scripts.ensemble_behavior_study')
    monkeypatch.setattr(torch, 'load', lambda *_a, **_k: pytest.fail('Archive loads forbidden'))
    from scripts import common
    monkeypatch.setattr(common, 'play_game', lambda *_a, **_k: pytest.fail('Games forbidden'))
    # Block a lazy simulator import as well as the ordinary game entry point.
    monkeypatch.setitem(sys.modules, 'luxai_s3.wrappers', None)
    return module


def test_behavior_entrypoint_exists():
    assert importlib.util.find_spec('scripts.ensemble_behavior_study'), 'Behavior contract not implemented'


def fixture_agent(start=48):
    cfg = old.training_config(AgentConfig(buffer_capacity=128, batch_size=8, learn_start=1,
                                         target_update_every=1).to_dict(), 'control')
    with torch.random.fork_rng(devices=[]):
        base = QNet(79, 6, 256, True).state_dict()
        states = []
        for i in range(36):
            state = {k: torch.zeros_like(v) for k,v in base.items()}
            state['adv.2.bias'][i % 6] = i + 1.
            states.append(state)
    a = dict(start=start, config={'control': cfg})
    agent = old.make_learner(a, states[18], 'control')
    return agent, states, cfg


def fake_decision(agent, *, fail=False):
    def act(step, obs):
        if obs == 'reset':
            return np.zeros((2,3), dtype=int)
        ids = [2,4] if obs != 'empty' else []
        x = torch.ones((len(ids),79), dtype=torch.float32)
        masks = np.ones((len(ids),6), dtype=bool)
        if ids: masks[0,5] = False
        agent._cache = (step, {}, ids, {u:x[k].numpy().copy() for k,u in enumerate(ids)},
                        {u:masks[k].copy() for k,u in enumerate(ids)}, {})
        if not ids: return np.zeros((2,3), dtype=int)
        with torch.no_grad(): output = agent.q(x)
        values = output.numpy(); values[~masks] = -np.inf
        if fail: raise RuntimeError('after forward')
        return values.argmax(1)
    agent._act_est = act
    return act


def test_order_current_member_once_alias_and_rng(study):
    agent, states, _ = fixture_agent(); original = fake_decision(agent)
    before = study.rng_identity(agent); identity = old.model_identity(agent)
    opt_ids = [id(p) for g in agent.opt.param_groups for p in g['params']]
    with study.BehaviorEnsemble(agent, states, True) as adapter:
        assert study.rng_identity(agent) == before and old.model_identity(agent) == identity
        calls = [0]*36; handles = []
        for index, net in [(18,agent.q), *adapter.frozen.items()]:
            def count(_m,_i,_o,index=index): calls[index] += 1
            handles.append(net.register_forward_hook(count))
        agent._act_est(7, 'active')
        assert calls == [1]*36
        last = adapter.last
        expected = torch.stack([torch.from_numpy(last['member_q'][i]) for i in range(36)]).mean(0).numpy()
        assert np.array_equal(last['mean_q'], expected) and np.isfinite(last['mean_q']).all()
        assert np.isfinite(last['raw_q']).all()  # Core masked its aliased output afterwards.
        assert np.array_equal(last['member_q'][18],last['raw_q'])
        for i,state in enumerate(states):
            bias=state['adv.2.bias'].numpy()
            assert np.array_equal(last['member_q'][i],np.tile(bias-bias.mean(),(2,1)))
        first = last['mean_q'].copy()
        with torch.no_grad(): agent.q.adv[2].bias[1] += 100
        agent._act_est(8,'active')
        assert not np.array_equal(adapter.last['mean_q'],first)
        assert adapter.stats['member_forwards'] == 72 and adapter.stats['proposal_changed_units'] > 0
        assert [id(p) for g in agent.opt.param_groups for p in g['params']] == opt_ids
        assert not agent.extra_q and all(not p.requires_grad and p.grad is None
                                        for net in adapter.frozen.values() for p in net.parameters())
        for h in handles: h.remove()
    assert agent._act_est is original and not agent.q._forward_hooks


@pytest.mark.parametrize('enabled',[False,True])
def test_noop_and_exception_cleanup(study,enabled):
    agent, states, _ = fixture_agent(); original = fake_decision(agent,fail=True)
    with study.BehaviorEnsemble(agent,states,enabled) as adapter:
        agent._act_est(0,'reset'); agent._act_est(1,'empty')
        assert adapter.stats['network_calls'] == 0
        before = study.rng_identity(agent)
        with pytest.raises(RuntimeError,match='after forward'): agent._act_est(2,'active')
        assert not agent.q._forward_hooks and study.rng_identity(agent) == before
    assert agent._act_est is original


def test_off_has_original_output_and_no_extra_forward(study):
    agent, states, _ = fixture_agent(); original = fake_decision(agent)
    expected = original(3,'active'); before = study.rng_identity(agent)
    with study.BehaviorEnsemble(agent,states,False) as adapter:
        assert not adapter.frozen
        assert np.array_equal(agent._act_est(3,'active'),expected)
        assert adapter.stats['member_forwards'] == 0 and study.rng_identity(agent) == before


def test_two_adapter_instances_cannot_double_install(study):
    agent,states,_=fixture_agent(); original=fake_decision(agent)
    first=study.BehaviorEnsemble(agent,states,True); second=study.BehaviorEnsemble(agent,states,True)
    with first:
        with pytest.raises(ValueError):
            with second: pass
        agent._act_est(1,'active')
        assert first.stats['member_forwards']==36 and second.stats['member_forwards']==0
    assert agent._act_est is original and not agent.q._forward_hooks


def test_original_ddqn_adam_and_target_unchanged_outside_act(study):
    agent, states, _ = fixture_agent(); baseline, _, _ = fixture_agent()
    for a in (agent,baseline):
        for i in range(12):
            a.buffer.push(np.full(79,i/12,np.float32),i%6,float(i%3-1),
                          np.full(79,(i+1)/12,np.float32),i%4==0,np.array([1,1,0,1,1,1],bool))
    with study.BehaviorEnsemble(agent,states,True) as adapter:
        frozen = {i:old.state_sha256(m.state_dict()) for i,m in adapter.frozen.items()}
        agent._learn(); baseline._learn()
        assert old.model_identity(agent) == old.model_identity(baseline)
        assert agent.learn_steps == baseline.learn_steps == 1
        assert study.rng_identity(agent)['agent'] == study.rng_identity(baseline)['agent']
        assert adapter.stats['member_forwards'] == 0
        assert frozen == {i:old.state_sha256(m.state_dict()) for i,m in adapter.frozen.items()}
        assert all(p.grad is None for m in adapter.frozen.values() for p in m.parameters())


@pytest.mark.parametrize('broken',['count','dtype','shape','nan','cpu','initial'])
def test_malformed_member_or_learner_rejected(study,broken):
    agent, states, _ = fixture_agent()
    if broken == 'count': states.pop()
    if broken == 'dtype': states[0]['body.0.weight'] = states[0]['body.0.weight'].double()
    if broken == 'shape': states[0]['body.0.weight'] = torch.zeros(256,78)
    if broken == 'nan': states[0]['body.0.weight'][0,0] = float('nan')
    if broken == 'cpu': agent.device = torch.device('cuda')
    if broken == 'initial': states[18]['adv.2.bias'][0] += 1
    with pytest.raises(ValueError):
        with study.BehaviorEnsemble(agent,states,True): pass


def test_joint_release_rejects_one_arm_stale_review_or_wrong_starts(study):
    a = dict(source={'head':'new'},out='/tmp/unused')
    pins = {'on48':'48','on49':'49'}
    valid = dict(profile=study.PROFILE,status='approved',source=a['source'],starts=[48,49],
        roles=['on48','on49'],admission_sha256='a',prefill_sha256=pins,root_review_sha256='review')
    study.validate_release(valid,a,'a',pins)
    for field,value in [('roles',['on48']),('starts',[48,48]),('prefill_sha256',{'on48':'48'}),
                        ('admission_sha256','stale'),('root_review_sha256','')]:
        with pytest.raises(ValueError): study.validate_release(dict(valid,**{field:value}),a,'a',pins)


def test_admission_rejects_phase_before_any_model_read(study,tmp_path):
    path = tmp_path/'a.json'; path.write_text(json.dumps({'profile':study.PROFILE,'stage':'resume'}))
    with pytest.raises(ValueError): study.admission(path,old.digest(path),'resume')


def test_technical_admission_current_bindings_without_any_archive_load(study,tmp_path,monkeypatch):
    monkeypatch.setattr(study,'ROOT',tmp_path); monkeypatch.chdir(tmp_path)
    weights=tmp_path/'agents/sherlock/weights'; weights.mkdir(parents=True)
    for i in (0,1): (weights/f'agent_p{i}.pth').write_bytes(b'fake weight bytes, never loaded')
    (tmp_path/'Gruppe15.zip').write_bytes(b'fake zip bytes')
    monkeypatch.setattr(old,'V14_SHA',old.digest(weights/'agent_p0.pth'))
    monkeypatch.setattr(old,'ZIP_SHA',old.digest(tmp_path/'Gruppe15.zip'))
    protected={str(weights/f'agent_p{i}.pth'):old.V14_SHA for i in (0,1)}
    protected[str(tmp_path/'Gruppe15.zip')]=old.ZIP_SHA
    source={'head':'new'}; initial={'48':{'q':'q'},'49':{'q':'q'}}
    monkeypatch.setattr(study,'source_identity',lambda *args:source)
    monkeypatch.setattr(study,'historical',lambda a:dict(initial=initial))
    a=dict(profile=study.PROFILE,schema_version=1,stage='technical',start_authorized=True,allow_battery=True,
        starts=[48,49],historical_runtime_gap_acknowledged=True,root=str(tmp_path),python=sys.executable,
        plans=[],source=source,runtime=study.runtime_identity(),protected=protected,inputs=protected,
        v14_source=str(weights/'agent_p0.pth'),initial=initial,
        out=str(tmp_path/'experiments/analysis'/study.PROFILE/'technical_v1'))
    p=tmp_path/'a.json'
    def admit(data): p.write_text(json.dumps(data)); return study.admission(p,old.digest(p),'technical')
    assert admit(a)==a
    for field,value in [('start_authorized',False),('starts',[48]),('historical_runtime_gap_acknowledged',False),
                        ('runtime',{}),('initial',{}),('out',str(tmp_path/'elsewhere'))]:
        with pytest.raises(ValueError): admit(dict(a,**{field:value}))


def test_worker_identity_requires_exact_both_registered_roles(study):
    a = dict(stage='training',source={},out='/tmp/out',root='/tmp',python='/python',plans=[],
             protected={},stop_file='/tmp/STOP',allow_battery=True,starts=[48,49])
    command = study.worker_command(a,'/a.json','sha','/tmp/out/state.json','on48')
    state = dict(a,profile=study.PROFILE,status='running',owner_pid=12,admission_sha256='sha',
        active=['on48','on49'],jobs={'on48':dict(pid=13,pgid=13,owner_pid=12,argv=command),'on49':{}})
    args = dict(pid=13,pgid=13,ppid=12,executable='/python',actual=command)
    study.check_worker(state,a,'sha','on48',command,**args)
    for key,value in [('owner_pid',1),('active',['on48','foreign']),('admission_sha256','wrong')]:
        with pytest.raises(ValueError): study.check_worker(dict(state,**{key:value}),a,'sha','on48',command,**args)


def synthetic_checkpoint_io(monkeypatch):
    payloads = {}
    def save(payload,stream):
        payloads[str(stream.name)] = copy.deepcopy(payload); stream.write(b'synthetic only')
    monkeypatch.setattr(torch,'save',save)
    def load(path,**kwargs):
        assert str(path) in payloads, 'Only synthetic test payloads may be read'
        return copy.deepcopy(payloads[str(path)])
    monkeypatch.setattr(torch,'load',load)
    return payloads


def test_actual_synthetic_prefill_and_joint_manual_release(study,tmp_path,monkeypatch):
    from agents.sherlock.replay_buffer import ReplayBuffer
    payloads = synthetic_checkpoint_io(monkeypatch)
    a = dict(stage='training',source={'head':'new'},out=str(tmp_path),starts=[48,49],config=None)
    proofs = {}; saved_agents={}; mechanisms={}
    for role,start in [('on48',48),('on49',49)]:
        agent, states, cfg = fixture_agent(start); a['config'] = cfg
        agent.buffer = ReplayBuffer(128,79)
        for i in range(80): agent.buffer.push(np.ones(79,np.float32),i%6,.25,
                    np.zeros(79,np.float32),False,np.ones(6,bool))
        initial = old.model_identity(agent); agent.env_steps = 72120
        a.setdefault('initial',{})[str(start)] = initial
        with study.BehaviorEnsemble(agent,states,True) as adapter:
            a['source_members'] = adapter.source_members
            adapter.stats.update(act_calls=12120,network_calls=40,member_forwards=1440,unit_steps=80)
            rows = [dict(key=key,role='control',behavior='ensemble',start=start,steps=303,
                point_counting_version=2,before={'env_steps':60000+303*i,'learn_steps':0},
                env_steps=60303+303*i,learn_steps=0,loss=None,reward_audit={'transitions':2},
                final_action_audit={'checked_replay_transitions':2})
                for i,key in enumerate(old.rollout_plan(start)[:40])]
            records = [dict(uid=np.arange(80),outcome=np.ones(80),control=np.full(80,.25),match=np.full(80,18.25))]
            directory=tmp_path/role; directory.mkdir()
            proof=study.prefill_proof(directory,agent,a,'sha',role,rows,initial,records,adapter)
            saved_agents[role]=agent; mechanisms[role]=proof['mechanism']
            study.write(directory/'prefill.json',proof)
            study.write(directory/'waiting.json',dict(profile=study.PROFILE,role=role,admission_sha256='sha',
                                                     prefill_sha256=old.digest(directory/'prefill.json')))
            assert study.validate_prefill_file(directory/'prefill.json',a,role)['learn_steps']==0
            proofs[role]=old.digest(directory/'prefill.json')
            cp=payloads[str(directory/'prefill.pth')]
            cp['cfg']['w_match']=20
            with pytest.raises(ValueError): study.validate_prefill_file(directory/'prefill.json',a,role)
            cp['cfg']['w_match']=2
    study.write(tmp_path/'state.json',dict(status='running',active=['on48','on49'],admission_sha256='sha'))
    review=tmp_path/'review.json'
    review.write_text(json.dumps(dict(status='PASS',profile=study.PROFILE,source=a['source'],
        admission_sha256='sha',prefill_sha256=proofs)))
    assert not (tmp_path/'release.json').exists()
    study.approve_prefill(a,'sha',review,old.digest(review))
    release=json.loads((tmp_path/'release.json').read_text())
    assert release['prefill_sha256']==proofs and release['roles']==['on48','on49']
    with pytest.raises(FileExistsError): study.approve_prefill(a,'sha',review,old.digest(review))
    role='on48'; directory=tmp_path/role; agent=saved_agents[role]
    rows=json.loads((directory/'prefill.json').read_text())['rows']
    for i,key in enumerate(old.rollout_plan(48)[40:],40):
        for _ in range(2): agent.buffer.push(np.ones(79,np.float32),i%6,.25,np.zeros(79,np.float32),False,np.ones(6,bool))
        rows.append(dict(key=key,role='control',behavior='ensemble',start=48,steps=303,point_counting_version=2,
            before=dict(env_steps=60000+303*i,learn_steps=(i-40)*150),env_steps=60303+303*i,
            learn_steps=(i-39)*150,loss=.1,reward_audit={'transitions':2},final_action_audit={'checked_replay_transitions':2}))
    agent._learn(); agent.env_steps=193320; agent.learn_steps=60000
    for state in agent.opt.state.values(): state['step'].fill_(60000)
    study.checkpoint(directory/'final.pth',agent,a,role,'complete',440)
    old.save_replay(directory/'final-replay.npz',agent.buffer)
    (directory/'games.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    mechanism=copy.deepcopy(mechanisms[role]); mechanism['stats'].update(act_calls=133320,unit_steps=880,
                                                                       network_calls=440,member_forwards=15840)
    final=dict(profile=study.PROFILE,status='complete',stage='training',role=role,start=48,source=a['source'],
        config=a['config'],behavior='ensemble',admission_sha256='sha',games=rows,mechanism=mechanism,
        release_sha256=old.digest(tmp_path/'release.json'),final_identity=old.model_identity(agent),
        final_replay_sha256=old.state_sha256(old.replay_data(agent.buffer)),files=old.hashes(directory.iterdir()))
    study.write(directory/'receipt.json',final)
    assert study.validate_final_receipt(directory/'receipt.json',a,'sha',role)['learn_steps']==60000
    cp=payloads[str(directory/'final.pth')]; next(iter(cp['opt']['state'].values()))['step'].fill_(59999)
    with pytest.raises(ValueError): study.validate_final_receipt(directory/'receipt.json',a,'sha',role)


def test_closed_history_runtime_rejects_changed_old_bytes(study):
    historical=dict(head='old',python='/python',executable='/real',executable_sha256='exe',files={'/old.py':'old'})
    current=dict(historical,head='new',files={'/old.py':'old','/new.py':'new'})
    study.check_runtime(current,historical)
    for broken in [dict(current,files={'/old.py':'changed'}),dict(current,executable_sha256='changed')]:
        with pytest.raises(ValueError): study.check_runtime(broken,historical)


def test_new_input_pin_cannot_replace_original_technical_hash(study,tmp_path,monkeypatch):
    from scripts import match_weight_compare
    def put(name,value):
        p=tmp_path/name; p.write_text(json.dumps(value)); return str(p)
    cfg={}; initial=put('control-initial.json',dict(start=48,config=cfg,initial={'q':'q'}))
    prefill=put('prefill.json',dict(initial={'q':'q'},current={'q':'q'},learn_steps=0,games=40))
    final=tmp_path/'final.pth'; final.write_bytes(b'not a model')
    receipt=put('receipt.json',{'files':old.hashes([initial,prefill])})
    source=dict(head='old',python='p',executable='p',executable_sha256='p',files={})
    tech=put('tech.json',dict(source=source,status='complete',profile=old.PROFILE,stage='technical',
                            start=48,config={'control':cfg},files={}))
    original_hash=old.digest(tech)
    train=put('train.json',dict(config={'control':cfg},rollout_plan=old.rollout_plan(48),
                              technical_receipt=tech,inputs={tech:original_hash}))
    pair=put('closure.json',{})
    closure=put('completion.json',dict(source=source,pairs={'48':dict(admission=train,closure=pair,
        closure_sha256=old.digest(pair),models={'control':{'receipt':receipt}})}))
    monkeypatch.setattr(study,'COMPLETION_SHA',old.digest(closure))
    monkeypatch.setattr(study,'CONTROL_SHA',(old.digest(final),'unused'))
    monkeypatch.setattr(match_weight_compare,'accepted_training',lambda a:{'control':[dict(path=final,config=cfg)]})
    changed=json.loads(Path(tech).read_text()); changed['unaccepted_change']=True; Path(tech).write_text(json.dumps(changed))
    a=dict(training_completion=closure,source=dict(source,head='new'),config=cfg,
           rollout_plans={'48':old.rollout_plan(48)},inputs=old.hashes(tmp_path.iterdir()))
    with pytest.raises(ValueError,match='Original technical'): study.historical(a)


def test_four_technical_cases_use_control_rows_not_global_match_replay(study,tmp_path):
    agent,states,cfg=fixture_agent(); initial=old.model_identity(agent)
    historical=dict(initial={'48':initial,'49':initial},technical={'games':[],
                    'final_replay_sha256':'irrelevant-MATCH20-global-hash'})
    rows=[]; files={}
    for enabled in (False,True):
        agent,_,_=fixture_agent(); fake_decision(agent)
        with study.BehaviorEnsemble(agent,states,enabled) as adapter:
            for i,(seed,side) in enumerate(old.TECH_KEYS):
                agent._act_est(i,'active'); mechanism=adapter.proof()
                mechanism['stats']['act_calls']=303*(i+1)
                data=dict(uid=np.array([2,4]),outcome=np.ones(2),control=np.array([.25,.5]),match=np.array([18.25,18.5]))
                evidence=old.save_reward_evidence(tmp_path/f'{enabled}-{i}.npz',data)
                files[evidence['path']]=evidence['sha256']
                row=dict(key=dict(phase='technical',game=i,seed=seed,side=side,opponent='solution92'),
                    role='control',behavior='ensemble' if enabled else 'off',start=48,steps=303,
                    point_counting_version=2,before=dict(env_steps=60000+303*i,learn_steps=0),
                    env_steps=60303+303*i,learn_steps=0,initial=initial,current=initial,
                    loss=None,epsilon=0.050000000000000044,game_win=0,point_win=0.,
                    reward_audit=dict(transitions=2,updates=303,nonzero_outcome_rows=2,masked_final_actions=16 if i==0 else 65),
                    final_action_audit={'checked_replay_transitions':2,'act_calls':303,'update_calls':303},our_wins=1,opp_wins=2,
                    our_points=30,opp_points=40,result=0.,native_sha256=f'native-{enabled}-{i}',
                    trajectory_sha256='public',reward_evidence=evidence,mechanism=mechanism)
                rows.append(row)
                if not enabled: historical['technical']['games'].append(copy.deepcopy(row))
    start49,_,_=fixture_agent(49)
    with study.BehaviorEnsemble(start49,states,True) as adapter: setup49=adapter.proof()
    receipt=dict(profile=study.PROFILE,status='complete',stage='technical',games=rows,files=files,
                 config=cfg,start49_setup=setup49)
    study.check_technical(receipt,historical)
    for kind in ('off_native','off_initial','on_exposure','on_final','changed_frozen','counter','epsilon','loss','game_win','updates'):
        broken=copy.deepcopy(receipt)
        if kind=='off_native': broken['games'][0]['native_sha256']='wrong'
        if kind=='off_initial': broken['games'][0]['initial']['q']='wrong'
        if kind=='on_exposure':
            for r in broken['games'][2:]: r['mechanism']['stats']['proposal_changed_units']=0
        if kind=='on_final':
            for r,h in zip(broken['games'][2:],rows[:2]): r['native_sha256']=h['native_sha256']
        if kind=='changed_frozen': broken['games'][2]['mechanism']['frozen']['0']='changed'
        if kind=='counter': broken['games'][1]['before']['env_steps']=60000
        if kind=='epsilon': broken['games'][2]['epsilon']=0.
        if kind=='loss': broken['games'][2]['loss']=.1
        if kind=='game_win': broken['games'][2]['game_win']=1
        if kind=='updates': broken['games'][2]['reward_audit']['updates']=302
        with pytest.raises(ValueError): study.check_technical(broken,historical)


def test_checkpoint_rejects_extra_members_and_wrong_update_count(study,tmp_path,monkeypatch):
    payloads=synthetic_checkpoint_io(monkeypatch)
    agent,states,cfg=fixture_agent(); a=dict(config=cfg,source={'head':'x'})
    agent.env_steps=72120
    study.checkpoint(tmp_path/'prefill.pth',agent,a,'on48','prefill',40)
    cp=payloads[str(tmp_path/'prefill.pth')]
    study.check_checkpoint(cp,a,'on48','prefill',40,0)
    for field,value in [('ensemble',[states[0]]),('learn_steps',1),('feature_dim',101)]:
        with pytest.raises(ValueError): study.check_checkpoint(dict(cp,**{field:value}),a,'on48','prefill',40,0)


def test_owner_entrypoint_exists():
    assert importlib.util.find_spec('scripts.ensemble_behavior_owner'), 'Joint owner not implemented'


def test_worker_keeps_one_env_stops_at_prefill_without_learning_and_saves_incomplete(study,tmp_path,monkeypatch):
    from types import SimpleNamespace
    payloads=synthetic_checkpoint_io(monkeypatch)
    seed_agent,states,cfg=fixture_agent(); initial=old.model_identity(seed_agent)
    a=dict(stage='training',out=str(tmp_path),config=cfg,initial={'48':initial,'49':initial},
           stop_file=str(tmp_path/'STOP'),source={'head':'fixed'})
    state_path=tmp_path/'state.json'; state_path.write_text(json.dumps({'jobs':{'on48':{},'on49':{}}}))
    made=[]; calls=[]
    class Env:
        def __init__(self,**kwargs): self.closed=False; made.append(self)
        def close(self): self.closed=True
    monkeypatch.setitem(sys.modules,'luxai_s3.wrappers',SimpleNamespace(LuxAIS3GymEnv=Env))
    monkeypatch.setattr(study,'load_members',lambda a:states)
    original=study.learner
    def learner(*args):
        assert len(made)==1 and not made[0].closed
        return original(*args)
    monkeypatch.setattr(study,'learner',learner)
    class Guard:
        def __init__(self,*args): self.command=['synthetic']; self.release_sha=None
        def __call__(self): pass
    monkeypatch.setattr(study,'WorkerGuard',Guard)
    def play(agent,key,env):
        assert env is made[0] and not agent.learn_enabled and agent.learn_steps==0
        calls.append(key)
        for i in range(2): agent.buffer.push(np.ones(79,np.float32),0,.25,np.zeros(79,np.float32),False,np.ones(6,bool))
        agent.env_steps+=303
        return {'key':key},dict(uid=np.arange(2),outcome=np.ones(2),control=np.full(2,.25),match=np.full(2,18.25))
    monkeypatch.setattr(old,'play_one',play)
    def stop(*args): raise ValueError('Root did not release')
    monkeypatch.setattr(study,'wait_release',stop)
    with pytest.raises(ValueError,match='Root did not release'):
        study.run_worker(a,tmp_path/'a.json','sha',state_path,'on48')
    assert len(calls)==40 and calls==old.rollout_plan(48)[:40] and len(made)==1 and made[0].closed
    result=json.loads((tmp_path/'on48/incomplete.json').read_text())
    assert result['completed_games']==40 and result['eligible'] is False
    cp=payloads[str(tmp_path/'on48/incomplete.pth')]
    assert cp['learn_steps']==0 and not cp['opt']['state'] and cp['behavior']['status']=='incomplete'
    assert not (tmp_path/'on48/final.pth').exists()


@pytest.mark.parametrize('stage,release,fault',[
    ('technical',False,None),('training',True,None),('training',False,None),('training',True,'worker')])
def test_owner_one_phase_both_workers_manual_barrier_and_cleanup(study,tmp_path,monkeypatch,stage,release,fault):
    if not importlib.util.find_spec('scripts.ensemble_behavior_owner'): pytest.skip('Owner not implemented yet')
    owner=importlib.import_module('scripts.ensemble_behavior_owner')
    out=tmp_path/'out'; admission_path=tmp_path/'a.json'; usage=tmp_path/'usage.json'; usage.write_text('{}')
    a=dict(profile=study.PROFILE,stage=stage,starts=[48,49],root=str(tmp_path),out=str(out),
        python=sys.executable,plans=[],source={'head':'x'},protected={},inputs={},allow_battery=True,
        stop_file=str(tmp_path/'STOP'))
    a['inputs'][str(Path(owner.__file__).resolve())]=old.digest(owner.__file__)
    admission_path.write_text(json.dumps(a)); sha=old.digest(admission_path)
    monkeypatch.setattr(study,'admission',lambda *args:a)
    monkeypatch.setattr(study,'output_dir',lambda a:out)
    monkeypatch.setattr(study,'historical',lambda a:{})
    checked=[]
    monkeypatch.setattr(study,'check_technical',lambda *_:checked.append('technical'))
    children={}; launched=[]; cleaned=[]; post_release=set(); saw_learning=[]
    class Child:
        def __init__(self,role): self.role=role
        def poll(self):
            if stage=='training' and not (out/'release.json').exists(): return None
            if stage=='training' and self.role not in post_release:
                post_release.add(self.role); return None
            return 1 if fault=='worker' else 0
    def spawn(state,role,command,owned):
        launched.append(role); child=Child(role); children[role]=child
        owned[role]=dict(process=child,pgid=90000+len(launched))
        state['jobs'][role]=dict(argv=command,returncode=None); state['active']=list(owned)
        directory=out/role; directory.mkdir()
        study.write(directory/'receipt.json',dict(status='complete',profile=study.PROFILE,stage=stage,
            role=role,start=49 if role=='on49' else 48,source=a['source'],admission_sha256=sha,
            command=command,games=[{}]*(4 if stage=='technical' else 440),release_sha256=None))
        if stage=='training':
            study.write(directory/'prefill.json',{'role':role}); study.write(directory/'waiting.json',{'role':role})
    def sleep(_):
        state=json.loads((out/'state.json').read_text())
        assert launched==['on48','on49'] and set(state['prefill_ready'])=={'on48','on49'}
        if (out/'release.json').exists():
            assert state['awaiting_root_release'] is False
            saw_learning.append(True); return
        assert not (out/'release.json').exists()
        if not release: raise RuntimeError('No Root release')
        review=tmp_path/'review.json'; review.write_text('{}')
        study.write(out/'release.json',dict(profile=study.PROFILE,status='approved',source=a['source'],
            starts=[48,49],roles=['on48','on49'],admission_sha256=sha,prefill_sha256=state['prefill_ready'],
            root_review=str(review),root_review_sha256=old.digest(review)))
        for role in launched:
            p=out/role/'receipt.json'; r=json.loads(p.read_text()); r['release_sha256']=old.digest(out/'release.json')
            p.write_text(json.dumps(r))
    def final(path,a,sha,role):
        assert all(c.poll()==0 for c in children.values()); checked.append(role)
        return dict(status='PASS')
    monkeypatch.setattr(study,'validate_final_receipt',final)
    monkeypatch.setattr(owner,'spawn_owned',spawn)
    monkeypatch.setattr(owner,'compute_lock',lambda root:nullcontext())
    monkeypatch.setattr(owner,'guard',lambda *args,**kwargs:None)
    monkeypatch.setattr(owner,'group_alive',lambda pgid:False)
    monkeypatch.setattr(owner,'shutdown_owned',lambda owned:cleaned.append(list(owned)))
    monkeypatch.setattr(owner,'request_stop',lambda path:Path(path).touch())
    monkeypatch.setattr(owner.time,'sleep',sleep)
    monkeypatch.setattr(sys,'argv',['owner','--stage',stage,'--admission',str(admission_path),
        '--admission-sha',sha,'--usage-file',str(usage)])
    if fault or (stage=='training' and not release):
        with pytest.raises((ValueError,RuntimeError)): owner.main()
        assert json.loads((out/'state.json').read_text())['status']=='incomplete'
    else:
        owner.main(); state=json.loads((out/'state.json').read_text())
        assert state['status']=='complete' and state['active']==[]
        assert checked==(['technical'] if stage=='technical' else ['on48','on49'])
        with pytest.raises(ValueError): owner.main()
    assert launched==(['technical'] if stage=='technical' else ['on48','on49']) and cleaned
    if stage=='training' and release: assert saw_learning
    if stage=='training' and not release: assert not (out/'release.json').exists()

