"""One delayed-route game for each of 14 registered historical Solution seats.

 From the frozen route-panel snapshot with this patch:
   python -m scripts.r3_delay_study --study MOVEMENT_SOFT_DIR --r3 R3_PTH --check
   python -m scripts.r3_delay_study --study MOVEMENT_SOFT_DIR --r3 R3_PTH --out NEW_DIR
"""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from scripts import r3_restart_study as dev
from scripts import r3_route_games as panel
from scripts.final_battle_select import SEATS
from scripts.train_combat_advice import publish_json

ROOT = dev.battle.ROOT
CAL = ROOT / "experiments/analysis/movement_soft_20261115/restart_route/verzoegerung"
SEEDS = tuple(sorted((*dev.SEEDS, 7273105)))
ROUTE_GAMES = "f0375ae37109cc10e38781fc83b0f71bc8c9ce51d0de5e1eb72d6a16e1da7ed0"
ROUTE_MANIFEST = "df8a18c7cb07ee8860189289a53973659ffeabcf20b934c3d7ddee8ecdc5da7b"
TRADE = {"player_0": "bb2bf3ad6d71619bed830d4547597461982a3b696e898aa7095f7489b2f94a82",
         "player_1": "bce1cc26b53fe3039ca9767903f2db60145b4eb88fcf26fc1cf61be14b80dc25"}


def read_json(path):
    return json.loads(path.read_bytes())


def checked(path, expected):
    if dev.battle.digest(path) != expected:
        raise ValueError(f"Changed registered evidence: {path}")


def prior(study, model):
    from scripts.r3_delay_route import MEDIAN
    route = study / "restart_route"
    a = SimpleNamespace(confirmation=study / "confirmation", dev=route / "dev", r3=model, out=route / "followup")
    original, stamp = panel.binding(a)
    routed, _, seals = panel.read(a, "development", "route", stamp)
    if (seals["games_sha256"], seals["manifest_sha256"]) != (ROUTE_GAMES, ROUTE_MANIFEST):
        raise ValueError("Wrong original full 120-seat route panel")
    reused = panel.archived(a, original)
    if any(routed[k] != v for k, v in reused.items()):
        raise ValueError("The twelve original trace rows differ from the full route panel")
    checked(CAL / "auswertung/ergebnis.json", "41289dac52eb17bb2d2c4de95ee156f2f8c030ffd4591f76b3d0cb512a4dc3ca")
    cal = read_json(CAL / "auswertung/ergebnis.json")
    checked(CAL / "KALIBRIERPLAN.md", cal["plan_sha256"])
    checked(CAL / "auswertung/matches.csv", cal["match_rows_sha256"])
    if cal["overall"]["first_median"] != MEDIAN or MEDIAN != 12.5:
        raise ValueError("Different calibration")
    cases = {}
    for seed in SEEDS:
        for side in SEATS:
            key = "solution92", seed, side
            if seed == 7273105:
                path = route / "tradeoff_replay" / (side + ".json")
                checked(path, TRADE[side])
            else:
                path = a.dev / f"{seed}_{side}.json"
            c = read_json(path)
            if (c["seed"], c["side"]) != (seed, side):
                raise ValueError(f"Wrong archived label: {key}")
            for name, expected in (("original", original["r3"][key]), ("restart", routed[key])):
                game = c[name]["game"]
                fields = ("opponent", "seed", "side", "steps", "result", "wins", "losses", "points", "opp_points", "study")
                if (any(game[k] != expected[k] for k in fields) or sum(m["won"] for m in c[name]["matches"]) != game["wins"]):
                    raise ValueError(f"Historical game was not reproduced: {name}, {key}")
            if len(c["restart"]["opportunities"]) != routed[key]["restored"]:
                raise ValueError("Historical intervention count differs")
            cases[seed, side] = c
    return cases, dict(panel=seals, calibration=dev.battle.digest(CAL/"auswertung/ergebnis.json"),
                       source={f: dev.battle.digest(ROOT / f) for f in ("scripts/r3_delay_route.py", "scripts/r3_delay_study.py")},
                       twelve_cases=panel.DEV_SUMMARY, tradeoff=TRADE, runtime_and_original_files=stamp,
                       median=MEDIAN, seeds=SEEDS, sides=SEATS)


def compare_events(reference, variant, before_change, after_change, team):
    """Reuse the exact two-stream checker for either direction of the binary switch."""
    return dev.compare_streams(reference, variant, before_change, after_change, team)["first_actual_step"]


def verify(study, case, actual, orders):
    from scripts.r3_delay_route import MEDIAN
    seed, side = case["seed"], case["side"]
    team = int(side[-1])
    events = actual["opportunities"]
    for e in events:
        selected = e["match_step"] > MEDIAN
        if (e["applied"] is not selected or e["step"] % 101 != e["match_step"]
                or orders[e["step"], team, e["uid"]].tolist() != e["v14_world" if selected else "r3_world"]):
            raise ValueError("Final world action does not match the registered delay")
    applied = [e for e in events if e["applied"]]
    skipped = [e for e in events if not e["applied"]]
    refs = case["original"], case["restart"]
    late = [e for e in refs[0]["opportunities"] if e["match_step"] > MEDIAN]
    early = [e for e in refs[1]["opportunities"] if e["match_step"] <= MEDIAN]
    expected = {"original": (late, applied), "restart": (early, skipped)}
    prefix = case.get("parity") or case["same_prefix"]
    if dev.stream_hash(orders[:101]) != prefix["match1_sha256"]:
        raise ValueError("Submitted first-match actions differ")
    full = dev.stream_hash(orders)
    differences = {}
    for name, (before, after) in expected.items():
        earliest = min((e["step"] for e in before), default=303)
        first_after = min((e["step"] for e in after), default=303)
        def by_uid(group):
            return {e["uid"]: {k: v for k, v in e.items() if k != "applied"} for e in group if e["step"] == earliest}
        if first_after != earliest or by_uid(before) != by_uid(after):
            raise ValueError(f"First effective switch differs from the known opportunity: {name}")
        if actual["matches"][:earliest//101] != case[name]["matches"][:earliest//101]:
            raise ValueError(f"Match already differs before first intervention: {name}")
        if earliest == 303 and full != prefix["r3_actions_sha256" if name == "original" else "restart_actions_sha256"]:
            raise ValueError(f"Unchanged game has different action stream: {name}")
        differences[name] = None if earliest == 303 else earliest
    if seed in dev.SEEDS:
        path = study / "restart_route/dev" / f"{seed}_{side}.npz"
        with np.load(path, allow_pickle=False) as old:
            a = compare_events(old["original"], orders, late, applied, team)
            b = compare_events(orders, old["restart"], skipped, early, team)
        if (a, b) != (differences["original"], differences["restart"]):
            raise ValueError("Measured stream differences disagree")
        evidence = "both full historical world-order streams"
    else:
        end = prefix["equal_steps_before_first_change"]
        if dev.stream_hash(orders[:end]) != prefix["equal_prefix_sha256"]:
            raise ValueError("Different historical shared prefix for 7273105")
        evidence = "historical shared prefix digest, per-UID events, full digests when no switch; raw reference streams unavailable"
    return dict(first_difference_global_step=differences, evidence=evidence, actions_sha256=full,
                applied=len(applied), withheld=len(skipped))


def outcome(item):
    r = item["game"]
    return dict(won=int(r["result"]), matches_won=r["wins"], points=r["points"], rival_points=r["opp_points"],
                matches=[{**m, "first_public_positive": m["first_own_point"]+1 if m["first_own_point"] not in
                          (100, None) else None} for m in item["matches"]])


def run(args):
    cases, pins = prior(args.study, args.r3)
    print(f"Verified {len(cases)} historical R3/route pairs, median {pins['median']}", flush=True)
    if args.check:
        return
    args.out.mkdir(exist_ok=False, parents=True)
    publish_json(args.out / "manifest.json", pins)
    model = str(args.r3.resolve())
    original_class = dev.battle.POLICIES["selective_movement"]
    try:
        dev.battle.POLICIES["selective_movement"] = "scripts.r3_delay_route:DelayedRouteAgent"
        dev.battle.init_worker("selective_movement", model)
    finally:
        dev.battle.POLICIES["selective_movement"] = original_class
    actor, env = dev.battle.evaluate.agent, dev.battle.evaluate.env
    rows, files = [], {}
    try:
        for (seed, side), c in sorted(cases.items()):
            actual, orders = dev.play(seed, side, actor, env, model, True)
            label = f"{seed}_{side}"
            array = args.out / (label + ".npz")
            np.savez_compressed(array, delayed=orders)
            casefile = args.out / (label + ".json")
            try:
                evidence = verify(args.study, c, actual, orders)
            except ValueError as error:
                publish_json(args.out / (label + "_failed.json"), dict(error=str(error), game=actual))
                raise
            row = dict(seed=seed, side=side, original=outcome(c["original"]), restart=outcome(c["restart"]),
                       delayed=outcome(actual), comparison=evidence)
            publish_json(casefile, dict(**row, delayed_record=actual, orders_file_sha256=dev.battle.digest(array)))
            files[casefile.name] = dev.battle.digest(casefile)
            rows.append(row)
            print(label, *(row[name]["won"] for name in ("original","restart","delayed")), flush=True)
    finally:
        env.close()
    if prior(args.study, args.r3)[1] != pins:
        raise ValueError("Sources changed while playing")
    summaries = {}
    for arm in ("original", "restart"):
        summaries[arm] = dict(wins=sum(r[arm]["won"] for r in rows), matches=sum(r[arm]["matches_won"] for r in rows),
            gained=[[r["seed"],r["side"]] for r in rows if r["delayed"]["won"] > r[arm]["won"]],
            lost=[[r["seed"],r["side"]] for r in rows if r["delayed"]["won"] < r[arm]["won"]])
    summaries["delayed"] = dict(wins=sum(r["delayed"]["won"] for r in rows), matches=sum(r["delayed"]["matches_won"] for r in rows))
    publish_json(args.out/"summary.json", dict(new_games=len(rows), reused_games=2*len(rows), outcomes=summaries,
                two_named_seats_both_won=all(r["delayed"]["won"] for r in rows if (r["seed"],r["side"]) in
                {(7273105,"player_0"),dev.LOSS}), cases=files, manifest_sha256=dev.battle.digest(args.out/"manifest.json")))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--study", type=Path, required=True)
    p.add_argument("--r3", type=Path, required=True)
    dest = p.add_mutually_exclusive_group(required=True)
    dest.add_argument("--check", action="store_true")
    dest.add_argument("--out", type=Path)
    run(p.parse_args())
