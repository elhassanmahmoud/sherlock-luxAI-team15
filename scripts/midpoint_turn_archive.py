"""Compare a fixed change to the movement adviser and its confidence window on the same archived states."""
import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np

from scripts.r3_turn_advice_audit import BLOCKS, OPPONENTS, digest, limit_threads, load_heads, score_case
from scripts.train_combat_advice import publish_json

ROOT = Path(__file__).resolve().parents[1]
STUDY = Path("experiments/analysis")
MODEL = Path("experiments/candidates/r8_warm_20261115/midpoint.pth")
MODEL_SHA = "51a52f0453d5ac8e9a4ea70b3792572356761054cb2890520005160f77097cf2"
TURN_AUDIT = "7067483ced3edd0d2b3beca65880f4bd87b518c919b309e2bc0c9dc58bf0628d"
MIDPOINT_AUDIT = "b80632ec1f7ad525bf8a469d38f38bbf8f4111acc0ed2a27455df9fe3837f1b9"
FOLDERS = {"old_validation": "final_20261115_movement_dagger", "new_validation": "final_20261115_r3_context"}


def checked_json(path, expected):
    if digest(path) != expected:
        raise ValueError(f"Changed reference: {path}")
    return json.loads(path.read_bytes())


def comparison(cases, left, right):
    maps = {}
    for case in cases:
        tally = maps.setdefault(case["seed"], Counter())
        tally.update(rows=case["rows"], difference=case[left]-case[right], seats=1)
    if not maps or any(t["seats"] != 2 or t["rows"] <= 0 for t in maps.values()):
        raise ValueError("Both seats required for every map")
    delta = np.array([v["difference"] for v in maps.values()])
    rows = np.array([v["rows"] for v in maps.values()])
    picks = np.random.default_rng(2711).integers(len(rows), size=(10000, len(rows)))
    samples = 100 * delta[picks].sum(axis=1) / rows[picks].sum(axis=1)
    return dict(net=int(delta.sum()), pp=100*float(delta.sum())/rows.sum(),
                ci95_pp=np.quantile(samples, [.025, .975]).tolist(), maps=len(maps))


def contrasts(cases):
    return {name:comparison(cases,left,right) for name,left,right in (
        ("combined_vs_original_turn","midpoint_turn","r3_turn"), ("combined_vs_midpoint","midpoint_turn","midpoint"),
        ("midpoint_vs_r3","midpoint","r3"), ("r3_turn_vs_r3","r3_turn","r3"))}


def run(project, out):
    if out.exists():
        raise FileExistsError(out)
    limit_threads()
    base = project/STUDY
    turn = checked_json(base/"r3_turn_advice_20261115/validation.json", TURN_AUDIT)
    midpoint = checked_json(base/"r8_midpoint_20261115/validation.json", MIDPOINT_AUDIT)
    if digest(project/MODEL) != MODEL_SHA or midpoint["model_sha256"] != MODEL_SHA:
        raise ValueError("Unexpected midpoint checkpoint")
    for name, sha in turn["source"].items():
        if digest(ROOT/name) != sha:
            raise ValueError(f"Different archived inference code: {name}")
    nets, own_tile = load_heads(project/MODEL)
    if len(nets) != 1 or not own_tile:
        raise ValueError("Expected one movement adviser")
    def key(case):
        return (case["cohort"], case["seed"], case["side"], case["opponent"])
    original = {key(r):r for r in turn["cases"]}
    cases = []
    for record in midpoint["archives"]:
        cohort, seed, side, foe = key(record)
        parent = original.pop(key(record))
        folder = project/"experiments/imitation"/FOLDERS[cohort]
        path = folder/f"g{seed}_{side}_{foe}.npz"
        if parent["sha256"] != record["sha256"] or digest(path) != record["sha256"] or digest(folder/"protocol.json") != record["protocol"]:
            raise ValueError(f"Archive differs: {path}")
        both, standard, _ = score_case(nets[0],path)
        known, old = record["counts"], parent["counts"]
        if ((both["rows"],both["r3_correct"],standard["base_matches"],standard["hurt"]) !=
                (known["rows"],known["midpoint_correct"],known["v14_correct"],known["midpoint_hurt_correct_v14"])
                or (old["r3_correct"],old["rows"]) != (known["r3_correct"],known["rows"])):
            raise ValueError(f"Prior measurements do not reproduce: {key(record)}")
        cases.append(dict(cohort=cohort,seed=seed,side=side,opponent=foe,sha256=record["sha256"],rows=known["rows"],
                          r3=old["r3_correct"],r3_turn=old["candidate_correct"],midpoint=known["midpoint_correct"],
                          midpoint_turn=both["candidate_correct"],window_gained=both["gained"],window_lost=both["lost"]))
    expected = {(cohort,n,s) for cohort,seeds in BLOCKS.items() for n in seeds for s in ("player_0","player_1")}
    if original or len(cases)!=len(expected) or {(r["cohort"],r["seed"],r["side"]) for r in cases}!=expected:
        raise ValueError("Incomplete paired cohorts")
    results = {}
    for cohort in BLOCKS:
        group = [r for r in cases if r["cohort"] == cohort]
        results[cohort] = dict(all=contrasts(group), by_opponent={
            foe:contrasts([r for r in group if r["opponent"]==foe]) for foe in OPPONENTS})
    checks = {f"{c}_{k}":results[c]["all"][k]["net"]>0 for c in BLOCKS
              for k in ("combined_vs_original_turn","combined_vs_midpoint")}
    checks["new_solution_nonnegative"] = results["new_validation"]["by_opponent"]["solution92"]["combined_vs_original_turn"]["net"]>=0
    publish_json(out,dict(model=MODEL_SHA,source=digest(Path(__file__)),original=TURN_AUDIT,midpoint=MIDPOINT_AUDIT,
                          cases=cases,results=results,checks=checks,qualified_archive=all(checks.values())))
    print(checks,flush=True)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    run(args.project.resolve(),args.out.resolve())
