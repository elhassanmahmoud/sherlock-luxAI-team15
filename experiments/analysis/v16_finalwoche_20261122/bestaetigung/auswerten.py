"""Final analysis only: require all 1,700 bound records before exposing any result."""
import argparse
from collections import Counter
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
SEEDS=list(range(160337000,160337200))
SIDES=("player_0","player_1")


def boot(values,draws):
    data=np.array(values,dtype=float)
    ci=np.percentile(data[draws].mean(1),[2.5,97.5],method="linear")
    return {"mean":float(data.mean()),"ci95":ci.tolist()}


def share(row):
    total=row["our_points"]+row["opp_points"]
    return row["our_points"]/total if total else 0.5


def read_all(directory):
    paths=sorted((directory/"partien").glob("*.json"))
    if len(paths)!=1700:
        raise ValueError(f"Blind until final completion: {len(paths)}/1700")
    origin=sha256((directory/"quellen.json").read_bytes()).hexdigest()
    choice_sha=sha256((directory/"auswahl.json").read_bytes()).hexdigest()
    choice=json.loads((directory/"auswahl.json").read_text())
    expected={(s,p,o,a) for s in SEEDS for p in SIDES for o in ("solution92","kaggle3","v16")
              for a in ("kandidat","referenz") if o!="v16" or (a=="kandidat" and s<160337050)}
    rows={}
    for p in paths:
        r=json.loads(p.read_text())
        k=tuple(r[x] for x in ("seed","side","opponent","arm"))
        if (k not in expected or k in rows or r["steps"]!=303 or r["point_counting_version"]!=2
                or r["our_wins"]+r["opp_wins"]!=3 or r["game_win"]!=int(r["our_wins"]>=2)
                or r["source"]!=origin or r["choice"]!=(choice_sha if r["arm"]=="kandidat" else None)):
            raise ValueError(f"Invalid game {p}")
        rows[k]=r
    if set(rows)!=expected:
        raise ValueError("Invalid seat coverage")
    return choice,rows


def analyze(choice,rows):
    rng=np.random.default_rng(221123)
    draws=rng.integers(0,200,(20000,200))
    counts,contrasts={},{}
    for o in ("solution92","kaggle3"):
        counts[o]={}
        metrics={"win_rate":lambda r:r["game_win"], "point_share":share, "matches_per_game":lambda r:r["our_wins"]}
        for arm in ("referenz","kandidat"):
            group=[r for k,r in rows.items() if k[2:]==(o,arm)]
            counts[o][arm]={"games":len(group),"wins":sum(r["game_win"] for r in group),
                             "matches":sum(r["our_wins"] for r in group),"mean_point_share":float(np.mean([share(r) for r in group]))}
        contrasts[o]={}
        for name,get in metrics.items():
            values=[np.mean([get(rows[s,p,o,"kandidat"])-get(rows[s,p,o,"referenz"]) for p in SIDES]) for s in SEEDS]
            contrasts[o][name]=boot(values,draws)
        cells=Counter((rows[s,p,o,"referenz"]["game_win"],rows[s,p,o,"kandidat"]["game_win"]) for s in SEEDS for p in SIDES)
        contrasts[o]["paired_seats"]={key:cells[code] for code,key in (((1,1),"both_won"),((0,1),"candidate_only"),
                                                                       ((1,0),"reference_only"),((0,0),"both_lost"))}
    duo=[r for k,r in rows.items() if k[2]=="v16"]
    counts["direct"]={"games":len(duo),"wins":sum(r["game_win"] for r in duo),"matches":sum(r["our_wins"] for r in duo)}
    direct=[np.mean([rows[s,p,"v16","kandidat"]["game_win"] for p in SIDES]) for s in SEEDS[:50]]
    contrasts["direct"]=boot(direct,rng.integers(0,50,(20000,50)))
    kag,sol=counts["kaggle3"],counts["solution92"]
    gates={"direct_at_least_50":counts["direct"]["wins"]>=50,"kaggle_wins_retained":kag["kandidat"]["wins"]>=kag["referenz"]["wins"]}
    if choice["name"]=="kontrolle":
        share_delta=contrasts["kaggle3"]["point_share"]
        gates.update(kaggle_point_share_delta_at_least_1pp=share_delta["mean"]>=0.01,
                     kaggle_point_share_lower95_positive=share_delta["ci95"][0]>0,
                     solution_wins_retained=sol["kandidat"]["wins"]>=sol["referenz"]["wins"])
    elif choice["name"]=="scout":
        gates.update(solution_winrate_lower95_positive=contrasts["solution92"]["win_rate"]["ci95"][0]>0,
                     kaggle_matches_retained=kag["kandidat"]["matches"]>=kag["referenz"]["matches"])
    else:
        raise ValueError("Unknown candidate")
    return {"candidate":choice["name"],"count":len(rows),"counts":counts,"contrasts":contrasts,"gates":gates,"passed":all(gates.values())}


def run(directory,out):
    choice,rows=read_all(directory)
    report=analyze(choice,rows)
    out.mkdir(exist_ok=True,parents=True)
    (out/"ergebnis.json").write_text(json.dumps(report,indent=2)+"\n")
    data="".join(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n" for _,r in sorted(rows.items()))
    (out/"partien.jsonl.gz").write_bytes(gzip.compress(data.encode(),mtime=0))
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directory",type=Path); ap.add_argument("out",type=Path)
    args=ap.parse_args(); run(args.directory,args.out)
