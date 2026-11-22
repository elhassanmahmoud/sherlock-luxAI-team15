"""One-off two-worker comparison from the validated historical source snapshot."""
import argparse
import fcntl
from hashlib import sha256
import json
from datetime import datetime
import os
from pathlib import Path
import subprocess
import sys
import time


def clock():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def save(f,r):
    tmp=f.with_suffix(".tmp")
    with tmp.open("w") as stream:
        json.dump(r,stream,indent=2);stream.write("\n");stream.flush();os.fsync(stream.fileno())
    tmp.replace(f)


def supervise(root,runner,eval_script):
    data=root/"messung"
    lock=(root/"leitung.lock").open("a")
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    subprocess.run([sys.executable,str(runner),str(data),"check"],check=True,stdout=subprocess.DEVNULL)
    processes={}; attempts=[0,0]
    exitcodes={}
    env={**os.environ,"PYTHONHASHSEED":"0","OMP_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1"}
    def start(lane):
        attempts[lane]+=1
        with (root/f"worker_{lane}_{attempts[lane]}.log").open("a") as log:
            return subprocess.Popen([sys.executable,"-u",str(runner),str(data),"frisch",str(lane),"2"],
                                    stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
    for lane in range(2):processes[lane]=start(lane)
    try:
        while len(exitcodes)<2:
            for lane,p in processes.items():
                if lane in exitcodes: continue
                rc=p.poll()
                if rc is None: continue
                if rc and attempts[lane]<2:
                    processes[lane]=start(lane)
                else:
                    exitcodes[lane]=rc
            n=sum(1 for _ in (data/"frisch").glob("*.json"))
            save(root/"status.json",dict(status="running",time=clock(),n=n,pids=[p.pid for p in processes.values()],
                                         attempts=attempts,exitcodes=exitcodes))
            if len(exitcodes)<2:time.sleep(15)
        if any(exitcodes.values()):raise RuntimeError(f"Worker failure: {exitcodes}")
        with (root/"auswertung.log").open("w") as f:
            subprocess.run([sys.executable,str(eval_script),str(data),str(data)],check=True,stdout=f,stderr=subprocess.STDOUT)
        files={s:sha256((data/s).read_bytes()).hexdigest() for s in ("auftrag.json","ergebnis.json","partien.jsonl.gz")}
        save(root/"status.json",dict(status="complete",time=clock(),n=1200,files=files,attempts=attempts))
    except Exception as exc:
        save(root/"status.json",dict(status="error",time=clock(),reason=repr(exc),attempts=attempts))
        raise


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("localdir",type=Path);ap.add_argument("runner",type=Path);ap.add_argument("analysis",type=Path)
    args=ap.parse_args(); supervise(args.localdir,args.runner,args.analysis)
