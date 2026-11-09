"""Synthetic comparison contracts; no production archives, processes, or games.

Targets scripts.match_weight_compare and scripts.match_weight_compare_owner.
Owner fixture follows tests/test_match_weight_owner.py.
"""
import copy
from contextlib import nullcontext
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.model import QNet
from scripts import match_weight_compare as s
from scripts import match_weight_compare_owner as owner
from scripts.early_curriculum_study import digest, require
from scripts.experiment import state_sha256
from scripts.final_training_supervisor import save_state, safe_path


@pytest.fixture(autouse=True)
def prohibit_real_archives_and_games(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("No real archive, simulator, or game in this synthetic suite")
    monkeypatch.setattr(torch, "load", forbidden)
    from scripts import common
    monkeypatch.setattr(common, "play_game", forbidden)
    monkeypatch.setitem(sys.modules, "luxai_s3.wrappers", SimpleNamespace(LuxAIS3GymEnv=forbidden))


@pytest.fixture
def models():
    base = QNet(79, 6, 256, True).state_dict()
    members = []
    for index in range(40):
        member = dict(base)
        member["body.0.bias"] = torch.full_like(base["body.0.bias"], float(index)/40)
        members.append(member)
    source = dict(q=members[0], target_q=members[0], ensemble=members[1:36], ensemble_dims=[79]*35,
                  feature_dim=79, n_actions=6, cfg=AgentConfig(buffer_capacity=8, frozen=True).to_dict())
    finals = [dict(q=members[36+i], cfg=dict(lr=999, w_match=20, frozen=True), opt={"not": "inference"})
              for i in range(2)]
    return source, finals, members[:36]


def test_append_preserves_original_36_then_both_starts_and_inference_config(models):
    source, finals, originals = models
    for additions, count in (([], 36), (finals, 38)):
        assembled = s.mount(source, additions)
        expected = originals + [f["q"] for f in additions]
        assert len(assembled["ensemble"]) == count-1 and assembled["ensemble_dims"] == [79]*(count-1)
        assert s.state_equal([assembled["q"], *assembled["ensemble"]], expected)
        assert s.state_equal(assembled["q"], originals[0])
        assert s.state_equal(assembled["target_q"], source["target_q"])
        assert assembled["cfg"] == dict(AgentConfig.from_dict(source["cfg"]).to_dict(), frozen=False)
        assert assembled["cfg"]["w_match"] == source["cfg"]["w_match"]
        assert assembled["cfg"]["lr"] != 999 and "opt" not in assembled
    assert source["cfg"]["frozen"] is True
    # Deep-copy proof: no assembly mutation can alter original or final source tensors.
    assembled["ensemble"][35]["body.0.bias"][0] = -999
    assert finals[0]["q"]["body.0.bias"][0] != -999
    with pytest.raises(ValueError): s.mount(source, finals[:1])
    with pytest.raises(ValueError): s.mount(source, finals+finals[:1])


def test_actual_stock_loader_uses_synthetic_archive_without_explicit_cfg(models, tmp_path, monkeypatch):
    source, finals, original = models
    cp = s.mount(source, finals)
    path = tmp_path/"synthetic.pth"; path.write_text("in-memory checkpoint witness")
    loads = []
    def load(name, **kwargs):
        assert Path(name) == path
        loads.append(kwargs)
        return copy.deepcopy(cp)
    monkeypatch.setattr(torch, "load", load)
    agent = s.validate_and_load(path, cp, [*original, *(f["q"] for f in finals)])
    assert len(agent.extra_q) == 37 and not agent.training
    assert loads and agent.cfg.to_dict() == cp["cfg"]


@pytest.mark.parametrize("fault", ["lost_member", "extra_member", "reorder", "width", "dtype", "nan", "loader_fallback"])
def test_actual_assembly_or_loader_difference_is_rejected(models, tmp_path, monkeypatch, fault):
    source, finals, original = models
    cp = s.mount(source, finals)
    expected = copy.deepcopy([*original, *(f["q"] for f in finals)])
    if fault == "lost_member": cp["ensemble"].pop(); cp["ensemble_dims"].pop()
    if fault == "extra_member": cp["ensemble"].append(cp["ensemble"][0]); cp["ensemble_dims"].append(79)
    if fault == "reorder": cp["ensemble"][-2:] = cp["ensemble"][-2:][::-1]
    if fault == "width": cp["ensemble"][-1]["body.0.weight"] = torch.zeros(256, 101)
    if fault == "dtype": cp["ensemble"][-1]["body.0.bias"] = cp["ensemble"][-1]["body.0.bias"].double()
    if fault == "nan": cp["ensemble"][-1]["body.0.bias"][0] = float("nan")
    path = tmp_path/"synthetic.pth"; path.write_text("synthetic")
    loaded = s.mount(source, []) if fault == "loader_fallback" else cp
    monkeypatch.setattr(torch, "load", lambda *_a, **_k: copy.deepcopy(loaded))
    with pytest.raises(ValueError): s.validate_and_load(path, cp, expected)


def comparison_admission(tmp_path, monkeypatch, stage="performance"):
    monkeypatch.setattr(s, "ROOT", tmp_path)
    return dict(profile=s.PROFILE, stage=stage, source={"head": "new-comparison-source"},
        root=str(tmp_path), out=str(tmp_path/"experiments/analysis"/s.PROFILE/(stage+"_v1")),
        python=sys.executable, inputs={}, protected={"synthetic-protected": "fixed"},
        models={r:str(tmp_path/(r+".pth")) for r in s.ROLES},
        cohorts={k:str(tmp_path/(k+".json")) for k in s.COHORTS})


def historical_completion(tmp_path, a, fault=None):
    """Only bound JSON/text witnesses; never a tensor archive or training invocation."""
    def save(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        s.write(path, value); a["inputs"][str(path)] = digest(path)
        return str(path)
    pairs = {}
    for start in (48, 49):
        out = tmp_path/f"historical-{start}"
        old_source = {"head": f"historical-training-{start}"}
        train = dict(profile="match_weight_20261109", stage=f"pair{start}", start=start,
                     protected=a["protected"], source=old_source, out=str(out),
                     config={r:dict(w_match=2 if r=="control" else 20) for r in ("control", "match")})
        admission = save(tmp_path/f"training-{start}.json", train)
        sha = digest(admission); models = {}; receipts = {}; checks = {}
        for role in ("control", "match"):
            final = save(out/role/"final.pth", {"synthetic_final": [start, role]})
            receipt = dict(status="complete", profile=train["profile"], stage=train["stage"], start=start,
                role=role, source=old_source, admission_sha256=sha, games=[{}]*440,
                files={final:digest(final)}, final_identity={"q":f"tensor-{start}-{role}"})
            target = start==49 and role=="control"
            if target and fault=="incomplete_receipt": receipt["status"]="incomplete"
            if target and fault=="wrong_role": receipt["role"]="match"
            if target and fault=="wrong_start": receipt["start"]=48
            if target and fault=="wrong_source": receipt["source"]={"head":"unrelated"}
            if target and fault=="short_training": receipt["games"].pop()
            receipt_path = save(out/role/"receipt.json", receipt)
            receipts[role] = dict(path=receipt_path, sha256=digest(receipt_path))
            checks[role] = dict(status="PASS", role=role, start=start, games=440, learn_steps=60000,
                                receipt_sha256=digest(receipt_path))
            models[role] = dict(path=final, sha256=digest(final), receipt=receipt_path,
                                receipt_sha256=digest(receipt_path))
        owner = dict(status="complete", profile=train["profile"], stage=train["stage"], start=start,
                     active=[], source=old_source, admission_sha256=sha, final_checks=checks, receipts=receipts,
                     jobs={role:dict(returncode=0) for role in ("control", "match")})
        if start==49 and fault=="running_owner": owner.update(status="running", active=["control"])
        if start==49 and fault=="missing_owner_job": del owner["jobs"]["match"]
        if start==49 and fault=="wrong_owner_job": owner["jobs"]["other"] = owner["jobs"].pop("match")
        if start==49 and fault=="failed_owner_job": owner["jobs"]["match"]["returncode"] = 1
        if start==49 and fault=="unfinished_owner_job": owner["jobs"]["control"]["returncode"] = None
        owner_path = save(out/"state.json", owner)
        pairs[str(start)] = dict(admission=admission, admission_sha256=sha, state=owner_path,
                                state_sha256=digest(owner_path), models=models)
    if fault=="missing_start": del pairs["49"]
    closure = dict(profile="match_weight_20261109", status="COMPLETE_TRAINING_NO_STRENGTH_CLAIM",
        source_and_input_bindings_valid=True, protected=a["protected"], pairs=pairs,
        actual=dict(technical_games=4, prefill_games=160, learning_games=1600, optimizer_updates=240000))
    if fault=="wrong_updates": closure["actual"]["optimizer_updates"]-=1
    a["training_completion"] = save(tmp_path/"closure.json", closure)
    if fault in ("missing_final", "changed_final"):
        final=Path(pairs["49"]["models"]["control"]["path"])
        if fault=="missing_final": final.unlink()
        else: final.write_text("different final bytes")
    return closure


def test_historical_sources_are_bound_without_readmitting_old_head(tmp_path, monkeypatch):
    a = comparison_admission(tmp_path, monkeypatch)
    historical_completion(tmp_path, a)
    from scripts import match_weight_study
    monkeypatch.setattr(match_weight_study, "admission", lambda *_a, **_k: pytest.fail("Do not re-admit old HEAD"))
    actual = s.accepted_training(a)
    assert set(actual)=={"control", "match"}
    for role in actual:
        assert [r["start"] for r in actual[role]]==[48,49]
        assert all(r["source"] != a["source"] for r in actual[role])
        assert [r["path"].parent.name for r in actual[role]]==[role,role]


@pytest.mark.parametrize("fault", ["missing_start", "running_owner", "incomplete_receipt", "wrong_role",
    "wrong_start", "wrong_source", "short_training", "wrong_updates", "missing_final", "changed_final",
    "missing_owner_job", "wrong_owner_job", "failed_owner_job", "unfinished_owner_job"])
def test_unaccepted_or_changed_historical_final_cannot_be_mounted(tmp_path, monkeypatch, fault):
    a = comparison_admission(tmp_path, monkeypatch)
    historical_completion(tmp_path, a, fault)
    with pytest.raises((ValueError, FileNotFoundError)): s.accepted_training(a)


@pytest.mark.parametrize("final_fault",[None,"incomplete","wrong_start"])
def test_technical_phase_uses_real_stock_loader_but_never_plays(models, tmp_path, monkeypatch, final_fault):
    from scripts import ensemble_diversity_train
    source, final_pair, originals = models
    a = comparison_admission(tmp_path, monkeypatch, "technical")
    out = s.output_dir(a); out.mkdir(parents=True)
    a["v14_source"] = str(tmp_path/"v14-source")
    Path(a["v14_source"]).write_text("synthetic original")
    a["inputs"][a["v14_source"]] = digest(a["v14_source"])
    a["training_completion"] = str(tmp_path/"accepted-closure.json")
    Path(a["training_completion"]).write_text("synthetic accepted closure")
    records={}; payloads={}; calls=[]
    for role in ("control","match"):
        records[role]=[]
        for start, final in zip((48,49),final_pair):
            path=tmp_path/f"{role}-{start}.pth"; path.write_text("synthetic final")
            cfg=dict(source["cfg"], w_match=2 if role=="control" else 20, lr=.00005)
            origin={"head":f"old-{start}"}
            payloads[str(path)]=dict(q=final["q"], feature_dim=79, n_actions=6, ensemble=[], cfg=cfg,
                env_steps=193320, learn_steps=60000, match_weight=dict(profile="match_weight_20261109",
                status="complete", role=role, start=start, source=origin, completed_games=440, component_index=18))
            if role=="control" and start==49:
                if final_fault=="incomplete": payloads[str(path)]["match_weight"]["status"]="incomplete"
                if final_fault=="wrong_start": payloads[str(path)]["match_weight"]["start"]=48
            records[role].append(dict(path=path,start=start,source=origin,config=cfg,
                                     identity={"q":state_sha256(final["q"])}))
    monkeypatch.setattr(s,"accepted_training",lambda _a:records)
    monkeypatch.setattr(s,"check_owned",lambda *_a:calls.append("guard"))
    monkeypatch.setattr(ensemble_diversity_train,"_source",lambda _p:(source,originals,source["cfg"]))
    def save(payload, stream):
        payloads[str(stream.name)]=copy.deepcopy(payload); stream.write(b"in-memory checkpoint witness")
    def load(path, **kwargs): return copy.deepcopy(payloads[str(path)])
    monkeypatch.setattr(torch,"save",save); monkeypatch.setattr(torch,"load",load)
    real_loader=s.validate_and_load; loaded=[]
    def loader(path,cp,expected):
        loaded.append((Path(path).stem,len(expected)))
        return real_loader(path,cp,expected)
    monkeypatch.setattr(s,"validate_and_load",loader)
    if final_fault:
        with pytest.raises(ValueError,match="accepted final"):
            s.run_technical(a,tmp_path/"admission.json","sha",out/"state.json")
        assert not (out/"technical-receipt.json").exists() and not list(out.glob("*.csv"))
        return
    s.run_technical(a,tmp_path/"admission.json","sha",out/"state.json")
    receipt=json.loads((out/"technical-receipt.json").read_text())
    assert receipt["games"]==0 and receipt["no_strength_claim"] is True
    assert loaded==[("v14",36),("control",38),("match",38)] and len(calls)>=5
    assert not list(out.glob("*.csv")) and not (out/"summary.json").exists()
    assert receipt["training_completion_sha256"]==digest(a["training_completion"])
    s.check_technical(receipt)


def test_exact_five_jobs_and_original_par_eval_commands(tmp_path, monkeypatch):
    a=comparison_admission(tmp_path,monkeypatch)
    assert s.JOBS==("v14_solution","control_solution","match_solution","match_v14","match_control")
    for name in s.JOBS:
        spec=s.job_spec(a,name); argv=s.performance_command(a,name)
        assert argv[:4]==[sys.executable,"-B","-m","scripts.par_eval"]
        assert argv[argv.index("--weights")+1]==a["models"][spec["role"]]
        assert argv[argv.index("--workers")+1]=="1" and "--set" not in argv
        assert argv[argv.index("--seed-list")+1]==a["cohorts"][spec["cohort"]]
    assert s.job_spec(a,"match_v14")["opponent"]=="self:"+a["models"]["v14"]
    assert s.job_spec(a,"match_control")["opponent"]=="self:"+a["models"]["control"]
    assert s.COHORTS==dict(solution=list(range(9970000,9970020)),
                          direct_v14=list(range(9970100,9970120)),direct_control=list(range(9970200,9970220)))


def rows_for(a,name,seeds,*,wins=23,draws=17):
    results=[1.]*wins+[.5]*draws+[0.]*(40-wins-draws)
    rows=[]
    for (seed,side),result in zip(((seed,side) for seed in seeds for side in ("player_0","player_1")),results):
        own,opp=(2,1) if result==1 else (1,1) if result==.5 else (1,2)
        rows.append(dict(seed=seed,side=side,opponent=s.job_spec(a,name)["opponent"],result=result,
            game_win=int(result==1),point_win=result,steps=303,point_counting_version=2,
            our_wins=own,opp_wins=opp,our_points=own*10,opp_points=opp*10))
    return pd.DataFrame(rows)


def test_gates_use_24_real_wins_and_both_solution_references(tmp_path,monkeypatch):
    a=comparison_admission(tmp_path,monkeypatch); seeds=list(range(20))
    frames={n:rows_for(a,n,seeds,wins=23,draws=17) for n in s.JOBS}
    monkeypatch.setattr(s,"validate_csv",lambda _a,n:frames[n])
    monkeypatch.setattr(s,"digest",lambda _p:"synthetic hash")
    report=s.analyze(a)
    assert report["games"]==200 and report["counts"]["match_v14"]==dict(wins=23,draws=17,losses=0)
    assert not report["gates"]["direct_v14"] and not report["gates"]["direct_control"] and not report["nominated"]
    for name in ("match_v14","match_control"): frames[name]=rows_for(a,name,seeds,wins=24,draws=16)
    assert s.analyze(a)["nominated"] is True
    for reference in ("v14","control"):
        key=reference+"_solution"; prior=frames[key]
        frames[key]=rows_for(a,key,seeds,wins=24,draws=16)
        assert not s.analyze(a)["gates"]["solution_"+reference] and not s.analyze(a)["nominated"]
        frames[key]=prior
    ordered=s.analyze(a)
    for name in frames: frames[name]=frames[name].iloc[::-1]
    shuffled=s.analyze(a)
    assert ordered["solution"]==shuffled["solution"] and ordered["direct"]==shuffled["direct"]


@pytest.mark.parametrize("fault", [None,"duplicate","missing_side","foreign_seed","foreign_opponent",
    "short_game","old_points","inconsistent_result","draw_counted_win","wrong_point_win","too_many_match_wins"])
def test_csv_full_fixed_keys_303_and_v2_required(tmp_path,monkeypatch,fault):
    a=comparison_admission(tmp_path,monkeypatch); name="match_v14"; seeds=list(range(20))
    frame=rows_for(a,name,seeds)
    if fault=="duplicate": frame.loc[1,["seed","side"]]=frame.loc[0,["seed","side"]]
    if fault=="missing_side": frame=frame.iloc[:-1]
    if fault=="foreign_seed": frame.loc[:1,"seed"]=999
    if fault=="foreign_opponent": frame.loc[:1,"opponent"]="default"
    if fault=="short_game": frame.loc[0,"steps"]=302
    if fault=="old_points": frame.loc[0,"point_counting_version"]=1
    if fault=="inconsistent_result": frame.loc[0,"result"]=0.
    if fault=="draw_counted_win": frame.loc[39,"game_win"]=1
    if fault=="wrong_point_win": frame.loc[0,"point_win"]=0.
    if fault=="too_many_match_wins": frame.loc[0,["our_wins","opp_wins"]]=[3,1]
    monkeypatch.setattr(s,"read_bound",lambda *_a:seeds)
    monkeypatch.setattr(pd,"read_csv",lambda _path:frame)
    if fault is None: assert len(s.validate_csv(a,name))==40
    else:
        with pytest.raises(ValueError): s.validate_csv(a,name)


@pytest.fixture
def owner_harness(tmp_path,monkeypatch):
    """Adapted existing owner fixture: no subprocess, simulator, or real archive."""
    from scripts import ensemble_diversity_supervisor as lifecycle
    from scripts import fog_reward_supervisor as supervisor
    out=tmp_path/"phase"; admission_path=tmp_path/"admission.json"
    usage=tmp_path/"usage.json"; usage.write_text("{}")
    config=dict(root=str(tmp_path),out=str(out),python=sys.executable,plans=[],source={"head":"fixed"},
                protected={},inputs={},stop_file=str(tmp_path/"STOP"),allow_battery=True)
    h=SimpleNamespace(out=out,config=config,launches=[],widths=[],returncodes={},fault=None,
                      cleanup=[],validations=[],children={},analysis=0)
    fake=SimpleNamespace(PROFILE=s.PROFILE,JOBS=s.JOBS,require=require,digest=digest,write=s.write,
                         output_dir=lambda _a:out,bound=lambda _a,p:Path(p))
    def admit(path,sha,stage):
        require(digest(path)==sha and json.loads(path.read_text())["stage"]==stage,"Wrong independent admission")
        return copy.deepcopy(config)
    fake.admission=admit
    fake.technical_command=lambda _a,p,sha:[sys.executable,"-B","-m","scripts.match_weight_compare","technical"]
    fake.performance_command=lambda _a,name:[sys.executable,"-B","-m","scripts.par_eval",name]
    fake.job_spec=lambda _a,name:dict(csv=str(out/(name+".csv")))
    def validate(_a,name):
        if h.fault=="csv": raise ValueError("Invalid actual CSV")
        h.validations.append(name)
    fake.validate_csv=validate
    fake.check_technical=lambda receipt:require(receipt["games"]==0,"Technical phase played games")
    def analyze(_a): h.analysis+=1; return dict(games=200)
    fake.analyze=analyze
    monkeypatch.setitem(sys.modules,"scripts.match_weight_compare",fake)
    import scripts
    monkeypatch.setattr(scripts,"match_weight_compare",fake)
    def guard(state,owned,*,allow_battery):
        assert allow_battery is True and state["inputs"]==config["inputs"]
        require(not Path(state["stop_file"]).exists(),"External STOP")
        if h.fault=="quota": raise ValueError("Quota reached 100%")
    monkeypatch.setattr(supervisor,"guard",guard)
    monkeypatch.setattr(lifecycle,"compute_lock",lambda _root:nullcontext())
    monkeypatch.setattr(lifecycle,"group_alive",lambda _pgid:False)
    monkeypatch.setattr(lifecycle,"request_stop",lambda path:Path(path).touch(exist_ok=True))
    class Child:
        def __init__(self,name,pid): self.name,self.pid=name,pid
        def poll(self): return h.returncodes.get(self.name,0)
    def spawn(state,name,argv,owned):
        assert len(owned)<2 and name not in h.children
        child=Child(name,90000+len(h.launches)); h.children[name]=child
        h.launches.append(name); owned[name]=dict(process=child,pgid=child.pid,owner_pid=state["owner_pid"])
        h.widths.append(len(owned)); state["active"]=list(owned)
        state["jobs"][name]=dict(pid=child.pid,pgid=child.pid,owner_pid=state["owner_pid"],argv=argv)
        save_state(state)
        if name=="technical":
            receipt=dict(status="complete",source=config["source"],admission_sha256=digest(admission_path),
                         command=argv,games=0)
            if h.fault=="receipt": receipt["source"]={"head":"wrong"}
            s.write(out/"technical-receipt.json",receipt)
        else: (out/(name+".csv")).write_text("synthetic complete CSV")
        if h.fault=="stop_after_spawn": Path(config["stop_file"]).touch()
        if h.fault=="admission_after_spawn": admission_path.write_text("changed")
    monkeypatch.setattr(lifecycle,"spawn_owned",spawn)
    def cleanup(owned):
        assert set(owned)<=set(h.children)
        h.cleanup.append(tuple(owned))
    monkeypatch.setattr(lifecycle,"shutdown_owned",cleanup)
    def run(stage):
        config["stage"]=stage; admission_path.write_text(json.dumps(config))
        monkeypatch.setattr(sys,"argv",["owner",stage,"--admission",str(admission_path),
            "--admission-sha",digest(admission_path),"--usage-file",str(usage)])
        return owner.main()
    h.run=run
    return h


@pytest.mark.parametrize("stage",["technical","performance"])
def test_owner_runs_only_admitted_phase_and_fixed_waves(owner_harness,stage):
    h=owner_harness; h.run(stage)
    state=json.loads((h.out/"state.json").read_text())
    expected=["technical"] if stage=="technical" else list(s.JOBS)
    assert h.launches==expected and state["status"]=="complete" and state["active"]==[]
    assert h.widths==([1] if stage=="technical" else [1,2,1,2,1])
    assert h.analysis==(0 if stage=="technical" else 1)
    assert (h.out/"summary.json").exists()==(stage=="performance")
    assert set(state["receipts"])==set(expected) and h.cleanup
    with pytest.raises(ValueError,match="no resume"): h.run(stage)
    assert h.launches==expected


@pytest.mark.parametrize("fault",["exit","csv","stop_after_spawn","admission_after_spawn"])
def test_owner_failure_stops_owned_jobs_without_retry_or_later_wave(owner_harness,fault):
    h=owner_harness
    if fault=="exit": h.returncodes[s.JOBS[0]]=1
    else: h.fault=fault
    with pytest.raises(ValueError): h.run("performance")
    state=json.loads((h.out/"state.json").read_text())
    assert state["status"]=="failed" and state["active"]==[] and h.cleanup
    assert h.launches==(list(s.JOBS[:1]) if fault in ("stop_after_spawn","admission_after_spawn") else list(s.JOBS[:2]))
    assert h.analysis==0 and not (h.out/"summary.json").exists()


def test_owner_quota_prevents_any_launch_and_bad_technical_receipt_never_starts_games(owner_harness):
    h=owner_harness; h.fault="quota"
    with pytest.raises(ValueError,match="Quota"): h.run("technical")
    assert h.launches==[] and not h.out.exists()
    h.fault="receipt"
    with pytest.raises(ValueError,match="receipt differs"): h.run("technical")
    assert h.launches==["technical"] and h.analysis==0 and h.cleanup


@pytest.mark.parametrize("approval_status",["PASS","pending"])
def test_performance_requires_separate_bound_root_technical_acceptance(tmp_path,monkeypatch,approval_status):
    a=comparison_admission(tmp_path,monkeypatch)
    monkeypatch.chdir(tmp_path)
    a.update(schema_version=1,start_authorized=True,allow_battery=True,plans=[],
             stop_file=str(tmp_path/"STOP"),v14_source=str(tmp_path/"original-v14.pth"))
    a["protected"]={str(tmp_path/f"agents/sherlock/weights/agent_p{i}.pth"):s.V14_SHA for i in (0,1)}
    a["protected"][str(tmp_path/"Gruppe15.zip")]=s.ZIP_SHA
    def save(name,value):
        path=tmp_path/name; s.write(path,value); a["inputs"][str(path)]=digest(path)
        return str(path)
    # Only the phase gate is isolated here; historical contracts are tested above.
    a["training_completion"]=save("accepted-training.json",{"synthetic_closed":True})
    a["v14_source"]=save("original-v14.pth",{"synthetic_original":True})
    monkeypatch.setattr(s,"accepted_training",lambda _a:{})
    monkeypatch.setattr(s,"source_identity",lambda *_args:a["source"])
    monkeypatch.setattr(s,"hashes",lambda paths:dict(paths))
    monkeypatch.setattr(s,"fixed_cohorts",lambda _a:s.COHORTS)
    monkeypatch.setattr(s,"digest",lambda p:s.V14_SHA if str(p)==a["v14_source"] else digest(p))
    monkeypatch.setattr(s,"bound",lambda _a,p:safe_path(p))
    originals=[f"member-{i}" for i in range(36)]; records={}
    for role in s.ROLES:
        path=save(role+".pth",{"synthetic_eval":role})
        a["models"][role]=path
        members=originals+([] if role=="v14" else [f"{role}-48",f"{role}-49"])
        records[role]=dict(path=path,sha256=digest(path),members=len(members),member_sha256=members,
                           loader_pass=True,batches=[1,8,16])
    receipt=dict(status="complete",profile=s.PROFILE,source=a["source"],models=records,games=0,
                 no_strength_claim=True,training_completion_sha256=digest(a["training_completion"]))
    a["technical_receipt"]=save("technical-receipt.json",receipt)
    a["technical_acceptance"]=save("root-acceptance.json",dict(status=approval_status,profile=s.PROFILE,
        source=a["source"],technical_receipt_sha256=digest(a["technical_receipt"])))
    path=tmp_path/"performance-admission.json"; s.write(path,a)
    if approval_status=="PASS": assert s.admission(path,digest(path),"performance")["stage"]=="performance"
    else:
        with pytest.raises(ValueError,match="Separate Root"): s.admission(path,digest(path),"performance")
    with pytest.raises(ValueError,match="separate phase"): s.admission(path,digest(path),"technical")
