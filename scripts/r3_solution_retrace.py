"""Reproduce three specific Solution cases on a clean 0105658 source tree (three games per arm).

    python -m scripts.r3_solution_retrace --arm v14 --confirmation CONF --out NEW/v14
    python -m scripts.r3_solution_retrace --arm r3 --confirmation CONF --r3 r3_soft.pth --out NEW/r3

The V14 orders inside each R3 trace are the actual pre-advice plan on that R3 trajectory.
"""
import argparse
from collections import Counter
from importlib.util import find_spec
import json
import sys
from pathlib import Path

import numpy as np

from scripts import final_battle_compare as battle
from scripts.final_battle_select import OPPONENTS, checked_run_files
from scripts.r3_solution_observation import Observation

CASES = ((7273148, "player_0"), (7273148, "player_1"), (7273116, "player_1"))
PINS = {
    "v14": ("v14", "2da38e26a9c863a348632ab3b558eae1d83fc9a3a1b26b319ce505181c98955e",
            "807963c7ebe4b278c7f85e72f8e71978c3438070311ef92e1e60871817e6d42c"),
    "r3": ("selective_movement", "5a7818a6333b036e476f11786f2013355e121cb1e6d8618f230d3b49a6630bf0",
           "cb904ef4d18ddbb6f05afc7092ba2dd5c86d63724c0b6193eb244c78173c49fd"),
}


def historical(args):
    name, rows_sha, manifest_sha = PINS[args.arm]
    rows, manifest, hashes = checked_run_files(args.confirmation / args.arm, name, range(7273100, 7273160), OPPONENTS)
    if hashes != {"games_sha256": rows_sha, "manifest_sha256": manifest_sha}:
        raise ValueError("Historical confirmation rows or manifest differ from registered bytes")
    engine = Path(find_spec("luxai_s3").origin).parent
    if {k: battle.digest(engine / k) for k in manifest["engine"]} != manifest["engine"]:
        raise ValueError("Original Lux engine required")
    # This diagnostic only instantiates the original Solution opponent.
    for path, sha in manifest["sources"].items():
        if path.startswith("experiments/opponents/"):
            continue
        if battle.digest(battle.ROOT / path) != sha:
            raise ValueError(f"Need the original 0105658 implementation: {path}")
    model = battle.digest(args.r3) if args.r3 else None
    if model != manifest["model"] or battle.digest(battle.WEIGHTS) != manifest["weights"]:
        raise ValueError("Original V14/R3 weights required")
    return rows, hashes


def endpoint(row, pos, energy, cost, tiles):
    """Intent in world coordinates, using only public tiles and the engine's movement lookup."""
    direction = int(row[0])
    if direction not in range(1, 5) or energy < cost:
        return tuple(map(int, pos))
    dx, dy = ((0, -1), (1, 0), (0, 1), (-1, 0))[direction - 1]
    x, y = int(pos[0]) + dx, int(pos[1]) + dy
    w, h = tiles.shape
    if tiles[min(x, w - 1), min(y, h - 1)] == 2:
        return tuple(map(int, pos))
    return max(0, min(x, w - 1)), max(0, min(y, h - 1))


def changes(actor, obs, base, played, known):
    from agents.sherlock.geometry import mirror_xy

    team = actor.team_id
    pos = np.asarray(obs["units"]["position"])[team]
    energy = np.asarray(obs["units"]["energy"])[team].reshape(-1)
    alive = np.asarray(obs["units_mask"])[team] & (energy >= 0)
    tiles = np.asarray(obs["map_features"]["tile_type"])
    events = []
    for uid in map(int, np.flatnonzero(np.any(base != played, axis=1))):
        if not alive[uid] or int(base[uid, 0]) == 5 or int(played[uid, 0]) == 5:
            raise ValueError("Unexpected non-movement or inactive intervention")
        xy = tuple(map(int, pos[uid]))
        canonical = mirror_xy(*xy, *tiles.shape) if actor.belief.mirrored else xy
        holder = bool(known[xy] and actor._prev_ctx["first_on_tile"].get(canonical) == uid)
        before, after = (endpoint(orders[uid], xy, energy[uid], actor.env_cfg["unit_move_cost"], tiles)
                         for orders in (base, played))
        events.append(dict(uid=uid, origin=xy, energy=int(energy[uid]), confirmed_origin=bool(known[xy]),
                           holder=holder, v14_world=base[uid].tolist(), played_world=played[uid].tolist(),
                           v14_intended=before, r3_intended=after, r3_intended_known=bool(known[after]),
                           leaves_holder_v14_would_keep=bool(holder and before == xy and after != xy)))
    return events


class TraceEnv:
    def __init__(self, env, actor, side):
        self.env, self.actor, self.side = env, actor, side
        self.team = int(side[-1])
        self.observation = Observation(self.team)
        self.pending = None
        self.events = []
        self.counts = [Counter() for _ in range(3)]

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        self.before = obs[self.side]
        return obs, info

    def step(self, orders):
        from agents.sherlock.geometry import mirror_map

        public = self.before
        step, mstep = int(public["steps"]), int(public["match_steps"])
        known = self.actor.belief.point_tiles
        if self.actor.belief.mirrored:
            known = mirror_map(known)
        events = []
        if self.pending is not None:
            s, before, played = self.pending
            if s != step or not np.array_equal(played, orders[self.side]):
                raise ValueError("Advice capture differs from submitted world orders")
            events = changes(self.actor, public, before, played, known)
            self.pending = None
        elif hasattr(self.actor, "selective_counts"):
            raise ValueError("Missing R3 advice call")
        result = self.env.step(orders)
        after = result[0][self.side]
        self.observation.record(public, after, result[4], known)
        for e in events:
            uid = e["uid"]
            active = (bool(after["units_mask"][self.team][uid])
                      and np.asarray(after["units"]["energy"])[self.team].reshape(-1)[uid] >= 0)
            e["next_active_world"] = (np.asarray(after["units"]["position"])[self.team, uid].tolist()
                                      if active and int(after["match_steps"]) != 0 else None)
            e.update(global_step=step, match_step=mstep, match=step // 101 + 1)
            count = self.counts[step // 101]
            count["changed_orders"] += 1
            count["on_confirmed_origin"] += int(e["confirmed_origin"])
            count["holder"] += int(e["holder"])
            count["leaves_holder_v14_would_keep"] += int(e["leaves_holder_v14_would_keep"])
        self.events.extend(events)
        self.before = after
        return result


def reproduce(arm, model, seed, side, expected, hashes):
    name = PINS[arm][0]
    actor, native = battle.evaluate.agent, battle.evaluate.env
    trace = TraceEnv(native, actor, side)
    if arm == "r3":
        advise = actor._advise
        def capture(step, public, base):
            if trace.pending is not None:
                raise ValueError("More than one R3 advice call on one engine step")
            original = base.copy()
            played = advise(step, public, base)
            trace.pending = step, original, played.copy()
            return played
        actor._advise = capture
    battle.evaluate.env = trace
    try:
        actual = battle.evaluate((name, "solution92", seed, side, model))
    finally:
        battle.evaluate.env = native
        if arm == "r3":
            del actor._advise
    differences = {k: [v, actual.get(k)] for k, v in expected.items() if k != "secs" and actual.get(k) != v}
    if arm == "r3" and len(trace.events) != actual["study"].get("changed_unit_orders", 0):
        raise ValueError("Changed-unit events do not equal the original R3 counter")
    observation = trace.observation.report()
    team = trace.team
    score = observation["team_points_total"]
    won = sum(m["final"]["own_won"] for m in observation["matches"])
    if [score[team], score[1-team], won] != [actual["points"], actual["opp_points"], actual["wins"]]:
        raise ValueError("Recorded matches differ from the whole game score")
    return dict(arm=arm, seed=seed, side=side, original_files=hashes, game=actual, historical=expected,
                reproduced=not differences, differences=differences, observation=observation,
                first_same_state_change=trace.events[0] if trace.events else None,
                interventions_by_match=trace.counts, changed_orders=trace.events)


def compare(reference_dir, candidate_dir):
    cases = []
    for seed, side in CASES:
        item = {"seed": seed, "side": side, "matches": []}
        reports = {}
        for arm, directory in (("v14", reference_dir), ("r3", candidate_dir)):
            path = directory / f"{seed}_{side}.json"
            report = json.loads(path.read_text())
            if (report["arm"], report["seed"], report["side"], report["reproduced"],
                    report["original_files"]["games_sha256"]) != (arm, seed, side, True, PINS[arm][1]):
                raise ValueError(f"Wrong or unreproduced case: {path}")
            reports[arm] = report
        for i in range(3):
            match = {}
            for arm, report in reports.items():
                obs = report["observation"]
                m = obs["matches"][i]
                ours = obs["team"]
                points = m["final"]["team_points"]
                match[arm] = dict(own_points=points[ours], rival_points=points[1-ours], won=m["final"]["own_won"],
                                  decided_by=m["final"]["decided_by"], confirmation=m["first_confirmed"],
                                  first_scored=m["first_own_point_gain"], occupied=m["first_known_occupied_after"],
                                  uid_departures=m["summary"]["plausible_uid_departures"],
                                  sections={key: {k: v[k] for k in ("mean_active_units", "mean_team_active_energy",
                                                                    "plausible_uid_departures", "known_occupied_cell_steps")}
                                            for key, v in m["sections"].items()})
            item["matches"].append(match)
        cand = reports["r3"]
        item["first_same_state_change"] = cand["first_same_state_change"]
        item["interventions_by_match"] = cand["interventions_by_match"]
        item["first_holder_departure"] = next((e for e in cand["changed_orders"] if e["leaves_holder_v14_would_keep"]), None)
        cases.append(item)
    return {"cases": cases, "interpretation": "Each intervention compares both commands on one R3 observation. "
            "Match outcomes and phase totals compare different played histories; they do not isolate an intervention."}


def main():
    if sys.argv[1:2] == ["compare"]:
        p = argparse.ArgumentParser(description="Read and pair the six reproduced case files.")
        p.add_argument("--v14", type=Path, required=True)
        p.add_argument("--r3", type=Path, required=True)
        args = p.parse_args(sys.argv[2:])
        print(json.dumps(compare(args.v14, args.r3), indent=2, allow_nan=False))
        return
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--arm", choices=tuple(PINS), required=True)
    p.add_argument("--r3", type=Path)
    p.add_argument("--confirmation", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    if bool(args.r3) != (args.arm == "r3"):
        p.error("--r3 is required only for the R3 arm")
    rows, hashes = historical(args)
    args.out.mkdir(parents=True, exist_ok=False)
    model = str(args.r3.resolve()) if args.r3 else None
    battle.init_worker(PINS[args.arm][0], model)
    try:
        for seed, side in CASES:
            report = reproduce(args.arm, model, seed, side, rows["solution92", seed, side], hashes)
            with (args.out / f"{seed}_{side}.json").open("x") as out:
                json.dump(report, out, allow_nan=False, separators=(",", ":"))
            if not report["reproduced"]:
                raise RuntimeError(f"{seed}/{side}: historical mismatch {report['differences']}")
            print(seed, side, report["game"]["result"], "reproduced", flush=True)
    finally:
        battle.evaluate.env.close()


if __name__ == "__main__":
    main()
