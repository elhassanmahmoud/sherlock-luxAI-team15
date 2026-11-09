"""Synthetic comparison checks; no real weights or games."""
import copy
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.model import QNet
from scripts import threat_warmstart_compare as s
from scripts import threat_warmstart_compare_owner as owner


@pytest.fixture(autouse=True)
def no_archives(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("This synthetic test must not load a tensor archive")
    monkeypatch.setattr(torch, "load", forbidden)


@pytest.fixture
def models():
    base = QNet(79,6,256,True).state_dict()
    members = []
    for index in range(36):
        member = dict(base)
        member["body.0.bias"] = torch.full_like(base["body.0.bias"], float(index))
        members.append(member)
    cfg = AgentConfig().to_dict()
    cfg.update(use_sap=True,hidden=256,dueling=True,threat_feats=False,frozen=True)
    source = dict(q=members[0],target_q=members[0],ensemble=members[1:],ensemble_dims=[79]*35,
                  feature_dim=79,n_actions=6,cfg=cfg)
    expanded = copy.deepcopy(members[18])
    expanded["body.0.weight"] = torch.cat([members[18]["body.0.weight"],torch.zeros(256,22)],1)
    final = dict(q=expanded,feature_dim=101,n_actions=6,ensemble=[],cfg={"lr":999})
    return source, final, members


def test_exact_member_18_replacement_order_and_inference_config(models):
    source, final, original = models
    cp = s.mount(source,final,"control")
    assert len(cp["ensemble"]) == 35 and cp["ensemble_dims"] == [79]*35
    assert s.state_equal(cp["q"],final["q"])
    assert all(s.state_equal(a,b) for a,b in zip(cp["ensemble"],original[:18]+original[19:]))
    assert cp["cfg"] == dict(source["cfg"],threat_feats=True,frozen=False)
    assert "opt" not in cp and final["cfg"]["lr"] == 999
    v14 = s.mount(source,None,"v14")
    assert s.state_equal([v14["q"],*v14["ensemble"]],original)
    assert v14["cfg"] == dict(source["cfg"],frozen=False)
    assert source["cfg"]["frozen"] is True


@pytest.mark.parametrize("corruption", ["37_members","35_members","wrong_width","missing_key","wrong_dtype","wrong_actions","training_config"])
def test_malformed_mixed_copies_rejected(models,corruption):
    source,final,_ = models
    cp = s.mount(source,final,"control")
    if corruption == "37_members": cp["ensemble"].append(cp["ensemble"][0]); cp["ensemble_dims"].append(79)
    if corruption == "35_members": cp["ensemble"].pop(); cp["ensemble_dims"].pop()
    if corruption == "wrong_width": cp["ensemble_dims"][0] = 101
    if corruption == "missing_key": cp["q"].pop("adv.2.bias")
    if corruption == "wrong_dtype": cp["q"]["body.0.bias"] = cp["q"]["body.0.bias"].double()
    if corruption == "wrong_actions": cp["n_actions"] = 5
    if corruption == "training_config": cp["cfg"]["lr"] = 999
    with pytest.raises(ValueError): s.validate_model(cp,source["cfg"],"control")


def test_control_and_threat_added_column_contract(models):
    source,final,_ = models
    with pytest.raises(ValueError): s.mount(source,final,"threat")
    final["q"]["body.0.weight"][0,79] = 1
    with pytest.raises(ValueError): s.mount(source,final,"control")
    assert s.mount(source,final,"threat")["q"]["body.0.weight"][0,79] == 1


def test_real_tensor_suffix_equality_and_nonzero_regression():
    q = torch.nn.Linear(101,6); q.feat_dim = 101
    extra = torch.nn.Linear(79,6); extra.feat_dim = 79
    with torch.no_grad(): q.weight[:,79:] = 0
    agent = SimpleNamespace(q=q,extra_q=[extra]*35,device=torch.device("cpu"))
    states = np.ones((16,101),dtype=np.float32)
    masks = np.ones((16,6),dtype=bool); masks[:,0] = False
    widths = []
    handle = q.register_forward_pre_hook(lambda _m,args: widths.append(tuple(args[0].shape)))
    try:
        proof = s.equal_suffix_batches(agent,states,masks)
        assert [len(p["indices"]) for p in proof] == [1,8,16]
        assert widths == [(1,101),(1,101),(8,101),(8,101),(16,101),(16,101)]
        with torch.no_grad(): q.weight[0,79] = 1
        with pytest.raises(ValueError,match="member outputs differ"):
            s.equal_suffix_batches(agent,states,masks)
    finally: handle.remove()


def test_legal_argmax_matches_core_even_below_minus_one_billion():
    from scripts.experiment import state_sha256
    q = torch.nn.Linear(101,6); q.feat_dim = 101
    extra = torch.nn.Linear(79,6); extra.feat_dim = 79
    with torch.no_grad():
        for model in (q,extra): model.weight.zero_(); model.bias.fill_(-2e9)
    agent = SimpleNamespace(q=q,extra_q=[extra]*35,device=torch.device("cpu"))
    states = np.ones((16,101),dtype=np.float32)
    masks = np.zeros((16,6),dtype=bool); masks[:,1] = True
    proof = s.equal_suffix_batches(agent,states,masks)
    for record in proof:
        assert record["greedy_sha256"] == state_sha256(torch.ones(len(record["indices"]),dtype=torch.int64))


def test_fixed_first_exposed_rows_are_not_silently_replaced():
    q = torch.nn.Linear(101,6); q.feat_dim = 101
    extra = torch.nn.Linear(79,6); extra.feat_dim = 79
    with torch.no_grad(): q.weight[:,79:] = 0
    agent = SimpleNamespace(q=q,extra_q=[extra]*35,device=torch.device("cpu"))
    states = np.ones((17,101),dtype=np.float32)
    masks = np.ones((17,6),dtype=bool); masks[0] = False
    with pytest.raises(ValueError,match="legal next action"):
        s.equal_suffix_batches(agent,states,masks)


def fake_admission(tmp_path,monkeypatch):
    monkeypatch.setattr(s,"ROOT",tmp_path)
    return dict(stage="performance",out=str(tmp_path/"experiments/analysis"/s.PROFILE/"performance_v1"),
                python="/admitted/python",inputs={},models={r:str(tmp_path/(r+".pth")) for r in s.ROLES},
                cohorts={k:str(tmp_path/(k+".json")) for k in ("solution","direct_v14","direct_control")})


def test_fixed_five_jobs_two_sides_and_self_path_config_binding(tmp_path,monkeypatch):
    a = fake_admission(tmp_path,monkeypatch)
    assert len(s.JOBS) == 5 and len(set(s.JOBS)) == 5
    for name in s.JOBS:
        command = s.performance_command(a,name); spec = s.job_spec(a,name)
        assert command[command.index("--workers")+1] == "1" and "--set" not in command
        assert command[command.index("--weights")+1] == a["models"][spec["role"]]
    assert s.job_spec(a,"threat_v14")["opponent"] == "self:"+a["models"]["v14"]
    assert s.job_spec(a,"threat_control")["opponent"] == "self:"+a["models"]["control"]


def test_three_fixed_cohorts_reject_wrong_size_duplicate_and_overlap(tmp_path,monkeypatch):
    a = fake_admission(tmp_path,monkeypatch)
    a["seed_acceptance"] = "synthetic-acceptance"
    cohorts = {"solution":list(range(9946000,9946020)),"direct_v14":list(range(9946100,9946120)),
               "direct_control":list(range(9946200,9946220))}
    def read(_a,path):
        if path == a["seed_acceptance"]:
            return dict(status="PASS",profile=s.PROFILE,cohorts=cohorts,no_observed_conflicts=True,
                        limitations="synthetic fixture",files={"synthetic-evidence":"fixture-sha"})
        return cohorts[next(k for k,v in a["cohorts"].items() if v == path)]
    monkeypatch.setattr(s,"read_bound",read)
    monkeypatch.setattr(s,"bound",lambda _a,p:p)
    monkeypatch.setattr(s,"digest",lambda _p:"fixture-sha")
    assert s.fixed_cohorts(a) == cohorts
    original = cohorts["direct_control"][:]
    for bad in (original[:-1],original[:-1]+[original[0]],[cohorts["solution"][0]]+original[1:]):
        cohorts["direct_control"] = bad
        with pytest.raises(ValueError): s.fixed_cohorts(a)


def test_historical_training_validators_do_not_readmit_old_source(tmp_path,monkeypatch):
    from scripts import threat_warmstart as warm
    a = fake_admission(tmp_path,monkeypatch)
    training = dict(profile=warm.PROFILE,stage="training",source={"head":"historical-training"},out=str(tmp_path))
    a["protected"] = {"synthetic-protected":"fixture-sha"}
    def save(name,value):
        path = tmp_path/name; s.write(path,value); a["inputs"][str(path)] = s.digest(path)
        return str(path)
    a["training_admission"] = save("training.json",training)
    sha = s.digest(a["training_admission"])
    receipts = {}; models = {}
    for role in ("control","threat"):
        (tmp_path/role).mkdir()
        receipt = save(role+"/receipt.json",{"synthetic":True})
        models[role] = save(role+"/final.pth",{"synthetic":True})  # Text witness, not a tensor archive.
        receipts[role] = dict(path=receipt,sha256=s.digest(receipt))
    owner = save("state.json",dict(status="complete",active=[],admission_sha256=sha,source=training["source"],
        stage="training",jobs={r:dict(returncode=0) for r in ("control","threat")},receipts=receipts))
    a["training_completion"] = save("closure.json",dict(status="COMPLETE_TRAINING_NO_STRENGTH_CLAIM",profile=warm.PROFILE,
        source=training["source"],admission_sha256=sha,state_sha256=s.digest(owner),models=models,
        model_sha256={r:s.digest(p) for r,p in models.items()},source_and_input_bindings_valid=True,
        protected=a["protected"],actual=dict(technical_games=4,prefill_games=80,learning_games=800,optimizer_updates=120000)))
    monkeypatch.setattr(s,"FINAL_SHA",{r:s.digest(p) for r,p in models.items()})
    calls = []
    def forbid_readmission(*_args): raise AssertionError("Do not re-admit historical source")
    monkeypatch.setattr(warm,"admission",forbid_readmission)
    monkeypatch.setattr(warm,"validate_final_receipt",lambda p,t,h,r:calls.append((t,h,r)))
    assert set(s.accepted_training(a)) == {"control","threat"}
    assert calls == [(training,sha,"control"),(training,sha,"threat")]


def rows_for(a,name,seeds,*,wins=23,draws=17):
    results = [1.]*wins+[.5]*draws+[0.]*(40-wins-draws)
    result_rows = []
    for (seed,side),result in zip(((seed,side) for seed in seeds for side in ("player_0","player_1")),results):
        ours,opps = ((2,1) if result == 1 else (1,1) if result == .5 else (1,2))
        result_rows.append(dict(seed=seed,side=side,opponent=s.job_spec(a,name)["opponent"],result=result,
            game_win=int(result==1),point_win=result,steps=303,point_counting_version=2,
            our_wins=ours,opp_wins=opps,our_points=ours*10,opp_points=opps*10))
    return pd.DataFrame(result_rows)


def test_actual_win_gate_rejects_23_wins_even_with_17_draws(tmp_path,monkeypatch):
    a = fake_admission(tmp_path,monkeypatch)
    # Synthetic IDs only: no proposed or loaded performance-card list.
    seeds = list(range(20)); frames = {n:rows_for(a,n,seeds) for n in s.JOBS}
    frames["v14_solution"] = rows_for(a,"v14_solution",seeds,wins=22,draws=18)
    frames["control_solution"] = rows_for(a,"control_solution",seeds,wins=22,draws=18)
    monkeypatch.setattr(s,"validate_csv",lambda _a,name:frames[name])
    monkeypatch.setattr(s,"digest",lambda _p:"synthetic-not-a-file-hash")
    report = s.analyze(a)
    assert report["gates"]["solution_v14"] and report["gates"]["solution_control"]
    assert not report["gates"]["direct_v14"] and not report["nominated"]
    for n in ("threat_v14","threat_control"): frames[n] = rows_for(a,n,seeds,wins=24,draws=16)
    assert s.analyze(a)["nominated"] is True


def test_csv_duplicate_missing_side_and_point_version_rejected(tmp_path,monkeypatch):
    a = fake_admission(tmp_path,monkeypatch); seeds = list(range(20))
    monkeypatch.setattr(s,"read_bound",lambda *_:seeds)
    frame = rows_for(a,"threat_v14",seeds)
    monkeypatch.setattr(pd,"read_csv",lambda _p:frame)
    assert len(s.validate_csv(a,"threat_v14")) == 40
    frame.loc[1,"side"] = "player_0"
    with pytest.raises(ValueError): s.validate_csv(a,"threat_v14")
    frame.loc[1,"side"] = "player_1"; frame.loc[2,"point_counting_version"] = 1
    with pytest.raises(ValueError): s.validate_csv(a,"threat_v14")


def test_exclusive_publication_changed_input_and_output_escape(tmp_path,monkeypatch):
    a = fake_admission(tmp_path,monkeypatch)
    witness = tmp_path/"bound.json"; s.write(witness,{"status":"synthetic"})
    a["inputs"][str(witness)] = s.digest(witness)
    assert s.read_bound(a,witness) == {"status":"synthetic"}
    with pytest.raises(FileExistsError): s.write(witness,{"status":"overwrite"})
    witness.write_text("changed")
    with pytest.raises(ValueError): s.bound(a,witness)
    a["out"] = str(tmp_path/"agents/sherlock/weights")
    with pytest.raises(ValueError): s.output_dir(a)


@pytest.mark.parametrize("lingers",[False,True])
def test_owned_pool_cleanup_is_bounded_and_never_signals(monkeypatch,lingers):
    from scripts import ensemble_diversity_supervisor as lifecycle
    child = dict(process=SimpleNamespace(poll=lambda:0),pgid=98123)
    clock = [0.]; calls = []
    monkeypatch.setattr(owner.time,"monotonic",lambda:clock[0])
    monkeypatch.setattr(owner.time,"sleep",lambda seconds:clock.__setitem__(0,clock[0]+seconds))
    def alive(pgid):
        assert pgid == 98123
        return lingers or clock[0] < .1
    def signal_forbidden(*_args): raise AssertionError("Natural cleanup must not signal any group")
    monkeypatch.setattr(lifecycle,"group_alive",alive)
    monkeypatch.setattr(lifecycle.os,"killpg",signal_forbidden)
    if lingers:
        with pytest.raises(ValueError,match="cleanup deadline"):
            owner.await_group_exit(child,lambda:calls.append(clock[0]),timeout=.2)
        assert .2 <= clock[0] < .3
    else:
        owner.await_group_exit(child,lambda:calls.append(clock[0]),timeout=.2)
        assert clock[0] == .1
    assert calls
