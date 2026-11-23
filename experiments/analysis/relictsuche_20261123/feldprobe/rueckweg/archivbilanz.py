"""Score the fixed veto in the existing games; unchanged actions imply exact control reuse."""
from collections import Counter
import csv
import json
import gzip

import numpy as np


def calculate(raw,records,controls,work,here,sid):
    stages={}
    detailed=[]
    vetoes=[]
    for stage,rows in raw.items():
        idx={(r["seed"],r["team"],r["arm"],r["opponent"]):r for r in rows}
        cards=sorted({r["seed"] for r in rows})
        pairs=[]
        types=Counter()
        added=0;lost=0
        for s in cards:
            for t in (0,1):
                ref,probe,duel=[idx[s,t,k,o] for k,o in (("reference","solution92"),("probe","solution92"),("probe","v16"))]
                p=records.get((stage,s,t,"solution92"))
                q=records.get((stage,s,t,"v16"))
                pv=bool(p and p["veto"]);dv=bool(q and q["veto"])
                gain=0
                if p:
                    tick=p["event"]["t"]
                    assert ref["prefix"][str(tick)]==p["prefix"] and ref["profile"][:tick]==probe["profile"][:tick]
                    gain=probe["profile"][tick][0]-ref["profile"][tick][0]
                filtered=ref["win"] if pv else probe["win"]
                direct=duel["win"]
                direct_source="unverändert"
                if dv:
                    needs,other=controls[stage,s]
                    if other is None:
                        g=json.loads((work/"control"/stage/f"{s}.json").read_bytes())
                        assert g["identity"]==sid and g["seed"]==s
                        for uid in needs:
                            ev=records[stage,s,uid,"v16"]
                            # Engine hashes order P0 before P1 regardless of controlled seat.
                            assert g["prefix"][str(ev["event"]["t"])]==ev["prefix"]
                        original=g;direct_source="ein gemeinsames neu gespieltes Originalduell"
                    else:
                        original=other;direct_source="bereits archiviertes eingriffsfreies Originalduell"
                    direct=original["win"] if t==original["team"] else 1-original["win"]
                row=dict(phase=stage,seed=s,team=t,solution_v16=ref["win"],solution_simple=probe["win"],solution_verzicht=filtered,
                         direct_simple=duel["win"],direct_verzicht=direct,solution_veto=pv,direct_veto=dv,immediate_simple=gain,
                         immediate_verzicht=0 if pv else gain,direct_source=direct_source)
                detailed.append(row);pairs.append(row)
                for o,z in (("solution92",p),("v16",q)):
                    if not(z and z["veto"]):continue
                    data=dict(phase=stage,seed=s,team=t,gegner=o,zug=z["event"]["t"],uid=z["event"]["u"],
                              xy=z["event"]["xy"],previous=z["prior_position"],location=z["current_position"],bounds=z["bounds"],
                              target_scored=z["scored"],target_arrived=z["arrived"],immediate_prevented=gain if o=="solution92" else None,
                              delta_whole=(filtered-probe["win"]) if o=="solution92" else direct-duel["win"],
                              trigger=(s==162800176 and t==0 and o=="solution92"))
                    vetoes.append(data)
                    types[o,bool(z["scored"])]+=1
        groups={}
        for agent,col in (("v16_solution","solution_v16"),("simple_solution","solution_simple"),("verzicht_solution","solution_verzicht"),
                          ("simple_direct","direct_simple"),("verzicht_direct","direct_verzicht")):
            groups[agent]=sum(x[col] for x in pairs)
        stages[stage]=dict(maps=len(cards),seats=len(pairs),games=len(rows),original_attempts=sum(v["seed"] in cards for v in records.values()),
             veto_maps=len({r["seed"] for r in vetoes if r["phase"]==stage}),
             solution_veto=sum(x["solution_veto"] for x in pairs),direct_veto=sum(x["direct_veto"] for x in pairs),
             veto_solution_scoring=types["solution92",True],veto_direct_scoring=types["v16",True],groups=groups,
             immediate_simple=sum(x["immediate_simple"] for x in pairs),immediate_verzicht=sum(x["immediate_verzicht"] for x in pairs),
             direct_controls_new=sum(src is None for (k,s),(need,src) in controls.items() if k==stage),
             direct_controls_existing=sum(src is not None for (k,s),(need,src) in controls.items() if k==stage))
    mapset={r["seed"] for r in vetoes}
    useful=sum(r["target_scored"] for r in vetoes)
    lower_effect=sum(r["immediate_verzicht"]-r["immediate_simple"] for r in detailed)
    solution=sum(r["solution_verzicht"]-r["solution_simple"] for r in detailed)
    direct=sum(r["direct_verzicht"]-r["direct_simple"] for r in detailed)
    gates=dict(two_other_cards=len(mapset-{162800176})>=2,more_empty_than_scoring=len(vetoes)-useful>useful,
               immediate_preserved=lower_effect>=0,solution_wins_preserved=solution>=0,direct_wins_preserved=direct>=0)
    early=json.loads((here/"fruehe_tafeln.json").read_bytes())
    for split,data in early.items():
        vetos=[v for v in data["records"] if v["veto"]]
        data["veto_scoring_target"]=sum(bool(v["truth"][0]) for v in vetos)
        data["veto_scoring_orig"]=sum(bool(v["truth"][1]) for v in vetos)
        del data["records"]
    stats=dict(identity=sid,stages=stages,earlier=early,gates=gates,passed=all(gates.values()),all_vetoes=vetoes,
               distinct_maps=len(mapset),unnecessary_doubled_whole_games=0,scoring_rejected=useful,empty_rejected=len(vetoes)-useful,
               net_change_immediate=lower_effect,net_change_solution_wins=solution,net_change_direct_wins=direct)
    (here/"archivbilanz.json").write_text(json.dumps(stats,indent=2,ensure_ascii=False)+"\n")
    with (here/"archiv_sitze.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=detailed[0]);writer.writeheader();writer.writerows(detailed)
    prep=[dict(phase=k[0],**v) for k,v in sorted(records.items())]
    (here/"archiv_praefixe.jsonl.gz").write_bytes(gzip.compress(b"".join(json.dumps(v,separators=(",",":")).encode()+b"\n" for v in prep),mtime=0))
    print(json.dumps({k:v for k,v in stats.items() if k!="all_vetoes"}),flush=True)
