"""One 96-game movement screen with previously published original R3 and V14 controls."""
import argparse
from collections import Counter
import fcntl
from itertools import product
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import final_battle_assess as judge, final_battle_compare as game, r8_midpoint_games as single
from scripts.final_battle_select import OPPONENTS,SEATS,checked_run_files
from scripts.train_combat_advice import publish_json

ROOT=game.ROOT
STUDY=Path("experiments/analysis/r3_turn_advice_20261115")
MAPS=range(7170230,7170246)
ARMS={"external":OPPONENTS,"direct":("v14",)}
ACTOR="scripts.r3_turn_advice:TurnAdviceAgent"
OFFLINE="7067483ced3edd0d2b3beca65880f4bd87b518c919b309e2bc0c9dc58bf0628d"
ORIGINAL_REPORT="dbff39a2529c4db4812812223bc8e8a2eb716e9f4d967da33a75e8f76d48c1c1"
ORIGINAL_PROTOCOL="14fbef07e70090dc0d96eff822bf28ed3f51a1876225cc7bb0e072c8c40edff4"
ORIGINAL_ACTOR="1c300c6ad4cf2f92107c804c29e20414d86c5a2d3faa66ae5feb8100450e6e7b"
NAME="r3_turn_advice"


def turn_count(row):
    study=row["study"]
    n=study["turn_extra_played"]
    total=study.get("movement",0)
    if type(n) is not int or type(total) is not int or not 0<=n<=total or total!=study.get("changed_unit_orders",0):
        raise ValueError("Missing or impossible count of executed added movements")
    return n


def eligibility(s,totals):
    original=s["against_r3"]
    return {**s["gates"],"external_more_than_r3":original["external"]["net_wins"]>0,
            "solution_at_least_r3":original["by_opponent"]["solution92"]["net_wins"]>=0,
            **{side+"_additional_directions":totals[side]>0 for side in SEATS}}


def evidence(a):
    history=a.repo/single.STUDY/"games"
    single.checked(history/"protocol.json",ORIGINAL_PROTOCOL)
    single.checked(history/"screen/assessment.json",ORIGINAL_REPORT)
    original=json.loads((history/"screen/assessment.json").read_bytes())
    protocol=json.loads((history/"protocol.json").read_bytes())
    env=single.environment()
    if env!=protocol["runtime"] or original["protocol_sha256"]!=ORIGINAL_PROTOCOL:
        raise ValueError("Original game environment differs")
    single.checked(ROOT/"scripts/r8_midpoint_games.py",protocol["source"])
    path=a.repo/STUDY/"validation.json"
    single.checked(path,OFFLINE)
    proof=json.loads(path.read_bytes())
    if (proof["model"]!=judge.DISTILL_MODEL or proof["passes"] is not True or len(proof["checks"])!=5
            or not all(proof["checks"].values()) or proof["source"].get("scripts/r3_turn_advice.py")!=ORIGINAL_ACTOR):
        raise ValueError("Archive criteria not verified for the playing candidate")
    for name,sha in proof["source"].items(): single.checked(ROOT/name,sha)
    single.checked(a.repo/single.R3,judge.DISTILL_MODEL)
    refs={}
    for arm,key in (("r3",original["against_r3"]["files"]),("v14",original["reference_files"])):
        expected=single.expected(a.repo,"screen",arm)
        r=judge.load_run(history/"screen"/arm,expected["candidate"],MAPS,OPPONENTS)
        if r.hashes!=key or r.manifest!=expected:raise ValueError("Wrong original control: "+arm)
        refs[arm]=r
    return dict(archive=OFFLINE,actor=ORIGINAL_ACTOR,original_report=ORIGINAL_REPORT,original_protocol=ORIGINAL_PROTOCOL,
                control_files={k:r.hashes for k,r in refs.items()},environment=env,
                plan=game.digest(ROOT/STUDY/"VORAUSWAHLPLAN.md"),runner=game.digest(Path(__file__))),refs


def config(a,arm,receipt):
    # Original R3 game signature on both opponent sets, including the native external opponent files.
    base="r3" if arm=="external" else "direct"
    p=ROOT/"experiments/analysis/movement_soft_20261115/confirmation"/base/"manifest.json"
    single.checked(p,single.HIST[base])
    historic=json.loads(p.read_bytes())
    expected=dict(historic,first=MAPS.start,maps=len(MAPS))
    c=SimpleNamespace(candidate="selective_movement",model=a.repo/single.R3,opponents=",".join(ARMS[arm]),first=MAPS.start,maps=len(MAPS))
    if game.contract(c)!=expected or expected["model"]!=judge.DISTILL_MODEL:raise ValueError("Original actor source/weights differ")
    return dict(expected,candidate=NAME,actor_import=ACTOR,arm=arm,receipt=receipt)


def validate(row,expected):
    key=(row["opponent"],row["seed"],row["side"])
    if (key not in expected or row["candidate"]!=NAME or row["steps"]!=303 or row["wins"] not in range(4)
            or any(type(row[f]) is not int for f in ("seed","steps","wins","losses"))
            or row["wins"]+row["losses"]!=3 or row["result"]!=int(row["wins"]>row["losses"])):
        raise ValueError("Incomplete, unregistered or erroneous game")
    turn_count(row)
    return key


def play(a,arm):
    receipt,_=evidence(a)
    before=config(a,arm,receipt)
    folder=a.out/"screen"/arm
    folder.mkdir(parents=True,exist_ok=True)
    with (folder/".run.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if not (folder/"manifest.json").exists() and (folder/"games.jsonl").exists(): raise ValueError("Missing manifest")
        single.seal(folder/"manifest.json",before)
        raw=folder/"games.jsonl"
        rows=[json.loads(l) for l in raw.read_text().splitlines()] if raw.exists() else []
        keys=[(o,n,s) for n in MAPS for o in ARMS[arm] for s in SEATS]
        expected=set(keys)
        done={validate(r,expected) for r in rows}
        if len(rows)!=len(done):raise ValueError("Duplicate seat in saved data")
        todo=[k for k in keys if k not in done]
        if todo and (folder/"completed.json").exists(): raise ValueError("Incomplete sealed run")
        if todo:
            model=str(a.repo/single.R3)
            with patch.dict(game.POLICIES,selective_movement=ACTOR):
                game.init_worker("selective_movement",model)
            try:
                actor=game.evaluate.agent
                if type(actor).__module__+":"+type(actor).__name__!=ACTOR: raise ValueError("Wrong actor")
                for o,n,s in todo:
                    row=game.evaluate(("selective_movement",o,n,s,model))
                    counts=actor.selective_counts
                    if not isinstance(counts,Counter) or row["study"]!=dict(counts): raise ValueError("Wrong live game counters")
                    # The original frozen actor increments this key only after the native order was really applied.
                    row["study"]["turn_extra_played"]=counts["turn_extra_played"]
                    row["candidate"]=NAME
                    if validate(row,expected)!=(o,n,s): raise ValueError("Wrong completed game")
                    rows.append(row)
                    tmp=raw.with_suffix(".tmp")
                    tmp.write_text("".join(json.dumps(saved)+"\n" for saved in rows))
                    tmp.replace(raw)
                    print(arm,o,n,s,row["result"],turn_count(row),flush=True)
            finally: game.evaluate.env.close()
        final,_=evidence(a)
        if config(a,arm,final)!=before:raise ValueError("Source changed during play")
        summary={}
        for o in ARMS[arm]:
            rr=[r for r in rows if r["opponent"]==o]
            summary[o]=dict(played=len(rr),wins=sum(r["result"] for r in rr),matches=sum(r["wins"] for r in rr))
        single.seal(folder/"completed.json",dict(summary=summary,rows_sha256=game.digest(raw)))


def assess(a):
    receipt,refs=evidence(a);runs={}
    counts={s:Counter() for s in SEATS}
    for arm,opps in ARMS.items():
        rows,m,h=checked_run_files(a.out/"screen"/arm,NAME,MAPS,opps)
        if m!=config(a,arm,receipt):raise ValueError("Wrong source for "+arm)
        expected=set(product(opps,MAPS,SEATS))
        for key,row in rows.items():
            if validate(row,expected)!=key:raise ValueError("Wrong seat")
            counts[key[2]][key[0]]+=turn_count(row)
        runs[arm]=judge.Run(m,rows,h)
    s=judge.summarize(judge.Phase(refs["v14"],runs["external"],runs["direct"],MAPS,MAPS),"screen")
    by,ext=judge.external_comparison(refs["r3"],runs["external"],MAPS,"r3_wins")
    s["against_r3"]=dict(by_opponent=by,external=ext,files=refs["r3"].hashes)
    s["gates"]=eligibility(s,{k:sum(v.values()) for k,v in counts.items()})
    s.update(game_gates_pass=all(s["gates"].values()),additional_directions_by_side_and_opponent=counts,
             bootstrap=dict(draws=10000,seed=2711,unit="whole map with both seats and external opponents"),receipt=receipt)
    single.seal(a.out/"screen/assessment.json",s)
    print(json.dumps(s,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("operation",choices=("check","play","assess"))
    p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--out",type=Path)
    p.add_argument("--arm",choices=tuple(ARMS))
    a=p.parse_args();a.repo=a.repo.resolve()
    a.out=(a.out or a.repo/STUDY/"games").resolve()
    if a.arm and a.operation!="play":p.error("--arm is only for playing")
    if a.out==(a.repo/single.STUDY/"games").resolve():raise ValueError("Cannot write into the original controls")
    if a.operation=="play":
        for arm in ((a.arm,) if a.arm else ARMS):play(a,arm)
    elif a.operation=="assess":assess(a)
    else:
        receipt,refs=evidence(a)
        for arm in ARMS:config(a,arm,receipt)
        print(json.dumps(receipt,indent=2))
