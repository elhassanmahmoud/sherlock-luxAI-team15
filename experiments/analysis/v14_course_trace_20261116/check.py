#!/usr/bin/env python3
"""Replay native V14 opponent factories from two immutable Git trees against one course trace."""
import argparse
import dataclasses
import gzip
import hashlib
import io
import json
import os
import pickle
import platform
import random
import subprocess
import sys
import tarfile
import tempfile
import traceback
from collections import Counter
from pathlib import Path

REFS = {
    "historical": ("0105658188b2ec5eaf5c3a4b0ef477be9a1412f8", "e0160e77b4b9352e08d498d2383459ff2560b5e05a49dff11863f623e1a991fa"),
    "current": ("c13681debcbfee8274c8e7b04c84acdcdfea18d9", "1706f74a5b1f2f04076641b4f292154b351d79541fef49112019ff433d747f05"),
}
PACKED = "04f961be28ee0a80c0c194a0dc45029ee4af5bd99ebbdda622878e2059fc86e8"
PLAIN = "d6a2b14937e3687051f5fd5ac0dca7edfad2469e7a6bd7877e0170184f6b53eb"
WEIGHT = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
BASE = Path("experiments/analysis/continuation_20261102/existing_v14_preflight")
EVIDENCE = {"v14_4242.pkl.gz": PACKED, "process.json": "f9abcd112ddd065de9e5e61cee95557af7e6f0310e2bf3e06680f60e9d792423",
            "V14_py310_final_review.json": "5435d7cde1eacc4a5ee20ce0f8e985952cf5da65c474db3b2d7f247f0fdaa04d",
            "record313.log": "e40619da62bb276ff53e4fec3bab233a9a2f326e44f8c80e48ae169e1d5c449c",
            "replay310.log": "459d3ae2a7048dcca9b07dcf2e7170503fc5b7a56c0d1302b624cc1dbd0ca908"}
SIDES = ("player_0", "player_1")
ACTION = dict(zip(SIDES, ("1469fb90281e7a46c62efc435dae2593539ca08d01422588b0a289d2a54d3894",
                          "226d56f4b7dc93e7bd8f9cef51754c0eb178c2a0c3ab0603093942a62a835a7d")))
WEIGHTS = tuple("agents/sherlock/weights/agent_p%d.pth" % i for i in range(2))
HERE = Path(__file__).resolve()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(ok, message):
    if not ok:
        raise ValueError(message)


def tree(repo, name, dest):
    revision, expected = REFS[name]
    content = subprocess.check_output(["git", "-C", str(repo), "archive", revision, "agents", "scripts", "lux"])
    hashes = {}
    with tarfile.open(fileobj=io.BytesIO(content)) as archive:
        for member in archive:
            path = member.name
            if not member.isfile() or not (path.endswith(".py") or path in WEIGHTS):
                continue
            blob = archive.extractfile(member).read()
            hashes[path] = sha(blob)
            file = dest / path
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(blob)
    digest = sha("".join(f"{k}\0{hashes[k]}\n" for k in sorted(hashes)).encode())
    need(digest == expected and all(hashes[p] == WEIGHT for p in WEIGHTS), f"{name} archive mismatch")
    return {"commit": revision, "manifest_sha256": digest, "files": hashes}


def load_fixture(repo):
    import numpy as np
    for name, digest in EVIDENCE.items():
        need(sha((repo / BASE / name).read_bytes()) == digest, f"course provenance: {name}")
    blob = gzip.decompress((repo / BASE / "v14_4242.pkl.gz").read_bytes())
    need(sha(blob) == PLAIN, "uncompressed pickle checksum")
    data = pickle.loads(blob)
    rec = data["rec"]
    need(len(rec) == 303 and list(data["wins"]) == [1, 2], "course trace length or winner")
    for seat in SIDES:
        digest = hashlib.sha256()
        for step, row in enumerate(rec):
            obs = row["obs"][seat]
            need(int(obs["steps"]) == row["step"] == step and int(obs["match_steps"]) == step % 101,
                 f"timeline {step} {seat}")
            need(bool(row["done"]) == (step == 302), "terminal flag")
            if step % 101 == 0:
                need(list(obs["team_wins"]) == [0, step // 101], "restart scoreboard")
            act = matrix(row["acts"][seat], np)
            digest.update(act.tobytes())
        need(list(rec[-1]["next_obs"][seat]["team_wins"]) == [1, 2] and digest.hexdigest() == ACTION[seat],
             f"course {seat} actions/outcome")
    return data


def matrix(actions, np):
    actions = np.asarray(actions)
    need(actions.shape == (16, 3) and actions.dtype.kind in "iu", f"unexpected action shape/type {actions.shape}/{actions.dtype}")
    return np.ascontiguousarray(actions, dtype="<i8")


def seat_replay(root, data, seat):
    import numpy as np
    import torch
    from agents.sherlock.main import Agent_x, checkpoint_kind
    from scripts.common import make_opponent
    from scripts.xversion_replay import arrays

    weight = str(root / WEIGHTS[0])
    branches = Counter()
    kinds = []
    observed = {Agent_x.load_agent.__code__: "native_load", Agent_x.set_to_eval_mode.__code__: "eval",
                checkpoint_kind.__code__: "checkpoint_kind"}
    def track(frame, event, arg):
        key = observed.get(frame.f_code)
        if key and event == "call":
            branches[key] += 1
        if key == "checkpoint_kind" and event == "return":
            kinds.append(arg)

    sys.setprofile(track)
    try:
        a = make_opponent("self", seat, self_play_path=weight)
    finally:
        sys.setprofile(None)
    need(type(a) is Agent_x and a.player == seat and Path(a.agent_path).samefile(weight), "factory or weight")
    need(branches == {"checkpoint_kind": 1, "native_load": 1, "eval": 1} and kinds == [None],
         f"unexpected factory lifecycle {branches}/{kinds}")
    a.new_game(seat)
    random.seed(4242)
    np.random.seed(4242)
    a.set_env_cfg(data["cfg"])
    nets = [a.q, *a.extra_q]
    need(not a.training and a._imitation is None and a.cnn_policy is None and len(nets) == 36
         and not any(net.training for net in nets) and a.env_steps == 909000, "native eval/ensemble")
    config = dataclasses.asdict(a.cfg)
    calls = Counter()
    def count_method(obj, method):
        old = getattr(obj, method, None)
        if old is None:
            return
        calls[method] = 0
        def counted(*args, **kwargs):
            calls[method] += 1
            return old(*args, **kwargs)
        setattr(obj, method, counted)
    for name in ("_act_est", "_act", "_decide", "_network_values", "update"):
        count_method(a, name)
    for name in ("observe", "remember", "record_played_actions"):
        count_method(a.param_est, name)

    stats = []
    parts, total = [hashlib.sha256() for _ in range(3)], hashlib.sha256()
    forwards = [[0] * 36 for _ in range(3)]
    def hook(index):
        def count(net, inputs, output):
            forwards[match][index] += 1
        return count
    hooks = [net.register_forward_hook(hook(i)) for i, net in enumerate(nets)]
    first_diff = None
    mismatch_steps = [0, 0, 0]
    mismatch_units = [0, 0, 0]
    re_starts = []
    try:
        for step, row in enumerate(data["rec"]):
            match = step // 101
            obs = arrays(row["obs"][seat])
            got = matrix(a.act(step=step, obs=obs), np)
            need(a.caught_errors == 0, f"policy caught an error at {seat}/{step}")
            if step % 101 == 0:
                re_starts.append({"step": step, "team_wins": obs["team_wins"].tolist(), "all_zero": bool(not got.any())})
            expected = matrix(row["acts"][seat], np)
            diffs = np.flatnonzero((got != expected).any(axis=1))
            if len(diffs):
                mismatch_steps[match] += 1
                mismatch_units[match] += len(diffs)
                if first_diff is None:
                    u = int(diffs[0])
                    first_diff = {"step": step, "uid": u, "native": got[u].tolist(), "course": expected[u].tolist()}
            parts[match].update(got.tobytes())
            total.update(got.tobytes())
    finally:
        for h in hooks:
            h.remove()
    for match, per_net in enumerate(forwards):
        need(min(per_net) > 0 and len(set(per_net)) == 1, f"{seat} M{match+1} partial ensemble {per_net}")
        stats.append({"network_calls_each": per_net, "action_sha256": parts[match].hexdigest(),
                      "mismatch_steps": mismatch_steps[match], "mismatch_units": mismatch_units[match]})
    use_est = any(config[key] for key in ("nebula_avoid", "dodge_auto", "sap_dropoff_est", "art_splash", "sap_still_splash"))
    need(calls["_act_est"] == calls["_act"] == 303 and calls["_decide"] == 300 and calls["update"] == 0
         and calls["_network_values"] == sum(f[0] for f in forwards)
         and calls["observe"] == calls["remember"] == 303 * bool(use_est)
         and calls.get("record_played_actions", 0) == 0 and all(b["all_zero"] for b in re_starts), f"branch counts {calls}")
    return {"pass": first_diff is None and total.hexdigest() == ACTION[seat], "action_sha256": total.hexdigest(),
            "first_difference": first_diff, "caught_errors": a.caught_errors, "factory": dict(branches),
            "checkpoint_kind": kinds[0], "method_calls": dict(calls), "raw_config": config,
            "env_steps_at_load": int(a.env_steps), "device": str(a.device), "network_widths": [n.feat_dim for n in nets],
            "match_starts": re_starts, "matches": stats}


def one(root, repo):
    os.chdir(root)
    sys.path.insert(0, str(root))
    import numpy as np
    import torch
    torch.set_num_threads(1)
    torch.manual_seed(0)
    data = load_fixture(repo)
    seats = {}
    for seat in SIDES:
        try:
            seats[seat] = seat_replay(root, data, seat)
        except Exception:
            seats[seat] = {"pass": False, "error": traceback.format_exc()}
    imports = {}
    for key, mod in tuple(sys.modules.items()):
        if key.split(".")[0] in ("agents", "scripts", "lux") and getattr(mod, "__file__", None):
            p = Path(mod.__file__).resolve()
            need(p.is_relative_to(root), f"foreign import: {p}")
            imports[key] = {"file": str(p.relative_to(root)), "sha256": sha(p.read_bytes())}
    return {"pass": all(x["pass"] for x in seats.values()), "python": sys.version, "numpy": np.__version__,
            "torch": str(torch.__version__), "platform": platform.platform(), "seats": seats, "actual_imports": imports}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=["check", "run", "_one"])
    cli.add_argument("--repo", type=Path, required=True)
    cli.add_argument("--out", type=Path, required=True, help="new JSON path")
    cli.add_argument("--root", type=Path, help=argparse.SUPPRESS)
    a = cli.parse_args()
    repo, out = a.repo.resolve(), a.out.resolve()
    need(not out.exists(), f"report already exists: {out}")
    if a.mode == "_one":
        report = one(a.root.resolve(), repo)
    else:
        fixture = load_fixture(repo)
        report = {"mode": a.mode, "check_script_sha256": sha(HERE.read_bytes()), "course_evidence": EVIDENCE, "seed": 4242,
                  "pickle_sha256": PLAIN, "course_action_sha256": ACTION, "course_team_wins": [1, 2],
                  "course_record_python": fixture["py"], "sources": {}}
        with tempfile.TemporaryDirectory(prefix="sherlock-native-replay-") as temp:
            for name in REFS:
                root = Path(temp).resolve() / name
                src = tree(repo, name, root)
                report["sources"][name] = src
                if a.mode == "run":
                    result = root.parent / (name + ".json")
                    proc = subprocess.run([sys.executable, "-I", "-B", str(HERE), "_one", "--root", str(root),
                                           "--repo", str(repo), "--out", str(result)])
                    src["replay"] = json.loads(result.read_text()) if result.is_file() else {"pass": False, "exit": proc.returncode}
                    if proc.returncode:
                        src["replay"]["pass"] = False
        report["pass"] = a.mode == "check" or all(src["replay"]["pass"] for src in report["sources"].values())
        if a.mode == "run":
            seats = [report["sources"][name]["replay"].get("seats", {}) for name in REFS]
            report["native_action_streams_equal"] = {
                seat: (seats[0].get(seat, {}).get("action_sha256") == seats[1].get(seat, {}).get("action_sha256")
                       if all("action_sha256" in run.get(seat, {}) for run in seats) else None)
                for seat in SIDES}
            report["pass"] = report["pass"] and all(report["native_action_streams_equal"].values())
    with out.open("x") as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"{a.mode}: {report['pass']} ({out})", flush=True)
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
