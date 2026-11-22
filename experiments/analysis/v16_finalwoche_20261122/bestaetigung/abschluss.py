"""One-off local supervisor for this exact confirmation, without Git or release writes."""
import argparse
import contextlib
from datetime import datetime
import fcntl
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def save(path, data):
    tmp=path.with_suffix(".tmp")
    with tmp.open("w") as f:
        json.dump(data,f,indent=2); f.write("\n"); f.flush(); os.fsync(f.fileno())
    tmp.replace(path)


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def matches(pid, runner, phase):
    check=subprocess.run(["ps","-p",str(pid),"-o","state=","-o","command="],capture_output=True,text=True)
    line=check.stdout.strip()
    if not line or line[0]=="Z":
        return False
    return str(runner)+" "+phase+" " in line


def run(config_file):
    config=json.loads(config_file.read_text())
    d=Path(config["measurement"]).resolve()
    runner=Path(config["runner"]).resolve()
    analyze=Path(config["analyzer"]).resolve()
    weight=Path(config["checkpoint"]).resolve()
    status=d/"abschlussstatus.json"
    lock=(d/"abschluss.lock").open("a")
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    done=d/"ende.json"
    if done.exists():
        result=json.loads(done.read_text())
        if result["status"]=="complete" and all(sha(d/k)==v for k,v in result["artifacts"].items()):
            return
        raise ValueError("Existing final receipt is invalid")
    if any(sha(Path(config[key]))!=config[key+"_sha256"] for key in ("runner","analyzer","checkpoint")):
        raise ValueError("Pinned local files changed")
    phases=("referenz","kandidat")
    goal={"referenz":800,"kandidat":900}
    jobs=list(config["workers"])
    for j in jobs:
        j["checked"]=False
    children={}
    launches={p:0 for p in phases}
    def start(phase):
        launches[phase]+=1
        log=d/f"zusatz_{phase}_{os.getpid()}_{launches[phase]}.log"
        cmd=[sys.executable,"-u",str(runner),phase,str(d)]
        if phase=="kandidat":
            cmd+=["--weight",str(weight)]
        with log.open("x") as stream:
            child=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,
                                   start_new_session=True)
        children[child.pid]=child
        jobs.append(dict(pid=child.pid,phase=phase,log=str(log),checked=False))
        print(now(),"Hilfsworker",phase,child.pid,flush=True)
    issues=[]
    try:
        while True:
            counts={p:sum(1 for _ in (d/"partien").glob(p+"_*.json")) for p in phases}
            if any(counts[p]>goal[p] for p in phases):
                raise RuntimeError("More than the fixed 1,700 games")
            running={p:0 for p in phases}
            for j in jobs:
                if j["checked"]:
                    continue
                child=children.get(j["pid"])
                live=child.poll() is None if child is not None else matches(j["pid"],runner,j["phase"])
                if live:
                    running[j["phase"]]+=1
                    continue
                j["checked"]=True
                lg=Path(j["log"])
                # Read only the trailer for the technical final receipt, not any games.
                trailer=""
                if lg.is_file():
                    with lg.open("rb") as f:
                        f.seek(max(0,lg.stat().st_size-700))
                        trailer=f.read().decode(errors="replace")
                if f"Worker regulär beendet {j['phase']} " not in trailer:
                    issues.append(dict(when=now(),phase=j["phase"],pid=j["pid"],log=str(lg),
                                       reason="Worker ended without final technical receipt"))
            if all(counts[p]==goal[p] for p in phases):
                if sum(running.values())==0:
                    break
            else:
                # No duplicate seats: the identical immutable runner takes a per-seat
                # lock. One recovery for a failed lane; once one arm finishes, the
                # freed second lane assists the remaining arm.
                for phase in phases:
                    if counts[phase]<goal[phase] and running[phase]==0:
                        if launches[phase]>=2:
                            raise RuntimeError(f"Repeated worker failure in {phase}; see status/logs")
                        start(phase); running[phase]+=1
                if sum(running.values())==1:
                    left=[p for p in phases if counts[p]<goal[p]]
                    if len(left)==1 and running[left[0]]==1 and launches[left[0]]<2:
                        start(left[0]); running[left[0]]+=1
            save(status,{"status":"running","time":now(),"counts":counts,"workers":running,"events":issues})
            time.sleep(15)
        if issues:
            # Source-/runtime mismatch must not silently appear as a finished result.
            # A counted game can still have all rows when the worker's final check failed.
            for phase in phases:
                if any(i["phase"]==phase for i in issues):
                    check=[sys.executable,"-u",str(runner),phase,str(d)]
                    if phase=="kandidat": check+=["--weight",str(weight)]
                    with (d/f"schlusspruefung_{phase}.log").open("a") as f:
                        subprocess.run(check,check=True,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT)
        if any(sha(Path(config[key]))!=config[key+"_sha256"] for key in ("runner","analyzer","checkpoint")):
            raise ValueError("Finalization sources changed")
        with (d/"gesamtauswertung.log").open("w") as f:
            subprocess.run([sys.executable,str(analyze),str(d),str(d)],check=True,stdin=subprocess.DEVNULL,
                           stdout=f,stderr=subprocess.STDOUT)
        report=json.loads((d/"ergebnis.json").read_text())
        if report["count"]!=1700:
            raise ValueError("Incomplete final report")
        result={"status":"complete","time":now(),"cases":1700,"events":issues,
                "artifacts":{k:sha(d/k) for k in ("quellen.json","auswahl.json","ergebnis.json","partien.jsonl.gz")}}
        save(done,result); save(status,result)
        print(now(),"Abschlussbeleg für 1.700 Spiele gespeichert",flush=True)
    except Exception as e:
        save(status,dict(status="error",time=now(),reason=repr(e),events=issues))
        raise


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("config",type=Path)
    run(p.parse_args().config)
