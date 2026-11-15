"""Measure movement advice on the validation archives recorded in its training checkpoint."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from scripts.collect_combat_advice import filename, opponent_for
from scripts.experiment import limit_threads
from scripts.imitate import PLANE_SCALE, prepare_labels
from scripts.selective_advice_agent import load_heads


def measure(members, archive):
    with np.load(archive, allow_pickle=False) as data:
        planes = torch.from_numpy(data["planes"])
        keys = ("step", "pos", "feats", "mask", "act", "sdx", "sdy", "base_act")
        rows = {key: torch.from_numpy(data[key]) for key in keys}
    prepare_labels(rows, *planes.shape[-2:])
    count = Counter()
    steps = rows["step"].numpy()
    for first in range(0, len(planes), 24):
        end = min(first + 24, len(planes))
        batch = slice(*np.searchsorted(steps, [first, end]))
        step = rows["step"][batch].long() - first
        maps = planes[first:end].float() / PLANE_SCALE
        args = (maps, step, rows["pos"][batch], rows["feats"][batch].float())
        logits = torch.stack([net.forward_all(*args)[0] for net in members]).mean(0)
        score, action = logits.masked_fill(~rows["mask"][batch], -torch.inf).softmax(1).max(1)
        base = rows["base_act"][batch]
        teacher = rows["act"][batch]
        override = (base != 5) & (action != 5) & (base != action) & (score >= 0.70)
        before = base == teacher
        after = torch.where(override, action, base) == teacher
        masks = dict(rows=torch.ones_like(override), changed=override, base_matches=before,
                     advised_matches=after, helped=after & ~before, hurt=before & ~after,
                     changed_both_disagree=override & ~before & ~after)
        count.update({name: int(bits.sum()) for name, bits in masks.items()})
    if (count["advised_matches"] - count["base_matches"] != count["helped"] - count["hurt"]
            or count["changed"] != count["helped"] + count["hurt"] + count["changed_both_disagree"]):
        raise AssertionError("Inconsistent movement agreement counts")
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, nargs="+", required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    limit_threads()
    checkpoint = torch.load(args.model, map_location="cpu", weights_only=True)
    identities = checkpoint["selective_training"]["inputs"]
    cohorts = {"original": identities} if "train" in identities else identities
    training = {r["seed"] for cohort in cohorts.values() for r in cohort["train"]}
    validation = [(group, r) for group, cohort in cohorts.items() for r in cohort["val"]]
    if training & {r["seed"] for _, r in validation}:
        raise ValueError("Training and evaluation share a map")
    members, _ = load_heads(args.model)
    games = []
    with torch.inference_mode():
        for group, row in validation:
            seed, side = row["seed"], row["side"]
            paths = [directory / filename(seed, side) for directory in args.data]
            found = [path for path in paths if path.exists()]
            if len(found) != 1 or hashlib.sha256(found[0].read_bytes()).hexdigest() != row["sha256"]:
                raise ValueError(f"Missing, duplicate or changed validation archive {seed}/{side}")
            games.append(dict(cohort=group, seed=seed, side=side, opponent=opponent_for(seed),
                              counts=dict(measure(members, found[0]))))
    totals = dict(sum((Counter(g["counts"]) for g in games), Counter()))
    result = dict(model_sha256=hashlib.sha256(args.model.read_bytes()).hexdigest(), totals=totals, games=games,
                  interpretation="Preserved observations, quantized inputs; movement advice before final engine legality check.")
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(totals))


if __name__ == "__main__":
    main()
