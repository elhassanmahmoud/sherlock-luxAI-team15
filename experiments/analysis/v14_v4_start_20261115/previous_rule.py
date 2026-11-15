"""Reconstruct the previously selected SAP rule separately from the Dev-A nomination."""
import argparse
from pathlib import Path
from route import TABLES, dataset, routing, sampler, save, summarize

p=argparse.ArgumentParser(description=__doc__)
p.add_argument("root",type=Path)
p.add_argument("--out",required=True,type=Path)
a=p.parse_args()
draw,_,_=sampler()
rule={"field":"unit_sap_range","v14_when":"low","midpoint":5}
panels={}
for name in TABLES:
    data,seeds,_=dataset(a.root,name)
    panels[name]=summarize(data,routing(rule,draw(seeds)))
save(a.out/"earlier_sap.json",dict(previous_rule=rule,descriptive_only=panels))
