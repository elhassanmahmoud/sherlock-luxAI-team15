"""Count attainable wins and tradeoffs among all real continuations without using selection utility."""
import gzip
import json
from pathlib import Path
from experiments.analysis.relictsuche_20261123.vergleich.spielen import sha,write_once

HERE=Path(__file__).resolve().parent


def main():
    output={}
    for period in ("train","pilot"):
        file=HERE/f"{period}_partien.jsonl.gz"
        selected=HERE/f"{period}_auswahl.jsonl.gz"
        with gzip.open(file,"rt") as f:all_rows=[json.loads(x) for x in f]
        with gzip.open(selected,"rt") as f:decisions={r["seed"]:r for r in map(json.loads,f)}
        groups={}
        for row in all_rows:
            group=groups.setdefault(row["seed"],{})
            assert row["id"] not in group
            group[row["id"]]=row
        stats={}
        for side in ("solution92","v16"):
            matches=[a for a in groups.values() if a["b0"]["opponent"]==side]
            records=[]
            for rows in matches:
                base=rows["b0"]
                assert set(rows)=={"b0","b1","b3"}
                dec=decisions[base["seed"]]
                chosen=rows[f'b{dec["budget"]}']
                assert dec["win"]==chosen["win"] and dec["base_win"]==base["win"]
                wins=[k for k,r in rows.items() if r["win"]]
                faster=[k for k,r in rows.items() if r["sight"]<base["sight"]]
                records.append(dict(seed=base["seed"],team=base["team"],base=base["win"],chosen=chosen["win"],
                                    winner=bool(wins),quicker=bool(faster),faster_win=bool(set(wins)&set(faster)),
                                    discriminates=len(wins) in (1,2)))
            s={k:sum(r[k] for r in records) for k in ("base","chosen","winner","quicker","faster_win","discriminates")}
            s["cards"]=len(records)
            s["recoverable_original_losses"]=[dict(seed=r["seed"],team=r["team"]) for r in records if not r["base"] and r["winner"]]
            s["invariant_original_losses"]=[dict(seed=r["seed"],team=r["team"]) for r in records if not r["winner"]]
            stats[side]=s
        output[period]=dict(comparisons=stats,continuations=sha(file),selection=sha(selected))
    write_once(HERE/"obergrenze.json",output)


if __name__=="__main__":main()
