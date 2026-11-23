"""Independently reconstruct complete games, paired differences and bootstrap intervals from both players' commands."""
import argparse
import base64
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import zlib
import numpy as np
from experiments.analysis.relictsuche_20261123.vergleich.spielen import sha,write_once

HERE=Path(__file__).resolve().parent


def decode(r):
    packed=zlib.decompress(base64.b64decode(r["tape"],validate=True))
    moves=np.frombuffer(packed,np.int8).reshape(303,2,16,3)
    assert np.all((moves[:,:,:,0]>=0)&(moves[:,:,:,0]<=5))
    assert r["digest"]==hashlib.sha256(moves.astype("<i4").tobytes()).hexdigest()
    for m in r["matches"]:
        a,b=m["points"]
        assert a>=0 and b>=0 and (a==b or m["win"]==int(a>b)) and m["win"] in (0,1)
    assert len(r["matches"])==3 and r["win"]==int(sum(z["win"] for z in r["matches"])>=2)
    return moves


def sign_test(values):
    # Randomization of whole-map differences. Opposite seats stay together even if both changed.
    pmf={0:1}
    for v in abs(np.array(values,dtype=int)):
        if not v:continue
        nxt=Counter()
        for s,count in pmf.items():
            nxt[s+int(v)]+=count;nxt[s-int(v)]+=count
        pmf=nxt
    return sum(c for s,c in pmf.items() if s>=sum(values))/sum(pmf.values())


def summarize(pairs):
    maps=sorted({v["seed"] for v in pairs})
    sel={(v["seed"],v["team"]):v for v in pairs}
    values=np.array([[[sel[s,t][k] for k in ("base","new","direct","gain","sight","credit","changed")] for t in (0,1)] for s in maps])
    m=values.mean(axis=1);n=len(m)
    indices=np.random.default_rng(231123).integers(0,n,(20000,n))
    ci=np.quantile(m[indices].mean(1),[.025,.975],axis=0)
    result=dict(cards=n,seats=len(pairs),original=int(values[:,:,0].sum()),candidate=int(values[:,:,1].sum()),
                direct=int(values[:,:,2].sum()),gain=float(m[:,3].mean()),gain_ci=ci[:,3].tolist(),direct_ci=ci[:,2].tolist(),
                sight_gain=float(m[:,4].mean()),sight_ci=ci[:,4].tolist(),credit_gain=float(m[:,5].mean()),credit_ci=ci[:,5].tolist(),
                changed=int(values[:,:,6].sum()),rescued=int((values[:,:,3]>0).sum()),lost=int((values[:,:,3]<0).sum()),
                winning_cards=int((m[:,3]>0).sum()),losing_cards=int((m[:,3]<0).sum()),
                exact_p_solution=sign_test(np.rint(2*m[:,3]).astype(int)),exact_p_direct=sign_test(np.rint(2*m[:,2]-1).astype(int)))
    return result


def verify(rows,label):
    maps=sorted({k[0] for k in rows});pairs=[]
    assert len(rows)==6*len(maps) and len({r["source"] for r in rows.values()})==1
    for s in maps:
        b,h2=(rows[s,t,label,"v16"] for t in (0,1))
        for t in (0,1):
            ref,new,h=[rows[s,t,arm,opp] for arm,opp in (("v16","solution92"),(label,"solution92"),(label,"v16"))]
            a,c,_=map(decode,(ref,new,h))
            level=ref["sensor"];assert level==new["sensor"]==h["sensor"]
            div=np.flatnonzero(np.any(a!=c,axis=(1,2,3)))
            if not len(div):assert new["matches"]==ref["matches"] and new["sight"]==ref["sight"] and new["credit"]==ref["credit"]
            if level!=1:assert not len(div) and b["digest"]==h2["digest"] and b["win"]+h2["win"]==1
            if len(div) and label=="ortundflotte":
                # Until this point both teams observed identical environments; just one own ship may deviate on the first differing tick.
                j=int(div[0])
                assert np.array_equal(a[j,1-t],c[j,1-t]) and np.any(a[j,t]!=c[j,t],axis=1).sum()==1
                assert 16<=j<=83 and j<ref["sight"] and j<=ref["credit"]
            pairs.append(dict(seed=s,team=t,level=level,base=ref["win"],new=new["win"],direct=h["win"],gain=new["win"]-ref["win"],
                      sight=ref["sight"]-new["sight"],credit=ref["credit"]-new["credit"],changed=int(bool(len(div))),
                      diverged=int(div[0]) if len(div) else None))
    return {"all":summarize(pairs),**{str(k):summarize([r for r in pairs if r["level"]==k]) for k in sorted({r["level"] for r in pairs})}},pairs


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("mode",choices=("reference","final"));a=p.parse_args()
    reference=a.mode=="reference";folder=HERE.parent/"punktwissen" if reference else HERE
    archive=folder/("allgemein_partien.jsonl.gz" if reference else "partien.jsonl.gz")
    gate=json.loads((folder/("allgemein.json" if reference else "ergebnis.json")).read_bytes())
    label="neu" if reference else gate["player"];rows={}
    with gzip.open(archive,"rt") as f:
        for line in f:
            r=json.loads(line)
            k=(r["seed"],r["team"],r["version"],r["opponent"]) if reference else tuple(r["key"])
            assert k not in rows and r["source"]==gate["source"]
            rows[k]=r
    assert len(rows)==960 and sorted({k[0] for k in rows})==list(range(162860000,162860160) if reference else range(164300000,164300160))
    groups,pairs=verify(rows,label);overall=groups["all"]
    if reference:
        keys=(gate["baseline"],gate["solution"],gate["direct_wins"]);diff=gate["solution_gain"]["ci95"];dire=gate["direct"]["ci95"]
    else:
        keys=(gate["original"],gate["candidate"],gate["direct"]);diff=gate["solution_gain_ci"];dire=gate["direct_ci"]
    assert keys==(overall["original"],overall["candidate"],overall["direct"]) and np.allclose(diff,overall["gain_ci"]) and np.allclose(dire,overall["direct_ci"])
    qualified=(diff[0]>0 and keys[2]>=160 and dire[0]>=.45) or (dire[0]>.5 and diff[0]>=-.01)
    assert bool(qualified)==gate["qualified"]
    if not reference:write_once(HERE/"nachrechnung.json",dict(archive=sha(archive),qualified=bool(qualified),groups=groups,seats=pairs))
    print(overall)


if __name__=="__main__":main()
