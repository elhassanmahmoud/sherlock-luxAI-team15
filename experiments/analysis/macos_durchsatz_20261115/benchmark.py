"""macOS V14 / Solution throughput on one reference map. Coordinator does not import Torch or JAX."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
from importlib import metadata
import json
import multiprocessing as mp
from multiprocessing.connection import wait
import os
from pathlib import Path
import platform
import re
import statistics
import subprocess
import sys
import time
import traceback

REFERENCE = Path("experiments/analysis/r8_midpoint_20261115/games/screen/v14")
SEATS = ("player_0","player_1")
SEED = 7170230
FIELDS = ("wins","losses","points","opp_points","steps")
THREAD_VARS = ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","GOTO_NUM_THREADS","MKL_NUM_THREADS",
               "BLIS_NUM_THREADS","VECLIB_MAXIMUM_THREADS","NUMEXPR_NUM_THREADS")
SYSCTL = "/usr/sbin/sysctl"


def digest(f):
    return sha256(f.read_bytes()).hexdigest()


def reference(args):
    d=args.project/REFERENCE
    pins={"games.jsonl":"8ad616a468ca56a32748af3742205c759db05a23f45487f329f92bcd8a934c6c",
          "manifest.json":"534384f537dea6e882de9daf237026c1dea90e43655e09c3137f8499f7e3bf51"}
    for fn,h in pins.items():
        if digest(d/fn)!=h: raise ValueError(f"Different reference {fn}")
    m=json.loads((d/"manifest.json").read_bytes())
    for f,h in m["sources"].items():
        if digest(args.frozen/f)!=h: raise ValueError(f"Different frozen source {f}")
    if digest(args.frozen/"agents/sherlock/weights/agent_p0.pth")!=m["weights"]: raise ValueError("Different V14")
    dist=metadata.distribution("luxai-s3")
    for name,h in m["engine"].items():
        if digest(dist.locate_file("luxai_s3/"+name))!=h: raise ValueError(f"Different engine {name}")
    rows=[r for r in map(json.loads,(d/"games.jsonl").open()) if r["seed"]==SEED and r["opponent"]=="solution92"]
    if len(rows)!=2 or {r["side"] for r in rows}!=set(SEATS): raise ValueError("Incomplete reference pair")
    return {r["side"]:[r[k] for k in FIELDS] for r in rows},pins


def pressure():
    raw=subprocess.check_output([SYSCTL,"-n","kern.memorystatus_vm_pressure_level","vm.swapusage"],text=True)
    level,usage=raw.strip().splitlines()
    match=re.search(r"\bused\s*=\s*([\d.]+)([KMGT]?)",usage)
    if match is None: raise ValueError(f"Unknown vm.swapusage format {usage!r}")
    value=float(match[1])*1024**({"":0,"K":1,"M":2,"G":3,"T":4}[match[2]])/1024**2
    vm=subprocess.check_output(["/usr/bin/vm_stat"],text=True)
    pages=int(re.search(r"page size of (\d+) bytes",vm).group(1))
    swapouts=int(re.search(r"^Swapouts:\s+(\d+)",vm,re.M).group(1))
    return dict(seconds=time.monotonic(),level=int(level),swap_used_mib=value,swapouts_mib=swapouts*pages/(1024**2))


def worker(ch,frozen,expected):
    try:
        os.chdir(frozen);sys.path.insert(0,str(frozen))
        import torch
        torch.set_num_interop_threads(1)
        from scripts.final_battle_compare import evaluate,init_worker
        init_worker("v14",None)
        if (torch.get_num_threads(),torch.get_num_interop_threads())!=(1,1): raise ValueError("Torch worker threads differ")
        def pair():
            for s in SEATS:
                r=evaluate(("v14","solution92",SEED,s,None))
                if [r[k] for k in FIELDS]!=expected[s]: raise ValueError(f"Outcome changed on {s}: {r}")
        pair()  # Both real courses, including compilation and first allocations, before READY.
        ch.send(("ready",os.getpid()))
        while ch.recv()=="pair":
            pair()
            ch.send(("done",time.monotonic()))
        evaluate.env.close()
    except BaseException:
        try: ch.send(("error",traceback.format_exc()))
        except (OSError,EOFError): pass
    finally: ch.close()


def stage(ctx,n,args,expected,log):
    pipes=[];procs=[];samples=log["memory_samples"];rounds=log["rounds"]
    warning_start = None
    def sample():
        nonlocal warning_start
        m=pressure();samples.append(m)
        if m["level"] >= 4:
            raise RuntimeError("Critical memory pressure")
        if m["level"] == 1:
            warning_start = None
        elif warning_start is None:
            warning_start = m["seconds"]
        elif m["seconds"]-warning_start >= 12:
            recent=[s for s in samples if m["seconds"]-s["seconds"]<=24]
            if m["swapouts_mib"]-recent[0]["swapouts_mib"]>100 or m["swap_used_mib"]-recent[0]["swap_used_mib"]>150:
                raise RuntimeError("Sustained memory warning with active paging")
    def collect(tag, active=None):
        todo=set(pipes if active is None else active);replies=[]
        while todo:
            sample()
            for ch in wait(todo,timeout=1.0):
                kind,value=ch.recv()
                if kind!=tag: raise RuntimeError(str(value))
                replies.append(value);todo.remove(ch)
        return replies
    try:
        sample()
        log["worker_pids"]=[]
        for _ in range(n):
            a,b=ctx.Pipe();proc=ctx.Process(target=worker,args=(b,args.frozen,expected))
            proc.start();b.close();pipes.append(a);procs.append(proc)
            log["worker_pids"]+=collect("ready",[a])
        sample()
        log["warm_end_sample"]=samples[-1]
        for i in range(args.pairs):
            start=time.monotonic()
            for ch in pipes:ch.send("pair")
            times=collect("done")
            elapsed=max(times)-start
            rounds.append(dict(games=2*n,seconds=elapsed,games_per_minute=120*n/elapsed))
            print(f"{n} workers, pair {i+1}: {120*n/elapsed:.2f} games/min",flush=True)
        sample()
        log["games"]=2*n*args.pairs
        log["games_per_minute"]=60*log["games"]/sum(r["seconds"] for r in rounds)
        log["swap_delta_mib"]=round(samples[-1]["swap_used_mib"]-samples[0]["swap_used_mib"],2)
        log["swap_change_after_warm_mib"]=round(samples[-1]["swap_used_mib"]-log["warm_end_sample"]["swap_used_mib"],2)
        log["peak_swap_growth_mib"]=round(max(x["swap_used_mib"] for x in samples)-samples[0]["swap_used_mib"],2)
        for ch in pipes:ch.send("stop")
    finally:
        for proc in procs:
            if sys.exc_info()[0] is None:proc.join(5)
        for proc in procs:
            if proc.is_alive():proc.terminate()
        for proc in procs:
            proc.join(2)
            if proc.is_alive():proc.kill();proc.join()
        for ch in pipes:ch.close()


def convincing(stages):
    latest=stages[-1]; prior=max(stages[:-1],key=lambda r:r["games_per_minute"])
    threshold=1.05*prior["games_per_minute"]
    wins=sum(r["games_per_minute"]>q["games_per_minute"] for r,q in zip(latest["rounds"],prior["rounds"]))
    return latest["games_per_minute"]>=threshold and 2*wins>len(latest["rounds"])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--frozen",type=Path,required=True);p.add_argument("--project",type=Path,required=True)
    p.add_argument("--max-workers",type=int,choices=(4,5,6,8),default=8)
    p.add_argument("--pairs",type=int,default=2,help="timed pairs per worker per stage; minimum two")
    p.add_argument("--out",type=Path,required=True,help="new JSON result file")
    p.add_argument("--check",action="store_true",help="read source hashes and memory; no games or worker processes")
    args=p.parse_args();args.frozen=args.frozen.resolve();args.project=args.project.resolve()
    if args.pairs<2:p.error("at least two measured pairs per worker")
    expected,pins=reference(args)
    if args.check:
        print(json.dumps(dict(expected=expected,reference=pins,macos=pressure()),indent=2));return
    if platform.system()!="Darwin":p.error("this benchmark uses macOS memory pressure")
    for var in THREAD_VARS:os.environ[var]="1"
    ctx=mp.get_context("spawn")
    report=dict(start=datetime.now(timezone.utc).isoformat(),hardware=subprocess.check_output([SYSCTL,"-n","hw.model"],text=True).strip(),
                os=platform.platform(),python=sys.version,versions={lib:metadata.version(lib) for lib in ("torch","numpy","jax","jaxlib","luxai-s3")},
                thread_env={k:os.environ[k] for k in THREAD_VARS},reference=pins,expected=expected,seed=SEED,
                fields=list(FIELDS),pairs_per_worker=args.pairs,frozen=str(args.frozen),benchmark_sha256=digest(Path(__file__)),
                selection="Beyond 4 only if prior stage is >=5% faster than earlier best and wins majority of timed pairs.",stages=[])
    with args.out.open("x") as f:json.dump(report,f,indent=2)
    def save():
        tmp=args.out.with_suffix(args.out.suffix+".tmp");tmp.write_text(json.dumps(report,indent=2)+"\n");tmp.replace(args.out)
    try:
        for n in (2,3,4,5,6,8):
            if n>args.max_workers: break
            if n>4 and not convincing(report["stages"]):
                report["optional_stop"]="previous stage did not show a repeatable >=5% improvement";break
            log=dict(workers=n,memory_samples=[],rounds=[],status="running");report["stages"].append(log);save()
            stage(ctx,n,args,expected,log)
            log["status"]="complete";save()
            print(f"stage {n}: {log['games_per_minute']:.2f} games/min, swap change {log['swap_delta_mib']:+.2f} MiB",flush=True)
        report["status"]="complete"
    except BaseException as e:
        report["status"]="aborted";report["reason"]=str(e) or type(e).__name__
        if report["stages"] and report["stages"][-1]["status"]=="running":report["stages"][-1]["status"]="aborted"
        raise
    finally:
        report["end"]=datetime.now(timezone.utc).isoformat();save()


if __name__=="__main__":main()
