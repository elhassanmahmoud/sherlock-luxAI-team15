"""Verify the completed WECHSEL panel without using its evaluator."""
import gzip
import json
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
import sys

import numpy as np


def run(directory):
    src=json.loads((directory/"ergebnis.json").read_text())
    source=sha256((directory/"auftrag.json").read_bytes()).hexdigest()
    if src["n"]!=1200:raise ValueError("Panel incomplete")
    all_rows=[json.loads(line) for line in gzip.decompress((directory/"partien.jsonl.gz").read_bytes()).splitlines()]
    records={(r["seed"], r["side"], r["opponent"],r["arm"]):r for r in all_rows}
    sites=[(s,seat) for s in range(160358000,160358120) for seat in ("player_0","player_1")]
    required={(s,seat,opponent,arm) for s,seat in sites for opponent in ("solution92","kaggle3","v16")
              for arm in ("original","wechsel") if opponent!="v16" or arm=="wechsel"}
    if (len(all_rows)!=1200 or set(records)!=required or
            any(r["steps"]!=303 or r["point_counting_version"]!=2 or r["source"]!=source or
                r["game_win"]!=int(r["our_wins"]>r["opp_wins"]) or r["our_wins"]+r["opp_wins"]!=3
                or r["swaps"]<0 or not 0<=r["changed_units"]<=2*r["swaps"] for r in all_rows)):
        raise ValueError("Invalid seat, outcome, or counter")
    for o in ("solution92","kaggle3","v16"):
        for name in (("wechsel",) if o=="v16" else ("original","wechsel")):
            rows=[records[s,p,o,name] for s,p in sites]
            implicit=src["counts"][o][name]
            for key,col in (("wins","game_win"),("matches","our_wins"),("swap_pairs","swaps"),("changed_orders","changed_units")):
                if implicit[key]!=sum(r[col] for r in rows):raise ValueError(f"Aggregate {o} {name} {key}")
    delta=defaultdict(list)
    for s,p in sites:
        delta[s].append(records[s,p,"kaggle3","wechsel"]["game_win"]-records[s,p,"kaggle3","original"]["game_win"])
    effects=np.array([sum(values)/2 for _,values in sorted(delta.items())])
    rng=np.random.default_rng(221124)
    replicates=[np.bincount(rng.choice(120,size=120,replace=True),minlength=120)@effects/120 for _ in range(20000)]
    ci=np.quantile(replicates,[.025,.975],method="linear")
    xs=src["contrasts"]["kaggle3"]["win_difference"]
    if not np.allclose([effects.mean(),*ci],[xs["mean"],*xs["ci95"]],atol=1e-12,rtol=0):
        raise ValueError("Mismatch on the primary estimated effect")
    direct=sum(records[s,p,"v16","wechsel"]["game_win"] for s,p in sites)
    sol_delta=sum(records[s,p,"solution92","wechsel"]["game_win"]-records[s,p,"solution92","original"]["game_win"] for s,p in sites)
    passed=(ci[0]>0) and (direct>=120) and (sol_delta>=0)
    if src["passed"]!=bool(passed): raise ValueError("Final decision mismatch")
    return dict(verified=True,n=1200,source_sha256=source,kaggle_winrate_difference=float(effects.mean()),
                kaggle_ci95=ci.tolist(),solution_wins_delta=sol_delta,direct_wins=direct,passed=bool(passed))


if __name__=="__main__":print(json.dumps(run(Path(sys.argv[1])),indent=2))
