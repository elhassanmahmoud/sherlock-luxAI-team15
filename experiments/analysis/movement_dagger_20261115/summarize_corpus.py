"""Summarize the fixed collection of on-policy teacher labels. Reads completed NPZ archives only."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np


def soft_targets(archive):
    """Reconstruct the exact training mask and count informative second choices at T=2."""
    raw = archive["teacher_action_scores"].astype(np.float64)
    legal = archive["mask"][:, :5]
    teacher = archive["act"]
    scores = np.where(legal, raw[:, :5], -np.inf)
    valid_frame = archive["teacher_frame_status"][archive["global_step"][archive["step"]]] == 1
    use = valid_frame & (archive["teacher_selected"] == 1) & np.isfinite(raw).all(axis=1)
    use &= (archive["base_act"] != 5) & (teacher >= 0) & (teacher < 5) & legal.any(axis=1)
    use &= scores.argmax(axis=1) == teacher
    multiple = use & (legal.sum(axis=1) >= 2)
    scores = scores[multiple] / 2
    if len(scores):
        weights = np.exp(scores - scores.max(axis=1, keepdims=True))
        probabilities = weights / weights.sum(axis=1, keepdims=True)
        runner_up = np.partition(probabilities, -2, axis=1)[:, -2]
    else:
        runner_up = np.empty(0)
    return dict(eligible_soft_rows=int(use.sum()), multiple_legal_soft_rows=int(multiple.sum()),
                second_choice_at_least_ten_percent=int((runner_up >= 0.10).sum()))


def summarize(directory):
    protocol = hashlib.sha256((directory / "protocol.json").read_bytes()).hexdigest()
    splits = {"train": range(7272000, 7272120), "validation": range(7272200, 7272224)}
    totals, games = {}, []
    for split, seeds in splits.items():
        counts = Counter()
        opponents = Counter()
        for seed in seeds:
            for seat in (0, 1):
                paths = list(directory.glob(f"g{seed}_player_{seat}_*.npz"))
                if len(paths) != 1:
                    raise ValueError(f"Expected one archive for {seed} / {seat}")
                path = paths[0]
                with np.load(path, allow_pickle=False) as z:
                    meta = json.loads(z["meta"].item())
                    if (meta["seed"], meta["side"], meta["protocol_sha256"]) != (seed, f"player_{seat}", protocol):
                        raise ValueError(f"Archive identity differs in {path}")
                    base, actual, teacher = z["base_act"], z["played_act"], z["act"]
                    changed = base != actual
                    if np.any(changed & ((base == 5) | (actual == 5))):
                        raise ValueError("Movement-only policy changed a shot")
                    for axis in ("sdx", "sdy"):
                        if np.any(z["played_" + axis][base == 5] != z["base_" + axis][base == 5]):
                            raise ValueError("Movement-only policy retargeted a shot")
                    valid = np.isfinite(z["teacher_action_scores"]).all(1)
                    selected = z["teacher_selected"]
                    row = dict(rows=len(base), changes=int(changed.sum()),
                               corrected=int(np.sum(changed & (actual == teacher))),
                               lost_agreement=int(np.sum(changed & (base == teacher))),
                               raw_score_rows=int(valid.sum()), selected_rows=int(np.sum(valid & (selected == 1))),
                               held_rows=int(np.sum(valid & (selected == 0))),
                               held_teacher_moves=int(np.sum(valid & (selected == 0) & (teacher != 0))),
                               **soft_targets(z))
                    if row["selected_rows"] + row["held_rows"] != row["raw_score_rows"]:
                        raise ValueError("Invalid teacher selection labels")
                    counts.update(row)
                    opponents[meta["opponent"]] += 1
                    games.append(dict(seed=seed, side=meta["side"], split=split, opponent=meta["opponent"],
                                      game_won=int(meta["our_wins"] > meta["opp_wins"]), **row,
                                      sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        if len(opponents) != 3 or len(set(opponents.values())) != 1:
            raise ValueError("Unbalanced map allocation")
        totals[split] = dict(**counts, games_by_opponent=dict(opponents))
    return dict(protocol_sha256=protocol, totals=totals, games=games)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = summarize(args.directory)
    with args.out.open("x") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    print(json.dumps(report["totals"]))
