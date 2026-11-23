"""Attribute discovery-panel changes to sight, scoring and match outcomes on identical seats."""
import argparse
import gzip
import json
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent


def key(row):
    return row["seed"],row["team"]


def diff(reference, candidate):
    old=reference["matches"][0]
    new=candidate["matches"][0]
    return dict(seed=reference["seed"],team=reference["team"],
                sight=reference["sight"]-candidate["sight"],credit=reference["credit"]-candidate["credit"],
                margin=(new["points"][0]-new["points"][1])-(old["points"][0]-old["points"][1]),
                match=new["win"]-old["win"],whole=candidate["win"]-reference["win"],
                changes=len(candidate["events"]))


def group(values):
    return dict(seats=len(values),cards=len({r["seed"] for r in values}),
                credit_earlier=sum(v["credit"]>0 for v in values),credit_later=sum(v["credit"]<0 for v in values),
                avg_m1_margin_delta=(float(np.mean([v["margin"] for v in values])) if values else None),
                match_rescued=sum(v["match"]>0 for v in values),match_lost=sum(v["match"]<0 for v in values),
                whole_rescued=sum(v["whole"]>0 for v in values),whole_lost=sum(v["whole"]<0 for v in values))


def calculate(archive):
    with gzip.open(archive,"rt") as src:
        rows=[json.loads(line) for line in src]
    records={key(r):r for r in rows if r["id"]=="reference" and r["opponent"]=="solution92"}
    if len(records)!=80 or len(rows)!=560:
        raise ValueError("Need the complete three-candidate discovery panel")
    out={}
    for name in ("route","wert","ziel"):
        current={key(r):r for r in rows if r["id"]==name and r["opponent"]=="solution92"}
        if records.keys()!=current.keys():
            raise ValueError("Missing matched seats")
        changes=[diff(records[k],current[k]) for k in sorted(records)]
        out[name]=dict(earlier=group([x for x in changes if x["sight"]>0]),
                       same=group([x for x in changes if x["sight"]==0]),
                       later=group([x for x in changes if x["sight"]<0]),
                       whole_swaps=[x for x in changes if x["whole"]],
                       most_advanced=max(changes,key=lambda q:q["sight"]),
                       most_delayed=min(changes,key=lambda q:q["sight"]))
    return out


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive",type=Path)
    args=p.parse_args()
    (HERE/"pfadwirkung.json").write_text(json.dumps(calculate(args.archive),indent=2,allow_nan=False)+"\n")
