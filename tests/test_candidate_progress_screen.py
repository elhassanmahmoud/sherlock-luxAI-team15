"""Synthetic runner contracts; no released weights or real engine games."""
import copy
import hashlib
import importlib
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.model import QNet


def runner():
    assert importlib.util.find_spec("scripts.candidate_progress_eval") is not None, "Runner not implemented"
    return importlib.import_module("scripts.candidate_progress_eval")


@pytest.fixture(autouse=True)
def forbid_archive_load(monkeypatch):
    def forbidden(*args, **kwargs): raise AssertionError("No real tensor archive in synthetic suite")
    monkeypatch.setattr(torch, "load", forbidden)


@pytest.fixture
def source():
    base = QNet(79, 6, 256, True).state_dict()
    members = []
    for i in range(36):
        member = dict(base)
        member["body.0.bias"] = torch.full_like(base["body.0.bias"], float(i))
        members.append(member)
    cfg = AgentConfig().to_dict()
    cfg.update(hidden=256, dueling=True, use_sap=True, threat_feats=False, frozen=True,
               cand_rescue=True, rescue_after=30, zone_rescue=False)
    cfg.pop("cand_stall_rescue", None)  # Historical checkpoint predates this field.
    return dict(cfg=cfg, q=members[0], target_q=members[0], ensemble=members[1:],
                ensemble_dims=[79]*35, feature_dim=79, n_actions=6)


def test_mount_preserves_all_36_tensor_members_and_only_changes_eval_flags(source):
    s = runner()
    off, on = [s.mount(source, role) for role in ("off", "on")]
    for cp, enabled in ((off, False), (on, True)):
        assert cp["cfg"] == dict(source["cfg"], frozen=False, cand_stall_rescue=enabled)
        assert s.state_equal([cp["q"], *cp["ensemble"]], [source["q"], *source["ensemble"]])
        assert s.state_equal(cp["target_q"], source["target_q"])
    assert source["cfg"]["frozen"] is True and "cand_stall_rescue" not in source["cfg"]


@pytest.mark.parametrize("corruption", ["count", "width", "nonfinite", "wrong_fallback"])
def test_mount_rejects_wrong_original_or_method(source, corruption):
    s = runner()
    if corruption == "count": source["ensemble"].pop()
    if corruption == "width": source["ensemble_dims"][0] = 101
    if corruption == "nonfinite": source["q"]["body.0.weight"][0, 0] = float("nan")
    if corruption == "wrong_fallback": source["cfg"]["rescue_after"] = 0
    with pytest.raises(ValueError): s.mount(source, "on")


def archived(seed, side):
    summary = dict(seed=seed, side=side, steps=303, point_counting_version=2,
        reset_steps=3, decision_steps=300, our_wins=1, opp_wins=2, our_points=100,
        opp_points=200, result=0., matches=[dict(match_idx=i, points=[1,2], cumulative_wins=[0,i+1]) for i in range(3)],
        action_sha256="a"*64, caught_errors=0, config={"frozen":False})
    return dict(key=dict(seed=seed,side=side), observed=summary, unobserved=copy.deepcopy(summary),
        passivity={"action_sha256":True}, baseline_reproduction={"result":True}, complete=True)


def test_baseline_selects_exact_archived_key_and_rejects_nonpassive_manifest():
    s = runner(); record = archived(9946007, "player_0")
    doc = dict(status="complete", games=[record])
    assert s.baseline_row(doc, 9946007, "player_0")["action_sha256"] == "a"*64
    with pytest.raises(ValueError): s.baseline_row(doc, 831006, "player_1")
    record["unobserved"]["action_sha256"] = "b"*64
    with pytest.raises(ValueError): s.baseline_row(doc, 9946007, "player_0")


def technical_rows():
    rows = []
    for role in ("off", "on"):
        for seed, side in ((9946007,"player_0"),(831006,"player_1")):
            rows.append(dict(role=role, **archived(seed,side)["observed"],
                cand_stall_early_unit_steps=int(role=="on"), baseline_equal=role=="off"))
            if role == "on": rows[-1]["action_sha256"] = "b"*64
    return rows


@pytest.mark.parametrize("fault", [None, "off", "no_exposure", "no_divergence", "incomplete", "caught"])
def test_technical_gate_requires_real_off_reproduction_and_on_effect(fault):
    s = runner(); rows = technical_rows()
    if fault == "off": rows[0]["baseline_equal"] = False
    if fault == "no_exposure":
        for row in rows[2:]: row["cand_stall_early_unit_steps"] = 0
    if fault == "no_divergence":
        for row in rows[2:]: row["action_sha256"] = "a"*64
    if fault == "incomplete": rows[-1]["steps"] = 302
    if fault == "caught": rows[-1]["caught_errors"] = 1
    if fault:
        with pytest.raises(ValueError): s.check_technical({"games":rows})
    else: s.check_technical({"games":rows})


def fake_admission(tmp_path, monkeypatch):
    s = runner(); monkeypatch.setattr(s, "ROOT", tmp_path)
    return dict(stage="performance", out=str(tmp_path/"experiments/analysis"/s.PROFILE/"performance_v1"),
        inputs={}, python="/python", models={r:str(tmp_path/(r+".pth")) for r in ("off","on")},
        cohorts={r:str(tmp_path/(r+".json")) for r in ("solution","direct")})


def test_performance_commands_have_three_fixed_jobs_and_bound_opponent_configs(tmp_path, monkeypatch):
    s = runner(); a = fake_admission(tmp_path, monkeypatch)
    assert s.JOBS == ("off_solution", "on_solution", "on_off")
    for name in s.JOBS:
        cmd = s.performance_command(a,name)
        assert cmd[cmd.index("--workers")+1] == "1" and "--set" not in cmd
    cmd = s.performance_command(a,"on_off")
    assert cmd[cmd.index("--weights")+1] == a["models"]["on"]
    assert cmd[cmd.index("--opponents")+1] == "self:"+a["models"]["off"]
    assert cmd[cmd.index("--seed-list")+1] == a["cohorts"]["direct"]


def frame(a, name, wins=23, draws=17):
    s = runner(); rows = []
    for i, score in enumerate([1.]*wins+[.5]*draws+[0.]*(40-wins-draws)):
        ours, theirs = (2,1) if score == 1 else (1,1) if score == .5 else (1,2)
        rows.append(dict(seed=i//2,side=("player_0","player_1")[i%2],opponent=s.job_spec(a,name)["opponent"],
            result=score,game_win=int(score==1),point_win=score,steps=303,point_counting_version=2,
            our_points=ours*10,opp_points=theirs*10,our_wins=ours,opp_wins=theirs))
    return pd.DataFrame(rows)


def test_actual_win_gate_rejects_draws_and_accepts_exact_24(tmp_path, monkeypatch):
    s = runner(); a = fake_admission(tmp_path,monkeypatch)
    frames = {n:frame(a,n) for n in s.JOBS}
    monkeypatch.setattr(s,"validate_csv",lambda _a,n:frames[n])
    monkeypatch.setattr(s,"digest",lambda _p:"fixture-sha")
    result = s.analyze(a)
    assert result["games"] == 120 and result["counts"]["on_off"]["wins"] == 23
    assert not result["nominated"] and result["direct"]["winrate"] == .7875
    frames["on_off"] = frame(a,"on_off",24,16)
    assert s.analyze(a)["nominated"]
    frames["off_solution"] = frame(a,"off_solution",24,16)
    assert not s.analyze(a)["nominated"]


@pytest.mark.parametrize("fault", [None,"duplicate","v1","result","point_result"])
def test_csv_requires_exact_complete_consistent_games(tmp_path, monkeypatch, fault):
    s = runner(); a = fake_admission(tmp_path,monkeypatch); df = frame(a,"on_off")
    monkeypatch.setattr(pd,"read_csv",lambda _p:df)
    monkeypatch.setattr(s,"read_bound",lambda *_:list(range(20)))
    if fault == "duplicate": df.loc[1,"side"] = "player_0"
    if fault == "v1": df.loc[0,"point_counting_version"] = 1
    if fault == "result": df.loc[0,"our_wins"] = 0
    if fault == "point_result": df.loc[0,"point_win"] = 0.
    if fault:
        with pytest.raises(ValueError): s.validate_csv(a,"on_off")
    else: assert len(s.validate_csv(a,"on_off")) == 40


def test_native_wrapper_hashes_both_actions_and_keeps_v2_match_results():
    s = runner()
    from scripts.targeting_probe import action_bytes
    obs = {p:dict(match_steps=100,team_points=np.array([4,3]),team_wins=np.array([0,0])) for p in ("player_0","player_1")}
    nxt = {p:dict(match_steps=0,team_points=np.array([0,0]),team_wins=np.array([1,0])) for p in obs}
    actions = {p:np.array([[1,0,0]],dtype=int) for p in obs}
    class Env:
        def reset(self, seed): return obs, {}
        def step(self, sent):
            assert sent is actions
            return nxt, {}, {p:False for p in obs}, {p:False for p in obs}, {"final_state":SimpleNamespace(relic_nodes_map_weights=np.array([[1]]),
                relic_nodes_mask=np.array([True,True]),units_mask=np.array([[True],[False]]),
                units=SimpleNamespace(position=np.array([[[0,0]],[[0,0]]]),energy=np.array([[[0]],[[0]]])))}
    wrapped = s.NativeTrace(Env(),"player_0")
    wrapped.reset(seed=1); wrapped.step(actions)
    assert wrapped.native.hexdigest() == hashlib.sha256(action_bytes(actions)).hexdigest()
    assert wrapped.matches == [dict(match_idx=0,points=[5,3],cumulative_wins=[1,0])]


def test_historical_missing_default_fields_normalize_without_changing_policy(source):
    s = runner()
    source["cfg"].pop("art_splash_in_training", None)
    cp = s.mount(source,"off")
    assert cp["cfg"]["art_splash_in_training"] is False
    assert s.inference_config(source["cfg"],"off") == cp["cfg"]
    old = dict(source["cfg"])
    for key in ("zone_rescue","art_move_guard","rescue_in_training","fog_unknown_reward_neutral","point_pair_swap"):
        old.pop(key,None)
    assert s.inference_config(old,"off") == cp["cfg"]
    old["point_pair_swap"] = True
    assert s.inference_config(old,"off") != cp["cfg"]


@pytest.mark.parametrize("errors", [(0,0),(1,0),(0,1)])
def test_par_eval_rejects_caught_errors_on_either_player(errors):
    from scripts import par_eval
    assert hasattr(par_eval,"require_no_agent_errors"), "par_eval drops caught errors"
    agent, opponent = [SimpleNamespace(caught_errors=e) for e in errors]
    if any(errors):
        with pytest.raises(RuntimeError): par_eval.require_no_agent_errors(agent,opponent)
    else:
        par_eval.require_no_agent_errors(agent,opponent)
        par_eval.require_no_agent_errors(object(),object())  # Baselines without this counter.


def test_fixed_cohort_admission_rejects_wrong_seed_even_with_matching_self_report(tmp_path,monkeypatch):
    s = runner(); a = fake_admission(tmp_path,monkeypatch)
    a["seed_acceptance"] = "acceptance"
    cohorts = {"solution":list(range(9948000,9948020)),"direct":list(range(9948100,9948120))}
    def read(_a,path):
        if path == "acceptance":
            return dict(status="PASS",profile=s.PROFILE,cohorts=cohorts,no_observed_conflicts=True,
                        limitations="synthetic",files={"evidence":"sha"})
        return cohorts[next(k for k,v in a["cohorts"].items() if v == path)]
    monkeypatch.setattr(s,"read_bound",read)
    monkeypatch.setattr(s,"bound",lambda _a,p:p)
    monkeypatch.setattr(s,"digest",lambda _p:"sha")
    assert s.fixed_cohorts(a) == cohorts
    cohorts["direct"][0] = 9946007
    with pytest.raises(ValueError): s.fixed_cohorts(a)


def test_real_par_eval_worker_propagates_game_error_counter_before_publishing(monkeypatch):
    import sys
    import agents.sherlock.main as core
    from scripts import common, par_eval
    class FakeAgent:
        def __init__(self,*args,**kwargs): self.caught_errors=0
        def set_to_eval_mode(self): pass
    class FakeEnv:
        def __init__(self,**kwargs): pass
        def close(self): pass
    def game(_env,agent,_opp,*args,**kwargs):
        agent.caught_errors += 1
        return {"result":1.}
    monkeypatch.setitem(sys.modules,"luxai_s3.wrappers",SimpleNamespace(LuxAIS3GymEnv=FakeEnv))
    monkeypatch.setattr(torch,"load",lambda *args,**kwargs:{})
    monkeypatch.setattr(core,"Agent_x",FakeAgent)
    monkeypatch.setattr(par_eval,"limit_threads",lambda:None)
    monkeypatch.setattr(par_eval,"build_cfg",lambda *args:None)
    monkeypatch.setattr(common,"make_opponent",lambda *args:object())
    monkeypatch.setattr(common,"play_game",game)
    with pytest.raises(RuntimeError): par_eval._worker(("synthetic.pth",[],[0],["solution92"]))
