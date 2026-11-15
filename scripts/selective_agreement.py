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


def read_rows(data, planes):
    keys = ("step", "pos", "feats", "mask", "act", "sdx", "sdy", "base_act")
    rows = {key: torch.from_numpy(data[key]) for key in keys}
    played = torch.from_numpy(data["played_act"]) if "played_act" in data.files else None
    # prepare_labels reconstructs the SAP mask solely from public energy and SAP cost.
    # The teacher action and offsets are scoring labels and never fed to forward_all.
    prepare_labels(rows, *planes.shape[-2:])
    return rows, played


def measure(members, archive, *, with_history_scope=False):
    with np.load(archive, allow_pickle=False) as data:
        planes = torch.from_numpy(data["planes"])
        rows, played = read_rows(data, planes)
        own_input = getattr(members[0], "arch", {}).get("feat_dim") == 85
        known = None
        if own_input or with_history_scope:
            from agents.sherlock.own_command import archive_features
            bit = torch.from_numpy(archive_features(data))
            known = bit.any(1).bool()
            if own_input:
                rows["feats"] = torch.cat((rows["feats"], bit.to(rows["feats"].dtype)),1)
    counts = count_agreement(members, planes, rows, played, near=known if with_history_scope else None)
    if with_history_scope:
        counts["all"].update({"history_" + k:v for k,v in counts["near"].items()})
    return counts["all"]


def count_agreement(members, planes, rows, played=None, near=None):
    counts = {"all": Counter()}
    if near is not None:
        counts["near"] = Counter()
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
        if played is not None:
            parent_match = played[batch] == teacher
            masks.update(parent_played_matches=parent_match,
                         parent_changed=played[batch] != base,
                         model_recovers_over_parent=~parent_match & after,
                         parent_matches_lost_by_model=parent_match & ~after)
        counts["all"].update({name: int(bits.sum()) for name,bits in masks.items()})
        if near is not None:
            counts["near"].update({name: int((bits & near[batch]).sum()) for name,bits in masks.items()})
    for count in counts.values():
        if (count["advised_matches"] - count["base_matches"] != count["helped"] - count["hurt"]
                or count["changed"] != count["helped"] + count["hurt"] + count["changed_both_disagree"]):
            raise AssertionError("Inconsistent movement agreement counts")
    return counts


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
    by_cohort = {group: dict(sum((Counter(g["counts"]) for g in games if g["cohort"] == group), Counter()))
                 for group in cohorts}
    result = dict(by_cohort=by_cohort, model_sha256=hashlib.sha256(args.model.read_bytes()).hexdigest(), totals=totals, games=games,
                  interpretation="Preserved observations, quantized inputs; movement advice before final engine legality check.")
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(totals))


if __name__ == "__main__":
    main()
