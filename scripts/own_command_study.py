"""Paired teacher-agreement screen for the opt-in own-command movement adviser against the pinned R2."""
import argparse
from collections import Counter
import json
from pathlib import Path

import torch

from agents.sherlock.own_command import KIND
from scripts import collect_combat_advice as collect
from scripts import selective_agreement

R2_SHA = "23fa6208d76e81940916388b9ee56c1d290693e8febfa53622442b64b0d33f96"
ROOT = Path(__file__).resolve().parents[1]
SOURCES = ("agents/sherlock/own_command.py", "agents/sherlock/imitation_net.py", "agents/sherlock/cnn_model.py",
           "agents/sherlock/geometry.py", "scripts/imitate.py", "scripts/selective_dagger.py",
           "scripts/selective_agreement.py", "scripts/selective_advice_agent.py", "scripts/own_command_study.py",
           "scripts/combat_teacher_counterfactual.py")


def bind_control(path, parent, inputs):
    if collect.file_sha(path) != R2_SHA:
        raise ValueError("Expected the fixed R2 weights")
    r2 = torch.load(path, map_location="cpu", mmap=True, weights_only=True)
    if r2["selective_training"]["inputs"] != inputs or r2["selective_training"]["parent_sha256"] != parent:
        raise ValueError("Training parent or dataset differs from R2")
    return dict(r2_sha256=R2_SHA, sources={name:collect.file_sha(ROOT/name) for name in SOURCES})


def widen_and_check(net):
    """Extend only the already-seeded input weights, without constructing another randomly initialized layer."""
    device = net.unit[0].weight.device
    f = torch.linspace(-1., 1., 7*79, device=device).reshape(7,79)
    board = torch.linspace(-1., 1., 16*8*8, device=device).reshape(1,16,8,8)
    pos = torch.tensor([(1,1), (2,3), (0,0), (1,2), (3,5), (2,3), (6,7)], device=device)
    steps = torch.zeros(7, dtype=torch.long, device=device)
    suffix = torch.cat((torch.eye(6, device=device), torch.zeros((1,6), device=device)))
    layer = net.unit[0]
    if layer.in_features != 79 or net.arch["feat_dim"] != 79:
        raise ValueError("Expected unexpanded R2 architecture")
    with torch.no_grad():
        before = net.forward_all(board,steps,pos,f)
        w = layer.weight.detach()
        layer.weight = torch.nn.Parameter(torch.cat((w, w.new_zeros((w.shape[0],6))), dim=1))
        layer.in_features = net.arch["feat_dim"] = 85
        after = net.forward_all(board,steps,pos,torch.cat((f,suffix), 1))
        delta = []
        for old, new in zip(before,after):
            torch.testing.assert_close(new,old,atol=1e-6,rtol=1e-5)
            delta.append(float((new-old).abs().max()))
    return dict(device=str(device),atol=1e-6,rtol=1e-5,max_abs_by_head=delta)


def offline_gate(mixed_summary):
    a, b = (mixed_summary[k] for k in ("r2","own_command"))
    checks = dict(improved_net_on_known_history=b["history_net"] > a["history_net"],
                  nondecreasing_total_net=b["net"] >= a["net"],
                  newly_hurt_within_ten_percent=10*b["hurt"] <= 11*a["hurt"])
    return checks


def screen(r2, candidate, data, out):
    from scripts.experiment import limit_threads
    from scripts.selective_advice_agent import load_heads
    from scripts.train_combat_advice import publish_json

    limit_threads()
    if out.exists():
        raise FileExistsError(out)
    h = collect.file_sha(candidate)
    ck = torch.load(candidate, map_location="cpu", weights_only=True)
    if ck["kind"] != KIND or ck["arch"]["feat_dim"] != 85:
        raise ValueError("Not an own-command movement adviser")
    train = ck["selective_training"]
    control = bind_control(r2, train["parent_sha256"], train["inputs"])
    if not all(ck["own_command"][k] == v for k,v in control.items()):
        raise ValueError("Control/source binding differs since training")
    models = (load_heads(r2)[0], load_heads(candidate)[0])
    paired = []
    summaries = {}
    with torch.inference_mode():
        for group, splits in train["inputs"].items():
            totals = [Counter(), Counter()]
            for row in splits["val"]:
                paths = [d/collect.filename(row["seed"],row["side"]) for d in data]
                found = [p for p in paths if p.is_file()]
                if len(found) != 1 or collect.file_sha(found[0]) != row["sha256"]:
                    raise ValueError("Missing, duplicate or changed validation file")
                count = [selective_agreement.measure(heads,found[0],with_history_scope=True) for heads in models]
                for name in ("rows","base_matches","history_rows","history_base_matches"):
                    if count[0][name] != count[1][name]:
                        raise ValueError("Unpaired base decisions or unit-history populations")
                for total, these in zip(totals,count):
                    total.update(these)
                paired.append(dict(cohort=group, **row, r2=dict(count[0]), own_command=dict(count[1])))
            summaries[group] = {}
            for label, c in zip(("r2","own_command"),totals):
                summaries[group][label] = dict(c, net=c["helped"] - c["hurt"],
                                               history_net=c["history_helped"] - c["history_hurt"])
                if c["history_advised_matches"] - c["history_base_matches"] != summaries[group][label]["history_net"]:
                    raise ValueError("Invalid history-only agreement counts")
    if collect.file_sha(r2) != R2_SHA or collect.file_sha(candidate) != h:
        raise ValueError("Checkpoint changed during screening")
    checks = offline_gate(summaries["mixed"])
    gate = all(checks.values())
    result = dict(r2_sha256=R2_SHA, candidate_sha256=h, sources=control["sources"], validation=summaries,
                  offline_checks=checks, passes_offline_gate=gate, initial_parity=ck["own_command"]["initial_parity"], games=paired)
    publish_json(out,result)
    print(json.dumps({"validation":summaries,"offline_checks":checks,"passes_offline_gate":gate}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("r2","candidate","out"):
        parser.add_argument("--"+name, type=Path,required=True)
    parser.add_argument("--data",nargs="+", type=Path,required=True)
    args = parser.parse_args()
    screen(args.r2,args.candidate,args.data,args.out)
