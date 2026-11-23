"""Confirm the frozen late move-value model on 120 unused, unfiltered maps."""
import argparse
from collections import Counter
import fcntl
import gzip
from hashlib import sha256
import json
import os
from pathlib import Path

import numpy as np
import torch

from spielen import HERE, PACKAGE, Policy, ValueNet, check_qualification, make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.fetch_kaggle3 import verify
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def verify_source():
    weight = check_qualification(True)
    screen = json.loads((HERE / "auswahl_ergebnis.json").read_text())
    archive = HERE / "auswahl_partien.jsonl.gz"
    if (not screen["qualifies"] or not all(screen["gates"].values()) or screen["actual_games"] != 400
            or screen["raw_sha256"] != digest(archive) or screen["seeds"] != list(range(160364400,160364440))
            or not verify() or os.environ.get("PYTHONHASHSEED") != "0"):
        raise ValueError("Unqualified selection or inconsistent opponents")
    files = [HERE.parent / "BEWEGUNG_BESTAETIGEN.md", HERE / "auswahl_ergebnis.json", HERE / "replikation.json",
             HERE / "PLAN.md", HERE / "berater.py", HERE / "spielen.py", Path(__file__), PACKAGE, weight]
    return {p.name:digest(p) for p in files}


def cases():
    return [(s,t,o,a) for s in range(160365000,160365120) for t in (0,1)
            for o in ("solution92","kaggle3","v16") for a in ("original","adviser")
            if o != "v16" or (a == "adviser" and s < 160365040)]


def validate(row, case, version):
    if (tuple(row[k] for k in ("seed","team","opponent","arm")) != case or row["source"] != version
            or row["steps"] != 303 or row["point_counting_version"] != 2 or row["changes"] < 0
            or row["our_wins"] + row["opp_wins"] != 3 or row["game_win"] != int(row["our_wins"] >= 2)
            or (row["arm"] == "original" and row["changes"])):
        raise ValueError(f"Invalid completed game {case}")


def simulate(env, case, net, version):
    seed,team,rival,arm=case
    side=f"player_{team}"
    other=f"player_{1-team}"
    agent=r3_package_agent(side, PACKAGE)
    if arm=="adviser":
        agent=Policy(agent,net)
    enemy=r3_package_agent(other, PACKAGE) if rival=="v16" else make_opponent(rival,other)
    g=play_game(env,agent,enemy,seed,side,train=False)
    require_no_agent_errors(agent.base if arm=="adviser" else agent,enemy)
    row={k:g[k] for k in ("steps","game_win","our_wins","opp_wins","our_points","opp_points","point_counting_version")}
    row.update(zip(("seed","team","opponent","arm"), case))
    row.update(source=version,changes=agent.changed if arm=="adviser" else 0)
    validate(row,case,version)
    return row


def run(folder, worker):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads()
    contract=verify_source()
    version=sha256(json.dumps(contract,sort_keys=True).encode()).hexdigest()
    folder.mkdir(exist_ok=True,parents=True)
    leases=folder/".leases"
    leases.mkdir(exist_ok=True)
    with (leases/"source.lock").open("a+") as guard:
        fcntl.flock(guard,fcntl.LOCK_EX)
        src=folder/"herkunft.json"
        if not src.exists(): src.write_text(json.dumps(contract,indent=2,sort_keys=True)+"\n")
        if json.loads(src.read_text())!=contract: raise ValueError("Different experiment source")
    net=ValueNet().eval()
    with np.load(HERE/"wertberater.npz",allow_pickle=False) as z:
        net.load_state_dict({k:torch.from_numpy(z[k]) for k in z.files})
    panel=cases()
    start=worker*179%len(panel)
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for case in panel[start:]+panel[:start]:
            name="_".join(map(str,case))
            target=folder/(name+".json")
            if target.exists():
                validate(json.loads(target.read_text()),case,version)
                continue
            with (leases/(name+".lock")).open("a+") as lease:
                try:
                    fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:
                    continue
                if target.exists():
                    validate(json.loads(target.read_text()),case,version)
                    continue
                r=simulate(env,case,net,version)
                tmp=target.with_suffix(f".{os.getpid()}.tmp")
                tmp.write_text(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n")
                tmp.replace(target)
                print(name,flush=True)
    finally:
        env.close()


def summarize(folder):
    contract=verify_source()
    if json.loads((folder/"herkunft.json").read_text())!=contract: raise ValueError("Changed source")
    version=sha256(json.dumps(contract,sort_keys=True).encode()).hexdigest()
    data={}
    for case in cases():
        row=json.loads((folder/("_".join(map(str,case))+".json")).read_text())
        validate(row,case,version)
        data[case]=row
    if len(data)!=1040: raise ValueError("Incomplete trial")
    scores={}
    distributions={}
    for opponent in ("solution92","kaggle3"):
        delta=[]
        arms={k:Counter() for k in ("original","adviser")}
        changed=[]
        for s in range(160365000,160365120):
            card=[]
            for t in (0,1):
                v,c=(data[s,t,opponent,k] for k in ("original","adviser"))
                if c["changes"]==0 and any(v[k]!=c[k] for k in ("game_win","our_wins","opp_wins","our_points","opp_points")):
                    raise ValueError("A behaviorally identical seat changed")
                for row in (v,c):
                    arms[row["arm"]].update({k:row[k] for k in ("game_win","our_wins","our_points","opp_points","changes")})
                swing=c["game_win"]-v["game_win"]
                if swing: changed.append(dict(seed=s,team=t,delta=swing))
                card.append(swing)
            delta.append(np.mean(card))
        distributions[opponent]=np.array(delta)
        scores[opponent]=dict(arms=arms,n_per_arm=240,swings=changed)
    primary=(distributions["solution92"]+distributions["kaggle3"])/2
    rng=np.random.default_rng(231150)
    indices=rng.integers(0,120,size=(20000,120))
    draws=100*primary[indices].mean(axis=1)
    ci=np.percentile(draws,[2.5,97.5]).tolist()
    for k,d in distributions.items():
        scores[k].update(delta_pp=float(100*d.mean()),ci95=np.percentile(100*d[indices].mean(1),[2.5,97.5]).tolist())
    direct=np.array([[data[s,t,"v16","adviser"]["game_win"] for t in (0,1)] for s in range(160365000,160365040)])
    direct_draws=direct.mean(1)[rng.integers(0,40,(20000,40))].mean(1)
    gates=dict(primary=ci[0]>0,solution=distributions["solution92"].sum()>=0,
               kaggle=distributions["kaggle3"].sum()>=0,direct=direct.sum()>=40)
    # If another of these movement screens qualifies later, use the respective stricter interval.
    intervals={str(n):np.percentile(draws,[2.5/n,100-2.5/n]).tolist() for n in (1,2,3)}
    payload=gzip.compress(("".join(json.dumps(v,separators=(",",":"),sort_keys=True)+"\n" for v in data.values())).encode(),mtime=0)
    (HERE/"bestaetigung_partien.jsonl.gz").write_bytes(payload)
    output=dict(games=1040,maps=120,source=contract,evidence_sha256=sha256(payload).hexdigest(),external=scores,
                direct=dict(wins=int(direct.sum()),games=80,ci95=np.percentile(100*direct_draws,[2.5,97.5]).tolist()),
                primary_delta_pp=float(100*primary.mean()),primary_ci95=ci,family_intervals=intervals,
                gates={k:bool(v) for k,v in gates.items()},all_gates=all(gates.values()))
    (HERE/"bestaetigung_ergebnis.json").write_text(json.dumps(output,indent=2)+"\n")
    print(output["gates"],ci,flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--worker",type=int)
    group.add_argument("--report",action="store_true")
    args=p.parse_args()
    if args.report:summarize(args.folder)
    else:run(args.folder,args.worker)
