"""A small bounded, movement-only adviser trained from actual low-visibility demonstrations."""
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
import torch
from torch import nn

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
from agents.sherlock.features import FEATURE_NAMES

IDX = {name: i for i, name in enumerate(FEATURE_NAMES)}
POINTS = [IDX[d + "_point"] for d in "curdl"]


def eligible(x, legal):
    return ((x[:, IDX["cfg_sensor_range"]] <= 0.51) & (x[:, IDX["match_idx_frac"]] < 0.5)
            & (x[:, IDX["self_low_energy"]] == 0) & (x[:, IDX["enemies_in_sap"]] == 0)
            & (x[:, POINTS].max(axis=1) == 0) & (legal.sum(axis=1) >= 2))


class Adviser(nn.Module):
    def __init__(self):
        super().__init__()
        self.hidden = nn.Linear(len(FEATURE_NAMES), 32)
        self.out = nn.Linear(32, 4)
        nn.init.zeros_(self.out.weight)
        nn.init.zeros_(self.out.bias)

    def forward(self, inputs):
        return 3 * torch.tanh(self.out(torch.relu(self.hidden(inputs))))


def reserve(seeds):
    order = sorted(set(seeds), key=lambda s: sha256(f"r3-moe-{s}".encode()).digest())
    return set(order[::3])


def report_data(base):
    all_rows = [json.loads(p.read_text()) for p in sorted((base / "lehrdaten").glob("*.json"))]
    if len(all_rows) != 92 or len({(r["actor"], r["seed"], r["side"]) for r in all_rows}) != 92:
        raise ValueError("All 92 source recordings are required")
    positive = [r for r in all_rows if r["actor"] == "r3" and r["group"] == "r3_only"]
    control = [r for r in all_rows if r["actor"] == "v16" and r["group"] != "r3_only"]
    if len(positive) != 25 or len(control) != 21:
        raise ValueError("Unexpected demonstration sources")
    held = reserve(r["seed"] for r in positive)
    held |= reserve(r["seed"] for r in control if r["seed"] not in held)
    groups = {}
    for source, name in ((positive, "r3"), (control, "v16")):
        for r in source:
            p = base / "logits" / (Path(r["file"]).stem + ".npz")
            with np.load(p, allow_pickle=False) as z:
                if str(z["sha256"]) != r["sha256"]:
                    raise ValueError("Incorrect teaching logits")
                x, y, legal = z["x"].astype(np.float32), z["y"].astype(np.int64), z["legal"]
                ok = eligible(x, legal) & (y >= 1) & (y <= 4)
                ok &= legal[np.arange(len(y)), np.clip(y-1, 0, 3)]
                rows = tuple(torch.from_numpy(a[ok]) for a in (x, z["logits"].astype(np.float32), legal, y-1))
            if not ok.any():
                continue
            dst = groups.setdefault((name, "valid" if r["seed"] in held else "train"), {})
            dst.setdefault(r["seed"], []).append(rows)
    for maps in groups.values():
        for seed, pairs in list(maps.items()):
            maps[seed] = tuple(torch.cat(xs) for xs in zip(*pairs, strict=True))
    return groups, held, all_rows


def batch(maps, n, rng):
    selected = rng.choice(list(maps), n)
    pieces = []
    for s, count in zip(*np.unique(selected, return_counts=True), strict=True):
        values = maps[s]
        ids = torch.from_numpy(rng.integers(len(values[0]), size=count))
        pieces.append(tuple(x[ids] for x in values))
    return tuple(torch.cat(xs) for xs in zip(*pieces, strict=True))


def summarize(net, maps):
    details = []
    with torch.inference_mode():
        for seed, (x, orig, legal, label) in sorted(maps.items()):
            baseline = orig.masked_fill(~legal, -torch.inf).argmax(1)
            pred = (orig + net(x)).masked_fill(~legal, -torch.inf).argmax(1)
            details.append(dict(seed=int(seed), n=len(label), baseline=int((baseline == label).sum()),
                                adviser=int((pred == label).sum()), changes=int((baseline != pred).sum())))
    return dict(maps=len(details), n=sum(r["n"] for r in details), per_map=details,
                improvement=float(np.mean([(r["adviser"] - r["baseline"])/r["n"] for r in details])))


def train(base, output):
    torch.set_num_threads(1)
    torch.manual_seed(231122)
    rng = np.random.default_rng(231122)
    groups, held, rows = report_data(base)
    net = Adviser()
    opt = torch.optim.Adam(net.parameters(), lr=0.002)
    for _ in range(700):
        examples = (batch(groups["r3", "train"], 384, rng), batch(groups["v16", "train"], 128, rng))
        x, scores, legal, y = [torch.cat(q) for q in zip(*examples, strict=True)]
        adjustment = net(x)
        estimate = (scores + adjustment).masked_fill(~legal, -torch.inf)
        loss = nn.functional.cross_entropy(estimate, y) + 0.005 * adjustment.square().mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
    reviews = {f"{actor}_{s}": summarize(net, maps) for (actor, s), maps in groups.items()}
    r, v = reviews["r3_valid"], reviews["v16_valid"]
    gates = dict(examples=r["maps"] >= 5 and r["n"] >= 250, r3_gain=r["improvement"] >= .04,
                 preserves_reference=v["improvement"] >= -.03)
    checkpoint = output / "bewegungsberater.npz"
    np.savez_compressed(checkpoint, **{k: v.detach().numpy() for k, v in net.state_dict().items()})
    findings = dict(eligible=all(gates.values()), gates=gates, results=reviews, validation_maps=sorted(held),
                    plan=sha256((HERE / "BEWEGUNG.md").read_bytes()).hexdigest(),
                    checkpoint=sha256(checkpoint.read_bytes()).hexdigest(),
                    inputs=[{k: row[k] for k in ("actor", "group", "sensor", "seed", "side", "rows", "sha256", "source_sha256")} for row in rows])
    (output / "bewegung_offline.json").write_text(json.dumps(findings, indent=2) + "\n")
    print({k: (v["maps"], v["n"], v["improvement"]) for k, v in reviews.items()}, gates, flush=True)


if __name__ == "__main__":
    import argparse
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("base", type=Path)
    cli.add_argument("output", type=Path)
    args = cli.parse_args()
    train(args.base, args.output)
