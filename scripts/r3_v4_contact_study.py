"""Run the pre-registered original-parent sentinel, diagnosis, or conditional fresh panel."""
import argparse
import csv
import fcntl
from hashlib import sha256
import io
import json
from pathlib import Path
import subprocess
import tarfile
from types import SimpleNamespace

from scripts.final_battle_compare import ROOT, WEIGHTS, contract, digest
from scripts.points_hybrid_screen import environment
from scripts.protocol import SIDES
from scripts.r3_v4_parent_source import R3_REF, verify

V4_REF = "b2bd67e43f213cd99669bf3eee759e3fdeb1c0f5"
R3_MODEL = "99b07775582e68efef8b63f545980e969cb0ed3c7d65052b48179508b87dd7b9"
V4_MODEL = "0e8b280cb2173c4efd0d0c94e38119bf2f570dd5af06f52e1b5a7c9743ad7b7f"
V14_MODEL = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
DATA = ROOT/"experiments/analysis/movement_soft_20261115/dev_a_solution/r3"
CSV = ROOT/"experiments/analysis/kaggle3_20261115/student_hyb_v4_mixed.csv"
R3_LOSS=((7150011,0),(7150011,1),(7150035,0),(7150079,1),(7150096,0))
V4_LOSS=((7150003,1),(7150026,0),(7150039,0),(7150068,1),(7150074,0),(7150083,1))
KEY = ("arm","opponent","seed","side")
GAME = ("game_win","our_wins","opp_wins","our_points","opp_points","steps")


def panel(stage):
    if stage == "sentinel":
        return [(arm,"solution92",seed,f"player_{seat}") for arm in ("r3","v4") for seed,seat in ((7150011,0),(7150068,1))]
    if stage == "diagnosis":
        return [("contact","solution92",seed,f"player_{seat}") for seed,seat in (*R3_LOSS,*V4_LOSS)]
    if stage == "screen":
        return [(arm,opp,seed,side) for seed in range(7170260,7170276) for side in SIDES
                for arm in ("r3","v4","v14","contact") for opp in ("solution92","kaggle3","v14")
                if arm!="v14" or opp!="v14"]
    raise ValueError(stage)


def source(repo, ref):
    blob = subprocess.check_output(["git","-C",str(repo),"archive",ref,"agents/sherlock","scripts"])
    with tarfile.open(fileobj=io.BytesIO(blob)) as archive:
        return {m.name:archive.extractfile(m).read() for m in archive if m.isfile() and m.name.endswith(".py")}


def binding(repo):
    from scripts.r3_v4_contact_agent import R3_MODEL as r3, V4_MODEL as v4
    if (digest(r3),digest(v4),digest(WEIGHTS)) != (R3_MODEL,V4_MODEL,V14_MODEL):
        raise ValueError("Different frozen models")
    archives = [DATA/"manifest.json", DATA/"games.jsonl", DATA/"completed.json", CSV]
    h = [digest(p) for p in archives]
    expected = ["06452ab615c2dd35f1b4e63261ce0f3d5014dabe8c35840b3113fef705e67dde",
                "7d407d4fd7322f65d6ae5d27a87a157e2cf0a144b9eac303a93c86db9fea27ae",
                "75cb58f9439c12784688b2eac1dcb4cbe753d040027993be863c0a214d5049fe",
                "dab8ad9200433eb46b311992ef940e8110aeaf520ef4b1995b81b7403b80381c"]
    if h != expected: raise ValueError("Different historical parents or rows")
    marks = json.loads(archives[0].read_bytes())
    legacy = verify(source(repo,R3_REF), marks["sources"])
    native = source(repo,V4_REF)
    for f in native:
        if (ROOT/f).read_bytes()!=native[f]: raise ValueError(f"Different original v4 source {f}")
    basis = contract(SimpleNamespace(candidate="v14",model=None,opponents="solution92,kaggle3",first=7170260,maps=16))
    src = dict(basis["sources"], **legacy)
    for f in ("scripts/r3_v4_contact_agent.py","scripts/r3_v4_contact_study.py","scripts/r3_v4_parent_source.py",
              "experiments/analysis/r3_v4_contact_20261115/PLAN.md","scripts/train_combat_advice.py",
              "scripts/protocol.py","scripts/points_hybrid_screen.py","scripts/variants.py"):
        src[f] = digest(ROOT/f)
    for p in (ROOT/"lux").glob("*.py"):
        src[str(p.relative_to(ROOT))] = digest(p)
    # Bind every prepared legacy file, including utility imports, to the two fixed Git trees.
    for p in sorted((ROOT/"r3_native").rglob("*.py")):
        src[str(p.relative_to(ROOT))] = digest(p)
    stamp = dict(r3_parent=R3_REF, v4_parent=V4_REF, r3=R3_MODEL, v4=V4_MODEL, v14=V14_MODEL,
                 files_sha256=sha256(json.dumps(src,sort_keys=True).encode()).hexdigest(),
                 engine=environment(),historical=h)
    old = {}
    for r in map(json.loads,(DATA/"games.jsonl").read_text().splitlines()):
        key=("r3","solution92",r["seed"],r["side"])
        old[key] = dict(zip(GAME,[int(r[k]) for k in ("result","wins","losses","points","opp_points","steps")]))
    with CSV.open() as f:
        for r in csv.DictReader(f):
            if r["opponent"] == "solution92":
                old["v4","solution92",int(r["seed"]),r["side"]] = {k:int(r[k]) for k in GAME}
    for arm, group in (("r3",R3_LOSS),("v4",V4_LOSS)):
        losses=sorted((s,int(t[-1])) for (a,o,s,t),r in old.items() if a==arm and not r["game_win"])
        if tuple(losses)!=group or sum(k[0]==arm for k in old)!=200: raise ValueError("Wrong historic outcome roster")
    return stamp,old


def target(out, stage, k):
    return out/stage/("_".join(map(str,k))+".json")


def accept(stage,out,stamp,old):
    keys = panel(stage)
    if set((out/stage).glob("*.json")) != {target(out,stage,k) for k in keys}:
        raise ValueError(f"Incomplete or extra {stage} rows")
    rows={}
    for k in keys:
        r=json.loads(target(out,stage,k).read_bytes())
        g=r["game"]
        if (r["source"]!=stamp or tuple(r[f] for f in KEY)!=k or g["steps"]!=303 or g["our_wins"]+g["opp_wins"]!=3
                or g["game_win"] != int(g["our_wins"]>=2)):
            raise ValueError(f"Different source, key or course outcome {k}")
        if stage=="sentinel" and g!=old[k]: raise ValueError(f"Different parent result {k}: {g} vs {old[k]}")
        rows[k]=r
    return rows


def diagnosis(rows):
    groups = {arm:[rows["contact","solution92",s,f"player_{t}"]["game"]["game_win"] for s,t in roster]
              for arm,roster in (("r3",R3_LOSS),("v4",V4_LOSS))}
    wins={k:sum(v) for k,v in groups.items()}
    return dict(group_wins=wins, total_wins=sum(wins.values()), passes=all(wins.values()) and sum(wins.values())>6)


def prerequisites(stage,out,stamp,old):
    if stage in ("diagnosis","screen"):
        accept("sentinel",out,stamp,old)
    if stage=="screen" and not diagnosis(accept("diagnosis",out,stamp,old))["passes"]:
        raise ValueError("Directed diagnosis gate failed")


def run(a):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    import torch
    from scripts.common import make_opponent,play_game
    from scripts.experiment import limit_threads
    from scripts.par_eval import require_no_agent_errors
    from scripts.r3_v4_contact_agent import ContactAgent,make_r3,make_v4
    from scripts.train_combat_advice import publish_json
    limit_threads()
    torch.manual_seed(0)
    stamp, old = binding(a.repo)
    out=a.out.resolve()
    prerequisites(a.stage,out,stamp,old)
    (out/a.stage).mkdir(parents=True,exist_ok=True)
    actors={}
    env=None
    with (out/(a.stage+".lock")).open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            for k in panel(a.stage):
                arm,foe,seed,seat=k
                p=target(out,a.stage,k)
                if p.exists():
                    prior=json.loads(p.read_bytes())
                    if prior["source"]!=stamp or tuple(prior[t] for t in KEY)!=k or (a.stage=="sentinel" and prior["game"]!=old[k]):
                        raise ValueError("Old or unreproduced game")
                    continue
                if env is None: env=LuxAIS3GymEnv(numpy_output=True)
                if arm not in actors:
                    actors[arm]={"r3":make_r3,"v4":make_v4,"contact":ContactAgent,
                                 "v14":lambda s:make_opponent("self",s,str(WEIGHTS))}[arm](seat)
                agent=actors[arm]
                other=SIDES[1-SIDES.index(seat)]
                rival=make_opponent("self" if foe=="v14" else foe,other,str(WEIGHTS))
                row=play_game(env,agent,rival,seed,seat,False)
                require_no_agent_errors(agent,rival)
                if arm=="v4": require_no_agent_errors(agent.v14,agent.student)
                g={t:int(row[t]) for t in GAME}
                if g["steps"]!=303 or g["our_wins"]+g["opp_wins"]!=3: raise ValueError("Incomplete game")
                stats=dict(agent.counts) if arm=="contact" else {}
                publish_json(p,dict(zip(KEY,k),game=g,source=stamp,routing=stats))
                print(k,g,stats,flush=True)
                if a.stage=="sentinel" and old[k]!=g: raise ValueError(f"Unexpected original score. Expected {old[k]}")
        finally:
            if env is not None: env.close()
    if stamp != binding(a.repo)[0]: raise ValueError("Source changed during run")
    rows=accept(a.stage,out,stamp,old)
    if a.stage=="diagnosis": print(json.dumps(diagnosis(rows)),flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage",choices=("sentinel","diagnosis","screen"))
    p.add_argument("--repo",required=True,type=Path,help="Git database containing both frozen parents")
    p.add_argument("--out",required=True,type=Path)
    run(p.parse_args())
