"""Synthetic-only contracts for the post-rule, pre-damage intervention."""
import importlib
import importlib.util
from collections import defaultdict
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from agents.sherlock.main import Agent_x


def implementation():
    assert importlib.util.find_spec('scripts.holder_sap_probe') is not None
    return importlib.import_module('scripts.holder_sap_probe')


def context(step=138):
    points = np.zeros((6, 6), bool); points[0, :3] = True
    return dict(step=step, match_step=step % 101, max_match_steps=100,
                W=6, H=6, ally_ids=np.array([0, 1, 2]),
                ally_pos=np.array([[0, 0], [0, 1], [0, 2]]), ally_ene=np.array([50., 53., 80.]),
                point_tiles=points, enemy_coords=np.array([[2, 3]]),
                enemy_energies=np.array([100.]), sap_cost=20., sap_range=4,
                own_points=34, opp_points=28)


def test_default_hook_has_no_effect():
    assert hasattr(Agent_x, '_final_sap_policy')
    a = object.__new__(Agent_x); sap = (2, 3, 1)
    assert a._final_sap_policy(context(), 0, np.ones(6, bool), 0, 5, sap, None) == (5, sap)


@pytest.mark.parametrize('change', ['none','move','net_sap','stay_final','fog','negative',
                                   'unconfirmed','stack','illegal','invisible','absent','reset'])
def test_eligibility_rejects_non_public_or_non_holder_events(change):
    m = implementation(); c = context(); mask=np.ones(6, bool)
    net, final, fog, uid, sap = 0, 5, None, 0, (2,3,1)
    if change=='move': net=1
    if change=='net_sap': net=5
    if change=='stay_final': final=0
    if change=='fog': fog=sap
    if change=='negative': c['ally_ene'][0]=-1
    if change=='unconfirmed': c['point_tiles'][0,0]=False
    if change=='stack': c['ally_pos'][1]=[0,0]
    if change=='illegal': mask[0]=False
    if change=='invisible': c['enemy_coords']=np.empty((0,2),int)
    if change=='absent': uid=4
    if change=='reset': c['match_step']=0
    assert m.eligible_holder_sap(c,uid,mask,net,final,sap,fog) == (change=='none')


def actor(m, mirrored=False):
    class Flags:
        sap_no_overkill=True
        def __getattr__(self, name): return False
    a=object.__new__(m.HolderSapProbeAgent)
    a.cfg=Flags();a.training=False;a.device='cpu';a.cnn_policy=None;a.env_cfg={'max_units':3}
    a.belief=SimpleNamespace(observe=lambda obs:None,relic_positions=[],mirrored=mirrored)
    a.ep_stats=defaultdict(int);a.collect=True;a.used_matches=set();a.candidate=None
    a.intervention=None;a.intervention_hits=0;a._final_sap_experiment=True
    c=context();ids=[0,1,2];a._decide=lambda obs:(c,ids,{u:np.zeros(79,np.float32) for u in ids},
        {u:np.ones(6,bool) for u in ids},{u:(2,3-u,1) for u in ids})
    a._network_values=lambda f:torch.tensor([[4.,0.,0.,0.,0.,0.]]*3)
    a._enemy_stationary=lambda c:{};a._rescue_for=lambda c,u:False;a._harmful_nebula=lambda:0
    a._rule_override=lambda c,u,mask,action:5
    a._overkill=lambda c,u,sap,planned:bool(planned[0]>=100)
    a.damage_calls=[]
    def damage(c,u,sap,planned):
        a.damage_calls.append(u);planned[0]+=100
    a._plan_damage=damage
    return a


@pytest.mark.parametrize('mirrored',[False,True])
def test_real_chain_veto_releases_damage_for_next_unit_and_tracks_actions(mirrored):
    m=implementation();a=actor(m,mirrored)
    normal=a._act(138,{'match_steps':37})
    assert normal[:,0].tolist()==[5,0,0] and a.damage_calls==[0]
    chosen=a.candidate.copy()
    assert chosen['uid']==0 and a.used_matches=={1}
    a.collect=False;a.intervention=chosen;a.damage_calls.clear()
    changed=a._act(138,{'match_steps':37})
    assert changed[:,0].tolist()==[0,5,0] and a.damage_calls==[1]
    assert changed[1,1:].tolist()==([-2,-2] if mirrored else [2,2])
    assert a._prev_actions=={0:0,1:5,2:0} and set(a._sap_hits)=={1}
    assert a.intervention_hits==1 and not a._sap_unknown
    # One occurrence only, not a persistent policy.
    with pytest.raises(ValueError): a._act(138,{'match_steps':37})


def test_event_consumed_even_when_later_steps_have_more_candidates():
    m=implementation();a=actor(m)
    a._act(138,{'match_steps':37});first=a.candidate.copy()
    a.candidate=None;a._act(139,{'match_steps':38})
    assert a.candidate is None and first['uid']==0


def test_hook_never_uses_post_policy_greedy_as_original_network_vote():
    m=implementation();a=actor(m)
    a._policy_greedy=lambda c,ids,masks,g:np.ones_like(g)
    a._act(138,{'match_steps':37})
    assert a.candidate['network_action']==0


def test_disabled_hook_is_not_called_in_training_or_default_agent():
    m=implementation();a=actor(m)
    a._final_sap_experiment=False
    a._final_sap_policy=lambda *args:(_ for _ in ()).throw(AssertionError('should not call'))
    assert a._act(138,{'match_steps':37})[:,0].tolist()==[5,0,0]


def test_frozen_reference_is_distinct_original_package():
    m=implementation();cls=m.load_reference_class()
    assert cls.__module__=='frozen_holder_v14.main'
    assert not hasattr(cls,'_final_sap_policy')
    assert cls is not Agent_x


def test_training_bypasses_final_hook():
    m=implementation();a=actor(m);a.training=True;a.cfg.eps_start=0.;a.cfg.eps_end=0.
    a.env_steps=0;a.rng=np.random.default_rng(0)
    a._final_sap_policy=lambda *args:(_ for _ in ()).throw(AssertionError('training hook'))
    assert a._act(138,{'match_steps':37})[:,0].tolist()==[5,5,5]


def test_veto_keeps_earlier_damage_and_fixes_own_prediction():
    m=implementation();a=actor(m);a._pred_pending=[]
    a.cfg.dodge_verify=True;a._check_predictions=lambda c:None
    a._predicted_hits=lambda c,s:{0:1.,1:1.,2:1.};a._pred_n=0;a._pred_hit=0
    a._overkill=lambda *args:False
    a._act(138,{'match_steps':37})
    event=a.candidate.copy();event.update(uid=1,sap=[2.,2.,1.],energy=53.,position=[0,1])
    a.collect=False;a.intervention=event;a.damage_calls.clear();a._pred_pending=[]
    result=a._act(138,{'match_steps':37})
    assert result[:,0].tolist()==[5,0,5] and a.damage_calls==[0,2]
    assert [x[-1] for x in a._pred_pending]==[True,False,True]
    assert set(a._sap_hits)=={0,2}


def test_wrong_key_never_intervenes_and_order_is_checked():
    m=implementation();a=actor(m);a._act(138,{'match_steps':37})
    a.collect=False;a.intervention={**a.candidate,'step':139}
    assert a._act(138,{'match_steps':37})[:,0].tolist()==[5,0,0]
    assert a.intervention_hits==0
    with pytest.raises(ValueError):
        m.HolderSapProbeAgent._policy_greedy(a,context(),[2,1],None,None)


def test_veto_restores_current_ram_reservation_but_keeps_earlier(monkeypatch):
    from agents.sherlock import main
    m=implementation();a=actor(m);a.cfg.ram=True;a._overkill=lambda *args:False
    seen=[]
    def ram(ctx,uid,mask,points,rammed,margin):
        seen.append((uid,set(rammed)));rammed.add(uid);return None
    monkeypatch.setattr(main.rules,'ram_move',ram)
    a.belief.point_tiles=context()['point_tiles']
    a._act(138,{'match_steps':37});event=a.candidate.copy()
    event.update(uid=1,sap=[2.,2.,1.],energy=53.,position=[0,1])
    a.collect=False;a.intervention=event;seen.clear()
    a._act(138,{'match_steps':37})
    assert seen==[(0,set()),(1,{0}),(2,{0})]
    assert event['rule_origin']=='rule_override'
