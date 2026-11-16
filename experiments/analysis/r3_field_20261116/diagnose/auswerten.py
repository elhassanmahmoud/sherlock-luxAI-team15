"""Compare the actual sole occupancy and the two legal-endpoint plans on each Blend position."""
from collections import Counter, defaultdict
import argparse
import csv
import gzip
import hashlib
import json
import struct
from pathlib import Path

DXY=((0,0),(0,-1),(1,0),(0,1),(-1,0),(0,0))


def destinations(f,orders,cost):
    blocks=set(map(tuple,f["known_asteroids"]))
    occupied=defaultdict(list)
    for uid,x,y,energy in f["own"]:
        dx,dy=DXY[orders[uid][0]]
        destination=(x+dx,y+dy)
        if energy<cost or destination in blocks or not all(0<=i<24 for i in destination):
            destination=x,y
        occupied[destination].append(uid)
    return occupied


def project(raw,out,repo):
    register=json.loads((repo/"experiments/analysis/r3_v15_blend_20261116/restkarten.json").read_bytes())["r3_comparison"]
    rows=[];events=[];hashes={}
    for outcome in ("gained","lost"):
        for seed,side in register[outcome]:
            for arm in ("r3","blend"):
                path=raw/f"{arm}-{seed}-{side}.json.gz";b=path.read_bytes()
                hashes[path.name]=hashlib.sha256(b).hexdigest()
                d=json.loads(gzip.decompress(b));fs=d["frames"]
                if d["actual"]!=d["expected"] or len(fs)!=303:raise ValueError(path)
                refpath=repo/f"experiments/analysis/r3_v15_blend_20261116/rest_{arm}/games.jsonl"
                ref=next(r for r in map(json.loads,refpath.read_bytes().splitlines()) if (r["seed"],r["seat"])==(seed,side))
                if d["actual"]!=ref:raise ValueError("Original mismatch")
                for player,k in ((side,"own_orders"),("player_"+str(1-int(side[-1])),"opp_orders")):
                    h=hashlib.sha256()
                    for f in fs:
                        h.update(struct.pack("<48q",*(x for cmd in f[k] for x in cmd)))
                    if h.hexdigest()!=d["command_sha256"][player]:raise ValueError("Action digest mismatch")
                for match in range(1,4):
                    ii=(match-1)*101
                    window=fs[ii:ii+101]
                    stats=Counter(both_parents_dropped=0,planned_solo_departures=0,planned_handoffs=0,
                                  realized_handoffs=0,planned_drops_without_handoff=0)
                    stats["first_public_points"]=next((i for i,f in enumerate(window) if f["before"][0]>0),None)
                    stats["first_confirmed"]=next((i for i,f in enumerate(window) if f["confirmed"] and i),None)
                    for t,f in enumerate(window):
                        if f["step"]!=ii+t:raise ValueError("Clock mismatch")
                        if t in (25,50,75,100):
                            stats[f"score_{t}"],stats[f"opp_{t}"]=f["after"]
                        if t in (0,100): continue  # next public observation crosses a match boundary
                        known=set(map(tuple,f["confirmed"]))
                        own=defaultdict(list);after=defaultdict(list)
                        for u,x,y,e in f["own"]: own[x,y].append(u)
                        for u,x,y in f["next_own"]: after[x,y].append(u)
                        # Public next position is independently recorded again as next frame.before.
                        if sorted(f["next_own"])!=sorted([p[:3] for p in window[t+1]["own"]]):
                            raise ValueError("Observation mismatch")
                        stats["occupied_field_turns"]+=len(known & own.keys())
                        stats["sole_field_turns"]+=sum(len(own[p])==1 for p in known)
                        stats["sole_vacated"]+=sum(len(own[p])==1 and not after[p] for p in known)
                        stats["sole_replaced"]+=sum(len(own[p])==1 and bool(after[p]) and own[p][0] not in after[p] for p in known)
                        stats["freshly_occupied"]+=sum(not own[p] and bool(after[p]) for p in known)
                        actual_plan=destinations(f,f["own_orders"],d["move_cost"])
                        for p,units in own.items():
                            if p not in known or len(units)!=1:continue
                            planned=actual_plan.get(p,[])
                            if units[0] in planned:continue
                            stats["planned_solo_departures"]+=1
                            if not planned:
                                stats["planned_drops_without_handoff"]+=1
                            else:
                                stats["planned_handoffs"]+=1
                                stats["realized_handoffs"]+=bool(set(planned)&set(after[p]))
                        if arm!="blend":continue
                        plans=[destinations(f,f[k],d["move_cost"]) for k in ("r3_orders","own_orders","v15_orders")]
                        # defaultdict access does not affect membership checks below.
                        for p in sorted(known):
                            r,b,v=(z.get(p,[]) for z in plans)
                            if bool(r)==bool(b):continue
                            typ="dropped" if r else "added"
                            stats[typ]+=1
                            if bool(after[p])==bool(b):stats[typ+"_realized"]+=1
                            if len(own[p])==1:stats[typ+"_from_sole"]+=1
                            if typ=="dropped" and v:stats["both_parents_dropped"]+=1
                            uids=sorted(set(r+b))
                            near=set(f["contact_uids"])
                            events.append(dict(outcome=outcome,seed=seed,side=side,match=match,turn=t,
                                x=p[0],y=p[1],kind=typ,before=own[p],after=after[p],r3_plan=r,blend_plan=b,v15_plan=v,
                                near=[u for u in uids if u in near],orders={u:[f["r3_orders"][u],f["own_orders"][u]] for u in uids},
                                prior_positions={u:[x,y] for u,x,y,_ in f["own"] if u in uids},
                                blend_before=f["before"],blend_after=f["after"]))
                    stats["won"]=window[-1]["next_wins"][0]-window[0]["next_wins"][0]
                    rows.append(dict(outcome=outcome,seed=seed,side=side,arm=arm,match=match,**stats))
                m=rows[-3:]
                if [sum(x[k] for x in m) for k in ("won","score_100","opp_100")]!=[ref[k] for k in ("our_wins","our_points","opp_points")]:
                    raise ValueError("Score totals disagree")
    out.mkdir(parents=True,exist_ok=True)
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with (out/"matches.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,restval=0);w.writeheader();w.writerows(rows)
    (out/"field_events.json.gz").write_bytes(gzip.compress(json.dumps(events,separators=(",",":")).encode(),mtime=0))
    (out/"hashes.json").write_text(json.dumps(hashes,indent=2,sort_keys=True)+"\n")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("raw","out","repo"):p.add_argument("--"+key,type=Path,required=True)
    a=p.parse_args();project(a.raw,a.out,a.repo)
