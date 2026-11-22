"""Compare first paired discoveries on the 46 unmodified, archived low-visibility histories."""
import argparse
import gzip
from hashlib import sha256
import inspect
import json
from pathlib import Path
import sys
import time

import numpy as np

from beweis import Evidence, crosscheck, pair_key

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"kurze_sicht"))
from sammeln import PACKAGES, ROOT, sample
from verlauf import public_obs


def compare(folder):
    pack=ROOT/"experiments/releases"/PACKAGES["v16"][0]/"agent.zip"
    if sha256(pack.read_bytes()).hexdigest()!=PACKAGES["v16"][1]:
        raise ValueError("Archive V16 identity")
    sys.path.insert(0,str(pack))
    from sherlock.belief import Belief
    ref=gzip.decompress((HERE.parent/"solution/frueh/wissenssprung.json.gz").read_bytes())
    flags=json.loads(ref)["v16"]["7261020"]["flags"]
    results=[]
    started=time.monotonic()
    for row in sample():
        team=int(row["side"][-1])
        receipt=json.loads((folder/f"v16_{row['seed']}_{row['side']}.json").read_text())
        path=folder/receipt["filename"]
        if sha256(path.read_bytes()).hexdigest()!=receipt["sha256"]:raise ValueError("Changed raw game")
        with np.load(path,allow_pickle=False) as z:
            states={k:z[k] for k in z.files if k!="commands"}
        kw=inspect.signature(Belief).parameters
        belief=Belief(team,**{k:v for k,v in flags.items() if k in kw})
        for k,v in flags.items():
            if k not in kw and k!="mirrored":setattr(belief,k,v)
        belief.sensor_range=row["sensor"]
        learner=Evidence(team)
        first={}
        for step in range(303):
            obs=public_obs(states,step)
            belief.observe(obs)
            learner.observe(obs)
            for f in belief._point:
                key=pair_key(*divmod(f,24))
                first.setdefault(key,step)
        pairs=[dict(key=int(k),early=int(v),original=first.get(k),lead=first.get(k,303)-v)
               for k,v in sorted(learner.known.items()) if first.get(k,303)>v]
        results.append(dict(seed=row["seed"],side=row["side"],sensor=row["sensor"],group=row["group"],
                            conflicts=learner.conflicts,proved=len(learner.known),earlier=pairs))
    positive=[r for r in results if any(q["lead"]>=3 for q in r["earlier"])]
    count=sum(sum(q["lead"]>=3 for q in r["earlier"]) for r in results)
    maps=len({r["seed"] for r in positive})
    tests=crosscheck()
    gates=dict(technical=tests==600, maps=maps>=6,seats=len(positive)>=8)
    result=dict(exhaustive_tests=tests,qualifies=all(gates.values()),gates=gates,
                maps_with_earlier_proof=maps,seats_with_earlier_proof=len(positive),pair_events=count,
                conflicts=sum(r["conflicts"] for r in results),duration_seconds=time.monotonic()-started,rows=results,
                source=sha256((HERE/"beweis.py").read_bytes()).hexdigest(),plan=sha256((HERE/"PLAN.md").read_bytes()).hexdigest())
    (HERE/"archiv.json").write_text(json.dumps(result,indent=2)+"\n")
    print({k:v for k,v in result.items() if k not in ("rows","source","plan")},flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    compare(p.parse_args().source)
