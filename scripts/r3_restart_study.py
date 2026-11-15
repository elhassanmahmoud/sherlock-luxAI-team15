"""Run 12 paired original-R3 / restart-route games against native Solution, on one worker.

python -m scripts.r3_restart_study --confirmation CONF --r3 r3_soft.pth --out NEW
"""
import argparse
from hashlib import sha256
from importlib.util import find_spec
import json
from pathlib import Path

import numpy as np

from scripts import final_battle_compare as battle
from scripts.final_battle_select import OPPONENTS, SEATS, checked_run_files
from scripts.scoring import match_points_after_step

SEEDS = (7273116, 7273131, 7273141, 7273148, 7273149, 7273152)
LOSS = (7273148, "player_0")
SAVED = {(7273116, "player_1"), (7273131, "player_0"), (7273141, "player_1"),
         (7273149, "player_1"), (7273152, "player_1")}
HISTORICAL = {"v14": ("v14", "2da38e26a9c863a348632ab3b558eae1d83fc9a3a1b26b319ce505181c98955e",
                      "807963c7ebe4b278c7f85e72f8e71978c3438070311ef92e1e60871817e6d42c"),
              "r3": ("selective_movement", "5a7818a6333b036e476f11786f2013355e121cb1e6d8618f230d3b49a6630bf0",
                     "cb904ef4d18ddbb6f05afc7092ba2dd5c86d63724c0b6193eb244c78173c49fd")}
SEAM = "scripts/selective_advice_agent.py"
ADVISER_SEAM_SHA = "2659086c1b58963da910f9a22739eec8f52a7dfcc818692040f852112bd21ba8"


def inputs(args):
    games, manifests, pins = {}, {}, {}
    for arm, (name, h, m) in HISTORICAL.items():
        games[arm], manifest, seals = checked_run_files(args.confirmation / arm, name, range(7273100, 7273160), OPPONENTS)
        if (seals["games_sha256"], seals["manifest_sha256"]) != (h, m):
            raise ValueError("Wrong original confirmation panel")
        manifests[arm], pins[arm] = manifest, seals
    manifest = manifests["r3"]
    engine = Path(find_spec("luxai_s3").origin).parent
    for path, expected in manifest["sources"].items():  # the R3 manifest, including original V14
        if path.startswith("experiments/opponents/"):  # no Kaggle games in this study
            continue
        if battle.digest(battle.ROOT / path) != (ADVISER_SEAM_SHA if path == SEAM else expected):
            raise ValueError(f"Need original 0105658 with registered adviser method seam: {path}")
    if ({k:battle.digest(engine/k) for k in manifest["engine"]} != manifest["engine"]
            or battle.digest(battle.WEIGHTS) != manifest["weights"] or battle.digest(args.r3) != manifest["model"]):
        raise ValueError("Wrong engine, V14 or R3 checkpoint")
    flips = {(s, side) for (opp, s, side), r in games["r3"].items() if opp == "solution92"
             and r["result"] != games["v14"][opp,s,side]["result"]}
    if flips != SAVED | {LOSS} or games["r3"][("solution92", *LOSS)]["result"] != 0:
        raise ValueError("Historical selection differs")
    pins["study_sha256"] = {f:battle.digest(battle.ROOT/f) for f in
                            (SEAM, "scripts/r3_restart_route.py", "scripts/r3_restart_study.py")}
    pins.update(r3_model=manifest["model"], v14_model=manifest["weights"], engine=manifest["engine"])
    return games, pins


class Trace:
    def __init__(self, env, side):
        self.env, self.side = env, side
        self.team = int(side[-1])
        self.orders, self.matches = [], []
        self.first = None

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        self.before = obs[self.side]
        return obs, info

    def step(self, orders):
        self.orders.append(np.stack([orders[s] for s in SEATS]).astype("<i2"))
        result = self.env.step(orders)
        after, before = result[0][self.side], self.before
        t, m = int(before["steps"]), int(before["match_steps"])
        if t != len(self.orders) - 1 or m != t % 101:
            raise ValueError("Unexpected course clock")
        points = match_points_after_step(before, after, result[4])
        if self.first is None and points[self.team] > 0:
            self.first = m
        if m == 100:
            win = np.asarray(after["team_wins"]) - np.asarray(before["team_wins"])
            if tuple(win) not in ((1, 0), (0, 1)):
                raise ValueError("Expected an official match winner")
            self.matches.append(dict(points_ours=int(points[self.team]), points_rival=int(points[1-self.team]),
                                     won=int(win[self.team]), first_own_point=self.first))
            self.first = None
        self.before = after
        return result


def stream_hash(array):
    return sha256(np.ascontiguousarray(array, dtype="<i2").tobytes()).hexdigest()


def compare_streams(original, changed, potential, applied, team):
    if original.shape != (303, 2, 16, 3) or changed.shape != original.shape:
        raise ValueError("Need two complete native world-order streams")
    for stream, events, expect_applied in ((original, potential, False), (changed, applied, True)):
        for e in events:
            command = e["v14_world" if expect_applied else "r3_world"]
            if (e["applied"] != expect_applied or e["step"] < 101 or command == e["r3_world" if expect_applied else "v14_world"]
                    or stream[e["step"],team,e["uid"]].tolist() != command):
                raise ValueError("Recorded opportunity differs from the actual game order")
    first = min((e["step"] for e in applied), default=303)
    original_first = min((e["step"] for e in potential), default=303)
    if first != original_first or not np.array_equal(original[:first], changed[:first]):
        raise ValueError("Both players' histories must agree before the first intervention")
    if first < 303:
        if not np.array_equal(original[first,1-team], changed[first,1-team]):
            raise ValueError("Opponent diverged before observing the first intervention")
        uids = set(np.flatnonzero(np.any(original[first,team] != changed[first,team], axis=1)).tolist())
        e0 = {e["uid"]:e for e in potential if e["step"] == first}
        e1 = {e["uid"]:e for e in applied if e["step"] == first}
        if uids != e0.keys() or uids != e1.keys() or any(e0[u] != {**e1[u], "applied": False} for u in uids):
            raise ValueError("First effective change differs from the nominal change on the same state")
    return dict(equal_steps_before_first_change=first, first_actual_step=first if applied else None,
                match1_sha256=stream_hash(original[:101]), equal_prefix_sha256=stream_hash(original[:first]),
                r3_actions_sha256=stream_hash(original), restart_actions_sha256=stream_hash(changed))


def play(seed, side, actor, env, model, restore):
    actor.restore = restore
    trace = Trace(env, side)
    battle.evaluate.env = trace
    try:
        row = battle.evaluate(("selective_movement", "solution92", seed, side, model))
    finally:
        battle.evaluate.env = env
    if (len(trace.matches) != 3 or sum(m["won"] for m in trace.matches) != row["wins"]
            or sum(m["points_ours"] for m in trace.matches) != row["points"]
            or sum(m["points_rival"] for m in trace.matches) != row["opp_points"]):
        raise ValueError("Per-match measurements differ from final row")
    return dict(game=row, matches=trace.matches, opportunities=actor.route_events), np.asarray(trace.orders)


def run(args):
    games, pins = inputs(args)
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "manifest.json").write_text(json.dumps(pins, indent=2))
    model = str(args.r3.resolve())
    # Use exactly the published setup (including movement mode), changing only the class under test.
    old = battle.POLICIES["selective_movement"]
    try:
        battle.POLICIES["selective_movement"] = "scripts.r3_restart_route:RestartRouteAgent"
        battle.init_worker("selective_movement", model)
    finally:
        battle.POLICIES["selective_movement"] = old
    actor, env = battle.evaluate.agent, battle.evaluate.env
    summary, result_hashes = {}, {}
    try:
        for seed in SEEDS:
            for side in SEATS:
                key = ("solution92", seed, side)
                baseline, a = play(seed, side, actor, env, model, False)
                expected = games["r3"][key]
                if any(baseline["game"].get(k) != v for k, v in expected.items() if k != "secs"):
                    (args.out / f"{seed}_{side}_failed.json").write_text(json.dumps({"original": baseline, "expected": expected}))
                    raise ValueError(f"Original R3 failed historical reproduction for {seed}/{side}")
                variant, b = play(seed, side, actor, env, model, True)
                group = "original_loss" if (seed, side) == LOSS else "previous_rescue" if (seed, side) in SAVED else "opposite_seat"
                label = f"{seed}_{side}"
                arrays = args.out / (label + ".npz")
                np.savez_compressed(arrays, original=a, restart=b)
                report = dict(seed=seed, side=side, group=group, historical_r3=expected, historical_v14=games["v14"][key],
                              original=baseline, restart=variant, orders_sha256=battle.digest(arrays))
                try:
                    parity = compare_streams(a, b, baseline["opportunities"], variant["opportunities"], int(side[-1]))
                    closed = parity["equal_steps_before_first_change"] // 101
                    if baseline["matches"][:closed] != variant["matches"][:closed]:
                        raise ValueError("Completed matches differ before first reversion")
                    if not variant["opportunities"] and any(variant["game"][k] != v for k,v in expected.items() if k != "secs"):
                        raise ValueError("Game with no reversion differs from original outcome")
                    report["parity"] = parity
                except ValueError as error:
                    report["error"] = str(error)
                    (args.out / (label + "_failed.json")).write_text(json.dumps(report, allow_nan=False))
                    raise
                case_file = args.out / (label + ".json")
                case_file.write_text(json.dumps(report, allow_nan=False))
                result_hashes[case_file.name] = battle.digest(case_file)
                s = summary.setdefault(group, dict(games=0, original_wins=0, restart_wins=0, original_matches=0,
                                                   restart_matches=0, gained=0, lost=0, nominal=0, actual=0, effective_games=0))
                u, v = int(expected["result"]), int(variant["game"]["result"])
                for k, n in dict(games=1,original_wins=u,restart_wins=v,original_matches=expected["wins"],
                                 restart_matches=variant["game"]["wins"],gained=v>u,lost=u>v,
                                 nominal=len(baseline["opportunities"]),actual=len(variant["opportunities"]),
                                 effective_games=bool(variant["opportunities"])).items():
                    s[k] += n
                print(label, group, u, v, len(variant["opportunities"]), flush=True)
    finally:
        env.close()
    result = dict(groups=summary, case_files=result_hashes, rescued_original_loss=summary["original_loss"]["gained"]==1,
                  preserved_five_rescues=summary["previous_rescue"]["lost"]==0,
                  preserved_six_opposite_seats=summary["opposite_seat"]["lost"]==0)
    (args.out / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("confirmation", "r3", "out"):
        p.add_argument("--" + name, type=Path, required=True)
    run(p.parse_args())


if __name__ == "__main__":
    main()
