"""Two separately admitted full-game phases, at most one process per fixed lane."""
import argparse
import fcntl
from hashlib import sha256
import json
from pathlib import Path

from scripts.final_battle_compare import ROOT, WEIGHTS, digest
from scripts.protocol import SIDES
from scripts.r3_v4_contact_study import KEY, GAME, binding
from scripts.train_combat_advice import publish_json

EXTERNAL = range(7170500,7170560)
DIRECT = range(7170600,7170660)
OPPONENTS = ("solution92","kaggle3")
BASE_SOURCE = "5e2a323f07b544950c80b6fb74769406498c3ed3d60fdfa69bb1cb36d5464b53"


def panel(phase,lane=None):
    if phase not in ("v14","parents") or lane not in (0,1,None):
        raise ValueError("Unregistered phase or lane")
    arms=("contact","v14") if phase=="v14" else ("r3","v4")
    games=[(arm,foe,seed,seat) for i,seed in enumerate(EXTERNAL) if lane is None or i%2==lane
           for seat in SIDES for foe in OPPONENTS for arm in arms]
    if phase=="v14":
        games.extend(("contact","v14",seed,seat) for i,seed in enumerate(DIRECT) if lane is None or i%2==lane for seat in SIDES)
    return games


def canonical(value):
    return sha256(json.dumps(value,separators=(",",":"),sort_keys=True,allow_nan=False).encode()).hexdigest()


def stamp_for(repo,selection):
    from scripts.r3_v4_contact_study import accept
    from scripts.r3_v4_contact_assess import rawcheck,diagnostic_report,fresh_report
    original,old=binding(repo)
    if original["files_sha256"]!=BASE_SOURCE:
        raise ValueError("This confirmation is bound to the selected exact playing source")
    from scripts.r3_v4_contact_study import target
    seals={}
    for stage in ("sentinel","diagnosis","screen"):
        rows=accept(stage,selection,original,old)
        rawcheck(rows)
        if stage=="diagnosis" and not diagnostic_report(rows,old)["passes"]:
            raise ValueError("Diagnosis did not qualify")
        if stage=="screen" and not fresh_report(rows)["passes"]:
            raise ValueError("Complete independent screen did not qualify")
        seals[stage]=canonical({str(target(selection,stage,k).relative_to(selection)):digest(target(selection,stage,k)) for k in rows})
    files=("scripts/r3_v4_contact_assess.py","scripts/r3_v4_contact_confirm.py",
           "scripts/r3_v4_contact_confirm_assess.py","experiments/analysis/r3_v4_contact_20261115/BESTAETIGUNGSPLAN.md",
           "scripts/final_battle_assess.py","scripts/residual_ensemble_compare.py")
    return dict(selected=original,selection_seals=seals,confirmation_sources={f:digest(ROOT/f) for f in files})


def lane_dir(out,phase,lane):
    return out/phase/f"lane{lane}"


def game_path(folder,k):
    return folder/("_".join(map(str,k))+".json")


def verify_row(row,k,sig):
    from scripts.r3_v4_contact_assess import rawcheck
    if tuple(row[x] for x in KEY)!=k or row["run_sha256"]!=sig:
        raise ValueError(f"Wrong game key or confirmation {k}")
    if canonical({a:b for a,b in row.items() if a!="row_sha256"})!=row["row_sha256"]:
        raise ValueError(f"Changed game payload {k}")
    g=row["game"]
    if set(g)!=set(GAME) or type(g["steps"]) is not int or g["steps"]!=303 or g["our_wins"]+g["opp_wins"]!=3:
        raise ValueError(f"Incomplete game {k}")
    rawcheck({k:row})


def read_lane(out,phase,lane,stamp,*,closed):
    path=lane_dir(out,phase,lane)
    expected=panel(phase,lane)
    meta=json.loads((path/"manifest.json").read_bytes())
    if meta!=dict(phase=phase,lane=lane,source=stamp,expected=len(expected)):
        raise ValueError("Invalid or stale lane manifest")
    sig=canonical(meta)
    paths=[game_path(path,k) for k in expected]
    if set(path.glob("*.json"))-{path/"manifest.json",path/"completed.json"}!=set(paths):
        raise ValueError("Wrong, missing or extra games in lane")
    rows,hashes={},{}
    for k,p in zip(expected,paths):
        r=json.loads(p.read_bytes())
        verify_row(r,k,sig)
        rows[k]=r
        hashes[p.name]=digest(p)
    seal=dict(phase=phase,lane=lane,manifest_sha256=digest(path/"manifest.json"),rows_sha256=hashes)
    if closed and (not (path/"completed.json").is_file() or json.loads((path/"completed.json").read_bytes())!=seal):
        raise ValueError("Unsealed or altered lane")
    return rows,seal


def lane_stamp(a):
    stamp=stamp_for(a.repo,a.selection.resolve())
    if a.phase=="parents":
        from scripts.r3_v4_contact_confirm_assess import sealed_primary
        stamp=dict(stamp,primary_report_sha256=sealed_primary(a.out.resolve(),stamp))
    return stamp


def run(a):
    from scripts.common import make_opponent,play_game
    from scripts.experiment import limit_threads
    from scripts.par_eval import require_no_agent_errors
    from scripts.r3_v4_contact_agent import ContactAgent,make_r3,make_v4
    from luxai_s3.wrappers import LuxAIS3GymEnv
    import torch
    limit_threads()
    torch.manual_seed(0)
    out=a.out.resolve()
    stamp=lane_stamp(a)
    folder=lane_dir(out,a.phase,a.lane)
    folder.mkdir(parents=True,exist_ok=True)
    expected=panel(a.phase,a.lane)
    with (folder/".lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        manifest=dict(phase=a.phase,lane=a.lane,source=stamp,expected=len(expected))
        sig=canonical(manifest)
        if (folder/"manifest.json").exists():
            if json.loads((folder/"manifest.json").read_bytes())!=manifest:
                raise ValueError("Cannot resume after a source or admission change")
        else:
            publish_json(folder/"manifest.json",manifest)
        if (folder/"completed.json").exists():
            read_lane(out,a.phase,a.lane,stamp,closed=True)
            return
        env=None
        actors={}
        try:
            for k in expected:
                arm,foe,seed,seat=k
                p=game_path(folder,k)
                if p.exists():
                    verify_row(json.loads(p.read_bytes()),k,sig)
                    continue
                if env is None: env=LuxAIS3GymEnv(numpy_output=True)
                if arm not in actors:
                    actors[arm]={"contact":ContactAgent,"r3":make_r3,"v4":make_v4,
                                 "v14":lambda s:make_opponent("self",s,str(WEIGHTS))}[arm](seat)
                agent=actors[arm]
                other=SIDES[1-SIDES.index(seat)]
                rival=make_opponent("self" if foe=="v14" else foe,other,str(WEIGHTS))
                scores=play_game(env,agent,rival,seed,seat,False)
                require_no_agent_errors(agent,rival)
                if arm=="v4": require_no_agent_errors(agent.v14,agent.student)
                row=dict(zip(KEY,k),game={t:int(scores[t]) for t in GAME},
                         routing=dict(agent.counts) if arm=="contact" else {},run_sha256=sig)
                row["row_sha256"]=canonical(row)
                verify_row(row,k,sig)
                publish_json(p,row)
                print(k,row["game"],flush=True)
        finally:
            if env is not None: env.close()
        if lane_stamp(a)!=stamp: raise ValueError("A bound source or admission changed")
        _,seal=read_lane(out,a.phase,a.lane,stamp,closed=False)
        publish_json(folder/"completed.json",seal)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("phase",choices=("v14","parents"))
    p.add_argument("--lane",required=True,type=int,choices=(0,1))
    p.add_argument("--repo",required=True,type=Path)
    p.add_argument("--selection",required=True,type=Path,help="All original sentinel/diagnosis/screen rows")
    p.add_argument("--out",required=True,type=Path)
    run(p.parse_args())
