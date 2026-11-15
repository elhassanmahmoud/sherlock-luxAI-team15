"""One fixed R3 reflection screen and its conditionally eligible independent confirmation."""
import argparse
import fcntl
from hashlib import sha256
from importlib import metadata,util
import json
import os
from pathlib import Path
import platform
from types import SimpleNamespace

from scripts import final_battle_assess as audit
from scripts import final_battle_compare as runner
from scripts.final_battle_select import OPPONENTS,SEATS,checked_run_files
from scripts.train_combat_advice import publish_json

ARCHIVE = "8f927db8b83927899d7dba2eeaf0fad23facba5901e05fe430f59632814857b1"
R3 = "99b07775582e68efef8b63f545980e969cb0ed3c7d65052b48179508b87dd7b9"
ENGINE = "551a263ede77ef6d64c0cac6faa02b5990eba3134942118783bb28cbdfb92b80"
FROZEN = {"v14":"b838dc94ca403992d92d1b38a086b957ddaa9f09d53f7c9621599cbd80fd0a62",
          "external":"adab51bd97b625718c0a9eb387afa61b45f3f66d409421dca08a7b3d148812ba",
          "direct":"7653cf6d331d01cdeced270f6d7d649f43a9d28dc41d1bbded3266dea3d7761f"}
ACTORS = {"v14":"agents.sherlock.main:Agent_x", "r3":"scripts.selective_advice_agent:SelectiveAdviceAgent",
          "diagonal":"scripts.r3_diagonal:DiagonalAgent"}


def schedule(stage):
    if stage=="screen":
        maps=range(7286000,7286016)
        return {"diagonal":(maps,(*OPPONENTS,"v14")), "v14":(maps,OPPONENTS),"r3":(maps,OPPONENTS)}
    if stage=="confirm":
        maps=range(7286100,7286160)
        return {"v14":(maps,OPPONENTS),"diagonal":(maps,OPPONENTS),"direct":(range(7286200,7286260),("v14",))}
    raise ValueError(f"Unregistered stage {stage}")


def json_sha(data):
    return sha256(json.dumps(data,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def manifest(a,stage,arm):
    raw=a.archive.read_bytes()
    if sha256(raw).hexdigest()!=ARCHIVE or runner.digest(a.model)!=R3:
        raise ValueError("Wrong offline confirmation or R3 weights")
    offline=json.loads(raw)
    m=offline["validation"]["mixed"]
    if (offline["model_sha256"]!=R3 or offline["passes_offline_gate"] is not True or
            m["pair"]["gained"] <= m["pair"]["lost"] or m["reflected"]["hurt"] > m["original"]["hurt"]):
        raise ValueError("Offline selection failed")
    for name,digest in offline["sources"].items():
        if runner.digest(runner.ROOT/name)!=digest:
            raise ValueError(f"Changed offline comparison source {name}")
    actor="diagonal" if arm=="direct" else arm
    seeds,opps=schedule(stage)[arm]
    policy="v14" if actor=="v14" else "selective_movement"
    conf=runner.contract(SimpleNamespace(candidate=policy,model=None if actor=="v14" else a.model,
                         opponents=",".join(opps),first=seeds.start,maps=len(seeds)))
    expected="v14" if actor=="v14" else "external" if "kaggle3" in opps else "direct"
    if json_sha(conf["sources"]) != FROZEN[expected] or conf["weights"]!=audit.V14_SHA:
        raise ValueError("Different original V14 / R3 / native opponent source tree")
    paths=set((runner.ROOT/"agents").rglob("*.py")) | set((runner.ROOT/"lux").glob("*.py"))
    paths.update(runner.ROOT/"scripts"/f for f in ("r3_diagonal.py","r3_diagonal_games.py","__init__.py",
                 "protocol.py","variants.py","fetch_kaggle3.py","final_battle_assess.py","final_battle_select.py",
                 "train_combat_advice.py","residual_ensemble_compare.py"))
    envdir=Path(util.find_spec("luxai_s3").origin).parent
    engine={p.name:runner.digest(p) for p in envdir.glob("*.py")}
    if json_sha(engine)!=ENGINE:
        raise ValueError("Lux engine differs from the registered build")
    environment=dict(engine=engine, python=platform.python_version(),machine=platform.machine(),platform=platform.system(),
                     versions={k:metadata.version(k) for k in ("numpy","scipy","jax","jaxlib","torch","luxai-s3")},
                     flags={k:os.environ.get(k) for k in ("JAX_PLATFORMS","XLA_FLAGS","CUDA_VISIBLE_DEVICES","PYTHONHASHSEED")})
    return dict(conf,candidate=actor,actor_import=ACTORS[actor],offline_sha256=ARCHIVE,environment=environment,
                study_sources={str(p.relative_to(runner.ROOT)):runner.digest(p) for p in sorted(paths)})


def play(a,stage,arm):
    seeds,opps=schedule(stage)[arm]
    dest=a.out/stage/arm
    dest.mkdir(parents=True,exist_ok=True)
    with (dest/".run.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        before=manifest(a,stage,arm)
        actor=before["candidate"]
        record=dest/"manifest.json"
        if record.exists():
            if json.loads(record.read_text())!=before:
                raise ValueError("Different game manifest on resume")
        else:
            if (dest/"games.jsonl").exists() or (dest/"completed.json").exists():
                raise ValueError("Game evidence exists without its source manifest")
            publish_json(record,before)
        if not (dest/"completed.json").exists():
            # Use the registered single-worker initializer and game evaluator; only the adviser class differs.
            policy="v14" if actor=="v14" else "selective_movement"
            model=None if actor=="v14" else str(a.model)
            jobs=[(opp,s,side) for s in seeds for opp in opps for side in SEATS]
            path=dest/"games.jsonl"
            saved=[json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
            keys={(r["opponent"],r["seed"],r["side"]) for r in saved}
            if len(keys)!=len(saved) or not keys.issubset(jobs):
                raise ValueError("Duplicate or extraneous saved game")
            for row in saved:
                if (row["candidate"]!=actor or row["steps"]!=303
                        or any(type(row[k]) is not int for k in ("seed","steps","wins","losses"))
                        or row["wins"] not in range(4) or row["wins"]+row["losses"]!=3
                        or type(row["result"]) not in (int,float) or row["result"]!=int(row["wins"]>row["losses"])
                        or row["study"].get("movement",0)!=row["study"].get("changed_unit_orders",0)):
                    raise ValueError("Invalid saved game")
            pending=[k for k in jobs if k not in keys]
            if pending:
                unmodified=runner.POLICIES[policy]
                runner.POLICIES[policy]=ACTORS[actor]
                try:
                    runner.init_worker(policy,model)
                finally:
                    runner.POLICIES[policy]=unmodified
                try:
                    cls=type(runner.evaluate.agent)
                    if cls.__module__+":"+cls.__name__!=ACTORS[actor]:
                        raise ValueError("Live agent class does not match the registered arm")
                    with path.open("a") as stream:
                        for opp,seed,side in pending:
                            row=runner.evaluate((policy,opp,seed,side,model))
                            row["candidate"]=actor
                            stream.write(json.dumps(row)+"\n")
                            stream.flush()
                            saved.append(row)
                finally:
                    runner.evaluate.env.close()
            if manifest(a,stage,arm)!=before:
                raise ValueError("Source or runtime changed during play")
            summary={}
            for opp in opps:
                matches=[r for r in saved if r["opponent"]==opp]
                summary[opp]=dict(played=len(matches),wins=sum(r["result"] for r in matches),
                                  matches=sum(r["wins"] for r in matches))
            publish_json(dest/"completed.json",dict(summary=summary,rows_sha256=runner.digest(path)))
        return checked(a,stage,arm,before)


def checked(a,stage,arm,expected=None):
    seeds,opps=schedule(stage)[arm]
    before=expected or manifest(a,stage,arm)
    rows,m,h=checked_run_files(a.out/stage/arm,before["candidate"],seeds,opps)
    if m != before or any(r["study"].get("movement",0)!=r["study"].get("changed_unit_orders",0) for r in rows.values()):
        raise ValueError("Unexpected game source or non-movement substitution")
    return audit.Run(m,rows,h)


def report(a,stage):
    runs={arm:checked(a,stage,arm) for arm in schedule(stage)}
    seeds=schedule(stage)["diagonal"][0]
    phase=audit.Phase(runs["v14"],runs["diagonal"],runs.get("direct",runs["diagonal"]),
                      seeds,schedule(stage).get("direct",(seeds,))[0])
    result=audit.summarize(phase,stage)
    if stage=="screen":
        contrast=audit.summarize(audit.Phase(runs["r3"],phase.candidate,phase.direct,seeds,seeds),"screen")
        for row in contrast["by_opponent"].values():
            row["r3_wins"]=row.pop("v14_wins")
        result["r3_control"]={"files":runs["r3"].hashes,"by_opponent":contrast["by_opponent"],"external":contrast["external"]}
        result["gates"]["external_strictly_above_r3"]=contrast["external"]["net_wins"]>0
        result["game_gates_pass"]=all(result["gates"].values())
    result.update(offline_sha256=ARCHIVE,bootstrap={"draws":10000,"seed":2711,"unit":"whole map with both seats and external opponents"})
    return result


def selection(a):
    value=report(a,"screen")
    path=a.out/"screen/assessment.json"
    if not value["game_gates_pass"] or not path.is_file() or json.loads(path.read_text())!=value:
        raise ValueError("Independent games require the verified positive selection")
    return value


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("operation",choices=("play","assess"))
    p.add_argument("stage",choices=("screen","confirm"))
    p.add_argument("--arm",choices=("diagonal","r3","v14","direct"))
    for k in ("archive","model","out"):
        p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args()
    if a.stage=="confirm":
        selection(a)
    if a.operation=="play":
        if a.arm and a.arm not in schedule(a.stage):
            p.error("Unregistered arm for this stage")
        for arm in ([a.arm] if a.arm else schedule(a.stage)):
            play(a,a.stage,arm)
    else:
        if a.arm:
            p.error("Assess a complete stage")
        value=report(a,a.stage)
        if a.stage=="confirm":
            value["screen_sha256"]=runner.digest(a.out/"screen/assessment.json")
        dest=a.out/a.stage/"assessment.json"
        if not dest.exists():
            publish_json(dest,value)
        elif value!=json.loads(dest.read_text()):
            raise ValueError("Different existing assessment")
        print(json.dumps(value,indent=2))
