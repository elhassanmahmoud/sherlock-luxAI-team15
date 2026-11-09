"""One explicitly admitted phase; fixed workers only, no retry or phase chaining."""
import argparse
import json
import os
from pathlib import Path
import signal
import sys
import time


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage",choices=("technical","performance"))
    p.add_argument("--admission",type=Path,required=True)
    p.add_argument("--admission-sha",required=True)
    p.add_argument("--usage-file",type=Path,required=True)
    args=p.parse_args()
    sys.path.insert(0,str(Path.cwd()))
    from scripts import rank_mean_eval as s
    from scripts.ensemble_diversity_supervisor import compute_lock,spawn_owned,shutdown_owned,group_alive,request_stop
    from scripts.final_training_supervisor import save_state,safe_path
    from scripts.fog_reward_supervisor import guard
    path=safe_path(args.admission);a=s.admission(path,args.admission_sha,args.stage)
    launcher=str(Path(__file__).resolve())
    s.require(a["inputs"].get(launcher)==s.digest(launcher),"External Root launcher must be a pinned input")
    s.require(sys.executable==a["python"],"Use the admitted interpreter for Root and workers")
    out=safe_path(a["out"]);s.require(not out.exists(),"Exclusive phase output already exists; no resume")
    state={k:a[k] for k in ("root","out","python","plans","source","protected","stop_file","allow_battery")}
    state.update(profile=s.PROFILE,status="running",stage=args.stage,owner_pid=os.getpid(),
        usage_file=str(safe_path(args.usage_file)),inputs={**a["inputs"],str(path):args.admission_sha},
        admission_sha256=args.admission_sha,jobs={},active=[],receipts={},started_at=time.time())
    waves=(("technical",),) if args.stage=="technical" else (s.JOBS[:2],(s.JOBS[2],))
    owned={};handlers={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP)}
    try:
        for sig in handlers:signal.signal(sig,lambda *_:request_stop(state["stop_file"]))
        with compute_lock(a["root"]):
            guard(state,owned,allow_battery=a["allow_battery"])
            out.mkdir(parents=True,exist_ok=False)
            s.write(out/"state.json",state)  # Initial state exclusive; existing helper updates it atomically.
            try:
                for wave in waves:
                    for name in wave:
                        guard(state,owned,allow_battery=a["allow_battery"])
                        command=[a["python"],"-B","-m","scripts.rank_mean_eval",
                            "technical" if name=="technical" else "run",
                            "--admission",str(path),"--admission-sha",args.admission_sha,
                            "--owner-state",str(out/"state.json")]
                        if name!="technical":command += ["--job",name]
                        spawn_owned(state,name,command,owned)
                    checked=0.
                    while owned:
                        s.require(not Path(state["stop_file"]).exists(),"External STOP")
                        if time.monotonic()-checked>=10:
                            guard(state,owned,allow_battery=a["allow_battery"]);checked=time.monotonic();save_state(state)
                        for name,child in list(owned.items()):
                            code=child["process"].poll()
                            if code is None:continue
                            state["jobs"][name].update(returncode=code,finished_at=time.time())
                            s.require(code==0 and not group_alive(child["pgid"]),"Worker failed or left descendants")
                            receipt=out/name/"receipt.json";data=json.loads(receipt.read_text())
                            s.require(data.get("status")=="complete" and data.get("job")==name
                                and data.get("admission_sha256")==args.admission_sha and data.get("source")==a["source"]
                                and data.get("command")==state["jobs"][name]["argv"],"Worker receipt differs")
                            if name=="technical":s.check_technical(data["games"])
                            else:s.require(len(data["games"])==40,"Incomplete fixed job")
                            state["receipts"][name]=dict(path=str(receipt),sha256=s.digest(receipt))
                            del owned[name];state["active"]=list(owned);save_state(state)
                        if owned:time.sleep(.25)
                guard(state,owned,allow_battery=a["allow_battery"])
                state.update(status="complete",finished_at=time.time());save_state(state)
            except BaseException as exc:
                request_stop(state["stop_file"])
                state.update(status="failed",error=f"{type(exc).__name__}: {exc}")
                raise
            finally:
                cleaned=False
                try:shutdown_owned(owned);cleaned=True
                except BaseException as exc:
                    state.update(status="failed",cleanup_error=f"{type(exc).__name__}: {exc}");raise
                finally:
                    for name,child in owned.items():state["jobs"][name].update(returncode=child["process"].poll(),finished_at=time.time())
                    state["active"]=[] if cleaned else list(owned);save_state(state)
    finally:
        for sig,handler in handlers.items():signal.signal(sig,handler)


if __name__=="__main__":main()
