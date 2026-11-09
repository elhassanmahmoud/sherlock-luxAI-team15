"""Own exactly one admitted technical phase or paired training start; never release learning."""
import argparse
import json
import os
from pathlib import Path
import signal
import sys
import time

from scripts.early_curriculum_study import digest, require
from scripts.ensemble_diversity_supervisor import (
    compute_lock, spawn_owned, shutdown_owned, group_alive, request_stop,
)
from scripts.final_training_supervisor import safe_path, save_state
from scripts.fog_reward_supervisor import guard
from scripts.threat_warmstart import write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("technical", "pair48", "pair49"))
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--admission-sha", required=True)
    parser.add_argument("--usage-file", type=Path, required=True)
    args = parser.parse_args()
    from scripts import match_weight_study as study
    path = safe_path(args.admission)
    a = study.admission(path, args.admission_sha, args.stage)
    require(a["profile"] == study.PROFILE and a["stage"] == args.stage
            and a["start"] == (49 if args.stage == "pair49" else 48)
            and a["allow_battery"] is True, "Wrong explicit phase/start/battery admission")
    launcher = str(Path(__file__).resolve())
    require(a["inputs"].get(launcher) == digest(launcher) and sys.executable == a["python"],
            "Owner source/interpreter not bound")
    out = safe_path(study.output_dir(a))
    require(not out.exists(), "Phase already exists; no resume/retry")
    state = {k: a[k] for k in ("root", "out", "python", "plans", "source", "protected", "allow_battery")}
    state.update(profile=study.PROFILE, stage=args.stage, start=a["start"], status="running", owner_pid=os.getpid(),
        usage_file=str(safe_path(args.usage_file)), stop_file=str(safe_path(a["stop_file"])),
        inputs={**a["inputs"], str(path): args.admission_sha}, admission_sha256=args.admission_sha,
        jobs={}, active=[], receipts={}, started_at=time.time(), promotion=False)
    roles = ("technical",) if args.stage == "technical" else ("control", "match")
    owned = {}
    handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}

    def check():
        require(digest(path) == args.admission_sha, "Admission changed")
        guard(state, owned, allow_battery=a["allow_battery"])

    try:
        for sig in handlers: signal.signal(sig, lambda *_: request_stop(state["stop_file"]))
        with compute_lock(a["root"]):
            check()
            out.mkdir(parents=True, exist_ok=False)
            write(out/"state.json", state)
            try:
                for role in roles:
                    check()
                    command = study.worker_command(a, path, args.admission_sha, out/"state.json", role)
                    spawn_owned(state, role, command, owned)
                checked = 0.
                while owned:
                    require(not Path(state["stop_file"]).exists(), "External STOP")
                    if time.monotonic()-checked >= 10:
                        check(); checked = time.monotonic(); save_state(state)
                    if args.stage != "technical" and "prefill_ready" not in state:
                        proofs = {r: safe_path(out/r/"prefill.json") for r in roles}
                        if all(p.is_file() and safe_path(out/r/"waiting.json").is_file() for r,p in proofs.items()):
                            # Readiness is informational. Only the external Root command may write release.json.
                            state["prefill_ready"] = {r: digest(p) for r,p in proofs.items()}
                            state["awaiting_root_release"] = True
                            save_state(state)
                    for role, child in list(owned.items()):
                        code = child["process"].poll()
                        if code is None: continue
                        state["jobs"][role].update(returncode=code, finished_at=time.time())
                        require(code == 0 and not group_alive(child["pgid"]), "Worker failed or left descendants")
                        receipt_path = safe_path(out/role/"receipt.json")
                        receipt = json.loads(receipt_path.read_text())
                        require(receipt.get("status") == "complete" and receipt.get("profile") == study.PROFILE
                            and receipt.get("role") == role and receipt.get("stage") == args.stage
                            and receipt.get("start") == a["start"] and receipt.get("source") == a["source"]
                            and receipt.get("admission_sha256") == args.admission_sha
                            and receipt.get("command") == state["jobs"][role]["argv"], "Worker receipt binding differs")
                        if role == "technical":
                            study.check_technical(receipt)
                        else:
                            release = safe_path(out/"release.json")
                            require("prefill_ready" in state and len(receipt["games"]) == 440 and release.is_file()
                                and receipt.get("release_sha256") == digest(release), "Incomplete/unreleased paired training")
                        state["receipts"][role] = dict(path=str(receipt_path), sha256=digest(receipt_path))
                        del owned[role]; state["active"] = list(owned); save_state(state)
                    if owned: time.sleep(.25)
                # Saved tensor/replay checks run after both model workers have exited.
                if args.stage != "technical":
                    state["final_checks"] = {}
                    for role in roles:
                        result = study.validate_final_receipt(safe_path(out/role/"receipt.json"), a, args.admission_sha, role)
                        require(result.get("status") == "PASS", "Final validator did not accept worker artifacts")
                        state["final_checks"][role] = result
                    state["awaiting_root_release"] = False
                check()
                state.update(status="complete", finished_at=time.time()); save_state(state)
            except BaseException as exc:
                request_stop(state["stop_file"])
                state.update(status="incomplete", error=f"{type(exc).__name__}: {exc}")
                raise
            finally:
                cleaned = False
                try: shutdown_owned(owned); cleaned = True
                except BaseException as exc:
                    state.update(status="incomplete", cleanup_error=f"{type(exc).__name__}: {exc}"); raise
                finally:
                    for role, child in owned.items():
                        state["jobs"][role].update(returncode=child["process"].poll(), finished_at=time.time())
                    state["active"] = [] if cleaned else list(owned)
                    save_state(state)
    finally:
        for sig, handler in handlers.items(): signal.signal(sig, handler)


if __name__ == "__main__": main()
