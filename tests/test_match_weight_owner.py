"""Synthetic owner lifecycle: no subprocesses, checkpoints, or engine games."""
import copy
from contextlib import nullcontext
import importlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from scripts.early_curriculum_study import digest, require
from scripts.final_training_supervisor import save_state, safe_path
from scripts.threat_warmstart import write


def owner_module():
    assert importlib.util.find_spec("scripts.match_weight_owner") is not None, "Owner not implemented"
    return importlib.import_module("scripts.match_weight_owner")


@pytest.fixture
def harness(tmp_path, monkeypatch):
    owner = owner_module()
    out = tmp_path/"phase"
    admission_path = tmp_path/"admission.json"
    usage = tmp_path/"usage.json"; usage.write_text('{}')
    config = dict(profile="match_weight_20261109",stage="pair48",start=48,root=str(tmp_path),out=str(out),
                  python=sys.executable,plans=[],source={"head":"fixed-source"},protected={},inputs={},
                  stop_file=str(tmp_path/"STOP"),allow_battery=True)
    config["inputs"][str(Path(owner.__file__).resolve())] = digest(owner.__file__)
    ctx = SimpleNamespace(stage="pair48",config=config,out=out,admission=admission_path,usage=usage,
        launches=[],validations=[],guards=0,children={},returncodes={},fault=None,waiting=False,
        manual_release=False,observed_wait=False,cleaned=False)
    study = SimpleNamespace(PROFILE="match_weight_20261109",ARMS=("control","match"),require=require,
                            digest=digest,write=write)
    def admission(path, sha, stage):
        assert Path(path)==admission_path and digest(path)==sha and stage==config["stage"]
        return copy.deepcopy(config)
    study.admission=admission; study.output_dir=lambda a:safe_path(a["out"])
    def command(a,path,sha,state,role):
        return [a["python"],"-B","-m","scripts.match_weight_study","worker","--admission",str(path),
                "--admission-sha",sha,"--owner-state",str(state),"--role",role]
    study.worker_command=command
    def technical(receipt):
        ctx.validations.append("technical")
        require(len(receipt["games"])==4,"Four technical games required")
        return {"status":"PASS"}
    study.check_technical=technical
    def final(path,a,sha,role):
        assert all(child.poll() is not None for child in ctx.children.values())
        ctx.validations.append(role)
        if ctx.fault=="final": raise ValueError("Final tensor evidence failed")
        return {"status":"PASS","role":role}
    study.validate_final_receipt=final
    monkeypatch.setitem(sys.modules,"scripts.match_weight_study",study)
    import scripts
    monkeypatch.setattr(scripts,"match_weight_study",study,raising=False)
    def guard(state,owned,*,allow_battery):
        ctx.guards+=1
        assert allow_battery is True and state["allow_battery"] is True
        assert state["inputs"][str(admission_path)]==digest(admission_path)
        if ctx.fault=="quota": raise ValueError("Quota reached 100%")
        require(not Path(state["stop_file"]).exists(),"External STOP")
    monkeypatch.setattr(owner,"guard",guard)
    monkeypatch.setattr(owner,"compute_lock",lambda root:nullcontext())
    monkeypatch.setattr(owner,"group_alive",lambda pgid:ctx.fault=="descendant")
    def stop(path): Path(path).touch(exist_ok=True)
    monkeypatch.setattr(owner,"request_stop",stop)
    class Child:
        def __init__(self,role,pid): self.role,self.pid=role,pid
        def poll(self):
            if ctx.waiting and not (out/"release.json").exists() and not ctx.cleaned: return None
            return ctx.returncodes.get(self.role,0)
    def spawn(state,role,argv,owned):
        assert len(owned)<2 and role not in ctx.children
        pid=90000+len(ctx.launches); child=Child(role,pid)
        ctx.children[role]=child; ctx.launches.append((role,argv))
        owned[role]=dict(process=child,pgid=pid,owner_pid=state["owner_pid"])
        state["jobs"][role]=dict(pid=pid,pgid=pid,owner_pid=state["owner_pid"],argv=argv,returncode=None)
        state["active"]=list(owned); save_state(state)
        directory=out/role; directory.mkdir()
        games=[{}]*(4 if role=="technical" else 440)
        receipt=dict(status="complete",profile=study.PROFILE,stage=config["stage"],start=config["start"],
            role=role,source=config["source"],admission_sha256=digest(admission_path),command=argv,games=games)
        if role!="technical":
            write(directory/"prefill.json",{"role":role})
            write(directory/"waiting.json",{"role":role})
            if not ctx.waiting and not (out/"release.json").exists(): write(out/"release.json",{"manual":True})
            receipt["release_sha256"]=digest(out/"release.json") if (out/"release.json").exists() else "pending"
        if ctx.fault in {"role","source","command","stage","start","profile","admission_sha256"}:
            receipt[ctx.fault]="wrong"
        write(directory/"receipt.json",receipt)
        if ctx.fault=="stop_after_spawn": Path(config["stop_file"]).touch()
        if ctx.fault=="admission_after_spawn": admission_path.write_text("changed after launch")
    monkeypatch.setattr(owner,"spawn_owned",spawn)
    def cleanup(owned):
        ctx.cleaned=True
        assert set(owned)<=set(ctx.children)
    monkeypatch.setattr(owner,"shutdown_owned",cleanup)
    def pause(_seconds):
        state=json.loads((out/"state.json").read_text())
        assert state["awaiting_root_release"] is True and set(state["prefill_ready"])=={"control","match"}
        assert not (out/"release.json").exists()
        ctx.observed_wait=True
        if ctx.manual_release:
            write(out/"release.json",{"manual":True})
            for role in ("control","match"):
                path=out/role/"receipt.json"; receipt=json.loads(path.read_text())
                receipt["release_sha256"]=digest(out/"release.json"); path.write_text(json.dumps(receipt))
        else: raise RuntimeError("No Root release; end synthetic wait")
    monkeypatch.setattr(owner.time,"sleep",pause)
    def run(stage="pair48"):
        config["stage"]=stage; config["start"]=49 if stage=="pair49" else 48
        admission_path.write_text(json.dumps(config))
        monkeypatch.setattr(sys,"argv",["match-owner",stage,"--admission",str(admission_path),
            "--admission-sha",digest(admission_path),"--usage-file",str(usage)])
        return owner.main()
    ctx.run=run
    return ctx


@pytest.mark.parametrize("stage,roles",[("technical",["technical"]),("pair48",["control","match"]),("pair49",["control","match"])])
def test_one_admitted_phase_only_and_validators_after_children_exit(harness,stage,roles):
    h=harness; h.run(stage)
    state=json.loads((h.out/"state.json").read_text())
    assert [r for r,_ in h.launches]==roles
    assert state["status"]=="complete" and state["active"]==[] and set(state["receipts"])==set(roles)
    assert h.validations==roles and h.cleaned and h.guards>=3
    assert state["start"]==(49 if stage=="pair49" else 48)
    for role,argv in h.launches: assert state["jobs"][role]["argv"]==argv
    with pytest.raises(ValueError): h.run(stage)
    assert len(h.launches)==len(roles)


def test_prefill_readiness_cannot_create_its_own_root_release(harness):
    h=harness; h.waiting=True
    with pytest.raises(RuntimeError,match="No Root release"): h.run()
    assert h.observed_wait and not (h.out/"release.json").exists() and h.cleaned
    state=json.loads((h.out/"state.json").read_text())
    assert state["status"]=="incomplete" and state["active"]==[] and h.validations==[]


def test_same_original_pair_finishes_only_after_external_release(harness):
    h=harness; h.waiting=True; h.manual_release=True; h.run()
    assert h.observed_wait and [r for r,_ in h.launches]==["control","match"]
    assert json.loads((h.out/"state.json").read_text())["status"]=="complete"


@pytest.mark.parametrize("fault",["role","source","command","stage","start","profile","admission_sha256","descendant","final"])
def test_mismatched_worker_receipt_or_failed_final_check_never_completes(harness,fault):
    h=harness; h.fault=fault
    with pytest.raises(ValueError): h.run()
    state=json.loads((h.out/"state.json").read_text())
    assert state["status"]=="incomplete" and state["active"]==[] and h.cleaned
    assert Path(h.config["stop_file"]).exists() and len(h.launches)==2


def test_nonzero_worker_exit_stops_original_pair_without_retry(harness):
    h=harness; h.returncodes["control"]=1
    with pytest.raises(ValueError): h.run()
    assert [r for r,_ in h.launches]==["control","match"] and h.cleaned
    assert json.loads((h.out/"state.json").read_text())["status"]=="incomplete"


def test_guard_quota_failure_prevents_any_launch(harness):
    h=harness; h.fault="quota"
    with pytest.raises(ValueError,match="Quota"): h.run()
    assert h.launches==[] and not h.out.exists()


def test_safe_physical_output_rejects_symlink(harness,tmp_path):
    h=harness; actual=tmp_path/"elsewhere"; actual.mkdir(); h.out.symlink_to(actual,target_is_directory=True)
    with pytest.raises(ValueError,match="Symlink"): h.run()
    assert h.launches==[] and list(actual.iterdir())==[]


@pytest.mark.parametrize("fault",["stop_after_spawn","admission_after_spawn"])
def test_stop_or_changed_admission_after_first_spawn_cleans_without_second_launch(harness,fault):
    h=harness; h.fault=fault
    with pytest.raises(ValueError): h.run()
    assert [role for role,_ in h.launches]==["control"] and h.cleaned
    state=json.loads((h.out/"state.json").read_text())
    assert state["status"]=="incomplete" and state["active"]==[]
