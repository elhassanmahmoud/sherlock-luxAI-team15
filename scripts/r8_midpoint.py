"""Evaluate one single-network average of two R3 warm starts on identical stored decisions."""
import argparse
from collections import Counter
import json
from pathlib import Path

import torch

from scripts.collect_combat_advice import file_sha
from scripts.experiment import limit_threads
from scripts.r8_warm import BLOCKS, R3, identities, index
from scripts.r8_warm_assess import measure
from scripts.selective_advice_agent import load_heads
from scripts.train_combat_advice import publish, publish_json

AUDIT_SHA = "3f05bde9320d9c718e404d2280590f76ab5de823c9fdea594f564433bbcc54de"
WEIGHTS = {
    "r3": R3,
    "control": "a5755fb1d4a006a95769cb7f19bd38401ffcb42d0058b5cb4f88a9fc7ef5ea32",
    "r8": "93046242f41e16a5e355bc75836b1630816d174890abb804b49969b49893c532",
}


def midpoint(left, right):
    if left.keys() != right.keys():
        raise ValueError("Warm starts have different parameters")
    state = {}
    for name, first in left.items():
        second = right[name]
        if first.dtype != second.dtype or first.shape != second.shape:
            raise ValueError(f"Different parameter type or shape: {name}")
        if first.is_floating_point():
            value = ((first.double() + second.double()) * 0.5).to(first.dtype)
            if not torch.isfinite(value).all():
                raise ValueError(f"Non-finite weight: {name}")
        elif torch.equal(first, second):
            value = first.clone()
        else:
            raise ValueError(f"Different non-floating state: {name}")
        state[name] = value
    return state


def run(args):
    limit_threads()
    files = {"r3": args.r3, **{k: args.warm / (k + ".pth") for k in ("control", "r8")}}
    audit_path = args.warm / "validation.json"
    if {k: file_sha(p) for k, p in files.items()} != WEIGHTS or file_sha(audit_path) != AUDIT_SHA:
        raise ValueError("The two fits or their paired source evaluation changed")
    audit = json.loads(audit_path.read_bytes())
    if audit["models"] != WEIGHTS:
        raise ValueError("Archived counts refer to a different model")
    args.out.mkdir(parents=True, exist_ok=True)
    destination = args.out / "midpoint.pth"
    left, right = [torch.load(files[k], map_location="cpu", weights_only=True) for k in ("control", "r8")]
    fields = ("kind", "cfg", "arch", "feature_dim", "sap_own_tile")
    config = {k: left[k] for k in fields}
    if config != {k: right[k] for k in fields}:
        raise ValueError("Different inference configurations")
    model = dict(config, policy=midpoint(left["policy"], right["policy"]), midpoint_parents=WEIGHTS)
    def save(path):
        with path.open("wb") as stream:
            torch.save(model, stream)
    publish(destination, save)
    # measure() treats the model named 'r8' as the proposed policy when counting gains and losses.
    networks = {}
    for name, path in (("r3", files["r3"]), ("control", files["control"]),
                       ("specialist", files["r8"]), ("r8", destination)):
        heads, own_tile = load_heads(path)
        if len(heads) != 1 or not own_tile:
            raise ValueError(f"Unexpected network in {path}")
        networks[name] = heads[0]
    rows, totals = [], {}
    archived = {(r["cohort"], r["seed"], r["side"]): r for r in audit["archives"]}
    for cohort, directory in (("old_validation", args.old), ("new_validation", args.new)):
        sums = Counter()
        for rec in index(directory, cohort):
            ref = archived[cohort, rec["seed"], rec["side"]]
            actual, _ = measure(networks, Path(rec["path"]), cohort)
            for now, previous in (("rows", "rows"), ("r3_correct", "r3_correct"), ("v14_correct", "v14_correct"),
                                  ("control_correct", "control_correct"), ("specialist_correct", "r8_correct")):
                if actual[now] != ref["counts"][previous] or rec["sha256"] != ref["sha256"]:
                    raise ValueError(f"Cannot reproduce the source counts for {rec['path']}")
            counts = {}
            for key, value in actual.items():
                if key.startswith("r8_"):
                    key = "midpoint_" + key[3:]
                elif key.startswith("specialist_"):
                    key = "r8_" + key[11:]
                counts[key] = value
            rows.append(dict(cohort=cohort, **identities([rec])[0], counts=counts))
            sums.update(counts)
        totals[cohort] = dict(sums)
    gate = {k: row["midpoint_correct"] > row["r3_correct"] for k, row in totals.items()}
    result = dict(parents=WEIGHTS, parent_audit=AUDIT_SHA, model_sha256=file_sha(destination),
                  cohort_map_ranges={k: [BLOCKS[k].start, BLOCKS[k].stop - 1] for k in totals},
                  totals=totals, archives=rows, checks=gate, passes=all(gate.values()),
                  averaging="equal mean using float64, cast back to original dtype", source_sha256=file_sha(Path(__file__)))
    publish_json(args.out / "validation.json", result)
    print(json.dumps({"totals": totals, "checks": gate}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("r3", "warm", "old", "new", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    run(parser.parse_args())
