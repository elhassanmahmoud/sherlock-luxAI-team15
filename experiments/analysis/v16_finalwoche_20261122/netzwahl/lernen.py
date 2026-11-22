"""Fit constant and unit-dependent weights on identical teacher minibatches."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import torch
from torch.nn import functional as F

from vorhersagen import FEATURES, HERE, V16


def load_rows(base, split, seeds):
    arrays = {k: [] for k in ("a", "b", "legal", "x", "y", "seed")}
    for seed in seeds:
        with np.load(base / f"{split}_{seed}.npz", allow_pickle=False) as game:
            if str(game["model"]) != V16:
                raise ValueError(f"Different policy on {seed}")
            for key in ("a", "b", "legal", "x", "y"):
                arrays[key].append(game[key])
            arrays["seed"].append(np.full(len(game["y"]), seed))
    rows = {k: torch.from_numpy(np.concatenate(v)) for k, v in arrays.items()}
    rows["y"] = rows["y"].long()
    if not rows["legal"].gather(1, rows["y"][:, None]).all():
        raise ValueError("Non-admissible teacher label")
    if not all(torch.isfinite(rows[k]).all() for k in ("a", "b", "x")):
        raise ValueError("Non-finite logit or input")
    return rows


def scores(rows, weight=None, bias=0.0):
    if weight is None:
        d = 0.65 * torch.tanh(torch.as_tensor(bias))
    else:
        d = 0.65 * torch.tanh(rows["x"] @ weight + bias)[:, None]
    return ((1 + d) * rows["a"] + (1 - d) * rows["b"]).masked_fill(~rows["legal"], -torch.inf)


def train(old, recent):
    gen = np.random.default_rng(23112026)
    constant = torch.zeros((), requires_grad=True)
    intercept = torch.zeros((), requires_grad=True)
    factors = torch.zeros(len(FEATURES), requires_grad=True)
    opt_const = torch.optim.Adam([constant], lr=0.015)
    opt_context = torch.optim.Adam([intercept, factors], lr=0.015)
    for _ in range(500):
        i = gen.integers(len(old["y"]), size=256)
        j = gen.integers(len(recent["y"]), size=256)
        batch = {k: torch.cat([old[k][i], recent[k][j]]) for k in ("a", "b", "legal", "x", "y")}
        opt_const.zero_grad()
        F.cross_entropy(scores(batch, bias=constant), batch["y"]).backward()
        opt_const.step()
        opt_context.zero_grad()
        loss = F.cross_entropy(scores(batch, factors, intercept), batch["y"]) + 0.003 * factors.square().mean()
        loss.backward()
        opt_context.step()
    return constant.detach(), factors.detach(), intercept.detach()


def fit(base, out):
    torch.set_num_threads(1)
    directory = base / "vorhersagen"
    old = load_rows(directory, "old", range(7172000, 7172120))
    recent = load_rows(directory, "new", [*range(19376200, 19376208), *range(160345000, 160345032)])
    constant, weight, bias = train(old, recent)
    # The candidate is now fixed; only now load the independent validation games.
    valid = load_rows(directory, "valid", range(160345100, 160345124))
    disagreement = (valid["a"].masked_fill(~valid["legal"], -torch.inf).argmax(1)
                    != valid["b"].masked_fill(~valid["legal"], -torch.inf).argmax(1))
    means = {}
    decisions = {}
    for name, logits in (("original", scores(valid)), ("constant", scores(valid, bias=constant)),
                         ("context", scores(valid, weight, bias))):
        predicted = logits.argmax(1)
        correct = predicted == valid["y"]
        decisions[name] = predicted
        means[name] = dict(correct=int(correct.sum()), disagreement_correct=int(correct[disagreement].sum()),
                           logloss=float(F.cross_entropy(logits, valid["y"])))
    n = int(disagreement.sum())
    cards = int(valid["seed"][disagreement].unique().numel())
    baseline, fixed, candidate = (means[k] for k in ("original", "constant", "context"))
    gates = dict(support=n >= 500 and cards >= 12,
                 original_disagreement_one_point=100 * (candidate["disagreement_correct"]
                     - baseline["disagreement_correct"]) >= n,
                 beats_fixed=candidate["disagreement_correct"] > fixed["disagreement_correct"],
                 logloss_improved=candidate["logloss"] < baseline["logloss"])
    paired = []
    for seed in valid["seed"].unique().tolist():
        idx = (valid["seed"] == seed) & disagreement
        local = {k: int((pred[idx] == valid["y"][idx]).sum()) for k, pred in decisions.items()}
        paired.append(dict(seed=seed, different=int(idx.sum()), **local))
    report = dict(release=V16, plan_sha256=sha256((HERE / "PLAN.md").read_bytes()).hexdigest(),
                  features=FEATURES, constant_logit=float(constant), context_bias=float(bias),
                  context_weights=weight.tolist(), old_rows=len(old["y"]), recent_rows=len(recent["y"]),
                  holdout_games=24, validation_rows=len(valid["y"]), disagreements=n, cards_with_disagreement=cards,
                  action_changes=int((decisions["original"] != decisions["context"]).sum()),
                  metrics=means, per_game=paired, gates=gates, eligible=all(gates.values()))
    target = out / "offline.json"
    with target.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({k: report[k] for k in ("metrics", "gates", "eligible")}, indent=2))


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("base", type=Path)
    cli.add_argument("out", type=Path)
    args = cli.parse_args()
    fit(args.base, args.out)
