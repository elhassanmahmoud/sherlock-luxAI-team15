"""Count the single registered trigger by outcome group, before any fresh test."""
from collections import Counter
import argparse
from hashlib import sha256
import gzip
import json
from pathlib import Path
from messen import HERE, SCORES, observations


def read(path):
    if path.is_dir():
        for f in sorted(path.glob("*.json")):
            yield json.loads(f.read_text())
    else:
        with gzip.open(path,"rt") as stream:
            for line in stream:
                yield json.loads(line)


def evaluate(data):
    expected=dict(observations());actual={};summary={}
    stamp={f:sha256((HERE/f).read_bytes()).hexdigest() for f in ("messen.py","PLAN.md")}
    for r in data:
        k=tuple(r[f] for f in ("seed","team","opponent","group"));id_=k[:3]
        if k not in expected or id_ in actual or r["steps"]!=303 or r["source"]!=stamp:
            raise ValueError("Bad run identity")
        if r["scores"]!={f:int(expected[k][f]) for f in SCORES}:
            raise ValueError("Score differs from archive")
        v=r["first"]
        if v:
            if not 1<=v["step"]<=40 or v["unseen_difference"]!=v["geometric_frontier_r3"]-v["geometric_frontier_v16"]:
                raise ValueError("Bad first divergence")
            condition=v["unseen_difference"]>0 and not (v["enemies_visible"] or v["known_relics"] or v["known_points"] or v["changed_sap"])
            if condition!=v["trigger"]:raise ValueError("Inconsistent trigger")
        actual[id_]=r
    if len(actual)!=len(expected) or len(expected)!=42:
        raise ValueError("Incomplete diagnostic panel")
    for group in ("solution_gerettet","kaggle_verloren","kaggle_gerettet","kontrolle"):
        rows=[r for r in actual.values() if r["group"]==group]
        positive=[r for r in rows if r["first"] and r["first"]["trigger"]]
        summary[group]=dict(games=len(rows),maps=len({r["seed"] for r in rows}),triggered=len(positive),
                positive_maps=len({r["seed"] for r in positive}),active_opponents=sorted({r["opponent"] for r in positive}),
                active_sides=sorted({r["team"] for r in positive}),steps=dict(Counter(r["first"]["step"] for r in rows if r["first"])),
                positive_by_sensor=dict(Counter(r["sensor"] for r in positive)))
    control=summary["kontrolle"]
    gates={"both_saved_solution":summary["solution_gerettet"]["triggered"]==2,
           "none_of_six_kaggle_losses":summary["kaggle_verloren"]["triggered"]==0,
           "control_frequency":4<=control["triggered"]<=24,
           "control_both_seats":len(control["active_sides"])==2,
           "control_both_opponents":len(control["active_opponents"])==2}
    return dict(groups=summary,gates=gates,passed=all(gates.values()))


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("data",type=Path);ap.add_argument("--archive",type=Path)
    args=ap.parse_args()
    rows=list(read(args.data));report=evaluate(rows)
    if args.archive:
        payload="".join(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n" for r in rows).encode()
        zipdata=gzip.compress(payload,mtime=0)
        if args.archive.exists() and args.archive.read_bytes()!=zipdata:
            raise ValueError("Another diagnostic archive exists")
        args.archive.write_bytes(zipdata)
        if evaluate(read(args.archive))!=report:raise ValueError("Archive readback differs")
    print(json.dumps(report,indent=2))
