"""Own one admitted phase; two training workers pause for explicit Root release."""
import argparse
import json
import os
from pathlib import Path
import signal
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("technical", "training"))
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--admission-sha", required=True)
    parser.add_argument("--usage-file", type=Path, required=True)
    args = parser.parse_args()
    from scripts import threat_warmstart as s
    from scripts.ensemble_diversity_supervisor import compute_lock, spawn_owned, shutdown_owned, group_alive, request_stop
    from scripts.final_training_supervisor import save_state, safe_path
    from scripts.fog_reward_supervisor import guard
    path = safe_path(args.admission)
    a = s.admission(path, args.admission_sha, args.stage)
    launcher = str(Path(__file__).resolve())
    s.require(a["inputs"].get(launcher) == s.digest(launcher) and sys.executable == a["python"],
              "Owner source/interpreter not bound")
    out = safe_path(a["out"])
    s.require(not out.exists(), "Phase already exists; no resume/retry")
    state = {k: a[k] for k in ("root", "out", "python", "plans", "source", "protected", "stop_file", "allow_battery")}
    state.update(profile=s.PROFILE, status="running", stage=args.stage, owner_pid=os.getpid(),
        usage_file=str(safe_path(args.usage_file)), inputs={**a["inputs"], str(path): args.admission_sha},
        admission_sha256=args.admission_sha, jobs={}, active=[], receipts={}, started_at=time.time())
    roles = ("technical",) if args.stage == "technical" else s.ARMS
    owned = {}; handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
    try:
        for sig in handlers: signal.signal(sig, lambda *_: request_stop(state["stop_file"]))
        with compute_lock(a["root"]):
            guard(state, owned, allow_battery=a["allow_battery"])
            out.mkdir(parents=True, exist_ok=False); s.write(out/"state.json", state)
            try:
                for role in roles:
                    guard(state, owned, allow_battery=a["allow_battery"])
                    spawn_owned(state, role, s.worker_command(a, path, args.admission_sha, out/"state.json", role), owned)
                checked = 0.
                while owned:
                    s.require(not Path(state["stop_file"]).exists(), "External STOP")
                    if time.monotonic()-checked >= 10:
                        guard(state, owned, allow_battery=a["allow_battery"]); checked = time.monotonic(); save_state(state)
                    if args.stage == "training" and "prefill_ready" not in state:
                        proofs = {role: out/role/"prefill.json" for role in s.ARMS}
                        if all(p.is_file() for p in proofs.values()):
                            state["prefill_ready"] = {role: s.digest(p) for role, p in proofs.items()}
                            state["awaiting_root_release"] = True; save_state(state)
                    for role, child in list(owned.items()):
                        code = child["process"].poll()
                        if code is None: continue
                        state["jobs"][role].update(returncode=code, finished_at=time.time())
                        s.require(code == 0 and not group_alive(child["pgid"]), "Worker failed or left descendants")
                        receipt_path = out/role/"receipt.json"
                        receipt = json.loads(receipt_path.read_text())
                        s.require(receipt.get("status") == "complete" and receipt.get("role") == role
                            and receipt.get("admission_sha256") == args.admission_sha and receipt.get("source") == a["source"]
                            and receipt.get("command") == state["jobs"][role]["argv"], "Worker receipt differs")
                        if role == "technical": s.check_technical(receipt["games"])
                        else: s.require(len(receipt["games"]) == 440, "Incomplete fixed training")
                        state["receipts"][role] = dict(path=str(receipt_path), sha256=s.digest(receipt_path))
                        del owned[role]; state["active"] = list(owned); save_state(state)
                    if owned: time.sleep(.25)
                # These reads deserialize saved tensors only after both model workers are gone.
                if args.stage == "training":
                    state["final_checks"] = {role: s.validate_final_receipt(out/role/"receipt.json", a, args.admission_sha, role)
                                             for role in s.ARMS}
                    state["awaiting_root_release"] = False
                guard(state, owned, allow_battery=a["allow_battery"])
                state.update(status="complete", finished_at=time.time(), promotion=False); save_state(state)
            except BaseException as exc:
                request_stop(state["stop_file"])
                state.update(status="incomplete", error=f"{type(exc).__name__}: {exc}", promotion=False)
                raise
            finally:
                cleaned = False
                try: shutdown_owned(owned); cleaned = True
                except BaseException as exc:
                    state.update(status="incomplete", cleanup_error=f"{type(exc).__name__}: {exc}"); raise
                finally:
                    for role, child in owned.items():
                        state["jobs"][role].update(returncode=child["process"].poll(), finished_at=time.time())
                    state["active"] = [] if cleaned else list(owned); save_state(state)
    finally:
        for sig, handler in handlers.items(): signal.signal(sig, handler)


if __name__ == "__main__": main()
