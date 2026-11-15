"""Registered diagnostic and gated panels for a movement fallback after losing match one."""
import argparse
import fcntl
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

from scripts import r3_diagonal_games as original
from scripts import final_battle_assess as audit
from scripts.final_battle_select import OPPONENTS, SEATS, checked_run_files
from scripts.train_combat_advice import publish_json

runner=original.runner
HISTORY=Path("experiments/analysis/movement_reflection_20261115")
CHECKPOINT=Path("experiments/candidates/movement_dagger_20261115/r3_soft.pth")
ACTORS={**original.ACTORS,"after_loss":"scripts.r3_diag_after_loss:AfterLossAgent"}
HISTORICAL={
    "v14":("95d3be78f62022e2431f6c7ebdbc4694a50753bfba1c14728639a1a72568768b",
           "88ade28462a24f96d7e7120b2d6157a04d65d034bd8cc5a2bdbcec656904f41f"),
    "diagonal":("e06715ca12db558f7055284bff5ff51ae8416b237722f80421d24f46eaaf8894",
                "3aa62eee437e849e1c745d48adf25891b83973b76e4b50052bd96b077daa0e84"),
    "direct":("e94d9d29faef522cc5c21ec0192cd7a4597d447de16842c744ce4736d3cfb5eb",
              "7e48be55e7a8191d12d439c4a5a00d612f597f00c9d8ba3fd50012e93801d578")}
CONTROL=[("solution92",7286100,"player_0"),("solution92",7286101,"player_1")]
KAGGLE=[("kaggle3",s,p) for s in (7286135,7286141) for p in SEATS]
SOLUTION=[("solution92",7286124,p) for p in SEATS]+[("solution92",7286142,"player_1")]
TARGET=[("solution92",7286137,p) for p in SEATS]
MATCH_KEYS=("wins","losses","result","points","opp_points","steps")


def layout(stage):
    if stage=="screen":
        seeds=range(7170800,7170816); direct=seeds
        return {"diagonal":(seeds,OPPONENTS),"v14":(seeds,OPPONENTS),"after_loss":(seeds,OPPONENTS),"direct":(direct,("v14",))}
    if stage=="solution":
        return {arm:(range(7170960,7170976),("solution92",)) for arm in ("diagonal","v14","after_loss")}
    if stage=="confirm":
        return {"v14":(range(7170820,7170880),OPPONENTS),"after_loss":(range(7170820,7170880),OPPONENTS),
                "direct":(range(7170900,7170960),("v14",))}
    raise ValueError(stage)


def jobs(stage,arm):
    if stage=="diagnose":
        return {"diagonal":CONTROL,"after_loss":KAGGLE+SOLUTION+TARGET+CONTROL}[arm]
    seeds,opps=layout(stage)[arm]
    return [(o,s,p) for s in seeds for o in opps for p in SEATS]


def historical(a):
    runs={}
    for name,hashes in HISTORICAL.items():
        folder=a.repo/HISTORY/"confirm"/name
        seeds,foes=original.schedule("confirm")[name]
        rows,m,h=checked_run_files(folder,"diagonal" if name=="direct" else name,seeds,foes)
        if ((h["manifest_sha256"],h["games_sha256"])!=hashes or original.manifest(a,"confirm",name)!=m):
            raise ValueError("Original confirmation sources / settings / row hashes differ: "+name)
        runs[name]=rows
    a0,a1=runs["v14"],runs["diagonal"]
    if (set(KAGGLE)!={k for k,r in a1.items() if k[0]=="kaggle3" and a0[k]["result"]>r["result"]}
            or set(SOLUTION)!={k for k,r in a1.items() if k[0]=="solution92" and r["wins"]==2 and a0[k]["result"]<r["result"]}
            or set(TARGET)!={k for k,r in a1.items() if k[0]=="solution92" and r["wins"]==0}
            or any(a1[k]["wins"]!=3 or a0[k]["wins"]!=3 for k in CONTROL)):
        raise ValueError("Registered diagnostic keys do not match the historical full games")
    return runs


def contract(a,stage,arm):
    keys=jobs(stage,arm)
    actor="after_loss" if arm=="direct" else arm
    source="direct" if arm=="direct" else ("v14" if actor=="v14" else "diagonal")
    m=original.manifest(a,"confirm",source)
    if stage=="diagnose":
        m.update(first=min(k[1] for k in keys),maps=len({k[1] for k in keys}),opponents=sorted({k[0] for k in keys}))
    else:
        seeds,foes=layout(stage)[arm]
        m.update(first=seeds.start,maps=len(seeds),opponents=list(foes))
    return dict(m,candidate=actor,actor_import=ACTORS[actor],stage=stage,arm=arm,keys=[list(k) for k in keys],
                history=HISTORICAL["diagonal"][1],
                protocol_sources={n:runner.digest(Path(__file__).with_name(n)) for n in
                                  ("r3_diag_after_loss.py","r3_diag_after_loss_games.py")})


class Actions:
    """Passive action provenance in world seat order after successful environment steps."""
    def __init__(self, env):
        self.env=env

    def reset(self, **kwargs):
        self.full=sha256(); self.steps=0; self.first=None; self.matches=[]
        initial=self.env.reset(**kwargs)
        self.previous=initial[0]["player_0"]
        return initial

    def step(self, orders):
        import numpy as np
        # Copy before handing mutable action arrays to the engine.
        pair=np.stack([np.asarray(orders[side],dtype="<i8") for side in SEATS])
        if pair.shape!=(2,16,3):
            raise ValueError("Unexpected world order dimensions")
        result=self.env.step(orders)
        self.full.update(pair.tobytes(order="C")); self.steps+=1
        obs=result[0]["player_0"]
        if self.steps%101==0:
            from scripts.scoring import match_points_after_step
            wins=[int(v) for v in obs["team_wins"]]
            change=[v-int(u) for v,u in zip(wins,self.previous["team_wins"])]
            if int(obs["match_steps"])!=0 or change not in ([1,0],[0,1]):
                raise ValueError("Missing public match result")
            points=match_points_after_step(self.previous,obs,result[4]).tolist()
            self.matches.append(dict(step=self.steps,points_world=points,wins_world=wins,winner=SEATS[change.index(1)]))
            if self.steps==101:
                self.first=dict(actions_sha256=self.full.hexdigest(),wins_world=wins)
        self.previous=obs
        return result


def validate_row(r,actor):
    if (r["candidate"]!=actor or r["steps"]!=303 or any(type(r[k]) is not int for k in ("wins","losses","steps","seed"))
            or r["wins"] not in range(4) or r["wins"]+r["losses"]!=3 or r["result"]!=int(r["wins"]>r["losses"])
            or r["first_match"]["wins_world"] not in ([0,1],[1,0]) or len(r["first_match"]["actions_sha256"])!=64
            or len(r["actions_sha256"])!=64):
        raise ValueError("Incomplete game or first match")
    matches=r["matches"]
    side=SEATS.index(r["side"])
    if ([m["step"] for m in matches]!=[101,202,303] or matches[0]["wins_world"]!=r["first_match"]["wins_world"]
            or matches[-1]["wins_world"][side]!=r["wins"] or sum(m["winner"]==r["side"] for m in matches)!=r["wins"]
            or sum(m["points_world"][side] for m in matches)!=r["points"]
            or sum(m["points_world"][1-side] for m in matches)!=r["opp_points"]):
        raise ValueError("Incomplete match score or winner accounting")
    counts=r['study']
    loss=r["first_match"]["wins_world"][SEATS.index(r["side"])]==0
    if (counts.get("movement",0)!=counts.get("changed_unit_orders",0)
            or counts.get("fallback_calls",0)!=(202 if actor=="after_loss" and loss else 0)):
        raise ValueError("Runtime fallback schedule differs from the first public result")


def key(r): return r["opponent"],r["seed"],r["side"]


def read_rows(folder,m,complete):
    path=folder/"games.jsonl"
    saved=[json.loads(l) for l in path.read_bytes().splitlines()] if path.is_file() else []
    keys={tuple(k) for k in m["keys"]}
    rows={key(r):r for r in saved}
    if len(saved)!=len(rows) or not set(rows)<=keys or (complete and set(rows)!=keys):
        raise ValueError("Missing, extra or repeated game")
    for r in saved: validate_row(r,m["candidate"])
    return rows


def completion(rows,path):
    returned={}
    for r in rows.values():
        group=returned.setdefault(r["opponent"],dict(played=0,wins=0,matches=0))
        group["played"]+=1; group["wins"]+=r["result"]; group["matches"]+=r["wins"]
    return dict(summary=returned,rows_sha256=runner.digest(path))


def checked(a,stage,arm):
    folder=a.out/stage/arm
    m=contract(a,stage,arm)
    if json.loads((folder/"manifest.json").read_bytes())!=m: raise ValueError("Changed arm manifest")
    if stage!="diagnose":
        rows,_,h=checked_run_files(folder,m["candidate"],*layout(stage)[arm])
        for r in rows.values(): validate_row(r,m["candidate"])
    else:
        rows=read_rows(folder,m,True)
        ch=completion(rows,folder/"games.jsonl")
        if json.loads((folder/"completed.json").read_bytes())!=ch: raise ValueError("Changed diagnostic rows")
        h={"manifest_sha256":runner.digest(folder/"manifest.json"),"games_sha256":ch["rows_sha256"]}
    return audit.Run(m,rows,h)


def play(a,stage,arm):
    dest=a.out/stage/arm; dest.mkdir(exist_ok=True,parents=True)
    with (dest/".run.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        m=contract(a,stage,arm); actor=m["candidate"]
        source=dest/"manifest.json"; path=dest/"games.jsonl"
        if source.is_file():
            if json.loads(source.read_bytes())!=m: raise ValueError("Changed run configuration")
        else:
            if path.exists() or (dest/"completed.json").exists(): raise ValueError("Unbound prior rows")
            publish_json(source,m)
        if not (dest/"completed.json").exists():
            saved=read_rows(dest,m,False)
            pending=[k for k in jobs(stage,arm) if k not in saved]
            policy="v14" if actor=="v14" else "selective_movement"
            model=None if actor=="v14" else str(a.model)
            if pending:
                with patch.dict(runner.POLICIES,{policy:ACTORS[actor]}):
                    runner.init_worker(policy,model)
                agent=runner.evaluate.agent; actual=type(agent)
                if actual.__module__+":"+actual.__name__!=ACTORS[actor]: raise ValueError("Unexpected live actor")
                live=runner.evaluate.env; observer=Actions(live)
                try:
                    with patch.object(runner.evaluate,"env",observer), path.open("a") as file:
                        for k in pending:
                            opp,seed,side=k
                            r=runner.evaluate((policy,opp,seed,side,model))
                            if observer.steps!=303: raise ValueError("Wrong engine duration")
                            r.update(candidate=actor,first_match=observer.first,actions_sha256=observer.full.hexdigest(),matches=observer.matches)
                            validate_row(r,actor)
                            if stage=="diagnose" and arm=="diagonal":
                                expected=a.history["diagonal"][k]
                                if any(r[f]!=expected[f] for f in MATCH_KEYS):
                                    raise ValueError("Original two-view result does not reproduce: "+str(k))
                            file.write(json.dumps(r)+"\n");file.flush()
                            saved[k]=r
                            print(stage,arm,k,r["result"],flush=True)
                finally:
                    live.close()
            if m!=contract(a,stage,arm): raise ValueError("Change during games")
            publish_json(dest/"completed.json",completion(saved,path))
        return checked(a,stage,arm)


def checked_control(a):
    controls=checked(a,"diagnose","diagonal")
    for k,r in controls.games.items():
        if any(r[f]!=a.history["diagonal"][k][f] for f in MATCH_KEYS):
            raise ValueError("Registered control did not reproduce "+str(k))
    return controls


def diagnosis(a):
    control=checked_control(a); candidate=checked(a,"diagnose","after_loss")
    unchanged=all(all(candidate.games[k][f]==control.games[k][f] for f in (*MATCH_KEYS,"first_match","actions_sha256","matches"))
                  for k in CONTROL)
    recovered=sum(candidate.games[k]["result"] for k in KAGGLE)
    protected=sum(candidate.games[k]["result"] for k in SOLUTION)
    target_wins=sum(candidate.games[k]["result"] for k in TARGET)
    separate=dict(one_solution_target_recovered=target_wins>=1,all_three_solution_preserved=protected==3,neutral_identical=unchanged)
    gates=dict(one_kaggle_recovered=recovered>=1,all_three_solution_preserved=protected==3,neutral_identical=unchanged)
    records=[dict(key=list(k),original={f:a.history["diagonal"][k][f] for f in MATCH_KEYS},
                  candidate={f:candidate.games[k][f] for f in (*MATCH_KEYS,"first_match","actions_sha256","study","matches")}) for k in jobs("diagnose","after_loss")]
    return dict(stage="diagnose",gates=gates,game_gates_pass=all(gates.values()),candidate_files=candidate.hashes,
                control_files=control.hashes,cases=records,solution_target_gates=separate,solution_target_pass=all(separate.values()))


def tier(a,stage):
    if stage=="diagnose": return diagnosis(a)
    runs={arm:checked(a,stage,arm) for arm in layout(stage)}
    if stage=="solution":
        seeds=layout(stage)["after_loss"][0]
        wins={k:sum(int(r["result"]) for r in run.games.values()) for k,run in runs.items()}
        matches={k:sum(r["wins"] for r in run.games.values()) for k,run in runs.items()}
        by={}
        for base in ("v14","diagonal"):
            deltas=[]; gained=lost=0
            for seed in seeds:
                diffs=[int(runs["after_loss"].games["solution92",seed,p]["result"])-
                       int(runs[base].games["solution92",seed,p]["result"]) for p in SEATS]
                gained+=diffs.count(1); lost+=diffs.count(-1); deltas.append(sum(diffs)/2)
            by[base]=dict(gained=gained,lost=lost,ci95=audit.bounds(deltas))
        gates=dict(solution_strictly_above_diagonal=wins["after_loss"]>wins["diagonal"],
                   solution_at_least_v14=wins["after_loss"]>=wins["v14"])
        return dict(stage=stage,wins=wins,matches=matches,paired=by,gates=gates,game_gates_pass=all(gates.values()),
                    files={k:run.hashes for k,run in runs.items()},purpose="separate Solution hypothesis")
    cand,ref,duel=(runs[k] for k in ("after_loss","v14","direct"))
    seeds=layout(stage)["after_loss"][0]
    result=audit.summarize(audit.Phase(ref,cand,duel,seeds,layout(stage)["direct"][0]),stage)
    if stage=="screen":
        contrast=audit.summarize(audit.Phase(runs["diagonal"],cand,duel,seeds,layout(stage)["direct"][0]),stage)
        by,ext=contrast["by_opponent"],contrast["external"]
        for row in by.values(): row["diagonal_wins"]=row.pop("v14_wins")
        result["diagonal_control"]=dict(by_opponent=by,external=ext,files=runs["diagonal"].hashes)
        result["gates"].update(external_beats_diagonal=ext["net_wins"]>0,solution_at_least_diagonal=by["solution92"]["net_wins"]>=0)
    result["game_gates_pass"]=all(result["gates"].values())
    result["fallback_games"]={k:sum(r["study"].get("fallback_calls",0)>0 for r in v.games.values()) for k,v in runs.items()}
    result["bootstrap"]=dict(unit="whole map, both seats and external opponents",draws=10000,seed=2711)
    return result


def current(a,stage):
    value=tier(a,stage)
    prev={"screen":"diagnose","solution":"diagnose","confirm":"screen"}.get(stage)
    if prev:
        value["previous_stage_sha256"]=required(a,prev,target=stage=="solution")
    return value


def required(a,stage,*,target=False):
    path=a.out/stage/"assessment.json"
    fresh=current(a,stage)
    if not path.is_file() or json.loads(path.read_bytes())!=fresh or not fresh["solution_target_pass" if target else "game_gates_pass"]:
        raise ValueError("Previous stage failed or differs from actual games: "+stage)
    return runner.digest(path)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("operation",choices=("check","run","assess"))
    p.add_argument("stage",choices=("diagnose","screen","confirm","solution"))
    p.add_argument("--repo",required=True,type=Path);p.add_argument("--out",required=True,type=Path)
    p.add_argument("--arm",choices=("v14","diagonal","after_loss","direct"))
    a=p.parse_args();a.repo=a.repo.resolve();a.out=a.out.resolve()
    a.archive=a.repo/HISTORY/"paired_validation.json";a.model=a.repo/CHECKPOINT
    a.history=historical(a)
    arms=("diagonal","after_loss") if a.stage=="diagnose" else tuple(layout(a.stage))
    if a.arm and (a.arm not in arms or a.operation!="run"): p.error("Unregistered arm or operation")
    if a.operation=="check":
        for arm in arms: contract(a,a.stage,arm)
        print(a.stage,{k:len(jobs(a.stage,k)) for k in arms});return
    prev={"screen":"diagnose","solution":"diagnose","confirm":"screen"}.get(a.stage)
    if prev: required(a,prev,target=a.stage=="solution")
    if a.operation=="run":
        for arm in ([a.arm] if a.arm else arms):
            if a.stage=="diagnose" and arm=="after_loss": checked_control(a)
            play(a,a.stage,arm)
        if a.arm: return
    value=current(a,a.stage); path=a.out/a.stage/"assessment.json"
    if not path.exists(): publish_json(path,value)
    elif json.loads(path.read_bytes())!=value: raise ValueError("Stored assessment differs")
    print(json.dumps(value,indent=2))


if __name__=="__main__": main()
