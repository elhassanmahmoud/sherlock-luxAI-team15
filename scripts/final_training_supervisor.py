"""Exclusive, finite two-arm rescue training supervisor. Nothing starts on import.

The caller must check actual Codex quota before --start. This controller enforces
the fixed local compute, input, source, power, signal and wall-clock contracts.
It never resumes a partial study and never starts evaluation or promotes weights.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time

from scripts.early_curriculum_study import (
    THREAD_ENV, digest, group_exists, hashes, require, resource_lock, source_identity,
)

ROOT = Path(__file__).resolve().parents[1]
PLAN = "docs/superpowers/plans/2026-11-03-final-battle.md"
SOURCE_SHA = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
ARMS = ("control18", "adapt18")
RUN_NAMES = {"control18": "20261103_rescue_control18", "adapt18": "20261103_rescue_adapt18"}
STOP_FILE = Path("/tmp/sherlock-final-20261103/STOP")
DEADLINE = datetime(2026, 11, 4, 12, 30, tzinfo=timezone.utc).timestamp()
START_CUTOFF = datetime(2026, 11, 4, 2, 0, tzinfo=timezone.utc).timestamp()
CHECK_INTERVAL = 10.0  # leaves margin below the15-second guard requirement
SIGNALS = {signal.SIGHUP, signal.SIGINT, signal.SIGTERM}


class StopRequested(BaseException):
    pass


def parse_power(text):
    source = re.search(r"Now drawing from '(AC Power|Battery Power)'", text)
    percent = re.search(r"\b(\d{1,3})%", text)
    require(source is not None and percent is not None, "Unknown battery/power state")
    value = int(percent.group(1))
    require(0 <= value <= 100, "Invalid battery percentage")
    return dict(ac=source.group(1) == "AC Power", percent=value)


def read_power():
    return parse_power(subprocess.check_output(["pmset", "-g", "batt"], text=True, timeout=5))


def admit_power(power, *, starting):
    require(type(power.get("ac")) is bool and type(power.get("percent")) is int
            and 0 <= power["percent"] <= 100, "Unknown battery/power state")
    if not power["ac"]:
        require(power["percent"] >= 35 if starting else power["percent"] > 25,
                "Battery is below the start/continuation threshold")


def required_seconds(elapsed):
    evaluation = ((7840 + 11200) * 2.22 + 1760 * 3.0) * 1.2
    return evaluation + max(0., 90 * 60 - elapsed) + 60 * 60


def admit_time(now, *, elapsed, starting):
    require(elapsed >= 0, "Invalid elapsed time")
    if starting:
        require(now < START_CUTOFF, "Training start cutoff reached")
    require(elapsed < 120 * 60, "Two-hour training wall-clock limit reached")
    require(now + required_seconds(elapsed) <= DEADLINE,
            "Training plus complete remaining evaluation chain no longer fits")


def foreign_jobs(text, *, owner_pid, owned_pgids):
    """Ignore only this owner and its explicitly registered process groups."""
    jobs = []
    modules = (r"(?:experiment|par_eval|train|finetune|evaluate|compare_weights|ppo_train|train_ppo|"
               r"distill|mechanism_probe|targeting_probe|night_train_pilot|targeting_adapt|"
               r"targeting_adapt_backup|final_rescue_train|final_training_supervisor|"
               r"final_battle_study|early_curriculum_study)")
    pattern = re.compile(r"(?:-m\s+scripts\.|scripts/)" + modules + r"(?:\s|\.py\b)")
    for line in text.splitlines():
        fields = line.strip().split(None, 2)
        if len(fields) != 3:
            continue
        pid, pgid = int(fields[0]), int(fields[1])
        if pid == owner_pid or pgid in owned_pgids:
            continue
        command = fields[2]
        executable = Path(command.split(None, 1)[0]).name.lower()
        if (("python" in executable and (pattern.search(command) or "-m pytest" in command))
                or executable.startswith("pytest")):
            jobs.append(pid)
    return jobs


def check_foreign(owned_pgids=()):
    snapshot = subprocess.check_output(["ps", "-axo", "pid=,pgid=,args="], text=True, timeout=5)
    jobs = foreign_jobs(snapshot, owner_pid=os.getpid(), owned_pgids=set(owned_pgids))
    require(not jobs, f"Foreign model/test processes are active: {jobs}")


def training_commands(state):
    return {arm: [state["python"], "-B", "-m", "scripts.final_rescue_train", "runarm",
                  "--prepared", state["prepared"], "--arm", arm, "--name", RUN_NAMES[arm]]
            for arm in ARMS}


def safe_path(path):
    path = Path(path).absolute()
    require(not any(part.is_symlink() for part in (path, *path.parents)), "Symlink output/input path")
    require(not path.exists() or path.stat().st_nlink == 1 or path.is_dir(), "Hardlinked input/output")
    return path.resolve()


def save_state(state):
    out = safe_path(state["out"])
    target = safe_path(out / "state.json")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", prefix="state-", suffix=".tmp", dir=out,
                                         delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(state, handle, indent=2, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def reserve_output(state):
    out = safe_path(state["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.mkdir()  # exclusive reservation, never adopt an existing output
    save_state(state)


def prepared_inputs(prepared):
    prepared = safe_path(prepared).resolve(strict=True)
    manifest_path = safe_path(prepared / "manifest.json")
    manifest = json.loads(manifest_path.read_text())
    require(manifest.get("source_sha256") == SOURCE_SHA and set(manifest.get("arms", {})) == set(ARMS),
            "Prepared source/arm binding differs from fixed V14 pair")
    files = [manifest_path, safe_path(manifest["source"])]
    for arm in ARMS:
        entry = manifest["arms"][arm]
        require(entry["component_index"] == 18 and entry["run_seed"] == 29
                and entry["config"].get("rescue_in_training") is (arm == "adapt18"),
                "Prepared arm has wrong role/component/seed")
        init = prepared / arm
        files.extend([safe_path(init / "manifest.json"), safe_path(init / "weights/agent.pth")])
        require(digest(init / "weights/agent.pth") == entry["weights_sha256"], "Prepared init hash changed")
        require({p.name for p in (init / "weights").iterdir()} == {"agent.pth"},
                "Prepared init contains replay or other unexpected files")
    require(digest(manifest["source"]) == SOURCE_SHA, "Prepared source changed")
    require(not (prepared / "run_records").exists(), "Prepared pair already has run records; no resume")
    require(not (prepared / "supervisor_launch.json").exists(), "Prepared pair already launched; no resume")
    return hashes(files)


def reserve_launch(state):
    """Persist single-use admission before any child can start importing."""
    path = safe_path(Path(state["prepared"]) / "supervisor_launch.json")
    with path.open("x") as handle:
        json.dump(dict(owner_pid=os.getpid(), out=state["out"],
                       expected_head=state.get("expected_head"), started_at=time.time()), handle)
        handle.flush()
        os.fsync(handle.fileno())
    state.setdefault("inputs", {})[str(path)] = digest(path)
    save_state(state)


def build_state(root, prepared, out, python, expected_head):
    root = Path(root).resolve(strict=True)
    require(root == ROOT.resolve(), "Run from the intended repository checkout")
    require(re.fullmatch(r"[0-9a-f]{40}", expected_head) is not None, "Expected HEAD must be a full git hash")
    python = Path(python).absolute()
    require(python.is_file() and os.access(python, os.X_OK), "Python executable is unavailable")
    plans = [str(root / PLAN)]
    identity = source_identity(root, python, plans)
    require(identity["head"] == expected_head, "Expected HEAD changed")
    protected = [root / "agents/sherlock/weights/agent_p0.pth", root / "agents/sherlock/weights/agent_p1.pth"]
    protected_hashes = hashes(map(safe_path, protected))
    require(set(protected_hashes.values()) == {SOURCE_SHA}, "Protected V14 weights differ")
    runs = {arm: str(safe_path(root / "experiments/runs" / RUN_NAMES[arm])) for arm in ARMS}
    require(all(not Path(path).exists() for path in runs.values()), "A fixed training run already exists; no resume")
    inputs = prepared_inputs(prepared)
    out = safe_path(out)
    require(not out.exists(), "Supervisor output already exists; no resume")
    prepared_path = Path(prepared).resolve()
    require(out not in [prepared_path, root] and prepared_path not in out.parents
            and not (root / "agents") in out.parents,
            "Unsafe supervisor output destination")
    return dict(schema_version=1, status="prepared", root=str(root), prepared=str(Path(prepared).resolve()),
                out=str(out), python=str(python), expected_head=expected_head, plans=plans,
                source=identity, protected=protected_hashes, inputs=inputs, runs=runs,
                owner_pid=os.getpid(), started_at=None, finished_at=None, jobs={}, active=[],
                quota_admission="External root check required before --start; no quota bypass/reset",
                chain_deadline=DEADLINE, training_max_seconds=7200, check_interval=CHECK_INTERVAL)


def check_inputs(state):
    current = source_identity(state["root"], state["python"], state["plans"])
    require(current == state["source"] and current["head"] == state["expected_head"],
            "Frozen source, HEAD, plan, interpreter or engine changed")
    require(hashes(state["protected"]) == state["protected"], "Protected V14 weights changed")
    require(hashes(state["inputs"]) == state["inputs"], "Prepared inputs changed")
    for path in [*state["protected"], *state["inputs"]]:
        safe_path(path)


def guard(state, owned, *, elapsed, starting=False):
    require(not STOP_FILE.exists(), "External STOP requested")
    admit_time(time.time(), elapsed=elapsed, starting=starting)
    power = read_power()
    admit_power(power, starting=starting)
    check_inputs(state)
    check_foreign([child["pgid"] for child in owned.values()])
    state["last_guard_at"] = time.time()
    state["last_power"] = power


@contextmanager
def block_signals():
    previous = signal.pthread_sigmask(signal.SIG_BLOCK, SIGNALS)
    try:
        yield previous
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous)


def spawn_owned(state, arm, command, owned):
    require(arm in ARMS and arm not in owned and len(owned) < 2, "Duplicate/excess child")
    log_path = safe_path(Path(state["out"]) / f"{arm}.log")
    with log_path.open("xb") as log:
        with block_signals() as previous:
            # Child restores the pre-block signal mask before exec; parent keeps
            # signals blocked until Popen ownership is registered and journaled.
            launcher = ("import os,signal,sys; "
                        f"signal.pthread_sigmask(signal.SIG_SETMASK,{sorted(map(int, previous))!r}); "
                        "os.execvpe(sys.argv[1],sys.argv[1:],os.environ)")
            process = subprocess.Popen([state["python"], "-B", "-c", launcher, *command],
                                       cwd=state["root"], env={**os.environ, **THREAD_ENV},
                                       start_new_session=True, stdout=log, stderr=subprocess.STDOUT)
            owned[arm] = dict(process=process, owner_pid=os.getpid(), pgid=process.pid)
            state["jobs"][arm] = dict(argv=command, pid=process.pid, pgid=process.pid,
                                      owner_pid=os.getpid(), log=str(log_path),
                                      started_at=time.time(), returncode=None)
            state["active"] = [dict(arm=name, pid=child["process"].pid, pgid=child["pgid"])
                               for name, child in owned.items()]
            save_state(state)


def stop_owned(child):
    process = child["process"]
    require(child["owner_pid"] == os.getpid() and child["pgid"] == process.pid,
            "Refusing to signal an unowned process group")
    try:
        require(os.getpgid(process.pid) == child["pgid"], "Owned process group changed")
    except ProcessLookupError:
        pass
    for sig in (signal.SIGTERM, signal.SIGKILL):
        if group_exists(child["pgid"]):
            os.killpg(child["pgid"], sig)
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass
        until = time.monotonic() + 2
        while group_exists(child["pgid"]) and time.monotonic() < until:
            time.sleep(.05)
        if not group_exists(child["pgid"]):
            return
    raise ValueError("Owned process group did not stop")


def validate_outputs(state):
    # Import/loading occurs only after both compute children have exited.
    from scripts.final_rescue_train import validate_final_receipt
    result = {}
    for arm in ARMS:
        receipt_path = Path(state["runs"][arm]) / "final_receipt.json"
        receipt = validate_final_receipt(receipt_path, arm=arm)
        result[arm] = dict(path=str(receipt_path), sha256=digest(receipt_path),
                           final_checkpoint_sha256=receipt["final_checkpoint_sha256"])
    return result


def run_owned_pair(state):
    """Run exactly one pair; failure always cleans all registered own groups."""
    owned = {}
    start_monotonic = time.monotonic()
    start_wall = time.time()
    state.update(status="running", started_at=start_wall)
    save_state(state)
    def elapsed():
        return max(time.monotonic() - start_monotonic, time.time() - start_wall)
    try:
        reserve_launch(state)
        guard(state, owned, elapsed=0., starting=True)
        commands = training_commands(state)
        for arm in ARMS:
            guard(state, owned, elapsed=elapsed(), starting=True)
            spawn_owned(state, arm, commands[arm], owned)
        next_check = time.monotonic()
        while True:
            require(not STOP_FILE.exists(), "External STOP requested")
            admit_time(time.time(), elapsed=elapsed(), starting=False)
            completed = []
            for arm, child in owned.items():
                code = child["process"].poll()
                if code is not None:
                    state["jobs"][arm]["returncode"] = code
                    require(code == 0, f"Training arm {arm} failed with exit {code}")
                    require(not group_exists(child["pgid"]), f"Training arm {arm} left descendants")
                    completed.append(arm)
            if time.monotonic() >= next_check or len(completed) == 2:
                guard(state, owned, elapsed=elapsed())
                save_state(state)
                next_check = time.monotonic() + CHECK_INTERVAL
            if len(completed) == 2:
                break
            time.sleep(.2)
        state["receipts"] = validate_outputs(state)
        guard(state, owned, elapsed=elapsed())
        state["status"] = "complete"
    except BaseException as exc:
        state.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        with block_signals():
            cleanup_errors = []
            unresolved = []
            for arm, child in owned.items():
                try:
                    if child["process"].poll() is None or group_exists(child["pgid"]):
                        stop_owned(child)
                    state["jobs"][arm]["returncode"] = child["process"].wait(timeout=2)
                    state["jobs"][arm]["finished_at"] = time.time()
                except BaseException as exc:
                    cleanup_errors.append(f"{arm}: {type(exc).__name__}: {exc}")
                    unresolved.append(dict(arm=arm, pid=child["process"].pid, pgid=child["pgid"]))
            state["active"] = unresolved
            state["finished_at"] = time.time()
            if cleanup_errors:
                state.update(status="failed", cleanup_errors=cleanup_errors)
            save_state(state)
            if cleanup_errors:
                raise ValueError("Owned process cleanup failed: " + "; ".join(cleanup_errors))
    return state


def run_supervisor(prepared, out, python, expected_head):
    root = Path.cwd().resolve()
    def terminate(signum, frame):
        raise StopRequested(f"Received signal {signum}")
    original_handlers = {sig: signal.getsignal(sig) for sig in SIGNALS}
    try:
        for sig in SIGNALS:
            signal.signal(sig, terminate)
        with resource_lock(root):
            check_foreign()
            state = build_state(root, prepared, out, python, expected_head)
            guard(state, {}, elapsed=0., starting=True)
            reserve_output(state)
            return run_owned_pair(state)
    finally:
        for sig, handler in original_handlers.items():
            signal.signal(sig, handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--start", action="store_true")
    args = parser.parse_args()
    if not args.start:
        parser.error("Explicit --start is required; this controller has no resume mode")
    try:
        state = run_supervisor(args.prepared, args.out, args.python, args.expected_head)
    except (Exception, StopRequested) as exc:
        print(f"Training supervisor stopped: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps(dict(status=state["status"], state=str(Path(state["out"]) / "state.json"))))


if __name__ == "__main__":
    main()
