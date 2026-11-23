"""Attribute the observed margin to real flat-grid positions and ex-ante V16 classifications."""
from collections import Counter
import csv
import gzip
import json
from pathlib import Path

import numpy as np

OUT=Path(__file__).resolve().parent/"verlust"


def names(field):
    return f"({field//24},{field%24})"


def category(row,cell):
    if cell in row["known"]:return "bekannt_punktend"
    if cell in row["dead"]:return "als_leer"
    if cell in row["zone"]:return "gebiet_offen"
    return "ausserhalb_gebiet"


def combine(rows,team):
    c=Counter();types=Counter();per={}
    for row in rows:
        for xy in row["points"][team]:
            c[xy]+=1
            kind=category(row,xy)
            types[kind]+=1
            per.setdefault(xy,Counter())[kind]+=1
    return c,types,per


def groups(rows):
    if len(rows)!=2 or not all(len(x)==303 for x in rows):raise ValueError("Incomplete trajectories")
    r,p=rows
    output={}
    turns=[]
    for mi in range(3):
        a,b=(x[mi*101:(mi+1)*101] for x in rows)
        totals=[np.cumsum([q["credit"] for q in x],axis=0) for x in (a,b)]
        data={}
        for team in range(2):
            (ra,ka,kra),(rb,kb,krb)=(combine(x,team) for x in (a,b))
            ordered=sorted(set(ra)|set(rb),key=lambda z:-abs(rb[z]-ra[z]))
            data[str(team)]=dict(reference=sum(ra.values()),probe=sum(rb.values()),cat_reference=dict(ka),cat_probe=dict(kb),
              fields=[dict(xy=names(z),ref=ra[z],probe=rb[z],delta=rb[z]-ra[z],
                      ref_public=dict(kra.get(z,{})),probe_public=dict(krb.get(z,{})),
                      start_status=[category(x[0],z) for x in (a,b)],
                      ever_known=[next((i for i,h in enumerate(x) if z in h["known"]),None) for x in (a,b)],
                      ever_zone=[next((i for i,h in enumerate(x) if z in h["zone"]),None) for x in (a,b)]) for z in ordered])
        for t in range(101):
            ra,rb=a[t],b[t]
            p0,p1=totals[0][t].tolist(),totals[1][t].tolist()
            turns.append(dict(match=mi+1,turn=t,total=mi*101+t,ref_gain_own=ra["credit"][0],ref_gain_opp=ra["credit"][1],
                probe_gain_own=rb["credit"][0],probe_gain_opp=rb["credit"][1],ref_own=p0[0],ref_opp=p0[1],probe_own=p1[0],probe_opp=p1[1],
                ref_margin=p0[0]-p0[1],probe_margin=p1[0]-p1[1],
                changed_actions=sum(x!=y for x,y in zip(ra["own_cmd"],rb["own_cmd"])),
                changed_opponent_actions=sum(x!=y for x,y in zip(ra["opp_cmd"],rb["opp_cmd"])),
                known_points_ref=len(ra["known"]),known_points_probe=len(rb["known"]),zone_ref=len(ra["zone"]),zone_probe=len(rb["zone"])))
        output[str(mi+1)]=data
    differences={}
    for name in ("own_cmd","opp_cmd","known","dead","zone","points","credit","occupancy"):
        d=[i for i,(a,b) in enumerate(zip(r,p)) if a[name]!=b[name]]
        differences[name]=dict(first=d[0] if d else None,count=len(d),match3_first=next((t-202 for t in d if t>=202),None))
    with (OUT/"zugbilanz.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=turns[0]);w.writeheader();w.writerows(turns)
    (OUT/"bilanz.json").write_text(json.dumps(dict(per_match=output,first_differences=differences),indent=2)+"\n")


if __name__=="__main__":
    with gzip.open(OUT/"zuege.jsonl.gz","rt") as f:data=[json.loads(z)["trace"] for z in f]
    groups(data)
