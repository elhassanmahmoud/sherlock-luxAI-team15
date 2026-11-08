"""Synthetic study admission/provenance tests; no Lux games."""
import copy
import json
import os
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.geometry import mirror_delta
from scripts import artillery_alignment_study as S
from scripts import artillery_alignment_supervisor as H


def source_config():
    return dict(AgentConfig().to_dict(), art_sap=True, art_splash=True,
                sap_no_overkill=True, art_still=False, sap_still_all=False,
                smart_sap=False, idle_sap=False, art_move_guard=False, siege=False,
                end_sap=0, w_sap_hit=.3, train_every=2)


def test_fixed_recipe_and_paired_schedules():
    assert S.ARMS == {'control43': (43, False), 'aligned43': (43, True),
                      'control44': (44, False), 'aligned44': (44, True)}
    for seed in (43, 44):
        a, b = [S.rollout_plan(f'{role}{seed}') for role in ('control', 'aligned')]
        assert a == b and len(a) == 440
        assert [r['seed'] for r in a[:40]] == [9_000_000+seed*10000+5000+g//2 for g in range(40)]
        assert [r['seed'] for r in a[40:]] == [9_000_000+seed*10000+g//2 for g in range(400)]
        assert [r['side'] for r in a] == ['player_0', 'player_1']*220
        rng = np.random.default_rng(seed)
        expected = rng.choice(list(S.MIX), size=440, p=list(S.MIX.values())).tolist()
        assert [r['opponent'] for r in a] == expected
    assert len(S.validation_plan()) == 32
    assert {r['seed'] for r in S.validation_plan()} == set(range(9_600_000, 9_600_004))
    assert {r['after_games'] for r in S.validation_plan()} == {0, 400}
    a, b = [S.training_config(source_config(), flag) for flag in (False, True)]
    assert {k for k in a if a[k] != b[k]} == {'art_splash_in_training'}
    assert a['lr'] == 5e-5 and a['rules_in_training_all'] and a['rescue_in_training']
    assert a['rules_in_training'] and not a['frozen'] and not a['fog_unknown_reward_neutral']


@pytest.mark.parametrize('key,value', [('art_still',True),('sap_still_all',True),('smart_sap',True),
    ('idle_sap',True),('art_move_guard',True),('siege',True),('end_sap',1),
    ('art_splash',False),('art_sap',False),('sap_no_overkill',False),('train_every',3),
    ('w_sap_hit',0),('fog_unknown_reward_neutral',True),('art_splash_in_training',True)])
def test_unsupported_source_is_rejected(key,value):
    with pytest.raises(ValueError): S.training_config(dict(source_config(), **{key:value}), True)


def test_prepare_checks_exact_component_and_exclusivity(tmp_path,monkeypatch):
    source = tmp_path/'v14.pth';source.write_bytes(b'synthetic')
    cfg = source_config(); states = [{'w':torch.tensor([float(i)])} for i in range(36)]
    monkeypatch.setattr(S,'SOURCE_SHA',S.file_sha256(source))
    monkeypatch.setattr(S,'_source',lambda _: ({},states,cfg))
    monkeypatch.setattr(S,'_pins',lambda: {'synthetic':'frozen'})
    out = tmp_path/'prepared'
    S.prepare(source,out)
    for arm in S.ARMS:
        _,entry,init = S.check_prepared(out,arm)
        cp = torch.load(init/'weights/agent.pth',weights_only=True)
        assert cp['q']['w'].item() == 18 and cp['env_steps'] == 60000 and cp['learn_steps'] == 0
        assert S.tensor_sha256(cp['q']) == S.tensor_sha256(cp['target_q']) == entry['tensor_sha256']
        assert 'opt' not in cp
    with pytest.raises(FileExistsError): S.prepare(source,out)
    path = out/'aligned43/weights/agent.pth'
    cp = torch.load(path,weights_only=True);cp['target_q']['w'][0]=19;torch.save(cp,path)
    with pytest.raises(ValueError): S.check_prepared(out,'aligned43')


class SyntheticAgent:
    """Calls the real observer interfaces, with a minimal replay ring."""
    def __init__(self, *, enabled=True, mirrored=False, cancel=False, replace=False, bad_replay=False):
        self.cfg=AgentConfig.from_dict(S.training_config(source_config(),enabled))
        self.training=True;self.rng=np.random.default_rng(7)
        self.param_est=SimpleNamespace(n_drop=3, _prev={'enemies':{(1,2)}})
        self.belief=SimpleNamespace(mirrored=mirrored,point_tiles=np.zeros((3,3),bool))
        self.buffer=SimpleNamespace(pos=0,capacity=4,a=np.zeros(4,int))
        self.cancel=cancel;self.replace=replace;self.bad_replay=bad_replay
        self._prev_feats={};self._prev_actions={};self._sap_hits={}
    def _artillery_ok(self,ctx,uid,sap):
        return np.bool_(self.cfg.art_splash_in_training)
    def _plan_damage(self,ctx,uid,sap,planned):
        planned[uid]=1
    def act(self,step,obs):
        self._prev_feats={0:np.zeros(2)};self._prev_actions={0:0};self._sap_hits={}
        ctx={'step':step,'ally_pos':np.array([[1,1]])};sap=(2,-1,2)
        allowed=self._artillery_ok(ctx,0,sap)
        actions=np.zeros((1,3),int)
        if allowed and not self.cancel:
            target=tuple(list(sap)) if self.replace else sap
            self._plan_damage(ctx,0,target,{})
            self._prev_actions[0]=5;self._sap_hits[0]=2
            dx,dy=mirror_delta(*sap[:2]) if self.belief.mirrored else sap[:2]
            actions[0]=[5,dx,dy]
        return actions
    def update(self,**kwargs):
        self.buffer.a[self.buffer.pos]=0 if self.bad_replay else self._prev_actions[0]
        self.buffer.pos=(self.buffer.pos+1)%self.buffer.capacity


@pytest.mark.parametrize('enabled,mirrored,cancel', [(True,False,False),(True,True,False),
    (True,True,True),(False,True,False)])
def test_observer_tracks_final_native_canonical_replay_and_restores(enabled,mirrored,cancel):
    agent=SyntheticAgent(enabled=enabled,mirrored=mirrored,cancel=cancel);events=[]
    methods={k:getattr(agent,k) for k in ('act','update','_artillery_ok','_plan_damage')}
    with S.artillery_audit(agent,events.append) as proof:
        action=agent.act(9,{})
        agent.update(action=action)
    assert len(events)==1
    event=events[0]
    assert event['baseline'] is False and event['aligned'] is True
    assert event['actual'] is enabled and event['new_permission'] is True
    assert proof['executed_additional_saps']==int(enabled and not cancel)
    assert proof['canceled_additional_saps']==int(enabled and cancel)
    assert proof['checked_helper_replay']==1 and proof['helper_calls']==1
    assert event['replay_action']==event['canonical_action']==int(action[0,0])
    assert event['native_action']==action[0].tolist()
    assert event['mirrored'] is mirrored
    assert event['input_sha256']==event['restored_sha256']
    assert all(getattr(agent,k)==method and k not in vars(agent) for k,method in methods.items())


@pytest.mark.parametrize('kind', ['exception','mutation','rng','context','config'])
def test_observer_failure_restores_hooks_and_flag(kind):
    agent=SyntheticAgent();original=agent._artillery_ok
    def broken(ctx,uid,sap):
        if not agent.cfg.art_splash_in_training:
            if kind=='exception': raise RuntimeError('alternate failed')
            if kind=='mutation': agent.param_est.n_drop+=1
            if kind=='rng': agent.rng.random()
            if kind=='context': ctx['step']+=1
            if kind=='config': agent.cfg.art_reserve+=1
        return original(ctx,uid,sap)
    agent._artillery_ok=broken
    with pytest.raises((RuntimeError,ValueError)),S.artillery_audit(agent,lambda _:None):
        agent.act(1,{})
    assert agent.cfg.art_splash_in_training is True and agent._artillery_ok is broken
    assert 'act' not in vars(agent) and 'update' not in vars(agent) and '_plan_damage' not in vars(agent)


@pytest.mark.parametrize('option', ['replace','bad_replay'])
def test_observer_rejects_wrong_sap_identity_and_replay(option):
    agent=SyntheticAgent(**{option:True})
    with pytest.raises(ValueError),S.artillery_audit(agent,lambda _:None):
        action=agent.act(1,{});agent.update(action=action)


def real_belief_context():
    from agents.sherlock.belief import Belief
    from agents.sherlock.features import make_context
    from tests.conftest import ENV_CFG, make_obs
    agent=SyntheticAgent()
    agent.belief=Belief(0);agent.env_cfg=dict(ENV_CFG)
    obs=make_obs(10,10,units=[(5,5,100)],enemies=[(8,8,100)],relics=[(12,12)])
    agent.belief.observe(obs)
    agent._prev_actions={0:0}
    return agent,make_context(agent,obs)


def test_helper_state_supports_real_belief_from_make_context():
    agent,ctx=real_belief_context()
    assert ctx['belief'] is agent.belief
    before=S.helper_state(agent,ctx,(2,-1,2))
    assert len(before)==64 and S.helper_state(agent,copy.deepcopy(ctx),(2,-1,2))==before
    projected=S._tree(ctx['belief'])
    assert projected[0]=='agents.sherlock.belief.Belief'
    with pytest.raises(TypeError):
        S.experiment.state_sha256(S._tree(SimpleNamespace(unrecognized=True)))


@pytest.mark.parametrize('field', ['energy_map','relic_positions','records'])
def test_observer_detects_real_belief_mutations(field):
    agent,ctx=real_belief_context();original=agent._artillery_ok
    def mutate(context,uid,sap):
        if not agent.cfg.art_splash_in_training:
            belief=context['belief']
            if field=='energy_map': belief.energy_map[0,0]+=1
            if field=='relic_positions': belief.relic_positions.add((1,2))
            if field=='records': belief.records.append(((1,2),1))
        return original(context,uid,sap)
    agent._artillery_ok=mutate
    with pytest.raises(ValueError,match='Alternate helper mutated'),S.artillery_audit(agent,lambda _:None):
        agent._artillery_ok(ctx,0,(2,-1,2))
    assert agent._artillery_ok is mutate and agent.cfg.art_splash_in_training is True


def pair_proofs():
    common=dict(status='prefill_ready',run_seed=43,component_index=18,
        actual_prefill_games=40,learn_steps=0,unchanged_q=True,unchanged_target=True,
        unchanged_optimizer=True,initial_tensor_sha256='a'*64,initial_optimizer_sha256='b'*64,
        schedule_sha256=S.experiment.state_sha256(S.rollout_plan('control43')),
        initial_agent_rng_sha256='c'*64,initial_global_rng_sha256='d'*64,
        replay_size=6000,executed_additional_saps=0,new_permissions=4,
        trajectory_sha256='different trajectories allowed')
    return [dict(common,arm='control43',config=S.training_config(source_config(),False)),
            dict(common,arm='aligned43',config=S.training_config(source_config(),True),
                 executed_additional_saps=2,replay_size=6100,trajectory_sha256='different')]


def test_pair_accepts_divergent_trajectories():
    assert S.compare_prefill_proofs(*pair_proofs(),43)['status']=='matched'


@pytest.mark.parametrize('key,value', [('executed_additional_saps',0),('learn_steps',1),
    ('actual_prefill_games',39),('unchanged_optimizer',False),('initial_tensor_sha256','x'*64),
    ('schedule_sha256','x'*64),('initial_agent_rng_sha256','x'*64)])
def test_pair_null_or_learning_or_start_differences_stop(key,value):
    a,b=pair_proofs();b[key]=value
    with pytest.raises(ValueError): S.compare_prefill_proofs(a,b,43)


def test_partial_receipt_fails_before_loading(tmp_path):
    path=tmp_path/'final_receipt.json';path.write_text(json.dumps({'arm':'control43','status':'incomplete'}))
    with pytest.raises(ValueError): S.validate_final_receipt(path)


def test_usage_and_canonical_stop_guard(tmp_path,monkeypatch):
    from datetime import datetime,timezone
    usage=tmp_path/'usage.json';now=10000.
    good=dict(timestamp=datetime.fromtimestamp(now,timezone.utc).isoformat(),usedPercent=99.9,ordinaryUsageAllowed=True)
    usage.write_text(json.dumps(good));H.check_usage(usage,now=now,max_used_percent=100)
    for change in ({'usedPercent':100},{'ordinaryUsageAllowed':False},{'timestamp':'1970-01-01T00:00:00Z'}):
        usage.write_text(json.dumps(dict(good,**change)))
        with pytest.raises(ValueError): H.check_usage(usage,now=now,max_used_percent=100)
    assert str(H.STOP_FILE)=='/private/tmp/sherlock-artillery-alignment-20261108/STOP'
    assert str(H.USAGE_FILE).endswith('experiments/analysis/artillery_alignment_20261108/operations/usage.json')


def test_guard_rejects_hash_changes_and_foreign_jobs(tmp_path,monkeypatch):
    file=tmp_path/'input';file.write_text('original')
    state=dict(stop_file=str(tmp_path/'STOP'),usage_file='usage',source={},plans=[],python='python',
        protected={},inputs={str(file):S.file_sha256(file)},owner_pid=1,jobs={},active=[])
    monkeypatch.setattr(H,'read_power',lambda:dict(ac=True))
    monkeypatch.setattr(H,'check_usage',lambda *a,**kw:{})
    monkeypatch.setattr(H,'source_identity',lambda *a:{})
    monkeypatch.setattr(H,'check_model_processes',lambda *a:None)
    H.guard(state,{})
    file.write_text('changed')
    with pytest.raises(ValueError): H.guard(state,{})
    snapshot='11 11 python -m scripts.artillery_alignment_study run\n12 12 python -m scripts.holder_rollout_probe\n13 13 python -m pytest\n'
    assert H.foreign_processes(snapshot,owner_pid=10,owned_pgids={11})==[12,13]


def test_worker_requires_exact_owned_launch(tmp_path,monkeypatch):
    prepared=tmp_path/'prepared';prepared.mkdir()
    state=dict(status='running',prepared=str(prepared),out=str(tmp_path),python='python',
        owner_pid=123,active=['control43'],jobs={})
    state['jobs']['control43']=dict(pid=os.getpid(),pgid=os.getpgrp(),owner_pid=123,
        argv=H.training_command(state,'control43'))
    path=tmp_path/'state.json';path.write_text(json.dumps(state))
    monkeypatch.setattr(H,'guard',lambda *a:None);monkeypatch.setattr(H.os,'kill',lambda *_:None)
    H.worker_guard(path,'control43',H.run_name('control43'),prepared)
    with pytest.raises(ValueError): H.worker_guard(path,'aligned43',H.run_name('aligned43'),prepared)


def make_prefill_bundle(tmp_path):
    arm='aligned43';config=S.training_config(source_config(),True)
    entry=dict(component_index=18,run_seed=43,config=config,tensor_sha256='f'*64,
               rollout_plan=S.rollout_plan(arm))
    initial=dict(q_tensor_sha256='f'*64,target_tensor_sha256='f'*64,
        agent_rng_sha256='a'*64,global_rng_sha256='b'*64,
        learning=dict(config=config,env_steps=60000,learn_steps=0,recent_losses=[],
            learn_enabled=True,optimizer_sha256='opt',replay=dict(size=0,pos=0,_mask_dim=1)))
    prefill=copy.deepcopy(initial)
    prefill['learning'].update(env_steps=72120,learn_enabled=False,replay=dict(size=6000))
    events=[];agent=SyntheticAgent()
    with S.artillery_audit(agent,events.append) as one:
        action=agent.act(1,{});agent.update(action=action)
    empty=dict(S.empty_exposure(),transcript_sha256=S.hashlib.sha256().hexdigest())
    rows=[]
    for index,plan in enumerate(entry['rollout_plan'][:40]):
        rows.append(dict(plan,steps=303,point_counting_version=2,updates=0,learn_steps=0,
            env_steps=60000+(index+1)*303,rollout_config_id=S.experiment.state_sha256(config),
            action_audit=dict(act_calls=303,update_calls=303,checked_replay_transitions=100,
                              transcript_sha256='a'*64),artillery_audit=one if index==0 else empty))
    bundle=dict(arm=arm,entry=entry,initial=initial,prefill=prefill,rows=rows)
    prepared=tmp_path/'prepared';prepared.mkdir()
    S._write(prepared/'manifest.json',dict(arms={arm:entry}))
    directory=tmp_path/'run';directory.mkdir()
    S._write(directory/'prefill_bundle.json',bundle)
    (directory/'prefill_events.jsonl').write_text(json.dumps(dict(rollout_index=0,event=events[0]))+'\n')
    proof=S._prefill_summary(arm,entry,initial,prefill,rows)
    proof.update(bundle_sha256=S.file_sha256(directory/'prefill_bundle.json'),
                 events_sha256=S.file_sha256(directory/'prefill_events.jsonl'))
    S._write(directory/'prefill_proof.json',proof)
    return directory,prepared,proof


def test_prefill_counts_recomputed_from_concrete_action_replay_events(tmp_path):
    directory,prepared,proof=make_prefill_bundle(tmp_path)
    actual=S.validate_prefill_bundle(directory,prepared,'aligned43')
    assert actual==proof and actual['executed_additional_saps']==1
    raw=json.loads((directory/'prefill_events.jsonl').read_text())
    raw['event']['replay_action']=0
    (directory/'prefill_events.jsonl').write_text(json.dumps(raw)+'\n')
    # Updating the file checksum cannot make an invalid action/replay proof pass.
    proof['events_sha256']=S.file_sha256(directory/'prefill_events.jsonl')
    S._write(directory/'prefill_proof.json',proof)
    with pytest.raises(ValueError): S.validate_prefill_bundle(directory,prepared,'aligned43')


def test_prefill_digest_and_complete_chronology_recomputed(tmp_path):
    directory,prepared,proof=make_prefill_bundle(tmp_path)
    bundle=json.loads((directory/'prefill_bundle.json').read_text())
    bundle['rows'][0]['artillery_audit']['executed_additional_saps']=0
    S._write(directory/'prefill_bundle.json',bundle)
    proof['bundle_sha256']=S.file_sha256(directory/'prefill_bundle.json')
    S._write(directory/'prefill_proof.json',proof)
    with pytest.raises(ValueError,match='counts/digests'): S.validate_prefill_bundle(directory,prepared,'aligned43')


@pytest.mark.parametrize('mutation', ['q','target','opt','counter','nan','reload'])
def test_end_proof_rejects_untrained_nonfinite_or_unreloaded_state(tmp_path,mutation):
    cfg=S.training_config(source_config(),True)
    initial={'w':torch.tensor([0.])};q={'w':torch.tensor([1.])};target={'w':torch.tensor([.5])}
    opt=dict(state={0:dict(step=torch.tensor(60000.),exp_avg=torch.tensor([.1]),exp_avg_sq=torch.tensor([.01]))},
             param_groups=[dict(lr=5e-5,params=[0])])
    cp=dict(q=q,target_q=target,opt=opt,cfg=cfg,feature_dim=79,n_actions=6,
            ensemble=[],ensemble_dims=[],env_steps=193320,learn_steps=60000)
    entry=dict(config=cfg,tensor_sha256=S.tensor_sha256(initial))
    audit=dict(initial=dict(learning=dict(optimizer_sha256='empty')),
        end=dict(reload_verified=True,q_tensor_sha256=S.tensor_sha256(q),
            target_tensor_sha256=S.tensor_sha256(target),learning=dict(config=cfg,env_steps=193320,
                learn_steps=60000,optimizer_sha256=S.experiment.state_sha256(opt))))
    (tmp_path/'weights').mkdir();path=tmp_path/'weights/agent.pth';torch.save(cp,path)
    receipt=dict(artifacts={'weights/agent.pth':S.file_sha256(path)})
    audit['end']['saved_weights_sha256']=receipt['artifacts']['weights/agent.pth']
    S._validate_end(tmp_path,receipt,entry,audit)
    if mutation=='q': cp['q']=initial
    if mutation=='target': cp['target_q']=initial
    if mutation=='opt': cp['opt']['state'][0]['step']=torch.tensor(1.)
    if mutation=='counter': cp['learn_steps']=59999
    if mutation=='nan': cp['q']['w'][0]=float('nan')
    if mutation=='reload': audit['end']['reload_verified']=False
    torch.save(cp,path)
    with pytest.raises(ValueError): S._validate_end(tmp_path,receipt,entry,audit)


@pytest.mark.parametrize('power', [{'ac':False},{'ac':None}])
def test_power_requires_actual_ac(tmp_path,monkeypatch,power):
    monkeypatch.setattr(H,'check_usage',lambda *a,**kw:{})
    monkeypatch.setattr(H,'read_power',lambda:power)
    with pytest.raises(ValueError,match='AC power'):
        H.guard(dict(stop_file=str(tmp_path/'STOP'),usage_file='unused'),{})


def test_stop_prevents_any_other_guard_work(tmp_path,monkeypatch):
    stop=tmp_path/'STOP';stop.touch()
    monkeypatch.setattr(H,'check_usage',lambda *a,**kw:pytest.fail('usage checked after STOP'))
    with pytest.raises(ValueError,match='STOP'): H.guard(dict(stop_file=str(stop)),{})


def test_more_than_two_workers_rejected(tmp_path,monkeypatch):
    monkeypatch.setattr(H,'check_usage',lambda *a,**kw:{})
    monkeypatch.setattr(H,'read_power',lambda:{'ac':True})
    monkeypatch.setattr(H,'source_identity',lambda *a:{})
    with pytest.raises(ValueError,match='Maximum two'):
        H.guard(dict(stop_file=str(tmp_path/'STOP'),usage_file='unused',python='python',plans=[],
            source={},inputs={},protected={},active=['a','b','c']),{})


def test_null_prefill_stops_queue_without_retries(tmp_path,monkeypatch):
    state=dict(status='prepared',root=str(tmp_path),out=str(tmp_path),prepared='unused',python='python',
        stop_file=str(tmp_path/'STOP'),queue=list(H.ARMS),jobs={},active=[],paired_prefill={},receipts={})
    started=[];shutdown=[]
    monkeypatch.setattr(H,'ROOT',tmp_path);monkeypatch.setattr(H,'save_state',lambda _:None)
    monkeypatch.setattr(H,'guard',lambda *a:None)
    monkeypatch.setattr(H,'shutdown_owned',lambda owned:shutdown.extend(owned))
    def spawn(state,arm,command,owned):
        started.append(arm);owned[arm]={'process':SimpleNamespace(poll=lambda:None),'pgid':1}
        directory=tmp_path/'experiments/runs'/H.run_name(arm);directory.mkdir(parents=True)
        (directory/'prefill_proof.json').touch()
    monkeypatch.setattr(H,'spawn_owned',spawn)
    def reject(*_): raise ValueError('zero executed additional SAP')
    monkeypatch.setattr(H,'compare_pair',reject)
    with pytest.raises(ValueError,match='zero executed'): H.run_queue(state)
    assert started==['control43','aligned43'] and shutdown==started
    assert state['status']=='incomplete' and state['queue']==['control44','aligned44']
    assert (tmp_path/'STOP').exists()


@pytest.mark.parametrize('admit', [True,False])
def test_direct_runner_gates_gradients_and_saves_only_final_without_games(tmp_path,monkeypatch,admit):
    """Exercise real controller/file flow with no environment, network or updates."""
    from contextlib import contextmanager
    import sys
    arm='aligned43';cfg=S.training_config(source_config(),True)
    entry=dict(config=cfg,run_seed=43,tensor_sha256='f'*64,rollout_plan=S.rollout_plan(arm))
    manifest=dict(pins={},source_config=source_config())
    init=tmp_path/'init';(init/'weights').mkdir(parents=True);(init/'weights/agent.pth').write_bytes(b'init')
    run_root=tmp_path/'runs';name=H.run_name(arm);directory=run_root/name
    agent=SimpleNamespace(cfg=AgentConfig.from_dict(cfg),training=True,learn_enabled=True,
        epsilon=.05,autosave_on_terminate=False,env_steps=60000,learn_steps=0,
        pop_mean_loss=lambda:.125)
    calls=[];saved=[];validated=[];gated=[];closed=[]
    class Learners:
        def __init__(self,*args,**kwargs): pass
        def train_mode(self): pass
        def save(self):
            saved.append(len(calls));(directory/'weights/agent.pth').write_bytes(b'final')
        def save_buffers(self): (directory/'weights/agent.buffer.npz').write_bytes(b'buffer')
    class Env:
        def __init__(self,**kwargs): pass
        def close(self): closed.append(True)
    monkeypatch.setitem(sys.modules,'luxai_s3.wrappers',SimpleNamespace(LuxAIS3GymEnv=Env))
    monkeypatch.setattr(S.experiment,'RUNS',run_root)
    monkeypatch.setattr(S,'check_prepared',lambda *a:(manifest,entry,init))
    monkeypatch.setattr(S,'_check_frozen',lambda *a:None)
    monkeypatch.setattr(H,'worker_guard',lambda *a:None)
    monkeypatch.setattr(S.experiment,'limit_threads',lambda:None)
    monkeypatch.setattr(S,'seed_everything',lambda *_:None)
    monkeypatch.setattr(S.experiment,'Learners',Learners)
    monkeypatch.setattr(S,'_canonical',lambda _:agent)
    identity=lambda _:dict(env_steps=agent.env_steps,learn_steps=agent.learn_steps)
    monkeypatch.setattr(S,'learner_identity',identity)
    monkeypatch.setattr(S,'prove_initial',lambda *a:identity(None))
    monkeypatch.setattr(S,'_prove_prefill',lambda *a:None)
    monkeypatch.setattr(S,'_prefill_summary',lambda *a:dict(status='prefill_ready'))
    def gate(*args):
        gated.append((len(calls),agent.learn_steps,agent.learn_enabled))
        if not admit: raise ValueError('no executed additional SAP')
    monkeypatch.setattr(S,'wait_prefill',gate)
    @contextmanager
    def action(_):
        yield dict(act_calls=303,update_calls=303,checked_replay_transitions=0,transcript_sha256='a'*64)
    @contextmanager
    def exposure(*_): yield dict(S.empty_exposure(),transcript_sha256='b'*64)
    monkeypatch.setattr(S,'action_audit',action);monkeypatch.setattr(S,'artillery_audit',exposure)
    monkeypatch.setattr(S.common,'make_opponent',lambda name,side:(name,side))
    def game(env,agent,opp,seed,side,train):
        index=len(calls);plan=entry['rollout_plan'][index]
        assert (seed,side,opp)==(plan['seed'],plan['side'],(plan['opponent'],'player_1' if side=='player_0' else 'player_0'))
        calls.append(agent.learn_enabled)
        agent.env_steps+=303
        agent.learn_steps+=150 if agent.learn_enabled else 0
        row=dict.fromkeys(S.experiment.GAME_FIELDS,0)
        row.update(seed=seed,side=side,steps=303,point_counting_version=2,result=1.)
        return row
    monkeypatch.setattr(S.common,'play_game',game)
    def validation(env,learners,seeds,opponents,source_cfg,*,completed_rows,stop_check):
        after=sum(calls);validated.append((len(calls),after,source_cfg))
        result=[dict(plan,steps=303,point_counting_version=2) for plan in S.validation_plan() if plan['after_games']==after]
        completed_rows.extend(result);return result
    monkeypatch.setattr(S,'validate_v14',validation)
    monkeypatch.setattr(S,'_prove_end',lambda *a:dict(reload_verified=True))
    monkeypatch.setattr(S,'validate_final_receipt',lambda *a,**kw:None)
    if admit:
        result=S.run_arm(tmp_path/'prepared',arm,name,supervisor_state=tmp_path/'state')
        assert result['status']=='done' and calls==[False]*40+[True]*400
        assert saved==[440] and [(n,a) for n,a,_ in validated]==[(40,0),(440,400)]
        assert all(c==manifest['source_config'] for _,_,c in validated)
        assert result['actual_validation_games']==32 and result['learn_steps']==60000
    else:
        with pytest.raises(ValueError,match='no executed'): S.run_arm(tmp_path/'prepared',arm,name,supervisor_state=tmp_path/'state')
        assert calls==[False]*40 and not saved and not validated
        assert not (directory/'final_receipt.json').exists()
    assert gated==[(40,0,False)] and closed==[True]
