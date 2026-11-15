"""Fixed single-worker games for the R3 restart-route follow-up, in the original R3 snapshot."""
import argparse
from collections import Counter
import fcntl
from importlib import metadata, util
import json
import os
from pathlib import Path
import platform

import numpy as np

from scripts import final_battle_compare as battle
from scripts import r3_restart_study as dev
from scripts.final_battle_select import SEATS, checked_run_files
from scripts.train_combat_advice import publish_json

PANELS = {"development": (range(7273100, 7273160), "solution92", ("route",)),
          "solution": (range(7283000, 7283060), "solution92", ("v14", "r3", "route")),
          "kaggle": (range(7283000, 7283060), "kaggle3", ("v14", "route")),
          "direct": (range(7283100, 7283160), "v14", ("route",))}
DEV_MANIFEST = "cce346b9b150687a01989ff159f0bbfa864d34c707d4e0b3b916068ad2660f39"
DEV_SUMMARY = "a77dcd82df969222a55330d3772f9a1c53002465dcb57b69efec3ed162810ac9"


def binding(a):
    original, pins = dev.inputs(a)
    confirm = json.loads((a.confirmation / "r3/manifest.json").read_text())
    for name, digest in confirm["sources"].items():
        if name.startswith("experiments/opponents/") and battle.digest(battle.ROOT / name) != digest:
            raise ValueError(f"Different native Kaggle opponent: {name}")
    if battle.digest(a.dev / "manifest.json") != DEV_MANIFEST or json.loads((a.dev / "manifest.json").read_text()) != pins:
        raise ValueError("The historical samples and current route implementation differ")
    if battle.digest(a.dev / "summary.json") != DEV_SUMMARY:
        raise ValueError("Wrong twelve historical samples")
    files = set((battle.ROOT / "agents").rglob("*.py")) | set((battle.ROOT / "lux").glob("*.py"))
    files.update(battle.ROOT / n for n in (*confirm["sources"], *pins["study_sha256"],
                 "scripts/r3_route_games.py", "scripts/protocol.py", "scripts/variants.py", "scripts/fetch_kaggle3.py",
                 "scripts/__init__.py", "scripts/final_battle_select.py", "scripts/train_combat_advice.py"))
    engine = Path(util.find_spec("luxai_s3").origin).parent
    stamp = dict(original=pins, historical_samples=DEV_SUMMARY,
                 sources={str(f.relative_to(battle.ROOT)): battle.digest(f) for f in sorted(files)},
                 lux_engine={f.name: battle.digest(f) for f in sorted(engine.glob("*.py"))},
                 python=platform.python_version(), machine=platform.machine(), platform=platform.system(),
                 runtime={k: metadata.version(k) for k in ("numpy", "torch", "scipy", "jax", "jaxlib", "luxai-s3")},
                 runtime_flags={k: os.environ.get(k) for k in ("JAX_PLATFORMS", "XLA_FLAGS", "PYTHONHASHSEED",
                                                                "CUDA_VISIBLE_DEVICES")})
    return original, stamp


def archived(a, original):
    summary = json.loads((a.dev / "summary.json").read_text())
    keys = {(seed, side) for seed in dev.SEEDS for side in SEATS}
    if set(summary["case_files"]) != {f"{n}_{s}.json" for n, s in keys}:
        raise ValueError("Unexpected twelve-game historical roster")
    rows = {}
    for seed, side in sorted(keys):
        path = a.dev / f"{seed}_{side}.json"
        case = json.loads(path.read_text())
        key = ("solution92", seed, side)
        if (battle.digest(path) != summary["case_files"][path.name]
                or battle.digest(path.with_suffix(".npz")) != case["orders_sha256"]
                or case["historical_r3"] != original["r3"][key] or case["historical_v14"] != original["v14"][key]):
            raise ValueError(f"Historical outcomes or commands changed for {key}")
        with np.load(path.with_suffix(".npz"), allow_pickle=False) as traces:
            parity = dev.compare_streams(traces["original"], traces["restart"], case["original"]["opportunities"],
                                         case["restart"]["opportunities"], int(side[-1]))
        item = case["restart"]
        if (parity != case["parity"] or any(case["original"]["game"][k] != v
                for k, v in original["r3"][key].items() if k != "secs")
                or (item["game"]["opponent"], item["game"]["seed"], item["game"]["side"]) != key):
            raise ValueError(f"Historical change does not reproduce for {key}")
        rows[key] = dict(item["game"], candidate="route", origin="archived", restored=len(item["opportunities"]))
    return rows


def manifest(stage, arm, stamp):
    seeds, opponent, arms = PANELS[stage]
    if arm not in arms:
        raise ValueError(f"Unregistered study arm {stage}/{arm}")
    return dict(candidate=arm, opponents=[opponent], first=seeds.start, maps=len(seeds), binding=stamp,
                model=None if arm == "v14" else stamp["original"]["r3_model"], weights=stamp["original"]["v14_model"])


def read(a, stage, arm, stamp):
    seeds, foe, _ = PANELS[stage]
    rows, m, hashes = checked_run_files(a.out / stage / arm, arm, seeds, (foe,))
    if m != manifest(stage, arm, stamp):
        raise ValueError("Mismatched route policy, models, or sources across games")
    return rows, m, hashes


def solution_gate(rows):
    wins = {arm: sum(int(r["result"]) for r in games.values()) for arm, games in rows.items()}
    return wins, wins["route"] >= wins["r3"] and wins["route"] > wins["v14"]


def initialize(arm, model):
    if arm == "v14":
        battle.init_worker("v14", None)
        return
    before = battle.POLICIES["selective_movement"]
    try:
        battle.POLICIES["selective_movement"] = "scripts.r3_restart_route:RestartRouteAgent"
        battle.init_worker("selective_movement", model)
    finally:
        battle.POLICIES["selective_movement"] = before
    battle.evaluate.agent.restore = arm == "route"


def run(a):
    original, stamp = binding(a)
    seeds, foe, _ = PANELS[a.stage]
    contract = manifest(a.stage, a.arm, stamp)
    if a.stage in ("kaggle", "direct"):
        panels = {arm: read(a, "solution", arm, stamp)[0] for arm in PANELS["solution"][2]}
        if not solution_gate(panels)[1]:
            raise ValueError("Independent Solution results do not justify further duels")
    injected = archived(a, original) if a.stage == "development" else {}
    out = a.out / a.stage / a.arm
    out.mkdir(parents=True, exist_ok=True)
    with (out / ".run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        mf = out / "manifest.json"
        if not mf.exists():
            publish_json(mf, contract)
        if json.loads(mf.read_text()) != contract:
            raise ValueError("Run source or configuration changed")
        if (out / "completed.json").exists():
            read(a, a.stage, a.arm, stamp)
            return
        keys = [(foe, seed, side) for seed in seeds for side in SEATS]
        path = out / "games.jsonl"
        seen = {}
        if path.exists():
            for line in path.read_text().splitlines():
                row = json.loads(line)
                key = row["opponent"], row["seed"], row["side"]
                if (key not in keys or key in seen or row["candidate"] != a.arm or row["steps"] != 303
                        or row["origin"] != ("archived" if key in injected else "fresh")
                        or (key in injected and row != injected[key])):
                    raise ValueError("Duplicate or invalid existing game")
                seen[key] = row
        model = str(a.r3.resolve())
        initialized = False
        try:
            with path.open("a") as f:
                for key in keys:
                    if key in seen:
                        continue
                    if key in injected:
                        row = injected[key]
                    else:
                        if not initialized:
                            initialize(a.arm, model)
                            initialized = True
                        identity = "v14" if a.arm == "v14" else "selective_movement"
                        row = battle.evaluate((identity, *key, None if a.arm == "v14" else model))
                        actor = battle.evaluate.agent
                        row.update(candidate=a.arm, origin="fresh",
                                   restored=sum(e["applied"] for e in getattr(actor, "route_events", ())))
                    f.write(json.dumps(row, allow_nan=False) + "\n")
                    f.flush()
                    seen[key] = row
                    print(*key, row["origin"], row["result"], flush=True)
        finally:
            if initialized:
                battle.evaluate.env.close()
        if binding(a)[1] != stamp:
            raise ValueError("Runtime, models or sources changed during play")
        result = {foe: dict(played=len(seen), wins=sum(r["result"] for r in seen.values()),
                            matches=sum(r["wins"] for r in seen.values()))}
        publish_json(out / "completed.json", dict(summary=result, rows_sha256=battle.digest(path)))
        read(a, a.stage, a.arm, stamp)
        print(result, Counter(r["origin"] for r in seen.values()), flush=True)


def arguments(p):
    for name in ("confirmation", "dev", "r3", "out"):
        p.add_argument("--" + name, required=True, type=Path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    arguments(parser)
    parser.add_argument("stage", choices=PANELS)
    parser.add_argument("arm", choices=("v14", "r3", "route"))
    run(parser.parse_args())
