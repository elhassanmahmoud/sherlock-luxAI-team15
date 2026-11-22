"""Final whole-game readout and intervention frequencies on the fixed 120 maps."""
import argparse
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
SEEDS=range(160358000,160358120)
SIDES=("player_0","player_1")


def sums(rows):
    ratio=[r["our_points"]/(r["our_points"]+r["opp_points"]) if r["our_points"]+r["opp_points"] else .5 for r in rows]
    return dict(n=len(rows),wins=sum(r["game_win"] for r in rows),matches=sum(r["our_wins"] for r in rows),
                score=sum(r["our_points"] for r in rows),enemy_score=sum(r["opp_points"] for r in rows),
                mean_point_share=float(np.mean(ratio)),swap_pairs=sum(r["swaps"] for r in rows),
                changed_orders=sum(r["changed_units"] for r in rows),games_with_swaps=sum(r["swaps"]>0 for r in rows))


def evaluate(folder,out):
    expected={(s,p,o,a) for s in SEEDS for p in SIDES for o in ("solution92","kaggle3","v16")
              for a in ("original","wechsel") if o!="v16" or a=="wechsel"}
    files=sorted((folder/"frisch").glob("*.json"))
    if len(files)!=1200:raise ValueError("Wait for all 1200 games")
    source=sha256((folder/"auftrag.json").read_bytes()).hexdigest()
    by={}
    for f in files:
        r=json.loads(f.read_text());k=tuple(r[x] for x in ("seed","side","opponent","arm"))
        if (k in by or k not in expected or r["source"]!=source or r["steps"]!=303 or r["point_counting_version"]!=2
                or r["our_wins"]+r["opp_wins"]!=3 or r["game_win"]!=int(r["our_wins"]>=2)):
            raise ValueError(f"Invalid game {k}")
        by[k]=r
    if set(by)!=expected:raise ValueError("Unexpected panel")
    counts={}; contrasts={}; draws=np.random.default_rng(221124).integers(0,120,(20000,120))
    def stat(per_map):
        v=np.asarray(per_map,dtype=float)
        return dict(mean=float(v.mean()),ci95=np.quantile(v[draws].mean(axis=1),[.025,.975],method="linear").tolist())
    for op in ("solution92","kaggle3","v16"):
        arms=("wechsel",) if op=="v16" else ("original","wechsel")
        counts[op]={a:sums([row for k,row in by.items() if k[2:]==(op,a)]) for a in arms}
        if op=="v16":
            contrasts[op]=stat([np.mean([by[s,p,op,"wechsel"]["game_win"] for p in SIDES]) for s in SEEDS]);continue
        pairs=[(by[s,p,op,"original"],by[s,p,op,"wechsel"]) for s in SEEDS for p in SIDES]
        diff=np.asarray([b["game_win"]-a["game_win"] for a,b in pairs]).reshape(120,2)
        contrasts[op]={"win_difference":stat(diff.mean(axis=1)),
                       "winner_flips":{"only_original":int((diff<0).sum()),"only_wechsel":int((diff>0).sum())},
                       "maps_with_win_advantage":int((diff.sum(axis=1)>0).sum()),
                       "maps_with_win_disadvantage":int((diff.sum(axis=1)<0).sum())}
    gates=dict(kaggle_win_gain_lower95_positive=contrasts["kaggle3"]["win_difference"]["ci95"][0]>0,
               solution_games_retained=counts["solution92"]["wechsel"]["wins"]>=counts["solution92"]["original"]["wins"],
               direct_at_least_half=counts["v16"]["wechsel"]["wins"]>=120)
    report=dict(n=1200,counts=counts,contrasts=contrasts,gates=gates,passed=all(gates.values()),
                direct_superiority=contrasts["v16"]["ci95"][0]>.5)
    out.mkdir(exist_ok=True,parents=True)
    (out/"ergebnis.json").write_text(json.dumps(report,indent=2)+"\n")
    raw="".join(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n" for _,r in sorted(by.items()))
    (out/"partien.jsonl.gz").write_bytes(gzip.compress(raw.encode(),mtime=0))
    return report


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("folder",type=Path); cli.add_argument("out",type=Path)
    a=cli.parse_args();print(json.dumps(evaluate(a.folder,a.out),indent=2))
