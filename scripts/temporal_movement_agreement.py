"""Paired, frozen R2/R4 movement-advice audit on eight original and 24 mixed validation maps."""
import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np
import torch
from torch.nn.functional import max_pool2d

from agents.sherlock.geometry import DIR_DX, DIR_DY
from scripts import collect_combat_advice as collect
from scripts.experiment import limit_threads
from scripts.imitate import PLANE_SCALE
from scripts.selective_advice_agent import HISTORY_KIND, live_history_board, load_heads
from scripts.selective_agreement import count_agreement, read_rows
from scripts.selective_dagger import fill_previous_enemy, require_r2_inputs
from scripts.train_combat_advice import make_plan


def paired_inputs(r2_path, r4_path):
    checkpoint = torch.load(r4_path, map_location="cpu", weights_only=True, mmap=True)
    if checkpoint.get("kind") != HISTORY_KIND or checkpoint["arch"]["in_ch"] != 17:
        raise ValueError("Expected a movement checkpoint with the previous observed enemy channel")
    metadata = dict(checkpoint["selective_training"])
    recorded = metadata.pop("previous_enemy_r2_sha256")
    parity = metadata.pop("initial_parity")
    if recorded != require_r2_inputs(r2_path,metadata):
        raise ValueError("R4 was trained against another R2 checkpoint")
    ref = torch.load(r2_path, map_location="cpu", weights_only=True, mmap=True)
    if (checkpoint["arch"] != {**ref["arch"], "in_ch":17} or checkpoint.get("epochs") != 5
            or checkpoint.get("sap_own_tile") is not True or bool(checkpoint.get("imitation_ensemble"))
            or parity.get("device") != "cpu" or parity.get("rtol") != 1e-5 or parity.get("atol") != 1e-6
            or len(parity.get("max_abs_by_head", [])) != 3 or not np.isfinite(parity["max_abs_by_head"]).all()):
        raise ValueError("Invalid R4 architecture or missing pre-training parity check")
    inputs = metadata["inputs"]
    plans = dict(original=make_plan(7271000,32,7271032,8), mixed=make_plan(7272000,120,7272200,24))
    if set(inputs) != set(plans):
        raise ValueError("Unexpected cohorts")
    for group, plan in plans.items():
        for split, keys in plan.items():
            if [(r["seed"],r["side"]) for r in inputs[group][split]] != keys:
                raise ValueError(f"Wrong or duplicate {group}/{split} maps/seats")
    return inputs, metadata["parent_sha256"], parity


def near_rows(boards, rows):
    # 1 visible opponent = round(.25*127) = 32. Two or more must not qualify.
    occupied = (boards[:,0] > 0) & (boards[:,10] == 32) & (boards[:,16] > 0)
    nearby = max_pool2d(occupied[:,None].float(), 7, stride=1, padding=3)[:,0].bool()
    pos = rows["pos"].long()
    return nearby[rows["step"].long(), pos[:,0], pos[:,1]]


def archived_boards(data):
    raw, frames = data["planes"], data["global_step"]
    boards = np.empty((len(frames),17,24,24), np.int8)
    boards[:,:16] = raw
    fill_previous_enemy(boards, frames)
    # Recover the exact public, quarter-count live values of channel 10 before the
    # online rounding. Replay in real step order, explicitly clearing unsaved turns.
    prior = None
    lookup = dict(zip(frames, range(len(frames))))
    for step in range(collect.STEPS):
        if step not in lookup:
            prior = None
            continue
        i = lookup[step]
        current = raw[i].astype(np.float32) / PLANE_SCALE
        current[10] = np.rint(4*current[10])/4
        if not np.array_equal(np.rint(current[10]*PLANE_SCALE), raw[i,10]):
            raise ValueError("Invalid public occupancy code")
        online, prior = live_history_board(current,step,step%101,prior)
        if not np.array_equal(online[16],boards[i,16].astype(np.float32)/PLANE_SCALE):
            raise ValueError(f"Stored and online previous occupancy differ at step {step}")
    return torch.from_numpy(boards)


def check_native_move_masks(boards, rows):
    # Each stored, mask-accepted MOVE must be affordable, in bounds and on a
    # non-asteroid according to V14. This is at least as strict as native_order.
    pos, steps = rows["pos"].long(), rows["step"].long()
    for a in range(1,5):
        x, y = pos[:,0] + int(DIR_DX[a]), pos[:,1] + int(DIR_DY[a])
        valid = (x >= 0) & (x < 24) & (y >= 0) & (y < 24) & (rows["feats"][:,3] == 0)
        valid &= boards[steps,5,x.clamp(0,23),y.clamp(0,23)] == 0
        if (rows["mask"][:,a] & ~valid).any():
            raise ValueError("Stored movement mask cannot certify native move legality")


def combine(games):
    groups = {}
    for model in ("r2","r4"):
        groups[model] = {}
        for scope in ("all","near"):
            count = Counter()
            for game in games:
                count.update(game[model][scope])
            count["net"] = count["helped"] - count["hurt"]
            groups[model][scope] = dict(count)
    return groups


def selection_gate(mixed):
    a, b = mixed["r2"], mixed["r4"]
    checks = dict(near_net_increases=b["near"]["net"] > a["near"]["net"],
                  overall_net_holds=b["all"]["net"] >= a["all"]["net"],
                  hurt_within_ten_percent=10*b["all"]["hurt"] <= 11*a["all"]["hurt"])
    return dict(criteria=checks, pass_offline=all(checks.values()))


def compare(r2, r4, directories):
    hashes = [collect.file_sha(p) for p in (r2,r4)]
    inputs, parent, parity = paired_inputs(r2,r4)
    models = {"r2":load_heads(r2)[0], "r4":load_heads(r4)[0]}
    games = []
    with torch.inference_mode():
        for group, splits in inputs.items():
            for record in splits["val"]:
                seed, side = record["seed"], record["side"]
                paths = [d/collect.filename(seed,side) for d in directories]
                found = [p for p in paths if p.is_file()]
                if len(found) != 1 or collect.file_sha(found[0]) != record["sha256"]:
                    raise ValueError(f"Missing, changed or duplicate holdout: {seed} {side}")
                path = found[0]
                if collect.file_sha(path.parent/"protocol.json") != record["protocol"]:
                    raise ValueError(f"Wrong data collection protocol: {path}")
                collect.check_archive(path,seed,side,record["protocol"],student_sha=parent if group=="mixed" else None)
                with np.load(path,allow_pickle=False) as data:
                    boards = archived_boards(data)
                    rows, played = read_rows(data,boards)
                if torch.any(rows["step"][1:] < rows["step"][:-1]):
                    raise ValueError(f"Validation rows out of frame order: {path}")
                check_native_move_masks(boards,rows)
                near = near_rows(boards,rows)
                game = dict(cohort=group, opponent=collect.opponent_for(seed), **record)
                for model, channels in (("r2",16), ("r4",17)):
                    game[model] = count_agreement(models[model],boards[:,:channels],rows,played,near)
                games.append(game)
    if [collect.file_sha(p) for p in (r2,r4)] != hashes:
        raise ValueError("Checkpoint changed during paired evaluation")
    cohorts = {g:combine([r for r in games if r["cohort"]==g]) for g in inputs}
    return dict(r2_sha256=hashes[0], r4_sha256=hashes[1], initial_parity=parity,
                by_cohort=cohorts, totals=combine(games), gate=selection_gate(cohorts["mixed"]), games=games,
                scope="Paired action-class agreement on quantized saved observations. Gate uses mixed holdout only.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("r2","r4","out"):
        parser.add_argument("--"+name, type=Path, required=True)
    parser.add_argument("--data", nargs="+", type=Path, required=True)
    args = parser.parse_args()
    limit_threads()
    result = compare(args.r2,args.r4,args.data)
    with args.out.open("x") as f:
        json.dump(result,f,indent=2,allow_nan=False)
        f.write("\n")
    print(json.dumps({"by_cohort":result["by_cohort"],"gate":result["gate"]},indent=2))


if __name__ == "__main__":
    main()
