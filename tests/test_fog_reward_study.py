"""Synthetic only: no environment construction or model games."""
import copy
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from scripts import fog_reward_study as S
from scripts import fog_reward_supervisor as H


def test_fixed_four_arms_and_plans():
    assert S.ARMS == {'control41': (41, False), 'neutral41': (41, True),
                      'control42': (42, False), 'neutral42': (42, True)}
    for seed in (41, 42):
        a, b = (S.rollout_plan(f'{role}{seed}') for role in ('control', 'neutral'))
        assert a == b and len(a) == 440
        assert [r['seed'] for r in a[:40]] == [7_000_000 + seed*10000 + 5000 + g//2 for g in range(40)]
        assert [r['seed'] for r in a[40:]] == [7_000_000 + seed*10000 + g//2 for g in range(400)]
        assert [r['side'] for r in a] == ['player_0', 'player_1'] * 220
    assert len(S.validation_plan()) == 32
    assert {r['seed'] for r in S.validation_plan()} == set(range(7_600_000, 7_600_004))
    assert {r['after_games'] for r in S.validation_plan()} == {0, 400}
    assert 4 * (440 + 32) == 1888


def test_configs_only_flag_differs():
    source = dict(w_sap_hit=.3, eps_end=.05, train_every=2)
    a, b = (S.training_config(source, x) for x in (False, True))
    assert {k for k in a if a[k] != b[k]} == {'fog_unknown_reward_neutral'}
    assert a['lr'] == 5e-5 and a['rescue_in_training'] and not a['frozen']
    assert a['rules_in_training'] and a['rules_in_training_all'] and a['w_sap_hit'] == .3


@pytest.mark.parametrize('arm', ['control', 'sap0', 'control43', '', None])
def test_unknown_arm(arm):
    with pytest.raises(ValueError): S.rollout_plan(arm)


def formula(cfg, ctx, nxt, actions, hits, unknown_sap=None):
    from agents.sherlock.geometry import SAP
    return {uid: 2. + (0 if not cfg.use_shaping or actions.get(uid) != SAP or
        (cfg.fog_unknown_reward_neutral and uid in (unknown_sap or set())) else
        cfg.w_sap_hit * (1 if hits.get(uid, 0)>0 else -1)*max(1,hits.get(uid,0)))
        for uid in ctx['ally_ids']}


@pytest.mark.parametrize('enabled,weight,shaping', [(False,.3,True),(True,.3,True),(True,0.,True),(True,.3,False)])
def test_reward_audit_reads_final_explicit_provenance(monkeypatch, enabled, weight, shaping):
    from agents.sherlock import main, geometry as geo
    monkeypatch.setattr(main, 'unit_rewards', formula)
    agent = SimpleNamespace(_sap_unknown={0}, _prev_actions={0:geo.SAP,1:geo.SAP,2:geo.SAP,3:geo.STAY},
        _sap_hits={0:0,1:0,2:2}, cfg=SimpleNamespace(fog_unknown_reward_neutral=enabled,w_sap_hit=weight,use_shaping=shaping))
    with S.reward_audit(agent) as proof:
        args=(agent.cfg,dict(ally_ids=np.array([0,1,2,3])),{},agent._prev_actions,agent._sap_hits)
        actual=main.unit_rewards(*args, **({'unknown_sap':{0}} if enabled else {}))
        assert actual == formula(*args,unknown_sap={0})
    assert proof['unknown_sap_transitions'] == 1
    assert proof['estimated_misses'] == 2 and proof['estimated_positive_hits'] == 1
    assert proof['unknown_reward_mass'] == pytest.approx(weight if shaping else 0)
    assert proof['actual_reward_sha256'] == proof['neutral_reward_sha256' if enabled else 'legacy_reward_sha256']
    assert main.unit_rewards is formula


@pytest.mark.parametrize('unknown,actions,hits', [({0},{0:0},{0:0}),({0},{0:5},{0:2}),({1},{0:5},{0:0})])
def test_reward_audit_rejects_invalid_provenance(monkeypatch,unknown,actions,hits):
    from agents.sherlock import main
    monkeypatch.setattr(main,'unit_rewards',formula)
    a=SimpleNamespace(_sap_unknown=unknown,_prev_actions=actions,_sap_hits=hits,
        cfg=SimpleNamespace(fog_unknown_reward_neutral=True,w_sap_hit=.3,use_shaping=True))
    with pytest.raises(ValueError), S.reward_audit(a):
        main.unit_rewards(a.cfg,dict(ally_ids=np.array([0])),{},actions,hits,unknown_sap=unknown)


def test_reward_audit_fails_closed_arithmetic_and_restores(monkeypatch):
    from agents.sherlock import main,geometry as geo
    def broken(*args,**kw):
        result=formula(*args,**kw)
        if args[0].fog_unknown_reward_neutral: result[0]+=1
        return result
    monkeypatch.setattr(main,'unit_rewards',broken)
    a=SimpleNamespace(_sap_unknown={0},_prev_actions={0:geo.SAP},_sap_hits={0:0},
        cfg=SimpleNamespace(fog_unknown_reward_neutral=True,w_sap_hit=.3,use_shaping=True))
    with pytest.raises(ValueError), S.reward_audit(a):
        main.unit_rewards(a.cfg,dict(ally_ids=np.array([0])),{},a._prev_actions,a._sap_hits,unknown_sap={0})
    assert main.unit_rewards is broken


def test_replay_hash_ignores_only_rewards():
    b=SimpleNamespace(size=2,pos=2,capacity=4,_mask_dim=2,
        s=np.zeros((4,2)),ns=np.ones((4,2)),a=np.array([0,1,0,0]),r=np.array([1.,2.,0.,0.]),
        done=np.zeros(4),mask=np.ones((4,2),bool))
    initial=S.replay_without_reward(b)
    b.r[0]=42
    assert S.replay_without_reward(b)==initial
    b.a[0]=2
    assert S.replay_without_reward(b)!=initial


def pair_proofs():
    shared=dict(status='prefill_ready',smoke=False,run_seed=41,component_index=18,
        actual_prefill_games=40,unknown_sap_transitions=5,unknown_reward_mass=1.5,
        trajectory_sha256='a'*64,replay_without_reward_sha256='b'*64,
        legacy_reward_sha256='c'*64,neutral_reward_sha256='d'*64,
        unchanged_q=True,unchanged_target=True,unchanged_optimizer=True,learn_steps=0)
    return [dict(shared,arm='control41',actual_reward_sha256='c'*64),
            dict(shared,arm='neutral41',actual_reward_sha256='d'*64)]


def test_pair_proof_is_independent_of_end_results():
    a,b=pair_proofs()
    assert S.compare_prefill_proofs(a,b,41)['status']=='matched'


@pytest.mark.parametrize('key,value', [('trajectory_sha256','e'*64),('replay_without_reward_sha256','e'*64),
    ('legacy_reward_sha256','e'*64),('unknown_sap_transitions',0),('unchanged_optimizer',False),
    ('learn_steps',1),('actual_prefill_games',39),('arm','control41'),('actual_reward_sha256','e'*64)])
def test_pair_mismatch_fails_closed(key,value):
    a,b=pair_proofs();b[key]=value
    with pytest.raises(ValueError): S.compare_prefill_proofs(a,b,41)


def test_usage_strict_and_fresh(tmp_path):
    now=10000.
    from datetime import datetime,timezone
    path=tmp_path/'usage.json'
    data=dict(timestamp=datetime.fromtimestamp(now,timezone.utc).isoformat(),usedPercent=99.9,ordinaryUsageAllowed=True)
    path.write_text(json.dumps(data));assert H.check_usage(path,now=now,max_used_percent=100)['usedPercent']==99.9
    for updates in ({'usedPercent':100},{'ordinaryUsageAllowed':False},{'timestamp':'1970-01-01T00:00:00Z'}):
        path.write_text(json.dumps(dict(data,**updates)))
        with pytest.raises(ValueError): H.check_usage(path,now=now,max_used_percent=100)


def test_foreign_process_guards_allow_only_registered_groups():
    snapshot='11 11 python -m scripts.fog_reward_study run\n12 12 python -m scripts.holder_rollout_probe\n13 13 python -m pytest\n14 14 /usr/bin/caffeinate -i\n'
    assert H.foreign_processes(snapshot,owner_pid=10,owned_pgids={11}) == [12,13]


def test_worker_guard_rejects_changed_hash(tmp_path,monkeypatch):
    file=tmp_path/'input';file.write_text('original')
    state=dict(stop_file=str(tmp_path/'STOP'),usage_file='usage',source={},plans=[],python='python',
               protected={},inputs={str(file):S.file_sha256(file)},owner_pid=1,jobs={},active=[])
    monkeypatch.setattr(H,'read_power',lambda:dict(ac=True,percent=100))
    monkeypatch.setattr(H,'check_usage',lambda *a,**kw:{})
    monkeypatch.setattr(H,'source_identity',lambda *a:{})
    monkeypatch.setattr(H,'check_model_processes',lambda *a:None)
    H.guard(state,{})
    file.write_text('changed')
    with pytest.raises(ValueError): H.guard(state,{})


@pytest.mark.parametrize('power', [{'ac':False,'percent':100},{'ac':None,'percent':100}])
def test_ac_required(tmp_path,monkeypatch,power):
    monkeypatch.setattr(H,'read_power',lambda:power)
    state=dict(stop_file=str(tmp_path/'STOP'),usage_file='usage')
    monkeypatch.setattr(H,'check_usage',lambda *a,**kw:{})
    with pytest.raises(ValueError): H.guard(state,{})


def test_partial_receipt_rejected_before_loading(tmp_path):
    path=tmp_path/'final_receipt.json';path.write_text(json.dumps(dict(arm='control41',status='incomplete')))
    with pytest.raises(ValueError): S.validate_final_receipt(path)


def test_prepare_all_starts_identical_and_exclusive(tmp_path,monkeypatch):
    import torch
    from agents.sherlock.config import AgentConfig
    source=tmp_path/'v14.pth';source.write_bytes(b'synthetic source')
    cfg=AgentConfig().to_dict();cfg.update(w_sap_hit=.3,train_every=2,fog_unknown_reward_neutral=False)
    states=[{'w':torch.tensor([float(i)])} for i in range(36)]
    monkeypatch.setattr(S,'SOURCE_SHA',S.file_sha256(source))
    monkeypatch.setattr(S,'_source',lambda p:({},states,cfg))
    monkeypatch.setattr(S,'_pins',lambda:{'synthetic':'frozen'})
    out=tmp_path/'new'
    manifest=S.prepare(source,out)
    hashes=[]
    for arm in S.ARMS:
        _,entry,init=S.check_prepared(out,arm)
        cp=torch.load(init/'weights/agent.pth',weights_only=True)
        assert set(cp)=={'q','target_q','cfg','feature_dim','n_actions','ensemble','ensemble_dims','env_steps','learn_steps'}
        assert cp['q']['w'].item()==18 and cp['env_steps']==60000 and cp['learn_steps']==0
        assert S.tensor_sha256(cp['q'])==S.tensor_sha256(cp['target_q'])
        hashes.append(entry['tensor_sha256'])
    assert len(set(hashes))==1
    with pytest.raises(FileExistsError): S.prepare(source,out)
    path=out/'neutral41/weights/agent.pth'
    cp=torch.load(path,weights_only=True);cp['target_q']['w'][0]=19;torch.save(cp,path)
    with pytest.raises(ValueError): S.check_prepared(out,'neutral41')


def test_worker_launch_guard_survives_finetune_argv(tmp_path,monkeypatch):
    prepared=tmp_path/'prepared';prepared.mkdir()
    state=dict(status='running',prepared=str(prepared),out=str(tmp_path),python='python',
        owner_pid=123,active=['control41'],jobs={})
    state['jobs']['control41']=dict(pid=os.getpid(),pgid=os.getpgrp(),owner_pid=123,
        argv=H.training_command(state,'control41'))
    path=tmp_path/'state.json';path.write_text(json.dumps(state))
    monkeypatch.setattr(H.sys,'argv',['fog_reward_study/finetune','--init','synthetic'])
    monkeypatch.setattr(H,'guard',lambda *a:None)
    monkeypatch.setattr(H.os,'kill',lambda pid,sig:None)
    H.worker_guard(path,'control41',H.run_name('control41'),prepared)
    with pytest.raises(ValueError): H.worker_guard(path,'neutral41',H.run_name('neutral41'),prepared)


@pytest.mark.parametrize('stored', [0.,-1.,float('nan')])
def test_actual_replay_reward_is_audited(monkeypatch,stored):
    from agents.sherlock import main,geometry as geo
    monkeypatch.setattr(main,'unit_rewards',formula)
    buffer=SimpleNamespace(push=Mock())
    agent=SimpleNamespace(buffer=buffer,_prev_feats={0:np.zeros(2)},_sap_unknown={0},
        _prev_actions={0:geo.SAP},_sap_hits={0:0},
        cfg=SimpleNamespace(fog_unknown_reward_neutral=True,w_sap_hit=.3,use_shaping=True))
    with pytest.raises(ValueError),S.reward_audit(agent):
        main.unit_rewards(agent.cfg,dict(ally_ids=np.array([0])),{},agent._prev_actions,agent._sap_hits,unknown_sap={0})
        buffer.push(np.zeros(2),geo.SAP,stored,np.ones(2),False,np.ones(6,bool))


def test_trajectory_hash_and_hooks_restore_without_games():
    class Env:
        state={'tick':0}
        def reset(self,seed): self.state={'tick':seed};return {'both':np.ones(2)},{}
        def step(self,actions): self.state={'tick':self.state['tick']+1};return {'both':np.zeros(2)},0,False,False,{}
    class Agent:
        _prev_feats={0:np.zeros(2)};_prev_actions={0:0};_prev_masks={0:np.ones(6,bool)}
        _sap_hits={};_sap_unknown=set()
        buffer=SimpleNamespace(push=lambda *args:None)
        def act(self,*args,**kwargs): return np.zeros((16,3),int)
    env,agent=Env(),Agent()
    original=env.reset
    with S.trajectory_audit(env,agent) as proof:
        env.reset(seed=9);agent.act(step=0,obs={});env.step({'both':np.zeros(2)})
        agent.buffer.push(np.zeros(2),0,5.,np.ones(2),False,np.ones(6,bool))
    assert env.reset==original
    assert proof['reset_calls']==proof['step_calls']==proof['act_calls']==proof['replay_pushes']==1
    assert len(proof['environment_sha256'])==64 and 'reset' not in vars(env) and 'act' not in vars(agent)


def test_prefill_bundle_is_recomputed_from_raw_rows(tmp_path):
    cfg={'learn_start':5000}
    entry=dict(run_seed=41,config=cfg,tensor_sha256='f'*64)
    initial=dict(q_tensor_sha256='f'*64,target_tensor_sha256='f'*64,
        learning=dict(config=cfg,env_steps=60000,learn_steps=0,recent_losses=[],optimizer_sha256='opt',
                      replay=dict(size=0,pos=0,_mask_dim=1)))
    prefill=copy.deepcopy(initial);prefill['learning'].update(env_steps=72120,learn_enabled=False,replay=dict(size=6000))
    rows=[]
    for index,plan in enumerate(S.rollout_plan('control41')[:40]):
        rows.append(dict(plan,steps=303,point_counting_version=2,updates=0,learn_steps=0,
            env_steps=60000+(index+1)*303,result=1.,our_wins=2,opp_wins=1,our_points=100,opp_points=99,
            trajectory=dict(reset_calls=1,step_calls=303,act_calls=303,replay_pushes=10),
            action_audit=dict(checked_replay_transitions=10),reward_audit=dict(transitions=10,
                unknown_sap_transitions=1,unknown_reward_mass=.3,
                legacy_reward_sha256='a'*64,neutral_reward_sha256='b'*64,actual_reward_sha256='a'*64)))
    bundle=dict(arm='control41',entry=entry,initial=initial,prefill=prefill,rows=rows,
                replay_without_reward_sha256='c'*64)
    prepared=tmp_path/'prepared';prepared.mkdir()
    S._write(prepared/'manifest.json',dict(arms={'control41':entry}))
    directory=tmp_path/'arm';directory.mkdir()
    S._write(directory/'prefill_bundle.json',bundle)
    proof=S._prefill_summary('control41',entry,initial,prefill,rows,'c'*64,0)
    proof['bundle_sha256']=S.file_sha256(directory/'prefill_bundle.json')
    S._write(directory/'prefill_proof.json',proof)
    assert S.validate_prefill_bundle(directory,prepared,'control41')==proof
    # Even if the bundle hash is rebound, raw chronology cannot claim a match.
    bundle['rows'][0]['updates']=1
    S._write(directory/'prefill_bundle.json',bundle)
    proof['bundle_sha256']=S.file_sha256(directory/'prefill_bundle.json')
    S._write(directory/'prefill_proof.json',proof)
    with pytest.raises(ValueError): S.validate_prefill_bundle(directory,prepared,'control41')


def test_failed_prefill_stops_pair_without_next_starts(tmp_path,monkeypatch):
    state=dict(out=str(tmp_path),stop_file=str(tmp_path/'STOP'),jobs={},active=[],queue=list(H.ARMS),
               paired_prefill={},receipts={},python='python',prepared=str(tmp_path/'prepared'))
    monkeypatch.setattr(H,'ROOT',tmp_path)
    monkeypatch.setattr(H,'guard',lambda *a:None)
    monkeypatch.setattr(H,'save_state',lambda *a:None)
    monkeypatch.setattr(H,'shutdown_owned',Mock())
    launched=[]
    def spawn(state,arm,command,owned):
        assert len(owned)<2
        launched.append(arm);owned[arm]=dict(process=SimpleNamespace(poll=lambda:None),pgid=1)
        state['jobs'][arm]={}
        path=tmp_path/'experiments/runs'/H.run_name(arm);path.mkdir(parents=True)
        (path/'prefill_proof.json').write_text('{}')
    monkeypatch.setattr(H,'spawn_owned',spawn)
    monkeypatch.setattr(H,'compare_pair',Mock(side_effect=ValueError('synthetic mismatched pair')))
    with pytest.raises(ValueError): H.run_queue(state)
    assert launched==['control41','neutral41'] and state['status']=='incomplete'
    assert Path(state['stop_file']).exists()
    assert H.shutdown_owned.call_count==1
