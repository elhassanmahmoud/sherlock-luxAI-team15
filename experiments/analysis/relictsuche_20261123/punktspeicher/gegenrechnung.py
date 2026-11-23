"""Independent public infeasibility certificates, referee comparisons and reachability recount."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import warnings

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import csr_matrix

HERE=Path(__file__).resolve().parent


def reflected(i):
    x,y=divmod(i,24)
    return (23-y)*24+23-x


def canonical(i):
    return min(i,reflected(i))


def unmask(x):
    n=int(x,16)
    return {i for i in range(n.bit_length()) if (n>>i)&1}


def neighbors(c):
    x,y=divmod(c,24)
    return [(d,24*xx+yy) for d,(xx,yy) in enumerate(((x,y),(x,y-1),(x+1,y),(x,y+1),(x-1,y)))
            if d and 0<=xx<24 and 0<=yy<24]


def certificates(raw, proofs):
    facts={q["pair"]:q["proof"] for q in proofs}
    proof_times=set(facts.values())
    validated=set()
    rows=[];stable_from=None;previous=0
    for old in raw:
        t=old["step"]
        if old["ms"]==0:
            stable_from=None
            previous=old["points"]
            continue
        if stable_from is None and (old["ms"]>=50 or old["epoch_seen"]):
            stable_from=t
        weight=Counter(canonical(x) for x in set(old["occupied"]))
        gain=old["points"]-previous
        rows.append((weight,gain,t))
        previous=old["points"]
        if t not in proof_times:continue
        candidates={k for k,v in facts.items() if v==t}
        labels=sorted(set().union(validated,candidates,*(set(w) for w,_,_ in rows)))
        pos={k:i for i,k in enumerate(labels)}
        matrix=np.zeros((len(rows),len(pos)),dtype=float)
        lows=[];highs=[]
        for j,(w,g,step) in enumerate(rows):
            for k,n in w.items():
                matrix[j,pos[k]]=n
            lows.append(g)
            exact=step==t or (stable_from is not None and step>=stable_from)
            highs.append(g if exact else np.inf)
        lc=LinearConstraint(csr_matrix(matrix),np.asarray(lows),np.asarray(highs))
        fixed=np.zeros(len(labels))
        for k in validated:
            fixed[pos[k]]=1
        for k in candidates:
            upper=np.ones(len(labels));upper[pos[k]]=0
            # Earlier facts were independently established. Test all same-tick discoveries separately.
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore",message="Unrecognized options detected.*threads.*")
                sol=milp(np.zeros(len(labels)),integrality=np.ones(len(labels)),bounds=Bounds(fixed,upper),constraints=lc,
                         options={"presolve":True,"threads":1,"time_limit":10.})
            if sol.status!=2:
                raise ValueError(f"Public score constraints allow claimed point {k} to be zero in step {t}: {sol.status}")
        validated.update(candidates)
    assert validated==set(facts)
    return len(validated)


def independent_access(public, policy, points, positives):
    codes={canonical(k) for k in points}
    occupied=set(public["occupied"])
    foe=set(policy["enemy"])
    safe=unmask(policy["known_passable"])
    targets=points & unmask(policy["visible"]) & safe - (occupied | foe | set(policy["planned"]))
    broad=set();adj=set();four=set()
    for _,origin,orig,assigned,allowed in policy["free"]:
        if origin in positives or assigned in positives:
            continue
        for d,start in neighbors(origin):
            if not allowed & (1<<d):continue
            if start in points:
                broad.add(canonical(start))
            if d==orig or start in foe or start not in safe:
                continue
            if start in targets:adj.add(canonical(start))
            reached={start};level={start}
            for _ in range(3):
                level={n for p in level for _,n in neighbors(p) if n!=origin and n in safe and n not in foe}-reached
                reached.update(level)
            four.update(canonical(c) for c in reached & targets)
    return broad,adj,four


def run(group):
    folder=HERE/group
    res=json.loads((folder/"ergebnis.json").read_text())
    with gzip.open(folder/"beobachtungen.jsonl.gz","rt") as f:
        games=[json.loads(line) for line in f]
    with gzip.open(folder/"beweise.jsonl.gz","rt") as f:
        proofs={(r["seed"],r["team"]):r for line in f if (r:=json.loads(line))}
    assert len(games)==len(proofs)==2*len(json.loads((HERE/"karten.json").read_text())[group])
    assert hashlib.sha256((folder/"beobachtungen.jsonl.gz").read_bytes()).hexdigest()==res["raw_sha256"]
    assert hashlib.sha256((folder/"beweise.jsonl.gz").read_bytes()).hexdigest()==res["proof_sha256"]
    all_checks=Counter();totals=Counter()
    strict=Counter()
    for g in games:
        s,seat=g["seed"],g["team"]
        r=proofs[s,seat]
        assert r["action_hash"]==g["action_hash"] and len(r["frames"])==len(g["public"])==303
        all_checks["milp_zero_hypotheses_rejected"]+=certificates(g["public"],r["points"])
        first={q["pair"]:q["proof"] for q in r["points"]}
        first_v={}
        prev=set()
        for data,pol,truthcode,saved in zip(g["public"],g["policy"],g["referee"],r["frames"],strict=True):
            t=data["step"]
            proof={k for k,step in first.items() if step<=t}
            assert proof==unmask(saved["p"])
            neg=unmask(saved["n"]); local=unmask(saved["local"])
            truth=unmask(truthcode)
            assert truth>=prev and truth=={reflected(c) for c in truth};prev=truth
            assert proof<=truth and not neg&truth and local<=proof
            if data["ms"]:
                expected_score=sum(c in truth for c in set(data["occupied"]))
                assert expected_score==data["points"]-g["public"][t-1]["points"]
                all_checks["public_score_equations"]+=1
            v16=unmask(pol["point"]);dead=unmask(pol["dead"])
            vpair={canonical(c) for c in v16}
            for k in vpair:first_v.setdefault(k,t)
            worlds=proof|{reflected(c) for c in proof}
            extra=proof-vpair
            falsedead={canonical(c) for c in worlds & dead}
            carried={c for c in extra if first[c]//101<t//101}
            only=extra-local
            targets=(extra|{reflected(c) for c in extra}) | (worlds & dead)
            broad,adj,four=independent_access(data,pol,targets,worlds|v16) if targets and data["ms"] else (set(),set(),set())
            fields=dict(extra=extra,dead=falsedead,local_extra=local-vpair,only_persistent=only,carried=carried,
                        all_false_dead={canonical(c) for c in dead&truth},legal_adj=broad,strict_adj=adj,strict_four=four,
                        dead_adj=adj&falsedead,dead_four=four&falsedead,persistent_adj=adj&only,persistent_four=four&only,
                        carried_four=four&carried)
            for name,values in fields.items():
                if values!=unmask(saved.get(name,"0")):
                    raise ValueError(f"Independent reach/knowledge difference on {s,seat,t,name}")
                totals[name]+=len(values)
            all_checks["public_readouts"]+=1
            all_checks["world_validated_positive_pair_ticks"]+=len(proof)
            all_checks["world_validated_negative_pair_ticks"]+=len(neg)
        for q in r["points"]:
            assert first_v.get(q["pair"])==q["v16"]
            if q["lead"]>0:strict["positive_leads"]+=1
    for name,v in totals.items():
        assert v==res["categories"][name]["pair_ticks"]
    assert strict["positive_leads"]==res["strict_leads"]["seat_pairs"]
    return dict(group=group,games=len(games),maps=len(games)//2,checks=dict(all_checks),pair_ticks=dict(totals),
                distinct_positive_leads_by_seat=strict["positive_leads"],passed=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("group",choices=("archiv","frisch"))
    args=parser.parse_args()
    print(json.dumps(run(args.group),indent=2))
