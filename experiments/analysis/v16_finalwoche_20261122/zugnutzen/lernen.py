"""Fit the fixed full-information training reward on public inputs and audit held-out decisions."""
import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import torch

from berater import HERE, NAMES, V16, ValueNet
from sammeln import games


def read(base, split):
    entries = []
    for seed, side, opponent in games(split):
        receipt = json.loads((base / f"{seed}.json").read_text())
        path = base / f"{seed}.npz"
        if ((receipt["seed"], receipt["split"], receipt["side"], receipt["opponent"]) != (seed, split, side, opponent)
                or receipt["package"] != V16 or receipt["sha256"] != sha256(path.read_bytes()).hexdigest()
                or receipt["steps"] != 303 or bool(receipt["calibration"]) != (receipt["alternatives"] > 0)):
            raise ValueError("Wrong sample provenance")
        with np.load(path, allow_pickle=False) as z:
            arrays = {k: z[k] for k in z.files}
        n = receipt["alternatives"]
        if arrays["x"].shape != (n, len(NAMES)) or arrays["delta"].shape != (n, 2) or not np.isfinite(arrays["x"]).all():
            raise ValueError("Invalid samples")
        entries.append((receipt, arrays))
    return entries


def run(base, out):
    torch.set_num_threads(1)
    torch.manual_seed(231130)
    rng = np.random.default_rng(231130)
    training = read(base, "train")
    used = [r for _, r in training if len(r["x"])]
    x = torch.from_numpy(np.concatenate([r["x"] for r in used]))
    rewards = np.concatenate([r["delta"] for r in used])
    y = torch.from_numpy((rewards[:, 0] - rewards[:, 1]).astype(np.float32))
    lengths = np.array([len(r["x"]) for r in used])
    starts = np.r_[0, np.cumsum(lengths)[:-1]]
    net = ValueNet()
    opt = torch.optim.Adam(net.parameters(), lr=0.002)
    for _ in range(600):
        seeds = rng.integers(len(used), size=256)
        rows = torch.from_numpy(starts[seeds] + rng.integers(lengths[seeds]))
        error = torch.nn.functional.smooth_l1_loss(net(x[rows]).flatten(), y[rows])
        opt.zero_grad()
        error.backward()
        opt.step()
    validation = read(base, "valid")
    if len({r["source"] for r, _ in training+validation}) != 1:
        raise ValueError("Inputs from different experimental versions")
    selected = []
    by_game = []
    with torch.inference_mode():
        for receipt, data in validation:
            scores = net(torch.from_numpy(data["x"])).flatten().numpy()
            row = {k: receipt[k] for k in ("seed", "side", "opponent")}
            n = len(selected)
            for step in np.unique(data["step"]):
                if int(step % 101) < 91:
                    continue
                options = np.flatnonzero(data["step"] == step)
                i = max(options, key=lambda k: (float(scores[k]), -data["uid"][k]))
                if scores[i] < .25:
                    continue
                own, enemy = map(int, data["delta"][i])
                selected.append(dict(**row, step=int(step), uid=int(data["uid"][i]), predicted=float(scores[i]),
                                     original=int(data["actions"][i,0]), alternative=int(data["actions"][i,1]),
                                     ours=own, opponent_delta=enemy, advantage=own-enemy))
            by_game.append(dict(**row, alternatives=len(scores), selected=len(selected)-n))
    def aggregate(items):
        return dict(turns=len(items), maps=len({s["seed"] for s in items}), own=sum(s["ours"] for s in items),
                    opponent=sum(s["opponent_delta"] for s in items), positive=sum(s["advantage"]>0 for s in items),
                    negative=sum(s["advantage"]<0 for s in items), zero=sum(s["advantage"]==0 for s in items),
                    mean=float(np.mean([s["advantage"] for s in items])) if items else 0.)
    overall = aggregate(selected)
    gates = dict(support=overall["turns"]>=60 and overall["maps"]>=12, immediate_gain=overall["mean"]>=.15,
                 net_positive=overall["positive"]>overall["negative"])
    checkpoint = out / "wertberater.npz"
    np.savez_compressed(checkpoint, **{k: v.detach().numpy() for k,v in net.state_dict().items()})
    result = dict(eligible=all(gates.values()), gates=gates, overall=overall,
                  by_opponent={o:aggregate([i for i in selected if i["opponent"]==o]) for o in ("solution92","kaggle3")},
                  by_side={s:aggregate([i for i in selected if i["side"]==s]) for s in ("player_0","player_1")},
                  training_maps=len(training), training_alternatives=len(y),
                  validation_maps=len(validation), validation_alternatives=sum(len(q["x"]) for _,q in validation),
                  checkpoint=sha256(checkpoint.read_bytes()).hexdigest(), release=V16,
                  plan=sha256((HERE/"PLAN.md").read_bytes()).hexdigest(), per_game=by_game, selected=selected,
                  manifests=[r for r,_ in training+validation])
    (out/"offline.json").write_text(json.dumps(result, separators=(",",":"), allow_nan=False) + "\n")
    print(overall, gates, flush=True)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base",type=Path)
    parser.add_argument("out",type=Path)
    args=parser.parse_args()
    run(args.base,args.out)
