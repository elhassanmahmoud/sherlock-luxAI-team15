"""Independently recount all general-panel winners and separate active and identical-command sight groups."""
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from experiments.analysis.relictsuche_20261123.punktwissen.spiele import HERE, decoded
from experiments.analysis.relictsuche_20261123.vergleich.spielen import sha,write_once


def verify(key,r):
    s,t,arm,opp=key
    assert int(r["seed"])==s and r["team"]==t and r["version"]==arm and r["opponent"]==opp
    actions=decoded(r)
    assert actions.shape==(303,2,16,3) and r["digest"]==hashlib.sha256(actions.astype("<i4").tobytes()).hexdigest()
    assert all(len(m["points"])==2 and all(p>=0 for p in m["points"]) and m["win"] in (0,1) for m in r["matches"])
    assert len(r["matches"])==3 and r["win"]==int(sum(m["win"] for m in r["matches"])>=2)
    assert all(m["win"]==int(m["points"][0]>m["points"][1]) for m in r["matches"] if m["points"][0]!=m["points"][1])
    return actions


def compute(rows):
    ids=sorted({k[0] for k in rows})
    groups={}
    marker=[]
    for seed in ids:
        local=[]
        twins=[rows[seed,t,"neu","v16"] for t in (0,1)]
        for t in (0,1):
            base, new, direct=[rows[seed,t,arm,opp] for arm,opp in (("v16","solution92"),("neu","solution92"),("neu","v16"))]
            rr,nn,dd=[verify((seed,t,r["version"],r["opponent"]),r) for r in (base,new,direct)]
            level=base["sensor"]
            assert level==new["sensor"]==direct["sensor"]
            distinct=np.flatnonzero(np.any(rr!=nn,axis=(1,2,3)))
            events=new["events"]
            if len(distinct):
                assert events and distinct[0]>=events[0]["t"]
            else:
                assert base["win"]==new["win"] and base["matches"]==new["matches"]
            if level!=1:
                assert not events and not direct["events"] and not len(distinct)
                assert twins[0]["digest"]==twins[1]["digest"] and twins[0]["win"]+twins[1]["win"]==1
            local.append(dict(seed=seed,team=t,level=level,base=base["win"],new=new["win"],direct=direct["win"],
                              changes=bool(len(distinct)),first=int(distinct[0]) if len(distinct) else None,
                              range_events=len(events),direct_events=len(direct["events"])))
        assert local[0]["level"]==local[1]["level"]
        marker.extend(local)
    for level in [1,2,3,4,"all"]:
        selected=[r for r in marker if level=="all" or r["level"]==level]
        n=len(selected)//2
        if not n:continue
        diff=np.array([r["new"]-r["base"] for r in selected]).reshape(n,2).mean(1)
        direct=np.array([r["direct"] for r in selected]).reshape(n,2).mean(1)
        ix=np.random.default_rng(231123).integers(0,n,(20000,n))
        groups[str(level)]=dict(cards=n,seats=2*n,original=sum(r["base"] for r in selected),candidate=sum(r["new"] for r in selected),
                                direct=sum(r["direct"] for r in selected),changed=sum(r["changes"] for r in selected),
                                rescued=sum(r["new"]>r["base"] for r in selected),lost=sum(r["new"]<r["base"] for r in selected),
                                cards_ahead=int(np.sum(diff>0)),cards_behind=int(np.sum(diff<0)),
                                gain_ci95=np.quantile(diff[ix].mean(1),[.025,.975]).tolist(),
                                direct_ci95=np.quantile(direct[ix].mean(1),[.025,.975]).tolist())
    return groups,marker


def main():
    record=HERE/"allgemein_partien.jsonl.gz"
    known=json.loads((HERE/"allgemein.json").read_text())
    with gzip.open(record,"rt") as f:
        rows={(r["seed"],r["team"],r["version"],r["opponent"]):r for r in map(json.loads,f)}
    assert len(rows)==960 and sorted({k[0] for k in rows})==list(range(162860000,162860160))
    assert all(r["source"]==known["source"] for r in rows.values())
    groups,marker=compute(rows)
    all_maps=groups["all"]
    assert (all_maps["candidate"],all_maps["original"],all_maps["direct"])==(known["solution"],known["baseline"],known["direct_wins"])
    assert np.allclose(all_maps["gain_ci95"],known["solution_gain"]["ci95"])
    assert np.allclose(all_maps["direct_ci95"],known["direct"]["ci95"])
    write_once(HERE/"allgemein_gegenrechnung.json",dict(source=sha(record),groups=groups,selected_seats=marker))


if __name__=="__main__":main()
