"""Check the completed blind study independently from its compressed JSON-lines artifact."""
import argparse
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np


def load_json(path):
    return json.loads(path.read_text())


def check(directory):
    end=load_json(directory/"ende.json")
    if end["status"]!="complete" or end["cases"]!=1700:
        raise AssertionError("Missing completion receipt")
    for filename,digest in end["artifacts"].items():
        if sha256((directory/filename).read_bytes()).hexdigest()!=digest:
            raise AssertionError(f"Receipt digest mismatch: {filename}")
    nomination=load_json(directory/"auswahl.json")
    if nomination["control_passed"]!=True or nomination["scout_passed"]!=False or nomination["name"]!="kontrolle":
        raise AssertionError("Unexpected candidate")
    manifest=load_json(directory/"quellen.json")
    if (nomination["candidate_sha256"]!="5b200d5a7fadfffb86ccb6c3e74324e49fe4c1e27510581ae810e6a452b2a67b"
            or manifest["release_sha256"]!="0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"):
        raise AssertionError("Original or candidate SHA mismatch")
    text=gzip.decompress((directory/"partien.jsonl.gz").read_bytes()).decode()
    records=[json.loads(line) for line in text.splitlines()]
    if len(records)!=1700:
        raise AssertionError("Archive length mismatch")
    cube=np.full((2,2,200,2,4),np.nan,dtype=np.float64)
    direct=np.full((50,2,2),np.nan,dtype=np.float64)
    for row in records:
        if row["steps"]!=303 or row["point_counting_version"]!=2 or row["our_wins"]+row["opp_wins"]!=3:
            raise AssertionError("Invalid course game")
        seed=row["seed"]-160337000
        side=("player_0","player_1").index(row["side"])
        arm=("referenz","kandidat").index(row["arm"])
        if not(0<=seed<200) or min(row["our_points"],row["opp_points"])<0:
            raise AssertionError("Invalid map or point total")
        if row["source"]!=end["artifacts"]["quellen.json"] or row["choice"]!=(end["artifacts"]["auswahl.json"] if arm==1 else None):
            raise AssertionError("Invalid row binding")
        won=int(row["our_wins"]>row["opp_wins"])
        if row["game_win"]!=won:
            raise AssertionError("Winner mismatch")
        if row["opponent"]=="v16":
            if seed>=50 or arm!=1 or np.isfinite(direct[seed,side,0]):
                raise AssertionError("Duplicate/unknown duel")
            direct[seed,side]=[won,row["our_wins"]]
        else:
            opponent=("solution92","kaggle3").index(row["opponent"])
            if np.isfinite(cube[arm,opponent,seed,side,0]):
                raise AssertionError("Duplicate external game")
            cube[arm,opponent,seed,side]=[won,row["our_wins"],row["our_points"],row["opp_points"]]
    if not np.isfinite(cube).all() or not np.isfinite(direct).all():
        raise AssertionError("Missing seat")
    result=load_json(directory/"ergebnis.json")
    if result["count"]!=1700 or result["candidate"]!="kontrolle":
        raise AssertionError("Invalid report")
    for arm,a in enumerate(("referenz","kandidat")):
        for o,opp in enumerate(("solution92","kaggle3")):
            c=result["counts"][opp][a]
            column=cube[arm,o]
            if (c["games"],c["wins"],c["matches"])!=(400,int(column[...,0].sum()),int(column[...,1].sum())):
                raise AssertionError("Reported wins/matches differ")
    k=cube[:,1]
    totals=k[:,:,:,2]+k[:,:,:,3]
    shares=np.divide(k[:,:,:,2],totals,where=totals>0,out=np.full_like(totals,.5))
    card_effect=shares[1].mean(axis=1)-shares[0].mean(axis=1)
    gen=np.random.default_rng(221123)
    # Aggregate bootstrap map multiplicities instead of expanding per-draw game rows.
    ci_draws=[]
    for _ in range(20000):
        count=np.bincount(gen.choice(200,200,replace=True),minlength=200)
        ci_draws.append(float(count @ card_effect / 200))
    ci=np.quantile(ci_draws,[.025,.975],method="linear").tolist()
    delta=float(card_effect.mean())
    declared=result["contrasts"]["kaggle3"]["point_share"]
    if not np.allclose([delta,*ci],[declared["mean"],*declared["ci95"]],atol=1e-12,rtol=0):
        raise AssertionError("Primary estimate or interval mismatch")
    direct_wins=int(direct[:,:,0].sum())
    direct_matches=int(direct[:,:,1].sum())
    d=result["counts"]["direct"]
    if (d["games"],d["wins"],d["matches"])!=(100,direct_wins,direct_matches):
        raise AssertionError("Reported duels differ")
    gates={"direct_at_least_50":direct_wins>=50,
           "kaggle_wins_retained":bool(cube[1,1,:,:,0].sum()>=cube[0,1,:,:,0].sum()),
           "solution_wins_retained":bool(cube[1,0,:,:,0].sum()>=cube[0,0,:,:,0].sum()),
           "kaggle_point_share_delta_at_least_1pp":delta>=.01,
           "kaggle_point_share_lower95_positive":ci[0]>0}
    if result["gates"]!=gates or result["passed"]!=all(gates.values()):
        raise AssertionError("Decision mismatch")
    return dict(verified=True,primary_point_share_delta=delta,primary_ci95=ci,
                direct_wins=direct_wins,direct_matches=direct_matches,gates=gates,
                source_files=end["artifacts"],notes="Independent array-based reconstruction from compressed whole-game rows")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory",type=Path)
    args=p.parse_args()
    print(json.dumps(check(args.directory),indent=2))
