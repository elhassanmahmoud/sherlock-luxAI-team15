from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest

from scripts.r3_v4_parent_source import materialize
from scripts.r3_v4_contact_study import panel
from scripts.r3_v4_contact_assess import diagnostic_report, fresh_report


@pytest.fixture(scope="module")
def contact_module(tmp_path_factory):
    root = Path(__file__).resolve().parents[1]
    historical = tmp_path_factory.mktemp("original_r3")
    materialize(root, historical)
    with pytest.MonkeyPatch.context() as paths:
        paths.syspath_prepend(str(historical))
        from scripts import r3_v4_contact_agent
        yield r3_v4_contact_agent


def obs(side=0, step=1):
    pos=np.zeros((2,5,2),dtype=int)
    pos[side]=[(3,3),(15,10),(10,8),(7,6),(8,5)]
    pos[1-side]=[(8,8),(15,10),(23,23),(-1,-1),(4,5)]
    mask=np.ones((2,5),dtype=bool)
    mask[side,3]=False
    mask[1-side,[1,4]]=False
    energy=np.full((2,5,1),25)
    energy[side,4]=-1
    return dict(units={"position":pos,"energy":energy},units_mask=mask,match_steps=step,sensor_mask=np.ones((24,24),bool))


@pytest.mark.parametrize("side",[0,1])
def test_visible_contact_includes_chebyshev_five_and_excludes_hidden_or_dead(side, contact_module):
    routing = contact_module.routing
    public=obs(side)
    live,near=routing(public,side)
    assert live.tolist()==[True,True,True,False,False]
    assert near.tolist()==[True,False,True,False,False]
    assert not routing(obs(side,0),side)[1].any()
    public["units_mask"][1-side]=False
    assert not routing(public,side)[1].any()


def test_world_action_feedback_stays_unmirrored_in_estimator_and_canonical_in_caches(contact_module):
    sync = contact_module.sync
    p=obs(1)
    ctx={"ally_pos":np.array([[20,20],[13,8]]),"enemy_coords":np.array([[18,21]]),"enemy_energies":np.array([40])}
    def actor():
        return SimpleNamespace(cfg=SimpleNamespace(dodge_verify=False,dodge_distrust=0,dodge_shape=False),
                    training=False,_pred_pending=[],_shape_pending=[],param_est=SimpleNamespace(_prev={"act":None}),
                    _prev_ctx=ctx,_prev_actions={0:0,1:0},_sap_hits={},_sap_unknown=set(),
                    belief=SimpleNamespace(mirrored=True),team_id=1)
    a=actor()
    played=np.array([[5,-1,2],[1,0,0]])
    sync(a,p,played,estimator=True)
    assert a.param_est._prev["act"].tolist()==played.tolist() and a._prev_actions=={0:5,1:2}
    assert a._sap_hits=={0:1}
    played[0]=0
    assert a.param_est._prev["act"][0].tolist()==[5,-1,2]
    a=actor()
    a.param_est._prev=None
    sync(a,p,played,estimator=False)
    assert a.param_est._prev is None


def test_route_keeps_entire_selected_parent_sap_row(monkeypatch, contact_module):
    from collections import Counter
    module = contact_module
    ContactAgent = module.ContactAgent
    parent=lambda rows:SimpleNamespace(act=lambda *args:np.array(rows),caught_errors=0)
    a=ContactAgent.__new__(ContactAgent)
    a.r3=parent([[5,2,1]]*5)
    a.v4=parent([[5,-1,-2]]*5)
    a.v4.v14=object()
    a.v4.student=object()
    a.counts=Counter()
    a.team=0
    seen=[]
    monkeypatch.setattr(module,"sync",lambda actor,obs,final,**kw:seen.append(np.copy(final)))
    final=a.act(1,obs())
    assert final.tolist()==[[5,-1,-2],[5,2,1],[5,-1,-2],[5,2,1],[5,2,1]]
    assert len(seen)==3 and all(np.array_equal(final,copy) for copy in seen)


def test_fresh_gate_requires_both_parents_and_the_same_maps():
    ks=panel("screen")
    assert len(ks)==len(set(ks))==352
    rows={k:dict(game=dict(game_win=int(k[0]=="contact"),our_wins=3 if k[0]=="contact" else 0)) for k in ks}
    assert fresh_report(rows)["passes"]
    for k in ks:
        if k[0]=="v4": rows[k]["game"]={"game_win":1,"our_wins":3}
    assert not fresh_report(rows)["passes"]


def test_diagnostic_requires_seven_wins_and_one_rescue_in_each_group():
    from scripts.r3_v4_contact_study import R3_LOSS,V4_LOSS
    rows,old={},{}
    def score(win):
        return {"game_win": int(win)}
    for s,t in (*R3_LOSS,*V4_LOSS):
        k=("solution92",s,f"player_{t}")
        old["r3",*k]=score((s,t) not in R3_LOSS)
        old["v4",*k]=score((s,t) not in V4_LOSS)
        rows["contact",*k]=dict(game=score((s,t) in V4_LOSS),routing={})
    assert not diagnostic_report(rows,old)["passes"]
    s,t=R3_LOSS[1]
    rows["contact","solution92",s,f"player_{t}"]["game"]={"game_win":1}
    assert diagnostic_report(rows,old)["passes"]
