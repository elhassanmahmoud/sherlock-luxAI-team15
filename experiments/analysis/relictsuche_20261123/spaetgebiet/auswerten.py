"""Check every public alarm against actual active relics and the awarded field points."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
RULES=("region","possible","old_joint")


def summarize(game,rule,match):
    frames=[r for r in game["frames"] if r["match"]==match]
    if len(frames)!=100 or [r["turn"] for r in frames]!=list(range(1,101)):
        raise ValueError("Invalid match chronology")
    triggers=[r for r in frames if r["known"] and r["alarms"][rule] and 10<=r["turn"]<=80]
    events=[]
    for r in triggers:
        hidden=set(map(tuple,r["missing"]))
        t=r["turn"]
        seen=next((q["turn"] for q in frames[t:] if hidden.intersection(map(tuple,q["known"]))),101)
        events.append(dict(t=t,true=bool(hidden),outside=any(r["outside"]),lead=seen-t,
                           public_delta=r["gains"],actual_outside=r["outside"],limits=r["limits"]))
    valid=next((e for e in events if e["true"] and e["outside"] and e["lead"]>=5),None)
    our,their=game["matches"][match-1]
    return dict(seed=game["seed"],team=game["team"],group=game["group"],match=match,rule=rule,
                n=len(events),false=sum(not e["true"] for e in events),
                no_outside=sum(not e["outside"] for e in events),
                first=events[0] if events else None,actionable=valid,score=[our,their])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    a=p.parse_args()
    games=[json.loads(gzip.decompress(f.read_bytes())) for f in sorted(a.source.glob("*.json.gz"))]
    if len(games)!=88 or len({(r["seed"],r["team"]) for r in games})!=88:
        raise ValueError("Incomplete late-area study")
    if len({json.dumps(g["sources"],sort_keys=True) for g in games})!=1:
        raise ValueError("Mixed code versions")
    rows=[summarize(g,rule,m) for g in games for rule in RULES for m in (2,3)]
    total={}
    for group in ("new","archive"):
        total[group]={}
        for rule in RULES:
            subset=[r for r in rows if r["rule"]==rule and r["group"]==group]
            good=[r for r in subset if r["actionable"]]
            true_loss=[r for r in good if r["score"][0]<r["score"][1]]
            total[group][rule]=dict(complete_matches=len(subset),alarmed_matches=sum(r["n"]>0 for r in subset),
                false_alarm_turns=sum(r["false"] for r in subset),unexplained_in_region_turns=sum(r["no_outside"] for r in subset),
                actionable_matches=len(good),actionable_maps=len({r["seed"] for r in good}),
                actionable_score_losses=len(true_loss),actionable_loss_seats=len({(r["seed"],r["team"]) for r in true_loss}),
                tied_among_actionable=sum(r["score"][0]==r["score"][1] for r in good),
                mean_lead=float(np.mean([r["actionable"]["lead"] for r in good])) if good else None)
    data=json.dumps(rows,separators=(",",":")).encode()
    (HERE/"meldungen.json.gz").write_bytes(gzip.compress(data,mtime=0))
    result=dict(design=dict(new_games=80,replayed_games=8),groups=total,
                inputs=[dict(path=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in sorted(a.source.glob("*.json.gz"))])
    (HERE/"ergebnis.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps(total,indent=2))


if __name__=="__main__":
    main()
