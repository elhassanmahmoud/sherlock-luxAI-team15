"""Only changed Rank-Mean runner contracts; no model loads or game starts."""
import copy
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import rank_mean_eval as s


def test_fixed_new_profile_matrix_and_original_technical_keys():
    assert s.PROFILE=="rank_mean_screen_20261109"
    assert s.COHORTS=={"panel":list(range(9944000,9944020)),"direct":list(range(9944100,9944120))}
    assert s.keys("off_solution")==s.keys("on_solution")
    assert len(s.keys("on_direct"))==40
    assert {k[0] for k in s.keys("on_direct")}==set(s.COHORTS["direct"])
    assert {k[0] for k in s.keys("off_solution")}==set(s.COHORTS["panel"])
    assert s.TECH_KEYS==((831006,"player_1"),(831000,"player_0"))


def test_numpy_midranks_ignore_illegal_values_and_preserve_exact_ties():
    q=np.array([[[2,2,9,-20,0,0],[7,0,0,0,0,0]],
                [[1,3,-9,-20,0,0],[9,0,0,0,0,0]]],float)
    mask=np.array([[1,1,0,0,0,0],[1,0,0,0,0,0]],bool)
    rank=s.numpy_rank_mean(q,mask)
    assert rank.tolist()==[[.25,.75,-1,-1,-1,-1],[.5,-1,-1,-1,-1,-1]]
    same=np.zeros((36,1,6));same[:18,0,0]=100;same[18:,0,1]=1
    result=s.numpy_rank_mean(same,mask[:1])
    assert result[0,:2].tolist()==[.5,.5] and result.argmax(1).tolist()==[0]
    assert np.array_equal(result,s.numpy_rank_mean(same*3+100,mask[:1]))


@pytest.mark.parametrize("fault",["nan","empty_mask","shape"])
def test_numpy_reconstruction_fails_closed(fault):
    q=np.zeros((36,1,6));mask=np.ones((1,6),bool)
    if fault=="nan":q[0,0,5]=float("nan")
    if fault=="empty_mask":mask[:]=False
    if fault=="shape":q=q[:,:,:5]
    with pytest.raises(ValueError):s.numpy_rank_mean(q,mask)


def frame_case(enabled=True):
    ids=(5,2);feats={5:np.arange(79,dtype=np.float32),2:np.arange(79,dtype=np.float32)+1}
    masks={u:np.array([1,1,0,0,0,0],bool) for u in ids}
    ctx=dict(step=3,match_step=3);members=tuple(SimpleNamespace(feat_dim=79 if i==0 else 43) for i in range(36))
    q=np.zeros((36,2,6),np.float32);q[0,:,0]=100;q[1:,:,1]=1
    raw=q.mean(0);rank=np.tile([0+1/36,35/36,-1,-1,-1,-1],(2,1)).astype(np.float32)
    captures={"members":[[(np.stack([feats[u] for u in ids])[:,:m.feat_dim],q[i].copy())] for i,m in enumerate(members)],
              "aggregate":[(np.stack([feats[u] for u in ids]),rank.copy())] if enabled else []}
    diag=dict(step=3,ids=ids,masks=np.stack([masks[u] for u in ids]),member_q=q.copy(),raw_mean=raw.copy(),
              rank_mean=rank.copy(),raw_greedy=np.array([0,0]),rank_greedy=np.array([1,1]))
    agent=SimpleNamespace(rank_enabled=enabled,aggregation_members=members,
        _cache=(3,ctx,ids,feats,masks,{}),_prev_ctx=ctx,aggregation_last=diag if enabled else None)
    return agent,captures


def test_passive_forward_reconstruction_finds_changed_legal_proposals():
    a,c=frame_case()
    record=s.check_aggregation(a,c,3,3)
    assert record["proposal_changes"]==2 and record["ids"]==[5,2]
    assert record["raw_greedy"]==[0,0] and record["rank_greedy"]==[1,1]
    a,c=frame_case(False)
    assert s.check_aggregation(a,c,3,3)["proposal_changes"]==0


def test_off_never_computes_unused_ranks(monkeypatch):
    a,c=frame_case(False)
    def forbidden(*args,**kwargs):raise AssertionError("Unused OFF rank computation")
    monkeypatch.setattr(s,"numpy_rank_mean",forbidden)
    assert s.check_aggregation(a,c,3,3)["proposal_changes"]==0


@pytest.mark.parametrize("fault",["double_forward","missing_forward","features","diag_ids","diag_mask",
                                  "diag_q","aggregate","rank_greedy","raw_greedy","stale_cache"])
def test_passive_validation_rejects_real_capture_or_diagnostic_faults(fault):
    a,c=frame_case()
    if fault=="double_forward":c["members"][1]*=2
    if fault=="missing_forward":c["members"][1]=[]
    if fault=="features":c["members"][2][0][0][0,0]+=1
    if fault=="diag_ids":a.aggregation_last["ids"]=(2,5)
    if fault=="diag_mask":a.aggregation_last["masks"][0,0]=False
    if fault=="diag_q":a.aggregation_last["member_q"][0,0,0]+=1
    if fault=="aggregate":c["aggregate"][0][1][0,0]+=.1
    if fault=="rank_greedy":a.aggregation_last["rank_greedy"][0]=0
    if fault=="raw_greedy":a.aggregation_last["raw_greedy"][0]=1
    if fault=="stale_cache":a._cache=(2,*a._cache[1:])
    with pytest.raises(ValueError):s.check_aggregation(a,c,3,3)


def test_reset_needs_no_network_and_rejects_stale_diagnostic():
    a,c=frame_case();a.aggregation_last=None;c={"members":[[] for _ in range(36)],"aggregate":[]}
    assert s.check_aggregation(a,c,4,0)["proposal_changes"]==0
    a.aggregation_last={"step":3}
    with pytest.raises(ValueError):s.check_aggregation(a,c,4,0)


@pytest.mark.parametrize("enabled,wrong_remember",[(False,False),(True,False),(True,True)])
def test_instance_hooks_capture_real_mock_calls_once_and_restore(enabled,wrong_remember):
    a,fixture=frame_case(enabled)
    class Net:
        def __init__(self,width,output):self.feat_dim=width;self.output=output;self.hooks=[];self.calls=0
        def register_forward_hook(self,hook):
            self.hooks.append(hook)
            return SimpleNamespace(remove=lambda:self.hooks.remove(hook))
        def __call__(self,features):
            self.calls+=1
            output=self.output.copy()
            for hook in self.hooks:hook(self,(features,),output)
            return output
    a.aggregation_members=tuple(Net(m.feat_dim,fixture["members"][i][0][1]) for i,m in enumerate(a.aggregation_members))
    a.q=Net(79,fixture["aggregate"][0][1]) if enabled else a.aggregation_members[0]
    a.caught_errors=0;a.aggregation_stats={};a.param_est=SimpleNamespace(_prev={})
    def core(step,obs):
        features=np.stack([a._cache[3][u] for u in a._cache[2]])
        for m in a.aggregation_members:m(features[:,:m.feat_dim])
        if enabled:
            output=a.q(features)
            output[:,2:]=-np.inf  # Core can mutate the output after the passive capture.
            a.aggregation_stats.update(calls=1,proposal_changes=2,proposal_changed_steps=1)
        return np.zeros((16,3),int)
    def act(step,obs):
        result=a._act(step,obs);a.param_est._prev["act"]=result.copy()
        if wrong_remember:a.param_est._prev["act"][0,0]=1
        return result
    a._act=core;a.act=act
    if wrong_remember:
        with pytest.raises(ValueError,match="remember"):
            with s.hook_audit(a,lambda:None,technical=True):a.act(3,{"steps":3,"match_steps":3})
    else:
        with s.hook_audit(a,lambda:None,technical=True) as audit:
            a.act(3,{"steps":3,"match_steps":3})
            assert audit["frames"]==1 and audit["proposal_changed_steps"]==int(enabled)
            assert len(audit["last"]["aggregation"]["member_q"])==36
    assert a.act is act and a._act is core
    assert all(m.calls==1 and not m.hooks for m in a.aggregation_members)
    assert not a.q.hooks


def test_rank_factory_preserves_config_weights_and_all_original_members(monkeypatch,tmp_path):
    calls=[]
    class Fake:
        def __init__(self,player,**kw):
            calls.append(kw);self.cfg=kw["cfg"];self.rank_enabled=kw["rank_enabled"]
            self.training=False;self.epsilon=0;self.learn_enabled=False;self.cnn_policy=None
            self.feat_dim=79;self.n_actions=6;self.aggregation_members=tuple(object() for _ in range(36))
        def set_to_eval_mode(self):pass
    monkeypatch.setitem(sys.modules,"scripts.rank_mean_agent",SimpleNamespace(RankMeanAgent=Fake))
    monkeypatch.setitem(sys.modules,"scripts.par_eval",SimpleNamespace(build_cfg=lambda *_:SimpleNamespace(frozen=False)))
    def wrong(*args,**kwargs):raise AssertionError("Wrong old factory")
    monkeypatch.setitem(sys.modules,"scripts.sap_motion_agent",SimpleNamespace(SapMotionAgent=wrong))
    a=dict(root=str(tmp_path),config={"frozen":False})
    off,on=s.make_agent(a,False),s.make_agent(a,True)
    assert [c["rank_enabled"] for c in calls]==[False,True]
    assert calls[0]["agent_path"]==calls[1]["agent_path"]
    assert vars(off.cfg)==vars(on.cfg)==a["config"]
    assert off.autosave_on_terminate is on.autosave_on_terminate is False


def rows():
    result={}
    for job in s.JOBS:
        result[job]=[]
        for i,(seed,side) in enumerate(s.keys(job)):
            win=i<(24 if job=="on_direct" else 20);changed=int(job!="off_solution" and i<10)
            result[job].append(dict(seed=seed,side=side,steps=303,point_counting_version=2,caught_errors=0,
                our_wins=2 if win else 1,opp_wins=1 if win else 2,result=float(win),our_points=1,opp_points=1,
                aggregation=dict(calls=300 if job!="off_solution" else 0,proposal_changes=changed*2,
                    proposal_changed_steps=changed),observed_proposal_changed_steps=changed))
    return result


def test_proposal_exposure_gates_use_aggregation_not_final_action_claims():
    r=rows();summary=s.summarize(r)
    assert summary["gates"]==dict(exposure=True,solution=True,direct=True)
    assert summary["exposed_panel_maps"]==5 and summary["promotion"] is False
    r["on_direct"][0].update(our_wins=1,opp_wins=1,result=.5)
    assert s.summarize(r)["gates"]["direct"] is False
    r["on_solution"][0]["observed_proposal_changed_steps"]+=1
    with pytest.raises(ValueError):s.summarize(r)


def test_technical_needs_both_proposal_and_native_stream_divergence():
    games=[dict(mode=mode,seed=seed,side=side,steps=303,off_reproduced=not mode,
        observed_proposal_changed_steps=int(mode),native_divergent_frames=int(mode))
        for mode in (False,True) for seed,side in s.TECH_KEYS]
    s.check_technical(games)
    for key in ("observed_proposal_changed_steps","native_divergent_frames"):
        bad=copy.deepcopy(games)
        for r in bad:r[key]=0
        with pytest.raises(ValueError):s.check_technical(bad)


def test_owner_is_only_a_module_name_change():
    folder=Path(__file__).resolve().parents[1]/"scripts"
    assert (folder/"rank_mean_owner.py").read_text()==(folder/"sap_motion_owner.py").read_text().replace("sap_motion_eval","rank_mean_eval")
