"""Fit the fixed public R3/V14 lookup table, then evaluate it once on separate teacher-labelled maps."""
import argparse
import json
from pathlib import Path

import numpy as np

from scripts.collect_combat_advice import file_sha, filename, opponent_for
from scripts.r3_context_table import CELLS, HARD_ONLY_PROTOCOL_SHA, PROTOCOL_SHA, R3_SHA, cell_indices, learn_cells
from scripts.residual_ensemble_compare import interval
from scripts.train_combat_advice import input_index, publish_json

TRAIN = range(7287000,7287048)
VALID = range(7287100,7287124)


def counters(directory, seeds):
    binding = file_sha(directory / "protocol.json")
    if binding == HARD_ONLY_PROTOCOL_SHA:
        raise ValueError("This collection omitted the registered teacher-score recording")
    if binding != PROTOCOL_SHA:
        raise ValueError("Unexpected collector source, V14, teacher or R3")
    keys = [(s, side) for s in seeds for side in ("player_0","player_1")]
    records = input_index([directory], {"train":keys,"val":[]},student_sha=R3_SHA)["train"]
    totals = np.zeros((len(seeds),CELLS,3), dtype=np.int64)
    inventory = {}
    for item in records:
        seed, side = item["seed"], item["side"]
        p = Path(item["path"])
        with np.load(p,allow_pickle=False) as z:
            # input_index/check_archive has already checked these three arrays against the
            # row roster, 303 frame statuses, dtypes, finite/NaN conventions and content hash.
            if json.loads(z["meta"].item()).get("raw_teacher_policy") != "pre_fallback_scores_v1":
                raise ValueError(f"Missing teacher-score trace despite the registered recording protocol: {p}")
            base, r3, teacher = z["base_act"], z["played_act"], z["act"]
            movement_difference = (base != r3) & (base < 5) & (r3 < 5)
            mask = z["mask"]
            idx = np.arange(len(base))
            moving = movement_difference & mask[idx,base] & mask[idx,r3]
            for command, prefix in ((base,"base_"),(r3,"played_")):
                for axis in ("sdx","sdy"):
                    if np.any(z[prefix+axis][command<5] != 0):
                        raise ValueError(f"Movement includes an offset in {p}")
            if np.any((base != r3) & ~movement_difference):
                raise ValueError(f"Selective R3 modified a SAP order in {p}")
            cells = cell_indices(z["feats"][moving], base[moving], r3[moving])
            dst = totals[seed - seeds.start]
            for i, keep in enumerate((np.ones(len(cells),bool), (base==teacher)[moving], (r3==teacher)[moving])):
                dst[:,i] += np.bincount(cells[keep],minlength=CELLS)
        inventory[filename(seed,side)] = item["sha256"]
    return totals, inventory


def fit(directory):
    counts, sources = counters(directory,TRAIN)
    gains = counts[:,:,1]-counts[:,:,2]
    return dict(kind="r3_public_context_v1",r3_sha256=R3_SHA,protocol_sha256=PROTOCOL_SHA,
                sources=sources,training_seeds=[TRAIN.start, TRAIN.stop-1], source_sha256=source_hashes(),
                use_v14=learn_cells(gains).tolist(), rows_per_cell=counts[:,:,0].sum(0).tolist(),
                training_v14_only_minus_r3_only=gains.sum(0).tolist(),
                strongest_positive_map=np.maximum(0,gains.max(axis=0)).tolist())


def source_hashes():
    return {name:file_sha(Path(__file__).with_name(name))
            for name in ("r3_context_table.py","r3_context_study.py")}


def assess(directory, trained, table_hash):
    if trained != fit(directory):
        raise ValueError("Saved table differs from deterministic training-only reproduction")
    counts, sources = counters(directory,VALID)
    result = validation_counts(counts, np.asarray(trained["use_v14"], dtype=bool))
    return dict(table_sha256=table_hash, source_sha256=source_hashes(), valid_sources=sources, **result)


def validation_counts(counts, use_v14):
    if counts.shape != (len(VALID), CELLS, 3) or use_v14.shape != (CELLS,):
        raise ValueError("Unexpected map and context dimensions")
    total = counts.sum(axis=1)
    chosen = np.where(use_v14[None,:], counts[:,:,1],counts[:,:,2]).sum(axis=1)
    switched = counts[:,use_v14,:].sum(axis=1)
    by_map = [dict(seed=s,opponent=opponent_for(s),disagreements=int(n),v14=int(a),r3=int(b),
                   selected=int(p),retained_v14=int(v),gained=int(g),lost=int(l),net=int(p-b))
              for s,(n,a,b),p,(v,g,l) in zip(VALID,total,chosen,switched)]
    summaries = {}
    for name in ("all","solution92","kaggle3","v14"):
        rows = [r for r in by_map if name=="all" or r["opponent"]==name]
        summary = {k:sum(r[k] for r in rows) for k in ("disagreements","v14","r3","selected","retained_v14","gained","lost","net")}
        summary["maps"] = len(rows)
        summary["mean_net_per_map_ci95"] = interval([r["net"] for r in rows],seed=2711,draws=10000)
        summaries[name]=summary
    checks = dict(whole_map_lower_positive=summaries["all"]["mean_net_per_map_ci95"][0]>0,
                  solution_nonnegative=summaries["solution92"]["net"]>=0)
    return dict(counts=summaries, by_map=by_map,
                map_cell_axes=["validation seed in ascending order","public cell 0..35",
                               ["disagreements","teacher picks V14","teacher picks R3"]],
                map_cell_counts=counts.tolist(), checks=checks,passes=all(checks.values()))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage",choices=("fit","assess"))
    p.add_argument("--data",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    table=a.out/"table.json"
    if a.stage=="fit":
        result=fit(a.data)
        dest=table
    else:
        result=assess(a.data,json.loads(table.read_bytes()),file_sha(table))
        dest=a.out/"validation.json"
    if dest.exists():
        raise FileExistsError(dest)
    publish_json(dest,result)
    print(json.dumps(result["counts"] if a.stage=="assess" else {"cells_using_v14":sum(result["use_v14"])},
                     indent=2))


if __name__=="__main__":
    main()
