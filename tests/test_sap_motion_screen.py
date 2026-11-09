"""Changed Motion runner contracts only; no model construction or game execution."""
import copy
import math
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import sap_motion_eval as s


def test_new_profile_and_disjoint_fixed_matrix():
    assert s.PROFILE == "sap_motion_screen_20261109"
    assert s.COHORTS == {"panel":list(range(9942000,9942020)),
                         "direct":list(range(9942100,9942120))}
    assert s.keys("off_solution") == s.keys("on_solution")
    assert len(s.keys("on_direct")) == 40
    assert {seed for seed,_ in s.keys("on_direct")} == set(s.COHORTS["direct"])
    assert {seed for seed,_ in s.keys("off_solution")} == set(s.COHORTS["panel"])
    assert s.TECH_KEYS == ((831006,"player_1"),(831000,"player_0"))


def test_unchanged_integer_gates_use_new_whole_map_cohorts():
    rows={}
    for job in s.JOBS:
        rows[job]=[]
        for i,(seed,side) in enumerate(s.keys(job)):
            win=i<(24 if job=="on_direct" else 20)
            changes=int(job!="off_solution" and i<10)
            rows[job].append(dict(seed=seed,side=side,steps=303,point_counting_version=2,
                our_wins=2 if win else 1,opp_wins=1 if win else 2,result=float(win),
                our_points=100,opp_points=100,caught_errors=0,leading={"changes":changes},
                observed_changes=changes))
    result=s.summarize(rows)
    assert result["gates"] == dict(exposure=True,solution=True,direct=True)
    assert result["games"]==120 and result["exposed_panel_maps"]==5
    assert result["direct"]["score"]==.6 and result["promotion"] is False
    rows["on_direct"][0].update(our_wins=1,opp_wins=1,result=.5)
    assert s.summarize(rows)["gates"]["direct"] is False
    rows["off_solution"][0]["seed"]=9940000
    with pytest.raises(ValueError,match="game key"):s.summarize(rows)


def test_factory_uses_motion_class_and_identical_explicit_config(monkeypatch,tmp_path):
    calls=[]
    class Fake:
        def __init__(self,player,**kw):
            calls.append((player,kw));self.cfg=kw["cfg"]
            self.training=False;self.epsilon=0;self.learn_enabled=False
            self.extra_q=[None]*35;self.feat_dim=79;self.n_actions=6;self.cnn_policy=None
        def set_to_eval_mode(self):pass
    def cfg(path,flags):
        assert flags==["frozen=false"]
        return SimpleNamespace(frozen=False,canonical=True)
    monkeypatch.setitem(sys.modules,"scripts.par_eval",SimpleNamespace(build_cfg=cfg))
    monkeypatch.setitem(sys.modules,"scripts.sap_motion_agent",SimpleNamespace(SapMotionAgent=Fake))
    def wrong_factory(*args,**kwargs):raise AssertionError("Old Leading factory selected")
    monkeypatch.setitem(sys.modules,"scripts.sap_leading_agent",SimpleNamespace(SapLeadingAgent=wrong_factory))
    a=dict(root=str(tmp_path),config=dict(frozen=False,canonical=True))
    off,on=s.make_agent(a,False),s.make_agent(a,True)
    assert [kw["lead_enabled"] for _,kw in calls]==[False,True]
    assert all(player=="player_0" and kw["train"] is False and kw["seed"]==0 for player,kw in calls)
    assert calls[0][1]["agent_path"]==calls[1][1]["agent_path"]
    assert vars(off.cfg)==vars(on.cfg)==a["config"]
    assert off.autosave_on_terminate is on.autosave_on_terminate is False


def frame(step,pos,*,energy=20,match=0,mirrored=False):
    return (step,step,match,mirrored,{7:(pos,energy)})


@pytest.mark.parametrize("end,category",[((4,2),0),((3,3),1),((2,2),2),((3,1),3),((3,2),4)])
def test_three_public_frames_count_relative_class_once(end,category):
    history=[];counts=[0]*5
    for record in (frame(1,(2,2)),frame(2,(3,2)),frame(3,end)):
        history,counts=s.observe_motion(history,record,counts,3)
    assert counts==[int(i==category) for i in range(5)]
    assert len(history)==2


@pytest.mark.parametrize("fault",["gap","match","mirror","uid_missing","negative","low_energy","nan","jump"])
def test_missing_or_invalid_transition_never_creates_label(fault):
    first=frame(1,(2,2));middle=frame(2,(3,2));last=frame(3,(4,2))
    if fault=="gap":last=frame(4,(4,2))
    if fault=="match":last=frame(3,(4,2),match=1)
    if fault=="mirror":last=frame(3,(4,2),mirrored=True)
    if fault=="uid_missing":middle=(*middle[:4],{})
    if fault=="negative":last=frame(3,(4,2),energy=-1)
    if fault=="low_energy":middle=frame(2,(3,2),energy=2)
    if fault=="nan":middle=frame(2,(3,2),energy=float("nan"))
    if fault=="jump":last=frame(3,(5,2))
    history,counts=s.observe_motion([first,middle],last,[0]*5,3)
    assert counts==[0]*5
    history,counts=s.observe_motion(history,None,[32,0,0,0,0],3)
    assert history==[] and counts==[32,0,0,0,0]


def case(mirrored=False):
    before=np.array([[0,0,0],[5,2,0],[5,2,0]])
    if mirrored:before[:,1:]=-before[:,1:][:,::-1]
    ctx=dict(ally_ids=np.array([2,1]),ally_pos=np.array([[0,0],[1,2],[1,2]]),ally_ene=[20,40,40],
        W=6,H=6,sap_cost=20,sap_range=4,move_cost=3,enemy_coords=np.array([[3,2]]),
        enemy_vis_ids=[7],enemy_energies=[20],passable=np.ones((6,6),bool))
    return before,ctx,np.ones((6,6),bool),frame(9,(2,2),mirrored=mirrored),frame(10,(3,2),mirrored=mirrored)


@pytest.mark.parametrize("mirrored",[False,True])
def test_posterior_uncertainty_and_smallest_uid_are_independently_reconstructed(mirrored):
    before,ctx,sensor,previous,current=case(mirrored)
    out,eligible=s.expected_action(before,ctx,sensor,previous,current,.25,True,mirrored,[32,0,0,0,0])
    assert [c["uid"] for c in eligible]==[1,2]
    assert out[1].tolist()==([5,0,-3] if mirrored else [5,3,0])
    assert np.array_equal(out[2],before[2])
    c=eligible[0];prob=np.array([33,1,1,1,1])/37;g=np.array([.75,0,-.25,0,-.75])
    mu=float(prob@g);var=float((prob@(g*g)-mu*mu)/38)
    assert c["counts"]==[32,0,0,0,0] and c["sample_count"]==32
    assert c["probabilities"]==pytest.approx(prob)
    assert c["focus_gains"]==pytest.approx(g)
    assert c["mean"]==pytest.approx(mu) and c["variance"]==pytest.approx(var)
    assert c["lower_bound"]==pytest.approx(mu-2*math.sqrt(var))


@pytest.mark.parametrize("counts,enabled",[([31,0,0,0,0],True),([0,0,0,0,32],True),([32,0,0,0,0],False)])
def test_low_support_unfavorable_or_off_preserves_original(counts,enabled):
    before,ctx,sensor,previous,current=case()
    out,eligible=s.expected_action(before,ctx,sensor,previous,current,.25,enabled,False,counts)
    assert not eligible and np.array_equal(out,before)


def test_known_obstacle_blocks_but_hidden_passability_is_not_used():
    _,ctx,sensor,_,_=case();ctx["passable"][3,3]=False
    a=s.motion_estimate(ctx,sensor,7,(3,2),(4,2),(1,0),.25,[32,0,0,0,0])
    assert a["blocked_classes"]==[1] and a["next_positions"][1]==[3,2]
    sensor[3,3]=False
    b=s.motion_estimate(ctx,sensor,7,(3,2),(4,2),(1,0),.25,[32,0,0,0,0])
    assert b["blocked_classes"]==[] and b["unknown_classes"]==[1]
    assert b["next_positions"][1]==[3,3]


def test_other_visible_targets_can_veto_focus_gain_without_negative_unit_credit():
    before,ctx,sensor,previous,current=case()
    ctx.update(enemy_vis_ids=[7,8,9,10],enemy_coords=np.array([[3,2],[2,1],[2,2],[2,3]]),
               enemy_energies=[20,20,20,20])
    out,eligible=s.expected_action(before,ctx,sensor,previous,current,.25,True,False,[32,0,0,0,0])
    assert not eligible and np.array_equal(out,before)
    ctx["enemy_energies"]=[20,-1,-1,-1]
    out,eligible=s.expected_action(before,ctx,sensor,previous,current,.25,True,False,[32,0,0,0,0])
    assert eligible and not np.array_equal(out,before)


@pytest.mark.parametrize("fault",["counts","labels","mean","prior","wrong_uid","spurious_diagnostic"])
def test_live_motion_check_rejects_count_or_decision_diagnostic_mismatch(fault):
    before,ctx,sensor,previous,current=case()
    counts=[32,0,0,0,0]
    out,eligible=s.expected_action(before,ctx,sensor,previous,current,.25,True,False,counts)
    chosen={k:v for k,v in eligible[0].items() if k!="target"}
    chosen.update(step=10,match_step=10,match_idx=0,dropoff=.25,native_action=out[1].tolist())
    a=SimpleNamespace(motion_counts=np.array(counts),leading_stats={"motion_labels":32,"motion_forward":32},
                      leading_last=copy.deepcopy(chosen))
    s.check_motion(a,counts,eligible,current,.25,out)
    if fault=="counts":a.motion_counts[0]+=1
    if fault=="labels":a.leading_stats["motion_labels"]+=1
    if fault=="mean":a.leading_last["mean"]+=.01
    if fault=="prior":a.leading_last["probabilities"]=[1,0,0,0,0]
    if fault=="wrong_uid":a.leading_last["uid"]=2
    if fault=="spurious_diagnostic":eligible=[]
    with pytest.raises(ValueError):s.check_motion(a,counts,eligible,current,.25,out)


def test_owner_only_changes_worker_module():
    root=Path(__file__).resolve().parents[1]/"scripts"
    expected=(root/"sap_leading_owner.py").read_text().replace("sap_leading_eval","sap_motion_eval")
    assert (root/"sap_motion_owner.py").read_text()==expected
