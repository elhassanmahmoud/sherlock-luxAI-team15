"""Synthetic runner/admission contracts; never load a model or start an env."""
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import sap_leading_eval as s


@pytest.fixture(autouse=True)
def no_model_loads(monkeypatch):
    import agents.sherlock.main as core
    def forbidden(*args,**kwargs):raise AssertionError("No real model or tensor load in synthetic runner tests")
    monkeypatch.setattr(core,"QNet",forbidden)
    monkeypatch.setattr(core.torch,"load",forbidden)


def rows():
    result = {}
    for job in s.JOBS:
        data = []
        for index, (seed, side) in enumerate(s.keys(job)):
            win = index < (24 if job == "on_direct" else 20)
            changes = int(job != "off_solution" and index < 10)
            data.append(dict(seed=seed, side=side, steps=303, point_counting_version=2,
                our_wins=2 if win else 1, opp_wins=1 if win else 2, result=float(win),
                our_points=100, opp_points=100, caught_errors=0,
                leading=dict(changes=changes), observed_changes=changes))
        result[job] = data
    return result


def test_fixed_120_matrix_and_exact_gates():
    result = s.summarize(rows())
    assert result.get("eligible_for_separate_design") is True
    assert result["games"] == 120 and result["exposed_panel_maps"] == 5
    assert result["direct"]["score"] == .6
    assert result["gates"] == dict(exposure=True, solution=True, direct=True)


@pytest.mark.parametrize("change,gate", [("exposure", "exposure"), ("solution", "solution"), ("direct", "direct")])
def test_each_gate_can_fail_without_extra_games(change, gate):
    data = rows()
    if change == "exposure":
        for r in data["on_solution"][8:10]: r["leading"]["changes"] = r["observed_changes"] = 0
    else:
        r = data["on_solution" if change == "solution" else "on_direct"][0]
        r.update(our_wins=1, opp_wins=1, result=.5)
    result = s.summarize(data)
    assert result["gates"][gate] is False
    assert result["eligible_for_separate_design"] is False


def test_draws_are_half_score_and_not_points():
    data = rows(); r = data["on_direct"]
    r[23].update(our_wins=1, opp_wins=1, result=.5)
    r[24].update(our_wins=1, opp_wins=1, result=.5)
    for item in r: item.update(our_points=0, opp_points=900)
    assert s.summarize(data)["direct"]["score"] == .6


@pytest.mark.parametrize("fault", ["missing", "duplicate", "wrong_side", "wrong_result", "short", "nan", "off_change"])
def test_invalid_results_are_rejected(fault):
    data = rows(); r = data["off_solution"]
    if fault == "missing": r.pop()
    if fault == "duplicate": r[-1] = copy.deepcopy(r[0])
    if fault == "wrong_side": r[0]["side"] = "player_2"
    if fault == "wrong_result": r[0]["result"] = .5
    if fault == "short": r[0]["steps"] = 302
    if fault == "nan": r[0]["our_points"] = float("nan")
    if fault == "off_change": r[0]["leading"]["changes"] = r[0]["observed_changes"] = 1
    with pytest.raises(ValueError): s.summarize(data)


def test_exclusive_write_serializes_before_reserving_and_never_overwrites(tmp_path):
    path = tmp_path / "result.json"
    with pytest.raises(ValueError): s.write(path, {"bad": float("nan")})
    assert not path.exists()
    s.write(path, {"good": 1})
    with pytest.raises(FileExistsError): s.write(path, {"good": 2})
    assert json.loads(path.read_text()) == {"good": 1}


def hook_case(mirrored=False):
    before = np.array([[0,0,0], [5,2,0], [5,2,0]])
    after = before.copy(); after[1] = [5,3,0]
    if mirrored:
        for arr in (before, after):
            arr[:,1:] = -arr[:,1:][:,::-1]
    book = dict(hits={1:2,2:2}, unknown=[1,2], stats={"sap_attempts":2,"sap_hits_est":2},
                prev={1:5,2:5}, pred=[(1,1,2,40,True)], shape=[], feats={1:[1.,2.]}, masks={1:[True]*6})
    changed = copy.deepcopy(book); changed["hits"][1] = 1; changed["unknown"] = [2]
    return before, after, book, changed


@pytest.mark.parametrize("mirrored", [False, True])
def test_hook_validator_accepts_exact_change_and_original_remember(mirrored):
    before, after, book, changed = hook_case(mirrored)
    s.check_change(before, after, book, changed, after.copy(), expected=after, calls=1)


@pytest.mark.parametrize("fault", ["other_uid", "class", "remember", "extra_sap", "hits", "pending", "calls"])
def test_hook_validator_rejects_real_bookkeeping_or_call_errors(fault):
    before, after, book, changed = hook_case()
    expected = after.copy(); remembered = after.copy(); calls = 1
    if fault == "other_uid": after[2,1] += 1
    if fault == "class": after[1,0] = 0
    if fault == "remember": remembered = before
    if fault == "extra_sap": changed["stats"]["sap_attempts"] += 1
    if fault == "hits": changed["stats"]["sap_hits_est"] += 1
    if fault == "pending": changed["pred"] = []
    if fault == "calls": calls = 2
    with pytest.raises(ValueError):
        s.check_change(before, after, book, changed, remembered, expected=expected, calls=calls)


def owner():
    argv = ["/venv/python", "-B", "-m", "scripts.sap_leading_screen", "technical"]
    state = dict(status="running", profile=s.PROFILE, owner_pid=10, active=["technical"],
                 jobs={"technical":dict(pid=20,pgid=20,owner_pid=10,argv=argv)})
    return state, argv


def test_framework_argv0_does_not_break_exact_ownership():
    state, argv = owner()
    s.check_owner(state,"technical",argv,pid=20,pgid=20,ppid=10,executable=argv[0],
                  actual=["/Framework/Python",*argv[1:]])


@pytest.mark.parametrize("fault", ["pid", "parent", "executable", "tail", "three_active"])
def test_wrong_ownership_rejected(fault):
    state, argv = owner(); kw=dict(pid=20,pgid=20,ppid=10,executable=argv[0],actual=argv.copy())
    if fault == "pid": kw["pid"] = 21
    if fault == "parent": kw["ppid"] = 11
    if fault == "executable": kw["executable"] = "/other/python"
    if fault == "tail": kw["actual"][-1] = "run"
    if fault == "three_active": state["active"] += ["on_solution","on_direct"]
    with pytest.raises(ValueError): s.check_owner(state,"technical",argv,**kw)


def test_technical_requires_all_four_off_reproductions_and_actual_on_change():
    games = [dict(mode=mode,seed=seed,side=side,steps=303,off_reproduced=not mode,
                  observed_changes=int(mode)) for mode in (False,True) for seed,side in s.TECH_KEYS]
    s.check_technical(games)
    for altered in (games[:-1], [dict(r,observed_changes=0) for r in games],
                    [dict(r,off_reproduced=False) for r in games]):
        with pytest.raises(ValueError): s.check_technical(altered)


def test_bound_evidence_rejects_changed_bytes(tmp_path):
    p = tmp_path / "proof.json"; p.write_text('{"status":"PASS"}')
    pin = s.digest(p)
    assert s.bound({str(p):pin},p)["status"] == "PASS"
    p.write_text('{"status":"FAIL"}')
    with pytest.raises(ValueError): s.bound({str(p):pin},p)


def test_root_start_denial_is_checked_before_sources_or_models(tmp_path):
    p=tmp_path/"admission.json"
    s.write(p,dict(schema_version=1,profile=s.PROFILE,stage="technical",start_authorized=False,root=str(tmp_path)))
    with pytest.raises(ValueError,match="Root start"):
        s.admission(p,s.digest(p),"technical")


def test_instance_and_class_wrappers_restore_after_core_exception(monkeypatch):
    from agents.sherlock.main import Agent_x
    def original(self,step,obs):raise RuntimeError("synthetic core failure")
    monkeypatch.setattr(Agent_x,"_act",original)
    a=SimpleNamespace()
    a.act=lambda step,obs:Agent_x._act(a,step,obs)
    saved=a.act
    with pytest.raises(RuntimeError,match="synthetic core failure"):
        with s.hook_audit(a,lambda:None): a.act(1,{})
    assert Agent_x._act is original and a.act is saved


def test_same_explicit_config_and_factory_for_both_roles(monkeypatch,tmp_path):
    import scripts.par_eval as pe
    import scripts.sap_leading_agent as agent_module
    calls=[]
    class Fake:
        def __init__(self,player,**kw):
            calls.append(kw)
            self.cfg=kw["cfg"];self.training=False;self.epsilon=0;self.learn_enabled=False
            self.extra_q=[None]*35;self.feat_dim=79;self.n_actions=6;self.cnn_policy=None
        def set_to_eval_mode(self):pass
    monkeypatch.setattr(agent_module,"SapLeadingAgent",Fake)
    monkeypatch.setattr(pe,"build_cfg",lambda path,flags:SimpleNamespace(frozen=False,canonical=True))
    a=dict(root=str(tmp_path),config=dict(frozen=False,canonical=True))
    off,on=s.make_agent(a,False),s.make_agent(a,True)
    assert calls[0]["agent_path"]==calls[1]["agent_path"]
    assert vars(off.cfg)==vars(on.cfg)==a["config"]
    assert calls[0]["lead_enabled"] is False and calls[1]["lead_enabled"] is True
    assert off.autosave_on_terminate is on.autosave_on_terminate is False


@pytest.mark.parametrize("fault", ["active", "exit", "missing_job"])
def test_analysis_requires_owned_jobs_fully_closed(fault):
    state=dict(profile=s.PROFILE,status="complete",active=[],admission_sha256="a"*64,
               jobs={j:dict(returncode=0,finished_at=1) for j in s.JOBS})
    s.check_closed_state(state,"a"*64)
    if fault=="active":state["active"]=["on_direct"]
    if fault=="exit":state["jobs"]["on_direct"]["returncode"]=1
    if fault=="missing_job":del state["jobs"]["on_direct"]
    with pytest.raises(ValueError):s.check_closed_state(state,"a"*64)


def test_public_reconstruction_requires_history_and_smallest_uid():
    before=np.array([[0,0,0],[5,2,0],[5,2,0]])
    ctx=dict(ally_ids=np.array([2,1]),ally_pos=np.array([[0,0],[1,2],[1,2]]),ally_ene=[20,40,40],
        W=6,H=6,sap_cost=20,sap_range=4,move_cost=3,enemy_coords=np.array([[3,2]]),
        enemy_vis_ids=[7],enemy_energies=[20],passable=np.ones((6,6),bool))
    previous=(9,9,0,{7:((2,2),20)})
    expected,eligible=s.expected_action(before,ctx,np.ones((6,6),bool),previous,(10,10,0),.25,True,False)
    assert [r["uid"] for r in eligible]==[1,2]
    assert expected.tolist()==[[0,0,0],[5,3,0],[5,2,0]]
    unchanged,_=s.expected_action(before,ctx,np.ones((6,6),bool),None,(10,10,0),.25,True,False)
    np.testing.assert_array_equal(unchanged,before)


@pytest.fixture
def battery_guard_fixture(monkeypatch,tmp_path):
    from scripts import fog_reward_supervisor as fog
    state=dict(stop_file=str(tmp_path/"STOP"),usage_file="usage",python="python",plans=[],
               source={"head":"fixed"},inputs={"input":"sha"},protected={"weight":"sha"})
    calls=[]
    monkeypatch.setattr(fog,"check_usage",lambda *a,**kw:calls.append("quota") or {})
    monkeypatch.setattr(fog,"read_power",lambda:dict(ac=False,percent=55))
    monkeypatch.setattr(fog,"source_identity",lambda *a:calls.append("source") or state["source"])
    monkeypatch.setattr(fog,"hashes",lambda paths:calls.append("hashes") or paths)
    monkeypatch.setattr(fog,"check_model_processes",lambda *a:calls.append("ownership"))
    return fog,state,calls


def test_battery_permission_is_default_off_and_explicit_true_only(battery_guard_fixture):
    fog,state,calls=battery_guard_fixture
    with pytest.raises(ValueError,match="AC power"):fog.guard(state,{})
    fog.guard(state,{},allow_battery=True)
    assert calls[-5:]==["quota","source","hashes","hashes","ownership"]
    assert state["last_power"]["ac"] is False
    with pytest.raises(ValueError):fog.guard(state,{},allow_battery=1)


@pytest.mark.parametrize("failure",["stop","quota","source","hashes","ownership"])
def test_battery_permission_keeps_every_other_guard(battery_guard_fixture,monkeypatch,failure):
    fog,state,_=battery_guard_fixture
    def fail(*a,**kw):raise ValueError("preserved "+failure)
    if failure=="stop":Path(state["stop_file"]).touch()
    elif failure=="quota":monkeypatch.setattr(fog,"check_usage",fail)
    elif failure=="source":monkeypatch.setattr(fog,"source_identity",lambda *a:{})
    elif failure=="hashes":monkeypatch.setattr(fog,"hashes",lambda *a:{})
    else:monkeypatch.setattr(fog,"check_model_processes",fail)
    with pytest.raises(ValueError):fog.guard(state,{},allow_battery=True)


@pytest.mark.parametrize("value",[None,1,"true"])
def test_battery_admission_requires_hashed_boolean(tmp_path,value):
    path=tmp_path/"admission.json"
    s.write(path,dict(schema_version=1,profile=s.PROFILE,stage="technical",start_authorized=True,
                      root=str(tmp_path),allow_battery=value))
    with pytest.raises(ValueError,match="allow_battery"):
        s.admission(path,s.digest(path),"technical")


@pytest.mark.parametrize("state_value",[True,False,1])
def test_battery_worker_forwards_only_matching_admitted_boolean(monkeypatch,tmp_path,state_value):
    from scripts import fog_reward_supervisor as fog
    a=dict(root="root",out="out",python="python",plans=[],source={},protected={},inputs={},
           stop_file=str(tmp_path/"STOP"),allow_battery=True)
    path=tmp_path/"admission.json";s.write(path,a);sha=s.digest(path)
    state=dict(a,jobs={"technical":{}},inputs={str(path):sha},admission_sha256=sha,allow_battery=state_value)
    statepath=tmp_path/"state.json";s.write(statepath,state)
    observed=[]
    monkeypatch.setattr(s,"check_owner",lambda *a,**kw:None)
    monkeypatch.setattr(fog,"guard",lambda *a,**kw:observed.append(kw))
    worker=s.Guard(a,path,sha,statepath,"technical",[])
    if state_value is True:
        worker(force=True);assert observed==[{"allow_battery":True}]
    else:
        with pytest.raises(ValueError):worker(force=True)
        assert not observed


def test_battery_owner_copies_admitted_boolean_before_first_guard(monkeypatch,tmp_path):
    from contextlib import nullcontext
    from scripts import sap_leading_owner as owner_module,sap_leading_eval as worker,fog_reward_supervisor as fog
    from scripts import ensemble_diversity_supervisor as shared
    launcher=str(Path(owner_module.__file__).resolve())
    a=dict(root=str(tmp_path),out=str(tmp_path/"unused"),python=sys.executable,plans=[],source={},protected={},
        stop_file=str(tmp_path/"STOP"),allow_battery=True,inputs={launcher:worker.digest(launcher)})
    admission=tmp_path/"admission.json";admission.write_text("{}")
    monkeypatch.setattr(worker,"admission",lambda *args:a)
    monkeypatch.setattr(shared,"compute_lock",lambda *args:nullcontext())
    def first_guard(state,owned,**kw):
        assert state.get("allow_battery") is True and kw=={"allow_battery":True}
        raise RuntimeError("stop before any output or child")
    monkeypatch.setattr(fog,"guard",first_guard)
    monkeypatch.setattr(sys,"argv",["owner","technical","--admission",str(admission),"--admission-sha","a"*64,
                                   "--usage-file",str(tmp_path/"usage.json")])
    with pytest.raises(RuntimeError,match="stop before any output"):owner_module.main()
    assert not Path(a["out"]).exists()
