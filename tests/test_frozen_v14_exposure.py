"""Synthetic contracts; real checkpoints, simulator imports and games are forbidden."""
import copy
import hashlib
from contextlib import nullcontext
import importlib
import json
from pathlib import Path
import random
import sys
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from scripts import match_weight_study as old
from scripts import ensemble_behavior_study as behavior


@pytest.fixture
def study(monkeypatch):
    assert importlib.util.find_spec('scripts.frozen_v14_exposure'), 'Exposure adapter is missing'
    module = importlib.import_module('scripts.frozen_v14_exposure')
    monkeypatch.setattr(torch, 'load', lambda *_a, **_k: pytest.fail('Real archive load forbidden'))
    from scripts import common
    monkeypatch.setattr(common, 'play_game', lambda *_a, **_k: pytest.fail('Real game forbidden'))
    monkeypatch.setitem(sys.modules, 'luxai_s3.wrappers', None)
    return module


@pytest.mark.parametrize('start', [48,49])
def test_exposure_replaces_only_non_solution_without_rng_draws(study,start):
    before = old.state_sha256((random.getstate(),np.random.get_state(),torch.get_rng_state()))
    keys = old.rollout_plan(start)
    for key in keys:
        snapshot = copy.deepcopy(key)
        actual = study.actual_opponent(key)
        assert actual == ('solution92' if key['opponent']=='solution92' else 'frozen_v14')
        assert key == snapshot
    assert len(keys)==440 and len({(k['seed'],k['side']) for k in keys})==440
    assert old.state_sha256((random.getstate(),np.random.get_state(),torch.get_rng_state()))==before
    with pytest.raises(ValueError): study.actual_opponent(dict(keys[0],opponent='self'))


class SyntheticOpponent:
    """Only the stock loader boundary is replaced, with RNG-consuming synthetic weights."""
    def __init__(self,player,agent_path,train,seed):
        assert train is False and seed==0
        random.random(); np.random.random(); torch.rand(1)
        self.player=player; self.opp_player='player_1' if player=='player_0' else 'player_0'
        self.team_id=int(player[-1]); self.opp_team_id=1-self.team_id
        self.cfg=SimpleNamespace(frozen=False,to_dict=lambda: {'frozen':False,'hidden':256})
        self.training=False; self.learn_enabled=True; self.autosave_on_terminate=True
        self.q=torch.nn.Linear(79,6); self.target_q=torch.nn.Linear(79,6)
        with torch.no_grad():
            self.q.weight.zero_(); self.q.bias.zero_()
            self.target_q.load_state_dict(self.q.state_dict())
        self.extra_q=[copy.deepcopy(self.q) for _ in range(35)]
        self.cnn_policy=None; self.feat_dim=79; self.n_actions=6; self.device=torch.device('cpu')
        self.opt=torch.optim.Adam(self.q.parameters()); self.buffer=[]
        self.rng=np.random.default_rng(seed); self.env_steps=77; self.learn_steps=22
        self.caught_errors=0; self.env_cfg=None; self._cache=None; self._prev_ctx=None
        self._paths=SimpleNamespace(step=None,maps={}); self.belief=SimpleNamespace(relic_positions=set())
        self._prev_feats={}; self._prev_actions={}; self._prev_masks={}
        self.recent_losses=[]; self.epsilon=0.
    def set_to_eval_mode(self): self.training=False; self.q.eval()
    def new_game(self,player=None):
        assert player==self.player
        self.belief.relic_positions.clear(); self._cache=None; self._prev_ctx=None
    def set_env_cfg(self,config): self.env_cfg=config
    def act(self,step,obs):
        assert self.env_cfg is not None and obs['side']==self.player
        self.belief.relic_positions.add((1,2))
        return np.zeros((16,3),dtype=int)
    def update(self,*_a,**_k): raise AssertionError('unguarded update')
    _update=update; _learn=update; save_agent=update; save_buffer=update


SyntheticOpponent.__module__='agents.sherlock.main'
SyntheticOpponent.__qualname__='Agent_x'


def opponent_setup(study,tmp_path,monkeypatch):
    from agents.sherlock import main
    path=tmp_path/'v14.pth'; path.write_bytes(b'synthetic checkpoint marker, never decoded')
    monkeypatch.setattr(study,'OPPONENT_SHA',old.digest(path))
    monkeypatch.setattr(main,'Agent_x',SyntheticOpponent)
    sample=SyntheticOpponent('player_0',str(path),False,0)
    a=dict(opponent_model=str(path),opponent_config=sample.cfg.to_dict(),
           source_members=[old.state_sha256(m.state_dict()) for m in [sample.q,*sample.extra_q]],
           inputs={str(path):old.digest(path)})
    learner=SimpleNamespace(rng=np.random.default_rng(48))
    return a,learner


@pytest.mark.parametrize('side',['player_0','player_1'])
def test_stock_opponent_is_fresh_rng_neutral_and_cannot_update_or_save(study,tmp_path,monkeypatch,side):
    a,learner=opponent_setup(study,tmp_path,monkeypatch)
    before=behavior.rng_identity(learner)
    first=study.frozen_opponent(a,learner,side)
    assert behavior.rng_identity(learner)==before
    assert first.player==side and not first.learn_enabled and not first.autosave_on_terminate
    assert all(not p.requires_grad and p.grad is None for net in [first.q,first.target_q,*first.extra_q]
               for p in net.parameters())
    for name in ('update','_update','_learn','save_agent','save_buffer'):
        with pytest.raises(ValueError,match='Frozen opponent'): getattr(first,name)()
    first.belief.relic_positions.add((4,4)); first._paths.step=302; first._paths.maps[(4,4)]=1
    second=study.frozen_opponent(a,learner,side)
    assert second is not first and second._paths.step is None and not second._paths.maps
    assert not second.belief.relic_positions and behavior.rng_identity(learner)==before


@pytest.mark.parametrize('broken',['hash','config','members','side','training','frozen','hook','counter','rng','gradient'])
def test_opponent_identity_rejects_wrong_or_mutated_state(study,tmp_path,monkeypatch,broken):
    a,learner=opponent_setup(study,tmp_path,monkeypatch)
    if broken=='hash':
        Path(a['opponent_model']).write_bytes(b'changed')
        with pytest.raises(ValueError): study.frozen_opponent(a,learner,'player_1')
        return
    opponent=study.frozen_opponent(a,learner,'player_1')
    expected=study.opponent_identity(opponent,a,'player_1')
    if broken=='config': a['opponent_config']={}
    if broken=='members': opponent.extra_q.pop()
    if broken=='side': opponent.player='player_0'
    if broken=='training': opponent.training=True
    if broken=='frozen': opponent.cfg.frozen=True
    if broken=='hook': opponent._behavior_ensemble_owner=object()
    if broken=='counter': opponent.env_steps+=1
    if broken=='rng': opponent.rng.random()
    if broken=='gradient': next(opponent.q.parameters()).requires_grad_(True)
    with pytest.raises(ValueError): study.opponent_identity(opponent,a,'player_1',expected=expected)


def test_failed_stock_load_restores_all_rngs(study,tmp_path,monkeypatch):
    a,learner=opponent_setup(study,tmp_path,monkeypatch)
    from agents.sherlock import main
    def fail(*args,**kwargs):
        random.random(); np.random.random(); torch.rand(1); learner.rng.random()
        raise RuntimeError('loader failed')
    monkeypatch.setattr(main,'Agent_x',fail)
    before=behavior.rng_identity(learner)
    with pytest.raises(RuntimeError,match='loader failed'): study.frozen_opponent(a,learner,'player_0')
    assert behavior.rng_identity(learner)==before


def test_participation_proves_real_calls_side_freshness_and_unchanged_opponent(study,tmp_path,monkeypatch):
    a,learner=opponent_setup(study,tmp_path,monkeypatch)
    opponent=study.frozen_opponent(a,learner,'player_1')
    key=dict(phase='prefill',game=0,seed=9960300,side='player_0',opponent='rush')
    with study.participation(opponent,key,a,'frozen_v14') as proof:
        opponent.new_game('player_1'); opponent.set_env_cfg({'map_width':24})
        for step in range(303): opponent.act(step,{'side':'player_1'})
    study.check_exposure(proof,key,a)
    assert proof['original_opponent']=='rush' and proof['actual_opponent']=='frozen_v14'
    assert proof['act_calls']==303 and proof['new_game_calls']==proof['env_cfg_calls']==1
    assert proof['before']==proof['after'] and proof['fresh'] is True
    for field,value in [('opponent_side','player_0'),('act_calls',302),('fresh',False),('after',{}),
                        ('opponent_class','scripts.style_opponents.RushBot')]:
        with pytest.raises(ValueError): study.check_exposure(dict(proof,**{field:value}),key,a)


def test_joint_release_only_fixed_roles_with_same_original_prefills(study):
    a=dict(source={'head':'new'})
    pins={'e48':'48','e49':'49'}
    good=dict(profile=study.PROFILE,status='approved',source=a['source'],starts=[48,49],roles=['e48','e49'],
              admission_sha256='a',prefill_sha256=pins,root_review_sha256='review')
    study.validate_release(good,a,'a',pins)
    for field,value in [('roles',['e48']),('starts',[48,48]),('source',{}),('prefill_sha256',{'e48':'48'}),
                        ('admission_sha256','stale'),('root_review_sha256','')]:
        with pytest.raises(ValueError): study.validate_release(dict(good,**{field:value}),a,'a',pins)


def test_live_owner_identity_and_exclusive_output(study,tmp_path,monkeypatch):
    monkeypatch.setattr(study,'ROOT',tmp_path)
    a=dict(stage='training',source={},out=str(tmp_path/'experiments/analysis'/study.PROFILE/'training_v1'),
           root=str(tmp_path),python='/python',plans=[],protected={},stop_file='/tmp/STOP',
           allow_battery=True,starts=[48,49],inputs={})
    assert study.output_dir(a)==Path(a['out'])
    with pytest.raises(ValueError): study.output_dir(dict(a,inputs={a['out']+'/file':'sha'}))
    command=study.worker_command(a,'/a.json','sha',a['out']+'/state.json','e48')
    state=dict(a,profile=study.PROFILE,status='running',owner_pid=12,admission_sha256='sha',
        active=['e48','e49'],jobs={'e48':dict(pid=13,pgid=13,owner_pid=12,argv=command),'e49':{}})
    args=dict(pid=13,pgid=13,ppid=12,executable='/python',actual=command)
    study.check_worker(state,a,'sha','e48',command,**args)
    for key,value in [('owner_pid',1),('active',['e48','foreign']),('admission_sha256','wrong')]:
        with pytest.raises(ValueError): study.check_worker(dict(state,**{key:value}),a,'sha','e48',command,**args)


def exposure_row(key,a):
    actual='solution92' if key['opponent']=='solution92' else 'frozen_v14'
    row=dict(original_opponent=key['opponent'],actual_opponent=actual,
             opponent_side='player_1' if key['side']=='player_0' else 'player_0',act_calls=303,
             new_game_calls=1 if actual=='frozen_v14' else 0,env_cfg_calls=1,
             action_sha256='0'*64,opponent_class=('agents.sherlock.main.Agent_x' if actual=='frozen_v14'
                                                else 'agents.Solution_92_Kaggle.agent.Agent'))
    if actual=='frozen_v14':
        identity=dict(members=a['source_members'],target='target',optimizer='opt',env_steps=42,learn_steps=13,
                      buffer_size=0,rng='rng',caught_errors=0)
        rng=dict(python='p',numpy='n',torch='t',agent='a')
        row.update(model_sha256=a['opponent_sha'],seed=0,fresh=True,config=a['opponent_config'],
                   setup_rng=dict(before=rng,after=rng),before=identity,after=copy.deepcopy(identity))
    return row


def test_original_chronology_and_counts_reject_bad_actual_exposure(study):
    a=dict(source_members=['m']*36,opponent_config={},opponent_sha=study.OPPONENT_SHA)
    rows=[]
    for i,key in enumerate(old.rollout_plan(48)[:40]):
        rows.append(dict(key=key,role='control',behavior='ensemble',start=48,steps=303,point_counting_version=2,
            before=dict(env_steps=60000+303*i,learn_steps=0),env_steps=60303+303*i,learn_steps=0,loss=None,
            reward_audit={'transitions':2},final_action_audit={'checked_replay_transitions':2},
            exposure=exposure_row(key,a)))
    study.check_rows(rows,48,40,a)
    for kind in ('wrong_key','wrong_actual','missing','extra','steps','updates'):
        broken=copy.deepcopy(rows)
        if kind=='wrong_key': broken[0]['key']['seed']+=1
        if kind=='wrong_actual': broken[0]['exposure']['actual_opponent']='unknown'
        if kind=='missing': broken.pop()
        if kind=='extra': broken.append(broken[-1])
        if kind=='steps': broken[0]['steps']=302
        if kind=='updates': broken[0]['learn_steps']=1
        with pytest.raises(ValueError): study.check_rows(broken,48,40,a)


def test_historical_on_initial_and_config_are_bound_to_original_receipts(study,tmp_path,monkeypatch):
    def put(path,value): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value)); return str(path)
    from agents.sherlock.config import AgentConfig
    source_cfg=AgentConfig().to_dict(); cfg=old.training_config(source_cfg,'control')
    metadata=put(tmp_path/'source-config.json',dict(source_sha256=old.V14_SHA,source_config=source_cfg))
    # The real historical assembly did not include this metadata wrapper in its inputs.
    reference_path=put(tmp_path/'ref.json',dict(inputs={}))
    monkeypatch.setattr(study,'SOURCE_CONFIG_SHA',old.digest(metadata),raising=False)
    refs=dict(models={'v14':dict(path=str(tmp_path/'v14.pth'),sha256=study.OPPONENT_SHA,
                               member_sha256=['m']*36)})
    records=[]; initials={}; model_entries={}
    for start in (48,49):
        directory=tmp_path/f'on{start}'; initial={'q':'q','target':'q','optimizer':str(start)}
        p=put(directory/'ensemble-initial.json',dict(initial=initial,start=start,config=cfg))
        f=put(directory/'prefill.json',dict(initial=initial,current=initial,games=40,learn_steps=0))
        receipt=put(directory/'receipt.json',dict(files=old.hashes([p,f])))
        records.append(dict(path=directory/'final.pth',start=start,config=cfg))
        model_entries[f'on{start}']=dict(receipt=receipt)
        initials[str(start)]=initial
    tech=put(tmp_path/'old-technical.json',dict(profile=behavior.PROFILE,status='complete',stage='technical',
                config=cfg,games=[dict(behavior='ensemble')]*2))
    train=put(tmp_path/'old-training.json',dict(config=cfg,technical_receipt=tech,
        rollout_plans={str(s):old.rollout_plan(s) for s in (48,49)}))
    closure=put(tmp_path/'closure.json',dict(admission=train,models=model_entries))
    monkeypatch.setattr(study,'ON_COMPLETION_SHA',old.digest(closure))
    monkeypatch.setattr(study.comparison,'accepted_references',lambda a:(refs,[]))
    monkeypatch.setattr(study.comparison,'accepted_training',lambda a:records)
    a=dict(training_completion=closure,reference_admission=reference_path,opponent_config_source=metadata,
        opponent_model=refs['models']['v14']['path'],opponent_config=study.comparison.inference_config({'cfg':source_cfg}),
        source_members=['m']*36,initial=initials,config=cfg,
        rollout_plans={str(s):old.rollout_plan(s) for s in (48,49)},inputs=old.hashes(tmp_path.rglob('*.json')))
    assert study.historical(a)['initial']==initials
    original_metadata=Path(metadata).read_bytes()
    Path(metadata).write_text(json.dumps(dict(source_sha256=old.V14_SHA,source_config=source_cfg,unaccepted=True)))
    a['inputs'][metadata]=old.digest(metadata)
    with pytest.raises(ValueError,match='source config'): study.historical(a)
    Path(metadata).write_bytes(original_metadata); a['inputs'][metadata]=old.digest(metadata)
    path=tmp_path/'on48/ensemble-initial.json'; bad=json.loads(path.read_text()); bad['initial']['q']='changed'
    path.write_text(json.dumps(bad)); a['inputs'][str(path)]=old.digest(path)
    with pytest.raises(ValueError,match='Historical initial'): study.historical(a)


def test_admission_rejects_invalid_stage_without_archive_load(study,tmp_path):
    path=tmp_path/'a.json'; path.write_text(json.dumps({'profile':study.PROFILE,'stage':'resume'}))
    with pytest.raises(ValueError): study.admission(path,old.digest(path),'resume')


def test_play_one_uses_real_frozen_instance_on_opposite_side_and_original_key(study,tmp_path,monkeypatch):
    a,agent=opponent_setup(study,tmp_path,monkeypatch)
    agent.env_steps=60000; agent.learn_steps=0; agent.learn_enabled=False; agent.caught_errors=0
    agent.cfg=SimpleNamespace(train_every=2); agent.role='control'; agent.epsilon=.05
    agent.pop_mean_loss=lambda: float('nan')
    key=dict(phase='prefill',game=0,seed=9960300,side='player_0',opponent='default')
    from scripts import common
    def game(env,learner,opp,seed,side,train):
        assert isinstance(opp,SyntheticOpponent) and opp.player=='player_1'
        assert learner is agent and seed==9960300 and side=='player_0' and train is True
        opp.new_game('player_1'); opp.set_env_cfg({'map_width':24})
        for step in range(303): opp.act(step,{'side':'player_1'})
        agent.env_steps+=303
        return dict(steps=303,point_counting_version=2)
    monkeypatch.setattr(common,'play_game',game)
    monkeypatch.setattr(old,'TraceEnv',lambda env:SimpleNamespace(native=hashlib.sha256(),trajectory=hashlib.sha256()))
    audit=dict(updates=303,transitions=2,records={'uid':np.array([1,2])})
    labels=dict(update_calls=303,act_calls=303,checked_replay_transitions=2)
    monkeypatch.setattr(old,'reward_audit',lambda *args,**kwargs:nullcontext(audit))
    monkeypatch.setattr(old,'action_audit',lambda *args,**kwargs:nullcontext(labels))
    row,records=study.play_one(agent,key,object(),a)
    assert row['key']==key and key['opponent']=='default' and row['exposure']['actual_opponent']=='frozen_v14'
    assert row['exposure']['opponent_side']=='player_1' and len(records['uid'])==2



from agents.sherlock.config import AgentConfig
from agents.sherlock.model import QNet

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
    a = dict(stage='training',source={'head':'new'},out=str(tmp_path),starts=[48,49],config=None,opponent_config={},opponent_sha=study.OPPONENT_SHA)
    proofs = {}; saved_agents={}; mechanisms={}
    for role,start in [('e48',48),('e49',49)]:
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
                final_action_audit={'checked_replay_transitions':2},exposure=exposure_row(key,a))
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
    study.write(tmp_path/'state.json',dict(status='running',active=['e48','e49'],admission_sha256='sha'))
    review=tmp_path/'review.json'
    review.write_text(json.dumps(dict(status='PASS',profile=study.PROFILE,source=a['source'],
        admission_sha256='sha',prefill_sha256=proofs)))
    assert not (tmp_path/'release.json').exists()
    study.approve_prefill(a,'sha',review,old.digest(review))
    release=json.loads((tmp_path/'release.json').read_text())
    assert release['prefill_sha256']==proofs and release['roles']==['e48','e49']
    with pytest.raises(FileExistsError): study.approve_prefill(a,'sha',review,old.digest(review))
    role='e48'; directory=tmp_path/role; agent=saved_agents[role]
    rows=json.loads((directory/'prefill.json').read_text())['rows']
    for i,key in enumerate(old.rollout_plan(48)[40:],40):
        for _ in range(2): agent.buffer.push(np.ones(79,np.float32),i%6,.25,np.zeros(79,np.float32),False,np.ones(6,bool))
        rows.append(dict(key=key,role='control',behavior='ensemble',start=48,steps=303,point_counting_version=2,
            before=dict(env_steps=60000+303*i,learn_steps=(i-40)*150),env_steps=60303+303*i,
            learn_steps=(i-39)*150,loss=.1,reward_audit={'transitions':2},final_action_audit={'checked_replay_transitions':2},exposure=exposure_row(key,a)))
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

def test_worker_keeps_one_env_stops_at_prefill_without_learning_and_saves_incomplete(study,tmp_path,monkeypatch):
    from types import SimpleNamespace
    payloads=synthetic_checkpoint_io(monkeypatch)
    seed_agent,states,cfg=fixture_agent(); initial=old.model_identity(seed_agent)
    a=dict(stage='training',out=str(tmp_path),config=cfg,initial={'48':initial,'49':initial},
           stop_file=str(tmp_path/'STOP'),source={'head':'fixed'},opponent_sha=study.OPPONENT_SHA,
           source_members=[old.state_sha256(s) for s in states])
    state_path=tmp_path/'state.json'; state_path.write_text(json.dumps({'jobs':{'e48':{},'e49':{}}}))
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
    def play(agent,key,env,a,*,actual=None):
        assert actual is None
        assert env is made[0] and not agent.learn_enabled and agent.learn_steps==0
        calls.append(key)
        for i in range(2): agent.buffer.push(np.ones(79,np.float32),0,.25,np.zeros(79,np.float32),False,np.ones(6,bool))
        agent.env_steps+=303
        return {'key':key},dict(uid=np.arange(2),outcome=np.ones(2),control=np.full(2,.25),match=np.full(2,18.25))
    monkeypatch.setattr(study,'play_one',play)
    def stop(*args): raise ValueError('Root did not release')
    monkeypatch.setattr(study,'wait_release',stop)
    with pytest.raises(ValueError,match='Root did not release'):
        study.run_worker(a,tmp_path/'a.json','sha',state_path,'e48')
    assert len(calls)==40 and calls==old.rollout_plan(48)[:40] and len(made)==1 and made[0].closed
    result=json.loads((tmp_path/'e48/incomplete.json').read_text())
    assert result['completed_games']==40 and result['eligible'] is False
    cp=payloads[str(tmp_path/'e48/incomplete.pth')]
    assert cp['learn_steps']==0 and not cp['opt']['state'] and cp['exposure']['status']=='incomplete'
    assert not (tmp_path/'e48/final.pth').exists()

@pytest.mark.parametrize('stage,release,fault',[
    ('technical',False,None),('training',True,None),('training',False,None),('training',True,'worker'),
    ('technical',False,'descendants'),('training',True,'stop')])
def test_owner_one_phase_both_workers_manual_barrier_and_cleanup(study,tmp_path,monkeypatch,stage,release,fault):
    assert importlib.util.find_spec('scripts.frozen_v14_exposure_owner'), 'Owner not implemented yet'
    owner=importlib.import_module('scripts.frozen_v14_exposure_owner')
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
            role=role,start=49 if role=='e49' else 48,source=a['source'],admission_sha256=sha,
            command=command,games=[{}]*(4 if stage=='technical' else 440),release_sha256=None))
        if stage=='training':
            study.write(directory/'prefill.json',{'role':role}); study.write(directory/'waiting.json',{'role':role})
    def sleep(_):
        state=json.loads((out/'state.json').read_text())
        assert launched==['e48','e49'] and set(state['prefill_ready'])=={'e48','e49'}
        if (out/'release.json').exists():
            assert state['awaiting_root_release'] is False
            saw_learning.append(True); return
        assert not (out/'release.json').exists()
        if not release: raise RuntimeError('No Root release')
        if fault=='stop': Path(a['stop_file']).touch(); return
        review=tmp_path/'review.json'; review.write_text('{}')
        study.write(out/'release.json',dict(profile=study.PROFILE,status='approved',source=a['source'],
            starts=[48,49],roles=['e48','e49'],admission_sha256=sha,prefill_sha256=state['prefill_ready'],
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
    monkeypatch.setattr(owner,'group_alive',lambda pgid:fault=='descendants')
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
        assert checked==(['technical'] if stage=='technical' else ['e48','e49'])
        with pytest.raises(ValueError): owner.main()
    assert launched==(['technical'] if stage=='technical' else ['e48','e49']) and cleaned
    if stage=='training' and release and fault!='stop': assert saw_learning
    if stage=='training' and not release: assert not (out/'release.json').exists()


def test_technical_two_historical_on_then_two_frozen_cases_are_complete(study,tmp_path):
    agent,states,cfg=fixture_agent(); initial=old.model_identity(agent)
    a=dict(source_members=[old.state_sha256(s) for s in states],opponent_config={},opponent_sha=study.OPPONENT_SHA)
    history=dict(initial={'48':initial,'49':initial},technical={'games':[]})
    rows=[]; files={}
    for group in ('solution92','frozen_v14'):
        agent,_,_=fixture_agent()
        with study.BehaviorEnsemble(agent,states,True) as adapter:
            for i,(seed,side) in enumerate(old.TECH_KEYS):
                adapter.stats.update(act_calls=303*(i+1),network_calls=i+1,member_forwards=36*(i+1),unit_steps=2*(i+1))
                data=dict(uid=np.array([2,4]),outcome=np.ones(2),control=np.array([.25,.5]),match=np.array([18.25,18.5]))
                evidence=old.save_reward_evidence(tmp_path/f'{group}-{i}.npz',data); files[evidence['path']]=evidence['sha256']
                key=dict(phase='technical',game=i,seed=seed,side=side,opponent='solution92')
                exposure=exposure_row(dict(key,opponent='rush') if group=='frozen_v14' else key,a)
                exposure['original_opponent']='solution92'
                row=dict(key=key,role='control',behavior='ensemble',technical_group=group,start=48,steps=303,
                    point_counting_version=2,before=dict(env_steps=60000+303*i,learn_steps=0),
                    env_steps=60303+303*i,learn_steps=0,initial=initial,current=initial,loss=None,epsilon=.05,
                    game_win=0,point_win=0.,reward_audit=dict(transitions=2,updates=303,nonzero_outcome_rows=2),
                    final_action_audit=dict(checked_replay_transitions=2,act_calls=303,update_calls=303),
                    our_wins=1,opp_wins=2,our_points=30,opp_points=40,result=0.,native_sha256=f'native-{group}-{i}',
                    trajectory_sha256='public',reward_evidence=evidence,mechanism=adapter.proof(),exposure=exposure)
                rows.append(row)
                if group=='solution92': history['technical']['games'].append(copy.deepcopy(row))
    probe,_,_=fixture_agent(49)
    with study.BehaviorEnsemble(probe,states,True) as adapter: setup=adapter.proof()
    history['initial']['49']=old.model_identity(probe)
    receipt=dict(profile=study.PROFILE,status='complete',stage='technical',games=rows,files=files,start49_setup=setup)
    study.check_technical(receipt,history,a)
    for fault in ('historical_native','frozen_side','frozen_tensor','row_count','updates','rng','setup49'):
        bad=copy.deepcopy(receipt)
        if fault=='historical_native': bad['games'][0]['native_sha256']='changed'
        if fault=='frozen_side': bad['games'][2]['exposure']['opponent_side']='player_0'
        if fault=='frozen_tensor': bad['games'][2]['exposure']['after']['members'][0]='changed'
        if fault=='row_count': bad['games'].pop()
        if fault=='updates': bad['games'][2]['learn_steps']=1
        if fault=='rng': bad['games'][2]['mechanism']['rng_before']['torch']='changed'
        if fault=='setup49': bad['start49_setup']['stats']['act_calls']=1
        with pytest.raises(ValueError): study.check_technical(bad,history,a)


def test_technical_worker_runs_exactly_two_solution_then_two_v14_without_learning(study,tmp_path,monkeypatch):
    agent,states,cfg=fixture_agent(); initial=old.model_identity(agent)
    a=dict(stage='technical',out=str(tmp_path),config=cfg,initial={'48':initial,'49':initial},
        stop_file=str(tmp_path/'STOP'),source={'head':'fixed'},source_members=[old.state_sha256(s) for s in states])
    state_path=tmp_path/'state.json'; state_path.write_text(json.dumps({'jobs':{'technical':{}}}))
    made=[]; calls=[]
    class Env:
        def __init__(self,**kwargs): self.closed=False; made.append(self)
        def close(self): self.closed=True
    monkeypatch.setitem(sys.modules,'luxai_s3.wrappers',SimpleNamespace(LuxAIS3GymEnv=Env))
    monkeypatch.setattr(study,'load_members',lambda a:states)
    class Guard:
        def __init__(self,*args): self.command=['synthetic']; self.release_sha=None
        def __call__(self): pass
    monkeypatch.setattr(study,'WorkerGuard',Guard)
    monkeypatch.setattr(study,'historical',lambda a:{})
    monkeypatch.setattr(study,'check_technical',lambda *args:None)
    def play(agent,key,env,a,*,actual=None):
        assert env is made[0] and not agent.learn_enabled and agent.learn_steps==0
        calls.append((actual,key['seed'],key['side'],agent.env_steps))
        agent.env_steps+=303
        return {'key':key},dict(uid=np.array([2]),outcome=np.ones(1),control=np.zeros(1),match=np.full(1,18.))
    monkeypatch.setattr(study,'play_one',play)
    receipt=study.run_worker(a,tmp_path/'a.json','sha',state_path,'technical')
    assert calls==[('solution92',9946007,'player_0',60000),('solution92',831006,'player_1',60303),
                  ('frozen_v14',9946007,'player_0',60000),('frozen_v14',831006,'player_1',60303)]
    assert receipt['status']=='complete' and len(receipt['games'])==4 and len(made)==1 and made[0].closed
    assert not (tmp_path/'technical/final.pth').exists() and not (tmp_path/'release.json').exists()


@pytest.mark.parametrize('stage',['technical','training'])
def test_admission_exact_current_and_historical_bindings_without_models(study,tmp_path,monkeypatch,stage):
    monkeypatch.setattr(study,'ROOT',tmp_path); monkeypatch.chdir(tmp_path)
    weights=tmp_path/'agents/sherlock/weights'; weights.mkdir(parents=True)
    for i in (0,1): (weights/f'agent_p{i}.pth').write_bytes(b'fake original')
    (tmp_path/'Gruppe15.zip').write_bytes(b'fake package')
    opponent=tmp_path/'v14.pth'; opponent.write_bytes(b'fake opponent')
    monkeypatch.setattr(old,'V14_SHA',old.digest(weights/'agent_p0.pth'))
    monkeypatch.setattr(old,'ZIP_SHA',old.digest(tmp_path/'Gruppe15.zip'))
    monkeypatch.setattr(study,'OPPONENT_SHA',old.digest(opponent))
    protected={str(weights/f'agent_p{i}.pth'):old.V14_SHA for i in (0,1)}
    protected[str(tmp_path/'Gruppe15.zip')]=old.ZIP_SHA
    source={'head':'new'}; runtime=study.runtime_identity()
    prior=tmp_path/'prior.json'; prior.write_text(json.dumps({'runtime':runtime}))
    closure=tmp_path/'closure.json'; closure.write_text(json.dumps({'admission':str(prior)}))
    monkeypatch.setattr(study,'source_identity',lambda *args:source)
    monkeypatch.setattr(study,'historical',lambda a:{})
    monkeypatch.setattr(study,'check_technical',lambda *args:None)
    a=dict(profile=study.PROFILE,schema_version=1,stage=stage,start_authorized=True,allow_battery=True,
        starts=[48,49],historical_runtime_gap_acknowledged=True,root=str(tmp_path),python=sys.executable,
        plans=[],source=source,runtime=runtime,protected=protected,training_completion=str(closure),
        v14_source=str(weights/'agent_p0.pth'),opponent_model=str(opponent),config={},
        out=str(tmp_path/'experiments/analysis'/study.PROFILE/f'{stage}_v1'))
    if stage=='training':
        tech=tmp_path/'tech.json'; tech.write_text(json.dumps(dict(source=source,config={},files={})))
        approval=tmp_path/'approval.json'; approval.write_text(json.dumps(dict(status='PASS',profile=study.PROFILE,
            source=source,technical_receipt_sha256=old.digest(tech),original_processes_ended=True)))
        a.update(technical_receipt=str(tech),technical_acceptance=str(approval))
    a['inputs']={**protected,**old.hashes([opponent,prior,closure]),
                 **(old.hashes([tech,approval]) if stage=='training' else {})}
    path=tmp_path/'a.json'
    def admit(value): path.write_text(json.dumps(value)); return study.admission(path,old.digest(path),stage)
    assert admit(a)==a
    for field,value in [('start_authorized',False),('starts',[48]),('historical_runtime_gap_acknowledged',False),
                        ('runtime',{}),('out',str(tmp_path/'elsewhere'))]:
        with pytest.raises(ValueError): admit(dict(a,**{field:value}))
    if stage=='training':
        value=json.loads(approval.read_text()); value['original_processes_ended']=False; approval.write_text(json.dumps(value))
        a['inputs'][str(approval)]=old.digest(approval)
        with pytest.raises(ValueError,match='Root technical'): admit(a)
