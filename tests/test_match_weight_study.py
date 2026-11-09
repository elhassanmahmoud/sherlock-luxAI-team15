"""Synthetic fixed-study contracts; never load production archives or play games."""
import copy
from contextlib import nullcontext
import importlib
import json
import sys
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.replay_buffer import ReplayBuffer
from agents.sherlock.reward import unit_rewards


@pytest.fixture
def study(monkeypatch):
    assert importlib.util.find_spec("scripts.match_weight_study"), "Fixed study not implemented"
    module = importlib.import_module("scripts.match_weight_study")
    monkeypatch.setattr(torch, "load", lambda *_a, **_k: pytest.fail("Archive loads prohibited"))
    from scripts import common
    monkeypatch.setattr(common, "play_game", lambda *_a, **_k: pytest.fail("Engine games prohibited"))
    return module


def contexts(outcome=1):
    pos = np.array([[1, 1], [2, 2], [3, 3]])
    base = dict(W=5, H=5, ally_ids=np.array([0, 1, 2]), ally_pos=pos,
        ally_ene=np.array([100., 100., 100.]), own_wins=0, opp_wins=0, match_step=99,
        assigned={0:(3, 3), 1:(3, 3)}, point_tiles=np.zeros((5, 5), bool), first_on_tile={},
        belief=SimpleNamespace(newly_explored=3, newly_proven=1, opp_gain=4))
    nxt = copy.deepcopy(base)
    nxt.update(ally_ids=np.array([0, 2]), ally_ene=np.array([111., 0., 97.]),
               own_wins=int(outcome > 0), opp_wins=int(outcome < 0), match_step=0)
    nxt['point_tiles'][1, 1] = True
    return base, nxt


class SyntheticAgent:
    def __init__(self, cfg, outcome, corrupt=None):
        self.cfg, self.role = cfg, "control" if cfg.w_match == 2 else "match"
        self.buffer = ReplayBuffer(12, 79)
        self._prev_ctx, self.next_ctx = contexts(outcome)
        self._prev_feats = {u:np.full(79, u, np.float32) for u in (2, 0, 1)}
        self._prev_actions = {2:5, 0:1, 1:0}
        self._sap_hits = {2:2}
        self._prev_masks = {u:np.array([True, True, True, True, True, False]) for u in (2, 0, 1)}
        self.corrupt, self._cache = corrupt, None
    def update(self, step, obs, reward, action, terminated, next_obs):
        feats = {u:np.full(79, 10+u, np.float32) for u in (0, 2)}
        masks = {u:np.array([True, False, True, False, True, False]) for u in (0, 2)}
        self._cache = (step+1, self.next_ctx, [0, 2], feats, masks, {})
        rewards = unit_rewards(self.cfg, self._prev_ctx, self.next_ctx, self._prev_actions, self._sap_hits)
        order = list(self._prev_feats)
        if self.corrupt == "order": order.reverse()
        for uid in order:
            alive = uid in feats
            s = self._prev_feats[uid]
            r = rewards[uid] + (1e-8 if self.corrupt == "reward" else 0.)
            ns = feats[uid] if alive else np.zeros(79, np.float32)
            mask = masks[uid] if alive else np.array([True, False, False, False, False, False])
            self.buffer.push(s, self._prev_actions[uid], r, ns, True, mask)


def test_fixed_configs_and_rollouts(study):
    original = AgentConfig().to_dict()
    control, match = [study.training_config(original, role) for role in study.ARMS]
    assert {k for k in control if control[k] != match[k]} == {'w_match'}
    assert (control['w_match'], match['w_match']) == (2, 20)
    assert control['lr'] == 5e-5 and control['rescue_in_training']
    assert not any(control[k] for k in ('cand_stall_rescue','threat_feats','fog_unknown_reward_neutral','art_splash_in_training'))
    for start, base in ((48,9960000),(49,9961000)):
        rows=study.rollout_plan(start)
        assert len(rows)==440 and sum(r['phase']=='prefill' for r in rows)==40
        assert [r['seed'] for r in rows[:40]]==[base+300+i//2 for i in range(40)]
        assert [r['seed'] for r in rows[40:]]==[base+i//2 for i in range(400)]
        expected=np.random.default_rng(start).choice(['solution92','sol92_sq','default','rush'],440,p=[.6,.2,.1,.1])
        assert [r['opponent'] for r in rows]==list(expected)
    assert set(study.COHORTS)=={'train48','prefill48','train49','prefill49','solution','direct_v14','direct_control'}


@pytest.mark.parametrize('role', ['control','match'])
@pytest.mark.parametrize('outcome', [-1,0,1])
def test_actual_push_formula_storage_dead_unit_and_uid_order(study, role, outcome):
    cfg=AgentConfig.from_dict(study.training_config(AgentConfig().to_dict(), role))
    agent=SyntheticAgent(cfg,outcome)
    original=agent.buffer.push
    with study.reward_audit(agent, retain=True) as audit:
        agent.update(0,None,999,None,False,None)
    assert agent.buffer.push==original and 'push' not in vars(agent.buffer)
    data=audit['records']
    assert list(data['uid'])==[2,0,1]
    assert np.allclose(data['match']-data['control'],18*outcome,atol=1e-10,rtol=1e-12)
    assert np.array_equal(agent.buffer.r[:3],data[role].astype(np.float32))
    assert audit['transitions']==3 and audit['nonzero_outcome_rows']==(3 if outcome else 0)
    assert not agent.buffer.ns[2].any() and agent.buffer.done[2]==1
    assert audit['masked_final_actions']==1  # Valid final Fog-SAP may bypass network mask.


@pytest.mark.parametrize('corrupt', ['reward','order','stored'])
def test_push_audit_rejects_real_mismatch_and_restores(study, corrupt):
    cfg=AgentConfig.from_dict(study.training_config(AgentConfig().to_dict(),'control'))
    agent=SyntheticAgent(cfg,1,corrupt)
    if corrupt=='stored':
        original=agent.buffer.push
        def broken(*args):
            pos=agent.buffer.pos; original(*args); agent.buffer.r[pos]+=1
        agent.buffer.push=broken
    previous=agent.buffer.push
    with pytest.raises(ValueError):
        with study.reward_audit(agent): agent.update(0,None,0,None,False,None)
    assert agent.buffer.push==previous


def test_float32_contrast_uses_actual_quantization_not_exact_18(study):
    control=np.array([2.123456789,-2.777777777,0.123456789])
    outcomes=np.array([1.,-1.,0.])
    match=control+18*outcomes
    assert np.any(match.astype(np.float32).astype(float)-control.astype(np.float32)!=18*outcomes)
    study.check_reward_arrays(dict(uid=np.arange(3),outcome=outcomes,control=control,match=match),match.astype(np.float32),'match')
    with pytest.raises(ValueError):
        study.check_reward_arrays(dict(uid=np.arange(3),outcome=outcomes,control=control,match=match),control.astype(np.float32),'match')


def test_fresh_learner_uses_seed_and_original_epsilon_formula(study):
    from agents.sherlock.model import QNet
    source=AgentConfig(buffer_capacity=20).to_dict()
    a=dict(start=48,config={r:study.training_config(source,r) for r in study.ARMS})
    initial=QNet(79,6,256,True).state_dict()
    agents=[study.make_learner(a,initial,r) for r in study.ARMS]
    assert study.model_identity(agents[0])==study.model_identity(agents[1])
    assert all(x.epsilon==0.050000000000000044 and x.env_steps==60000 and not x.learn_enabled for x in agents)
    assert [x.rng.integers(2**30) for x in agents]==[np.random.default_rng(48).integers(2**30)]*2


def test_release_binds_start_both_prefills_and_manual_review(study):
    pins={'control':'c','match':'m'}
    valid=dict(profile=study.PROFILE,status='approved',start=48,roles=list(study.ARMS),source={'head':'x'},
               admission_sha256='a',prefill_sha256=pins,root_review_sha256='r')
    study.validate_release(valid,dict(start=48,source={'head':'x'}),'a',pins)
    for key,value in [('start',49),('admission_sha256','old'),('prefill_sha256',{'control':'c'}),('root_review_sha256','')]:
        with pytest.raises(ValueError): study.validate_release(dict(valid,**{key:value}),dict(start=48,source={'head':'x'}),'a',pins)


def test_replay_order_and_saved_reward_evidence(study,tmp_path):
    cfg=AgentConfig.from_dict(study.training_config(AgentConfig().to_dict(),'control'))
    agent=SyntheticAgent(cfg,1)
    with study.reward_audit(agent,retain=True) as audit: agent.update(0,None,0,None,False,None)
    data=study.replay_data(agent.buffer)
    assert list(data['a'])==[5,1,0]
    assert study.check_reward_arrays(audit['records'],data['r'],'control') is None
    changed=copy.deepcopy(audit['records']); changed['match'][0]+=.01
    with pytest.raises(ValueError): study.check_reward_arrays(changed,data['r'],'control')


@pytest.mark.parametrize('mirrored', [False,True])
def test_actual_native_label_audit_composes_with_push_observer(study,mirrored):
    from agents.sherlock import geometry as geo
    cfg=AgentConfig.from_dict(study.training_config(AgentConfig().to_dict(),'control'))
    agent=SyntheticAgent(cfg,1)
    agent.belief=SimpleNamespace(mirrored=mirrored)
    native=np.zeros((3,3),int)
    for uid,action in agent._prev_actions.items():
        native[uid,0]=geo.mirror_dir(action) if mirrored and action<5 else action
    agent.act=lambda **kwargs:native.copy()
    with study.reward_audit(agent) as reward, study.action_audit(agent) as labels:
        returned=agent.act(step=0,obs={})
        agent.update(0,None,0,returned,False,None)
    assert labels['checked_replay_transitions']==reward['transitions']==3
    assert list(agent.buffer.a[:3])==[5,1,0]


def technical_row(study,role,key):
    return dict(role=role,key=key,steps=303,point_counting_version=2,learn_steps=0,
        initial={'q':'q'},current={'q':'q'},reward_audit=dict(transitions=3,nonzero_outcome_rows=3),
        final_action_audit={'checked_replay_transitions':3},native_sha256='native',trajectory_sha256='public',
        our_wins=1,opp_wins=2,our_points=80,opp_points=70,result=0.)


def test_technical_requires_actual_exposure_and_pair_identity(study,tmp_path):
    rows=[technical_row(study,r,dict(phase='technical',game=i,seed=seed,side=side,opponent='solution92'))
          for r in study.ARMS for i,(seed,side) in enumerate(study.TECH_KEYS)]
    files={}
    for i,row in enumerate(rows):
        data=dict(uid=np.array([2,0,1]),outcome=np.ones(3),control=np.array([2.,3.,4.]),match=np.array([20.,21.,22.]))
        row['reward_evidence']=study.save_reward_evidence(tmp_path/f'{i}.npz',data)
        files[row['reward_evidence']['path']]=row['reward_evidence']['sha256']
    receipt=dict(profile=study.PROFILE,stage='technical',start=48,status='complete',games=rows,files=files)
    study.check_technical(receipt)
    for field,value in [('native_sha256','changed'),('current',{'q':'changed'})]:
        broken=copy.deepcopy(receipt); broken['games'][2][field]=value
        with pytest.raises(ValueError): study.check_technical(broken)
    for row in rows: row['reward_audit']['nonzero_outcome_rows']=0
    with pytest.raises(ValueError): study.check_technical(receipt)


def test_prefill_actual_archives_pair_comparison_and_manual_release(study,tmp_path,monkeypatch):
    source=AgentConfig(buffer_capacity=20,learn_start=1).to_dict()
    a=dict(start=48,stage='pair48',source={'head':'fixed'},out=str(tmp_path),
           config={r:study.training_config(source,r) for r in study.ARMS})
    from agents.sherlock.model import QNet
    initial=QNet(79,6,256,True).state_dict()
    payloads={}
    def capture(payload,stream):
        payloads[str(stream.name)]=copy.deepcopy(payload); stream.write(b'synthetic checkpoint')
    monkeypatch.setattr(torch,'save',capture)
    monkeypatch.setattr(torch,'load',lambda path,**kwargs:copy.deepcopy(payloads[str(path)]))
    proofs=[]
    for role in study.ARMS:
        directory=tmp_path/role; directory.mkdir()
        agent=study.make_learner(a,initial,role); identity=study.model_identity(agent)
        synthetic=SyntheticAgent(agent.cfg,1)
        with study.reward_audit(synthetic,retain=True) as audit: synthetic.update(0,None,0,None,False,None)
        agent.buffer=synthetic.buffer; agent.env_steps=72120
        rows=[technical_row(study,role,dict(phase='prefill',game=i)) for i in range(40)]
        proof=study.prefill_proof(directory,agent,a,'admission',rows,identity,[audit['records']])
        study.write(directory/'prefill.json',proof)
        study.write(directory/'waiting.json',dict(profile=study.PROFILE,role=role,start=48,
                    admission_sha256='admission',prefill_sha256=study.digest(directory/'prefill.json')))
        proofs.append(study.validate_prefill_file(directory/'prefill.json'))
    study.compare_prefills(*proofs)
    broken=copy.deepcopy(proofs[1]); broken['paired_rows'][0]['trajectory_sha256']='changed'
    with pytest.raises(ValueError): study.compare_prefills(proofs[0],broken)
    assert not (tmp_path/'release.json').exists()
    study.write(tmp_path/'state.json',dict(status='running',active=list(study.ARMS),admission_sha256='admission',start=48))
    review=tmp_path/'root-review.json'
    pins={r:study.digest(tmp_path/r/'prefill.json') for r in study.ARMS}
    study.write(review,dict(status='PASS',profile=study.PROFILE,start=48,source=a['source'],
                           admission_sha256='admission',prefill_sha256=pins))
    study.approve_prefill(a,'admission',review,study.digest(review))
    release=json.loads((tmp_path/'release.json').read_text())
    study.validate_release(release,a,'admission',pins)
    with pytest.raises(FileExistsError): study.approve_prefill(a,'admission',review,study.digest(review))
    assert all((tmp_path/r/'waiting.json').exists() for r in study.ARMS)


def test_wait_never_enables_learning_or_creates_release(study,tmp_path,monkeypatch):
    calls=[]
    class Stop(Exception): pass
    def guard(): calls.append('guard'); raise Stop()
    with pytest.raises(Stop): study.wait_release(dict(out=str(tmp_path)),'admission',guard)
    assert calls==['guard'] and not list(tmp_path.iterdir())


@pytest.mark.parametrize('stop_after_game',[False,True])
def test_worker_one_env_cleanup_and_incomplete_checkpoint(study,tmp_path,monkeypatch,stop_after_game):
    a=dict(stage='technical',start=48,out=str(tmp_path),stop_file=str(tmp_path/'STOP'),
           source={'head':'fixed'},config={'control':{},'match':{}})
    state=tmp_path/'state.json'; state.write_text(json.dumps({'jobs':{'technical':{}}}))
    events=[]; calls=[]; saved=[]
    class Guard:
        command=['synthetic']; release_sha=None
        def __init__(self,*args): pass
        def __call__(self):
            if stop_after_game and calls: raise ValueError('STOP at game boundary')
    class Env:
        def __init__(self,**kwargs): events.append('create')
        def close(self): events.append('close')
    monkeypatch.setitem(sys.modules,'luxai_s3.wrappers',SimpleNamespace(LuxAIS3GymEnv=Env))
    monkeypatch.setattr(study,'WorkerGuard',Guard)
    monkeypatch.setattr(study,'load_initial',lambda a:{})
    monkeypatch.setattr(study,'make_learner',lambda a,w,role:SimpleNamespace(role=role,buffer=ReplayBuffer(4,79)))
    monkeypatch.setattr(study,'model_identity',lambda agent:{'q':'q'})
    def play(agent,key,env):
        calls.append(id(env))
        audit=dict(uid=np.array([2,0,1]),outcome=np.ones(3),control=np.array([2.,3.,4.]),match=np.array([20.,21.,22.]))
        row=technical_row(study,agent.role,key)
        return row,audit
    monkeypatch.setattr(study,'play_one',play)
    def save(path,agent,a,status,completed):
        saved.append((status,completed)); path.write_bytes(b'incomplete synthetic')
    monkeypatch.setattr(study,'save_checkpoint',save)
    if stop_after_game:
        with pytest.raises(ValueError,match='STOP'): study.run_worker(a,tmp_path/'admission','sha',state,'technical')
        assert saved==[('incomplete',1)]
        assert json.loads((tmp_path/'technical/incomplete.json').read_text())['eligible'] is False
    else:
        receipt=study.run_worker(a,tmp_path/'admission','sha',state,'technical')
        assert len(receipt['games'])==4 and len(calls)==4
        for row in receipt['games']:
            artifact=row['reward_evidence']
            assert study.digest(artifact['path'])==artifact['sha256']
            assert receipt['files'][artifact['path']]==artifact['sha256']
            with np.load(artifact['path'],allow_pickle=False) as data:
                assert np.array_equal(data['match']-data['control'],18*data['outcome'])
    assert len(set(calls))==1 and events==['create','close']


def test_opponent_caught_error_invalidates_game(study,monkeypatch):
    from scripts import common
    agent=SimpleNamespace(env_steps=60000,learn_steps=0,caught_errors=0)
    opponent=SimpleNamespace(caught_errors=1)
    monkeypatch.setattr(common,'make_opponent',lambda *args:opponent)
    monkeypatch.setattr(common,'play_game',lambda *args,**kwargs:dict(steps=303,point_counting_version=2))
    monkeypatch.setattr(study,'reward_audit',lambda *args,**kwargs:nullcontext({}))
    monkeypatch.setattr(study,'action_audit',lambda *args,**kwargs:nullcontext({}))
    with pytest.raises(RuntimeError,match='caught'):
        study.play_one(agent,dict(phase='technical',opponent='solution92',seed=9946007,side='player_0'),object())
