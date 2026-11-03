"""Supervisor guard/process tests; no models or Lux games."""
import importlib
import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import pytest


@pytest.fixture
def supervisor():
    assert importlib.util.find_spec("scripts.final_training_supervisor") is not None
    return importlib.import_module("scripts.final_training_supervisor")


def test_supervisor_available():
    assert importlib.util.find_spec("scripts.final_training_supervisor") is not None


@pytest.mark.parametrize("text,expected", [
    ("Now drawing from 'AC Power'\n -InternalBattery-0 34%; charging", {"ac": True, "percent": 34}),
    ("Now drawing from 'Battery Power'\n -InternalBattery-0 35%; discharging", {"ac": False, "percent": 35}),
])
def test_power_parser(supervisor, text, expected):
    assert supervisor.parse_power(text) == expected


def test_power_boundaries_fail_closed(supervisor):
    supervisor.admit_power({"ac": False, "percent": 35}, starting=True)
    supervisor.admit_power({"ac": True, "percent": 1}, starting=True)
    supervisor.admit_power({"ac": False, "percent": 26}, starting=False)
    for power, starting in (({"ac": False, "percent": 34}, True),
                            ({"ac": False, "percent": 25}, False)):
        with pytest.raises(ValueError):
            supervisor.admit_power(power, starting=starting)
    with pytest.raises(ValueError):
        supervisor.parse_power("unknown power source")


def test_chain_admission_uses_full_remaining_evaluation_and_training(supervisor):
    deadline = datetime(2026, 11, 4, 12, 30, tzinfo=timezone.utc).timestamp()
    # (7840+11200)*2.22 +1760*3, with20%reserve, plus90mintrain+60mintransition.
    assert supervisor.required_seconds(0) == pytest.approx(66058.56)
    supervisor.admit_time(deadline - 66059, elapsed=0, starting=True)
    with pytest.raises(ValueError):
        supervisor.admit_time(deadline - 66058, elapsed=0, starting=True)
    with pytest.raises(ValueError):
        supervisor.admit_time(deadline - 70000, elapsed=7200, starting=False)


def test_foreign_process_filter_ignores_only_own_registered_groups(supervisor):
    text = "101 101 /bin/python -m scripts.final_rescue_train runarm --arm control18\n202 202 /bin/python -m scripts.par_eval --games 2\n303 303 /bin/zsh -c echo scripts.finetune\n"
    assert supervisor.foreign_jobs(text, owner_pid=99, owned_pgids={101}) == [202]
    assert supervisor.foreign_jobs(text, owner_pid=99, owned_pgids=set()) == [101, 202]


def test_commands_are_fixed_and_thread_limits_cover_blas(supervisor, tmp_path):
    state = dict(root=str(tmp_path), python="/usr/bin/python3", prepared=str(tmp_path / "prepared"))
    commands = supervisor.training_commands(state)
    assert set(commands) == {"control18", "adapt18"}
    assert commands["control18"][-2:] == ["--name", "20261103_rescue_control18"]
    assert commands["adapt18"][-2:] == ["--name", "20261103_rescue_adapt18"]
    assert commands["adapt18"][1:4] == ["-B", "-m", "scripts.final_rescue_train"]
    for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        assert supervisor.THREAD_ENV[key] == "1"


def test_atomic_state_writer_and_existing_state_rejection(supervisor, tmp_path):
    out = tmp_path / "new"
    state = dict(out=str(out), status="prepared")
    supervisor.reserve_output(state)
    state["status"] = "failed"
    supervisor.save_state(state)
    import json
    assert json.loads((out / "state.json").read_text())["status"] == "failed"
    with pytest.raises(FileExistsError):
        supervisor.reserve_output(dict(out=str(out), status="prepared"))
    assert not list(out.glob("*.tmp"))


def process_state(tmp_path):
    import sys
    out = tmp_path / "control"
    out.mkdir()
    (tmp_path / "prepared").mkdir()
    return dict(root=str(tmp_path), python=sys.executable, out=str(out), jobs={}, active=[],
                prepared=str(tmp_path / "prepared"))


def test_prepared_launch_reservation_is_exclusive_before_any_child(supervisor, tmp_path):
    state = process_state(tmp_path)
    supervisor.reserve_launch(state)
    assert (tmp_path / "prepared/supervisor_launch.json").is_file()
    assert state["inputs"]
    with pytest.raises(FileExistsError):
        supervisor.reserve_launch(state)


def test_spawn_registers_group_before_unmask_and_stops_owned_child(supervisor, tmp_path):
    import sys
    import os
    state = process_state(tmp_path)
    owned = {}
    supervisor.spawn_owned(state, "control18", [sys.executable, "-c", "import time; time.sleep(30)"], owned)
    child = owned["control18"]
    try:
        assert child["owner_pid"] == os.getpid()
        assert child["process"].pid == child["pgid"]
        assert os.getpgid(child["process"].pid) == child["pgid"]
        assert state["jobs"]["control18"]["pgid"] == child["pgid"]
    finally:
        supervisor.stop_owned(child)
    assert child["process"].poll() is not None
    assert not supervisor.group_exists(child["pgid"])


def test_stop_owned_rejects_unregistered_owner(supervisor, tmp_path):
    import os
    from types import SimpleNamespace
    with pytest.raises(ValueError, match="unowned"):
        supervisor.stop_owned(dict(process=SimpleNamespace(pid=os.getpid()),
                                   pgid=os.getpid(), owner_pid=-1))


@pytest.mark.parametrize("failure", [None, "child", "guard", "receipt", "stop"])
def test_pair_completes_only_with_two_zero_exits_and_receipts_and_cleans_failures(
        supervisor, tmp_path, monkeypatch, failure):
    import sys
    import json
    state = process_state(tmp_path)
    monkeypatch.setattr(supervisor, "STOP_FILE", tmp_path / "STOP")
    monkeypatch.setattr(supervisor, "admit_time", lambda *args, **kwargs: None)
    calls = []
    def guard(state, owned, **kwargs):
        calls.append(len(owned))
        if len(owned) == 2 and failure == "guard":
            raise ValueError("synthetic input changed")
    monkeypatch.setattr(supervisor, "guard", guard)
    commands = {arm: [sys.executable, "-c", "pass"] for arm in supervisor.ARMS}
    if failure == "child":
        commands["control18"] = [sys.executable, "-c", "raise SystemExit(3)"]
        commands["adapt18"] = [sys.executable, "-c", "import time; time.sleep(30)"]
    if failure == "guard":
        commands = {arm: [sys.executable, "-c", "import time; time.sleep(30)"] for arm in supervisor.ARMS}
    if failure == "stop":
        code = f"from pathlib import Path; Path({str(supervisor.STOP_FILE)!r}).touch(); import time; time.sleep(30)"
        commands = {arm: [sys.executable, "-c", code] for arm in supervisor.ARMS}
    monkeypatch.setattr(supervisor, "training_commands", lambda state: commands)
    def receipts(state):
        if failure == "receipt":
            raise ValueError("synthetic missing receipt")
        return {arm: dict(sha256="verified") for arm in supervisor.ARMS}
    monkeypatch.setattr(supervisor, "validate_outputs", receipts)
    if failure:
        with pytest.raises(ValueError):
            supervisor.run_owned_pair(state)
    else:
        supervisor.run_owned_pair(state)
    saved = json.loads((Path(state["out"]) / "state.json").read_text())
    assert saved["status"] == ("failed" if failure else "complete")
    assert saved["active"] == [] and saved["finished_at"] is not None
    assert set(saved["jobs"]) == set(supervisor.ARMS)
    for job in saved["jobs"].values():
        assert job["returncode"] is not None
        assert not supervisor.group_exists(job["pgid"])
    assert 2 in calls


def test_guard_checks_stop_power_inputs_and_foreign_jobs(supervisor, tmp_path, monkeypatch):
    state = {}
    monkeypatch.setattr(supervisor, "STOP_FILE", tmp_path / "STOP")
    monkeypatch.setattr(supervisor, "admit_time", lambda *args, **kwargs: None)
    monkeypatch.setattr(supervisor, "read_power", lambda: dict(ac=True, percent=100))
    checked = []
    monkeypatch.setattr(supervisor, "check_inputs", lambda state: checked.append("inputs"))
    monkeypatch.setattr(supervisor, "check_foreign", lambda owned: checked.append(tuple(owned)))
    supervisor.guard(state, {"control18": dict(pgid=123)}, elapsed=1)
    assert checked == ["inputs", (123,)]
    supervisor.STOP_FILE.touch()
    with pytest.raises(ValueError, match="STOP"):
        supervisor.guard(state, {}, elapsed=1)
