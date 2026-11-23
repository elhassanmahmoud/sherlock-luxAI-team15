"""Fit on complete paired continuations and evaluate the sealed rule on other maps."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from gruppen import HERE, path, schedule
from politik import BUDGETS, NAMES, choose, utility


def read_blocks(folder, stage):
    by_map = {}
    ident = json.loads((folder / f"{stage}-sources.json").read_text())["source"]
    for key in schedule(stage):
        row = json.loads(path(folder, stage, key).read_text())
        seed, team, opp, arm = key
        assert (row["seed"], row["team"], row["opponent"], row["id"]) == key
        assert row["source"] == ident and row["actions_checked"] == [303, 303] and row["caught_errors"] == [0, 0]
        assert row["win"] == int(sum(m["win"] for m in row["matches"]) >= 2) and row["sensor"] == 1
        assert len({e[1] for e in row["events"]}) <= 1 and len(row["events"]) <= int(arm[1])
        by_map.setdefault((seed, team, opp), {})[int(arm[1])] = row
    for arms in by_map.values():
        assert set(arms) == set(BUDGETS)
        ref = arms[0]
        assert all(r["features"] == ref["features"] for r in arms.values())
        assert all(r["events"] or r["action_hash"] == ref["action_hash"] for r in arms.values())
        # Budget three agrees with the first diversion allowed under budget one.
        assert arms[1]["events"] == arms[3]["events"][:1]
    assert len(by_map) == {"train": 384, "pilot": 96}[stage]
    return by_map, ident


def fit(blocks):
    active = [arms for arms in blocks.values() if arms[0]["features"] is not None]
    x = np.array([arms[0]["features"] for arms in active])
    y = np.array([[utility(arms[b], arms[0]) for b in (1, 3)] for arms in active])
    center = x.mean(axis=0)
    scale = np.maximum(.001, x.std(axis=0))
    design = (x-center)/scale
    bias = y.mean(axis=0)
    coef = np.linalg.solve(design.T @ design + 48*np.eye(x.shape[1]), design.T @ (y-bias))
    return dict(features=list(NAMES), center=center.tolist(), scale=scale.tolist(), bias=bias.tolist(),
                weights=coef.T.tolist(), active=len(active), training_maps=len(blocks))


def measure(blocks, model):
    all_rows = []
    for (seed, seat, opp), arms in blocks.items():
        ref = arms[0]
        budget = 0 if ref["features"] is None else choose(ref["features"], model)
        row = arms[budget]
        values = {str(b): utility(arms[b], ref) for b in BUDGETS}
        oracle = max(BUDGETS, key=lambda b: values[str(b)])
        all_rows.append(dict(seed=seed, team=seat, opponent=opp, budget=budget, changed=bool(row["events"]),
            commands=len(row["events"]), utility=values[str(budget)], sight=ref["sight"]-row["sight"],
            credit=ref["credit"]-row["credit"], base_win=ref["win"], win=row["win"], base_wins=ref["wins"],
            wins=row["wins"], match_changes=[m["win"]-n["win"] for m,n in zip(row["matches"], ref["matches"],strict=True)],
            oracle_budget=oracle, oracle_value=values[str(oracle)], oracle_win=arms[oracle]["win"],
            chosen_hash=row["action_hash"], all_values=values))
    def summarize(rows):
        n=len(rows)
        out=dict(cards=n, changed=sum(r["changed"] for r in rows), wins=sum(r["win"] for r in rows),
            base_wins=sum(r["base_win"] for r in rows), rescues=sum(r["win"]>r["base_win"] for r in rows),
            losses=sum(r["win"]<r["base_win"] for r in rows), oracle_wins=sum(r["oracle_win"] for r in rows),
            actions=sum(r["commands"] for r in rows), changes_by_match=np.sum([r["match_changes"] for r in rows],axis=0).tolist(),
            choices={str(b):sum(r["budget"]==b for r in rows) for b in BUDGETS})
        sample = np.random.default_rng(231123).integers(0, n, size=(20000, n))
        for name in ("utility","sight","credit","oracle_value"):
            values=np.array([r[name] for r in rows])
            out[name]=dict(mean=float(values.mean()), ci95=np.percentile(values[sample].mean(axis=1),[2.5,97.5]).tolist())
        return out
    groups={opp:summarize([r for r in all_rows if r["opponent"]==opp]) for opp in ("solution92","v16")}
    overall=summarize(all_rows)
    gates=dict(actions=overall["changed"]>=12, earlier=overall["sight"]["mean"]>0, positive=overall["utility"]["mean"]>0,
               wins=all(g["wins"]>=g["base_wins"] for g in groups.values()))
    return dict(groups=groups, overall=overall, gates=gates, passed=all(gates.values())), all_rows


def immutable(path, raw):
    if path.exists():
        assert path.read_bytes()==raw, f"Existing artifact differs: {path}"
    else:
        path.write_bytes(raw)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    p.add_argument("stage",choices=("train","pilot"))
    args=p.parse_args()
    if args.stage=="pilot" and not (HERE/"modell.json").exists():
        raise ValueError("Pilot scoring requires the frozen model")
    blocks,ident=read_blocks(args.folder,args.stage)
    if args.stage=="train":
        model=fit(blocks)
        model["source"]=ident
        immutable(HERE/"modell.json",(json.dumps(model,indent=2,allow_nan=False)+"\n").encode())
    model=json.loads((HERE/"modell.json").read_text())
    stats,rows=measure(blocks, model)
    stats["source"]=ident
    stats["model_hash"]=hashlib.sha256((HERE/"modell.json").read_bytes()).hexdigest()
    # The training summary describes calibration on the fit sample. Only the pilot opens the next stage.
    if args.stage=="train":
        stats.pop("passed")
        stats.pop("gates")
    immutable(HERE/f"{args.stage}.json",(json.dumps(stats,indent=2,allow_nan=False)+"\n").encode())
    immutable(HERE/f"{args.stage}_auswahl.jsonl.gz",gzip.compress(("\n".join(json.dumps(r,separators=(",",":")) for r in rows)+"\n").encode(),mtime=0))
    ordered = [r for branches in blocks.values() for r in branches.values()]
    immutable(HERE/f"{args.stage}_partien.jsonl.gz",gzip.compress(("\n".join(json.dumps(r,separators=(",",":")) for r in ordered)+"\n").encode(),mtime=0))
    print(json.dumps(stats,indent=2))


if __name__=="__main__":
    main()
