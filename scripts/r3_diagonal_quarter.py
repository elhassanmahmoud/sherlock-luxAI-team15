"""One target-opponent replication on the first 100 published confirmation maps."""
import argparse
import fcntl
from hashlib import sha256
from importlib import metadata, util
import json
import os
from pathlib import Path
import platform
import zipfile

ROOT = Path(__file__).resolve().parents[1]
Q = ROOT / "references"
MAPS = range(7158000,7158100)
SEATS = ("player_0","player_1")
KEYS = [("solution92",seed,seat) for seed in MAPS for seat in SEATS]
REFERENCE_SHA = {
    "original.json":"e06715ca12db558f7055284bff5ff51ae8416b237722f80421d24f46eaaf8894",
    "previous.json":"0e19f04f02db6e56b595c70b5e4ced682f5860a4efc08f0809b508fdd53bc030",
    "parity.json":"f6fae49a5d3b2e290e5a5ffecd20fbf43af475aebbf5ffa6726e4ed2b521c9b5",
    "reference_reproduction.json":"d1123e38fac3fb0218a3b4d712c7a045c5ae620534b772bc8e337cd45f96aced",
    "original_r3_400.json":"27f6033f8a509e7b0a63b38586abebc4c0870f6cb5cb7780e1ead86a7054ecba",
    "diagonal.zip":"feaf20aa7058ad856634cd8a5a2daf56bfc6da4f6be296cff6d98fc55eefac25",
    "r3_soft.pth":"99b07775582e68efef8b63f545980e969cb0ed3c7d65052b48179508b87dd7b9",
}
STUDY = Path("experiments/analysis/movement_soft_20261115/shared_400/measured")


def need(ok, why):
    if not ok: raise ValueError(why)


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def store(path, data):
    with path.open("x") as f:
        json.dump(data,f,indent=2,allow_nan=False)
        f.write("\n")


def contract():
    for n,h in REFERENCE_SHA.items():
        need(digest(Q/n)==h,n)
    base=json.loads((Q/"original.json").read_bytes())
    for name,h in {**base["sources"],**base["study_sources"]}.items():
        need(digest(ROOT/name)==h,name)
    need(digest(ROOT/"agents/sherlock/weights/agent_p0.pth")==base["weights"],"V14")
    parity=json.loads((Q/"parity.json").read_bytes())
    with zipfile.ZipFile(Q/"diagonal.zip") as package:
        need(sha256(package.read("sherlock/weights/agent.pth")).hexdigest()==parity["course_weights_sha256"],"course weights")
    need(parity["result"]=="passed" and sum(g["equal_action_matrices"] for g in parity["games"])==606
         and base["actor_import"]=="scripts.r3_diagonal:DiagonalAgent","diagonal parity")
    e=base["environment"]; engine=Path(util.find_spec("luxai_s3").origin).parent
    need({p.name:digest(p) for p in engine.glob("*.py")}==e["engine"],"engine")
    need({n:metadata.version(n) for n in e["versions"]}==e["versions"],"runtime versions")
    need((platform.python_version(),platform.machine(),platform.system())==(e["python"],e["machine"],e["platform"]),"platform")
    need({k:os.environ.get(k) for k in e["flags"]}==e["flags"],"runtime flags")
    return dict(candidate="diagonal",actor_import=base["actor_import"],opponents=["solution92"],first=MAPS.start,
                maps=len(MAPS),weights=base["weights"],model=base["model"],previous_files=REFERENCE_SHA,
                study_sha256=digest(Path(__file__)),assessment_helper_sha256=digest(ROOT/"scripts/r3_shared_confirmation.py"))


def row_ok(r,key,candidate):
    need((r["opponent"],r["seed"],r["side"])==key and r["candidate"]==candidate and
         all(type(r[n]) is int for n in ("seed","steps","wins","losses","points","opp_points"))
         and r["steps"]==303 and r["wins"] in range(4) and r["wins"]+r["losses"]==3
         and r["result"]==int(r["wins"]>r["losses"]) and min(r["points"],r["opp_points"])>=0
         and r["study"].get("movement",0)==r["study"].get("changed_unit_orders",0),f"Bad game {key}")


def play(out):
    from scripts import final_battle_compare as battle
    from scripts.final_battle_select import checked_run_files
    os.chdir(ROOT)
    out.mkdir(parents=True,exist_ok=True)
    with (out/".lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        config=contract()
        record=out/"manifest.json"; path=out/"games.jsonl"; done=out/"completed.json"
        if record.exists():
            need(json.loads(record.read_bytes())==config,"different manifest on resume")
        else:
            need(not path.exists() and not done.exists(),"unbound games")
            store(record,config)
        saved=[json.loads(s) for s in path.read_bytes().splitlines()] if path.exists() else []
        need(len(saved)<=len(KEYS),"too many saved games")
        for r,k in zip(saved,KEYS): row_ok(r,k,"diagonal")
        if done.exists():
            checked_run_files(out,"diagonal",MAPS,("solution92",))
            return
        if len(saved)<len(KEYS):
            policy="selective_movement"; model=str(Q/"r3_soft.pth")
            battle.POLICIES[policy]=config["actor_import"]
            battle.init_worker(policy,model)
            try:
                a=battle.evaluate.agent
                need(type(a).__module__+":"+type(a).__name__==config["actor_import"],"actual class")
                with path.open("a") as f:
                    for key in KEYS[len(saved):]:
                        r=battle.evaluate((policy,*key,model))
                        r["candidate"]="diagonal";row_ok(r,key,"diagonal")
                        f.write(json.dumps(r,allow_nan=False)+"\n"); f.flush(); saved.append(r)
                        print(key[1],key[2],r["result"],flush=True)
            finally:
                battle.evaluate.env.close()
        need(contract()==config,"source drift")
        store(done,dict(rows_sha256=digest(path),summary={"solution92":dict(played=len(saved),
                   wins=sum(r["result"] for r in saved),matches=sum(r["wins"] for r in saved))}))
        checked_run_files(out,"diagonal",MAPS,("solution92",))


def assess(repo,out):
    import itertools
    import numpy as np
    from scripts import r3_shared_confirmation as shared
    from scripts.final_battle_select import checked_run_files
    got,meta,seals=checked_run_files(out,"diagonal",MAPS,("solution92",))
    need(meta==contract(),"diagonal manifest")
    for key,r in got.items(): row_ok(r,key,"diagonal")
    measured=repo/STUDY
    need(digest(measured/"reproduction.json")==REFERENCE_SHA["reference_reproduction.json"]
         and digest(measured/"r3/manifest.json")==REFERENCE_SHA["original_r3_400.json"],"external R3/V14 reference")
    # Once the deterministic prefix exists it can be compared immediately, without reading a partially written last line.
    p=measured/"r3/games.jsonl"
    with p.open("rb") as f: prefix=list(itertools.islice(f,400))
    need(len(prefix)==400 and all(line.endswith(b"\n") for line in prefix),"R3 has not finished all 400 prefix rows")
    keys=[(o,s,t) for s in MAPS for o in ("kaggle3","solution92") for t in SEATS]
    original={}
    for line,key in zip(prefix,keys,strict=True):
        r=json.loads(line);row_ok(r,key,"selective_movement")
        if key[0]=="solution92": original[key]=shared.score(r)
    csv_refs=shared.reference_tables(repo)
    arms=dict(r3=original,v14=csv_refs["v14"],v15=csv_refs["v4_mixed"],diagonal={k:shared.score(v) for k,v in got.items()})
    def arr(data): return np.asarray([data[k][:2] for k in KEYS]).reshape(len(MAPS),2,2)
    matrices={label:arr(data) for label,data in arms.items()}; candidate=matrices["diagonal"]; totals={}; comparisons={}
    for label,a in matrices.items():
        totals[label]=dict(games=200,wins=int(a[:,:,0].sum()),match_wins=int(a[:,:,1].sum()),matches=600,
            winrate_ci95=shared.bounds(a[:,:,0].mean(1)),wins_per_seat=dict(zip(SEATS,map(int,a[:,:,0].sum(0)))),
            losses=[(s,t) for i,s in enumerate(MAPS) for j,t in enumerate(SEATS) if a[i,j,0]==0])
        if label=="diagonal": continue
        delta=candidate-a
        comparisons[label]=dict(gained=[k[1:] for k,x in zip(KEYS,delta[:,:,0].flat) if x>0],
            lost=[k[1:] for k,x in zip(KEYS,delta[:,:,0].flat) if x<0],
            net_games=int(delta[:,:,0].sum()),winrate_delta=float(delta[:,:,0].mean()),
            ci95=shared.bounds(delta[:,:,0].mean(1)),match_rate_delta=float(delta[:,:,1].mean()/3),
            match_ci95=shared.bounds(delta[:,:,1].mean(1)/3))
    report=dict(arm_totals=totals,paired_candidate_minus_reference=comparisons,files=dict(diagonal=seals,
        csv={k:h for k,(_,h) in shared.CSV.items()},r3_400row_prefix=sha256(b"".join(prefix)).hexdigest(),
        r3_manifest=REFERENCE_SHA["original_r3_400.json"]),bootstrap="10000 whole paired maps with both seats, RNG 2711",
        scope="Solution_92 only; no release decision")
    destination=out/"assessment.json"
    if destination.exists(): need(json.loads(destination.read_bytes())==json.loads(json.dumps(report)),"assessment drift")
    else: store(destination,report)
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("check","play","assess"));p.add_argument("--repo",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path);a=p.parse_args()
    if a.mode=="check": print(json.dumps(contract(),indent=2))
    if a.mode=="play": play(a.out.resolve())
    if a.mode=="assess": assess(a.repo.resolve(),a.out.resolve())
