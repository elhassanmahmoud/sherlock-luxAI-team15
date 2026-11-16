"""Check all 24 complete replays against the original tables and derive comparable match-level figures."""
import argparse
from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path

from replay import digest, originals, require


def match_summary(game, frames, number):
    prev = frames[0]["before"]
    require(prev==[0,0],"Bad match start score")
    points = [0,0]
    row = dict(seed=game["seed"],side=game["side"],arm=game["arm"],match=number,
               first_positive_gain=None,first_public_points=None,first_enemy_gain=None,
               first_confirmed_occupied=None,first_contact=None,shots=0,shots_1_25=0,
               opp_submitted_shots=0,contact_unit_turns=0,own_unit_turns=0,energy_turns=0,
               confirmed_field_turns=0,confirmed_fields_1_25=0,contact_steps=0,shots_at_visible=0,
               shots_on_confirmed=0,shots_on_confirmed_no_visible_within_one=0)
    start_wins=frames[0]["next_wins"]
    for t,f in enumerate(frames):
        require(f["step"]==(number-1)*101+t and f["before"]==points, "Score/step continuity")
        points=f["after"]
        gains=[b-a for a,b in zip(f["before"],points)]
        require(min(gains)>=0 and (t==100 or points==f["next_public_points"]), "Public score/gain")
        if gains[0]>0 and row["first_positive_gain"] is None:
            row["first_positive_gain"]=t
        if gains[1]>0 and row["first_enemy_gain"] is None:
            row["first_enemy_gain"]=t
        if f["before"][0]>0 and row["first_public_points"] is None:
            row["first_public_points"]=t
        if t in (25,50,75,100):
            row[f"own_after_{t}"],row[f"opp_after_{t}"]=points
        if not t:
            continue
        own=f["own"]; visible={(x,y) for uid,x,y,e in f["visible"]}
        shots=[(x,y,*f["own_orders"][uid][1:]) for uid,x,y,e in own if f["own_orders"][uid][0]==5]
        contact=sum(any(max(abs(x-ex),abs(y-ey))<=game["radius"] for ex,ey in visible) for uid,x,y,e in own)
        confirmed=set(map(tuple,f["confirmed"]))
        fields=len({(x,y) for uid,x,y,e in own} & confirmed)
        if contact and row["first_contact"] is None: row["first_contact"]=t
        if fields and row["first_confirmed_occupied"] is None: row["first_confirmed_occupied"]=t
        row["own_unit_turns"]+=len(own)
        row["energy_turns"]+=sum(e for uid,x,y,e in own)
        row["contact_unit_turns"]+=contact
        row["contact_steps"]+=int(contact>0)
        row["confirmed_field_turns"]+=fields
        row["confirmed_fields_1_25"]+=fields if t<=25 else 0
        for x,y,dx,dy in shots:
            target=x+dx,y+dy
            if target in confirmed:
                row["shots_on_confirmed"]+=1
                if not any(max(abs(target[0]-ex),abs(target[1]-ey))<=1 for ex,ey in visible):
                    row["shots_on_confirmed_no_visible_within_one"]+=1
        row["shots"]+=len(shots)
        row["shots_1_25"]+=len(shots) if t<=25 else 0
        row["shots_at_visible"]+=sum((x+dx,y+dy) in visible for x,y,dx,dy in shots)
        row["opp_submitted_shots"]+=sum(a==5 for a,dx,dy in f["opp_orders"])
    wins=frames[-1]["next_wins"]
    increment=[b-a for a,b in zip(start_wins,wins)]
    require(increment in ([1,0],[0,1]),"Official winner")
    row["won"]=increment[0]
    row["points_tied"]=int(points[0]==points[1])
    require(points[0]==points[1] or row["won"]==int(points[0]>points[1]),"Winner not consistent with score")
    return row


def analyze(raw,repo,output):
    cases,refs=originals(repo)
    rows=[]; games=[]; evidence={}
    for seed,side in cases:
        first_pair={}
        for arm in ("r3","v15"):
            path=raw/f"{arm}-{seed}-{side}.json.gz"
            d=json.loads(gzip.decompress(path.read_bytes()))
            require((d["seed"],d["side"],d["arm"])==(seed,side,arm),"Wrong ID")
            require(d["actual"]==d["expected"]==refs[arm][seed,side],"Panel reproduction")
            fs=d["frames"]
            require(len(fs)==303 and all(len(f["own_orders"])==len(f["opp_orders"])==16 for f in fs),"Missing world orders")
            for order_field,player in (("own_orders",side),("opp_orders","player_"+str(1-int(side[-1])))):
                import struct
                h=hashlib.sha256()
                for f in fs:
                    h.update(struct.pack("<48q",*(x for order in f[order_field] for x in order)))
                require(h.hexdigest()==d["command_sha256"][player],"Bad world order digest")
            first_pair[arm]=fs
            m=[match_summary(d,fs[i*101:(i+1)*101],i+1) for i in range(3)]
            wins=sum(r["won"] for r in m); pts=[sum(r[k] for r in m) for k in ("own_after_100","opp_after_100")]
            require([int(wins>=2),wins,3-wins,*pts,303]==d["actual"],"Per-match scores disagree")
            rows.extend(m)
            evidence[path.name]=digest(path)
        both=zip(first_pair["r3"],first_pair["v15"])
        first=next((a["step"] for a,b in both if any(a[k]!=b[k] for k in ("own_orders","opp_orders"))),None)
        games.append(dict(seed=seed,side=side,r3=refs["r3"][seed,side],v15=refs["v15"][seed,side],first_joint_order_difference=first))
    output.mkdir(parents=True,exist_ok=True)
    with (output/"matches.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summary=dict(games=games,raw_sha256=evidence,rows=len(rows),tables_verified=2,steps_per_arm=12*303)
    for arm in ("r3","v15"):
        summary[arm]={}
        for i in (1,2,3):
            matches=[r for r in rows if r["arm"]==arm and r["match"]==i]
            summary[arm][i]={k:sum(r[k] for r in matches) for k in ("won","own_after_25","opp_after_25","own_after_100","opp_after_100","shots","shots_1_25","confirmed_field_turns","contact_steps","own_unit_turns","energy_turns")}
    (output/"summary.json").write_text(json.dumps(summary,indent=1)+"\n")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ("raw","repo","out"):p.add_argument("--"+arg,required=True,type=Path)
    a=p.parse_args();analyze(a.raw,a.repo,a.out)
