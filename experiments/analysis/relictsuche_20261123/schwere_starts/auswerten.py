"""Independently verify tapes and compare all 70 real game outcomes from their fixed sources."""
import base64
from collections import Counter
import csv
import gzip
from hashlib import sha256
import json
from pathlib import Path
import zlib

import numpy as np

HERE=Path(__file__).resolve().parent
D=HERE.parent
NAMES={"v16":"Original-V16","ort":"Früher Ortsprior","gemeinsam":"Ort und Flotte","spaet":"Späte Suchwahl","wissen":"Einfaches Punktwissen"}


def read(path):
    with gzip.open(path,"rt") as f:return [json.loads(s) for s in f]


def check(test,msg):
    if not test:raise ValueError(msg)


def commands(r,field):
    a=np.frombuffer(zlib.decompress(base64.b64decode(r["tape"])),np.int8).reshape(303,2,16,3)
    check(sha256(a.astype("<i4").tobytes()).hexdigest()==r[field],"Bad action digest")
    return a


def main():
    archive=HERE/"partien.jsonl.gz"
    manifest=json.loads((HERE/"manifest.json").read_bytes())
    cards=manifest["cards"]
    cases={(s,t) for s in cards for t in (0,1)}
    originals={}
    for src in (D/"punktwissen/partien.jsonl.gz",D/"punktwissen/allgemein_partien.jsonl.gz"):
        for r in read(src):
            if (r["seed"],r["team"]) in cases and r["opponent"]=="solution92":
                k=(r["seed"],r["team"],"v16" if r["version"]=="v16" else "wissen")
                check(k not in originals and r["sensor"]==1,"Duplicated source")
                originals[k]=r
    reps={(r["seed"],r["team"],r["name"]):r for r in read(archive)}
    check(len(reps)==56 and len(originals)==28 and len(cards)==7,"Wrong case size")
    losses={(s,t) for s,t in cases if originals[s,t,"v16"]["win"]==0}
    check(losses==set(map(tuple,manifest["losses"])) and len(losses)==8,"Wrong loss roster")
    detailed=[];incidents={};gaps={}
    for s,t in sorted(cases):
        old=originals[s,t,"v16"];baseline=commands(old,"digest")
        mirror=originals[s,1-t,"v16"]["win"]
        for name in NAMES:
            r=originals[s,t,name] if name=="wissen" else reps[s,t,name]
            a=commands(r,"digest")
            delta=np.any(a!=baseline,axis=(1,2,3))
            different=np.flatnonzero(delta)
            first=int(different[0]) if len(different) else None
            m=r["matches"]
            check(len(m)==3 and int(sum(q["win"] for q in m)>=2)==r["win"],"Wrong tournament result")
            if name!="wissen":
                check(r["source"]==manifest["identity"] and r["steps"]==303 and r["caught_errors"]==[0,0] and r["actions_checked"]==[303,303]
                      and len(r["profile"])==303,"Incomplete simulated game")
                p0=[len(z["scores"][0]["actual"]) for z in r["profile"][:101]]
                credit=next((i for i,v in enumerate(p0) if v),101)
                sight=next((i for i,v in enumerate(r["profile"][:101]) if v["visible_relic"]),101)
                check(credit==r["credit"] and sight==r["sight"],"Timing differs from field occupancy")
                bymatch=[]
                for j in range(3):
                    tick=r["profile"][101*j:101*(j+1)]
                    real=[sum(len(h["scores"][k]["actual"]) for h in tick) for k in (0,1)]
                    check(real==m[j]["points"],"Match score from occupancy differs")
                    bymatch.append({"own":real[0],"opp":real[1],"knowledge":
                                [[sum(h["scores"][k][attr] for h in tick) for attr in ("known","in_zone")] for k in (0,1)],
                                "early70":[sum(len(h["scores"][k]["actual"]) for h in tick[:71]) for k in (0,1)]})
                gaps[s,t,name]=bymatch
            if name=="v16":
                check(first is None and all(old[k]==r[k] for k in ("sight","credit","matches","win","digest")),"Failed byte-exact original")
            elif name=="wissen":
                check(r["source"]==old["source"] and r["seed"]==old["seed"] and r["team"]==old["team"],"Knowledge/control source differs")
                check(not different.size or (r["events"] and first>=r["events"][0]["t"]),"Knowledge without its public proof")
            elif r["events"]:
                e=r["events"][0]
                check(first==e[0] and np.array_equal(a[first,1-t],baseline[first,1-t]) and
                      np.flatnonzero(np.any(a[first,t]!=baseline[first,t],axis=1)).tolist()==[e[1]],"First scout intervention")
            else:
                check(first is None,"Inactive scout differs")
            row=dict(seed=s,seat=t,other_seat_v16_win=mirror,original_loss=(s,t) in losses,method=name,sight=r["sight"],credit=r["credit"],
                     m1_own=m[0]["points"][0],m1_opp=m[0]["points"][1],m2_own=m[1]["points"][0],m2_opp=m[1]["points"][1],
                     m3_own=m[2]["points"][0],m3_opp=m[2]["points"][1],match_wins="".join(str(z["win"]) for z in m),whole_win=r["win"],
                     first_action_difference=first,interventions_or_proofs=len(r["events"]),digest=r["digest"])
            detailed.append(row)
            incidents[s,t,name]=row
    summary={}
    for name in NAMES:
        rr=[r for r in detailed if r["method"]==name]
        orig=[r for r in detailed if r["method"]=="v16"]
        a=[r for r in rr if r["original_loss"]];b=[r for r in rr if not r["original_loss"]]
        g=dict(rescued=[[r["seed"],r["seat"]] for r in a if r["whole_win"]],
               lost_control=[[r["seed"],r["seat"]] for r in b if not r["whole_win"]],
               wins=sum(r["whole_win"] for r in rr),changed=sum(r["first_action_difference"] is not None for r in rr),
               changed_in_losses=sum(r["first_action_difference"] is not None for r in a),
               loss_sight_gain=float(np.mean([incidents[r["seed"],r["seat"],"v16"]["sight"]-r["sight"] for r in a])),
               loss_credit_gain=float(np.mean([incidents[r["seed"],r["seat"],"v16"]["credit"]-r["credit"] for r in a])))
        summary[name]=g
    with (HERE/"alle_sitze.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=detailed[0]);w.writeheader();w.writerows(detailed)
    with (HERE/"FALLTABELLE.md").open("w") as f:
        f.write("# Alle sieben Karten auf beiden Startseiten\n\nDie drei Punktestände jeder Zeile zeigen Sherlock zu Original-Solution. Zeitpunkte sind nullbasiert. Der Wert 101 bedeutet, dass die Sicht oder die erste eigene Gutschrift im ersten Match ausblieb. Der erste abweichende Befehl bezeichnet den tatsächlich eingesandten ersten Unterschied gegenüber der originalen V16-Gesamtaufzeichnung.\n")
        for s,t in sorted(cases):
            group="ursprüngliche Niederlage" if (s,t) in losses else "ursprünglicher Sieg auf der Gegenseite"
            f.write(f"\n## {s}, P{t} ({group})\n\n| Spieler | Erste Sicht | Erste Gutschrift | Match 1 | Match 2 | Match 3 | Ausgang | Erster abweichender Befehl |\n|---|---:|---:|---:|---:|---:|---|---:|\n")
            for name,display in NAMES.items():
                r=incidents[s,t,name]
                fields=[f"{r[f'm{j}_own']} zu {r[f'm{j}_opp']}" for j in (1,2,3)]
                first=r["first_action_difference"]
                f.write(f"| {display} | {r['sight']} | {r['credit']} | {' | '.join(fields)} | {'Sieg' if r['whole_win'] else 'Niederlage'} | {first if first is not None else '–'} |\n")
    diag=[dict(seed=s,seat=t,method=name,rounds=q) for (s,t,name),q in sorted(gaps.items())]
    (HERE/"rundenbilanz.json").write_text(json.dumps(diag,indent=2)+"\n")
    proof=dict(maps=cards,original_losses=len(losses),prior_wins=len(cases)-len(losses),new_games=len(reps),
        new_commands_checked=len(reps)*303*32,byte_exact_v16_controls=sum(r["method"]=="v16" for r in detailed),
        existing_knowledge_games=sum(r["method"]=="wissen" for r in detailed),archived_knowledge_digests_checked=14,
        cases=len(detailed),archive_sha256=sha256(archive.read_bytes()).hexdigest(),summary=summary)
    (HERE/"ergebnis.json").write_text(json.dumps(proof,indent=2)+"\n")
    print(json.dumps(summary,ensure_ascii=False),flush=True)


if __name__=="__main__":main()
