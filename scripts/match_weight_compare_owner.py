"""One assembly/loader phase or fixed 200 games; no automatic transition."""
import argparse
import json
import os
from pathlib import Path
import signal
import sys
import time


def await_group_exit(child, check, *, timeout=10.):
    """Allow an exited par_eval parent to finish its own Pool/tracker cleanup.

    Never signal here. The owner's existing failure cleanup owns any lingering
    registered group; no unrelated process is inspected or terminated here.
    """
    from scripts.ensemble_diversity_supervisor import group_alive
    from scripts.early_curriculum_study import require
    require(child["process"].poll() == 0, "Job failed or has not exited")
    deadline = time.monotonic()+timeout
    while group_alive(child["pgid"]):
        check()
        require(time.monotonic() < deadline, "Exited job left descendants beyond cleanup deadline")
        time.sleep(.05)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("technical","performance"))
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--admission-sha", required=True)
    parser.add_argument("--usage-file", type=Path, required=True)
    args = parser.parse_args()
    from scripts import match_weight_compare as s
    from scripts.ensemble_diversity_supervisor import compute_lock, spawn_owned, shutdown_owned, request_stop
    from scripts.final_training_supervisor import save_state, safe_path
    from scripts.fog_reward_supervisor import guard
    path = safe_path(args.admission); a = s.admission(path,args.admission_sha,args.stage)
    s.require(sys.executable == a["python"], "Wrong admitted interpreter")
    s.bound(a, Path(__file__).resolve())
    out = s.output_dir(a); s.require(not out.exists(), "Output already exists; no resume")
    state = {k:a[k] for k in ("root","out","python","plans","source","protected","inputs","stop_file","allow_battery")}
    # Keep inputs exactly as admitted for technical worker ownership checks.
    # Admission file is checked separately on every owner guard below.
    state.update(profile=s.PROFILE,stage=args.stage,status="running",owner_pid=os.getpid(),
                 usage_file=str(safe_path(args.usage_file)),admission_sha256=args.admission_sha,
                 jobs={},active=[],receipts={},started_at=time.time())
    waves = (("technical",),) if args.stage == "technical" else (s.JOBS[:2],s.JOBS[2:4],s.JOBS[4:])
    owned = {}; handlers = {sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP)}
    def check():
        s.require(s.digest(path) == args.admission_sha, "Admission changed")
        guard(state,owned,allow_battery=True)
    try:
        for sig in handlers: signal.signal(sig,lambda *_:request_stop(state["stop_file"]))
        with compute_lock(a["root"]):
            check(); out.mkdir(parents=True,exist_ok=False); s.write(out/"state.json",state)
            try:
                for wave in waves:
                    for name in wave:
                        check()
                        command = (s.technical_command(a,path,args.admission_sha) if name == "technical"
                                   else s.performance_command(a,name))
                        if name != "technical":
                            s.require(not safe_path(s.job_spec(a,name)["csv"]).exists(), "CSV already exists")
                        spawn_owned(state,name,command,owned)
                    last_check = 0.
                    while owned:
                        s.require(not Path(state["stop_file"]).exists(), "External STOP")
                        if time.monotonic()-last_check >= 10:
                            check(); last_check = time.monotonic(); save_state(state)
                        for name, child in list(owned.items()):
                            code = child["process"].poll()
                            if code is None: continue
                            state["jobs"][name].update(returncode=code,finished_at=time.time())
                            s.require(code == 0, "Job failed")
                            await_group_exit(child,check)
                            if name == "technical":
                                receipt_path = out/"technical-receipt.json"
                                receipt = json.loads(receipt_path.read_text()); s.check_technical(receipt)
                                s.require(receipt.get("status") == "complete" and receipt.get("source") == a["source"]
                                          and receipt.get("admission_sha256") == args.admission_sha
                                          and receipt.get("command") == state["jobs"][name]["argv"], "Technical receipt differs")
                                state["receipts"][name] = dict(path=str(receipt_path),sha256=s.digest(receipt_path))
                            else:
                                s.validate_csv(a,name)
                                csv_path = s.job_spec(a,name)["csv"]
                                state["receipts"][name] = dict(path=csv_path,sha256=s.digest(csv_path),games=40)
                            del owned[name]; state["active"] = list(owned); save_state(state)
                        if owned: time.sleep(.25)
                check()
                if args.stage == "performance":
                    summary = s.analyze(a)
                    summary.update(source=a["source"],admission_sha256=args.admission_sha)
                    s.write(out/"summary.json",summary)
                state.update(status="complete",finished_at=time.time()); save_state(state)
            except BaseException as error:
                request_stop(state["stop_file"])
                state.update(status="failed",error=f"{type(error).__name__}: {error}",
                    interrupted_game_count="Unknown for unfinished par_eval jobs: CSV is published only at job end. "
                                           "Completed validated jobs remain listed; no rerun/resume is admitted.")
                raise
            finally:
                cleaned = False
                try: shutdown_owned(owned); cleaned = True
                except BaseException as error:
                    state.update(status="failed",cleanup_error=f"{type(error).__name__}: {error}"); raise
                finally:
                    for name,child in owned.items():
                        state["jobs"][name].update(returncode=child["process"].poll(),finished_at=time.time())
                    state["active"] = [] if cleaned else list(owned); save_state(state)
    finally:
        for sig,handler in handlers.items(): signal.signal(sig,handler)


if __name__ == "__main__": main()
