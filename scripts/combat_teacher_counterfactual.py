"""Three diagnostic whole-game comparisons on the 12 fixed teacher-advice maps.

python -m scripts.combat_teacher_counterfactual --data ADVICE_DIR --out NEW_DIR --workers 1
control, combat and movement execute as separate phases. Each row compares with
the original archive, and the control checks both original actors' recorded orders.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import multiprocessing as mp
from pathlib import Path
import random

import numpy as np

from agents.sherlock import geometry as geo
from agents.sherlock.imitation_agent import canonical_action
from agents.sherlock.main import Agent_x
from scripts import collect_combat_advice as data
from scripts import imitate
from scripts.par_eval import build_cfg, require_no_agent_errors

ARMS = ("control", "combat", "movement")
KEYS = [(seed, side) for seed in range(data.FIRST, data.FIRST + 12) for side in data.SIDES]


def native_order(row, position, energy, cfg, tiles):
    """World actions. Unknown tiles remain available. The engine clips off-board moves."""
    a, dx, dy = map(int, row)
    x, y = map(int, position)
    w, h = tiles.shape
    if a == geo.STAY:
        return True
    if a == geo.SAP:
        return (energy >= cfg["unit_sap_cost"] and max(abs(dx), abs(dy)) <= cfg["unit_sap_range"]
                and 0 <= x + dx < w and 0 <= y + dy < h)
    if not 1 <= a <= 4 or energy < cfg["unit_move_cost"]:
        return False
    nx, ny = x + int(geo.DIR_DX[a]), y + int(geo.DIR_DY[a])
    # Match JAX's tile lookup before clipping: -1 indexes the last tile;
    # a positive index beyond a dimension indexes its last tile.
    return tiles[min(nx, w - 1), min(ny, h - 1)] != 2


def live_ids(public, team):
    energy = np.asarray(public["units"]["energy"])[team].reshape(-1)
    return np.flatnonzero(np.asarray(public["units_mask"])[team] & (energy >= 0))


def substitute(actor, public, base, advice, arm, counts):
    """Edit a copy of V14's final world actions; update its per-unit canonical records."""
    if arm == "control" or int(public["match_steps"]) == 0:
        return base
    if arm not in ARMS:
        raise ValueError(arm)
    ctx = actor._prev_ctx
    played = base.copy()
    team = actor.team_id
    energies = np.asarray(public["units"]["energy"])[team].reshape(-1)
    positions = np.asarray(public["units"]["position"])[team]
    tiles = np.asarray(public["map_features"]["tile_type"])
    changed = set()
    for uid in live_ids(public, team):
        before, after = int(base[uid, 0]), int(advice[uid, 0])
        combat = before == geo.SAP or after == geo.SAP
        if (arm == "combat") != combat or np.array_equal(base[uid], advice[uid]):
            continue
        if not native_order(advice[uid], positions[uid], energies[uid], actor.env_cfg, tiles):
            counts["rejected_orders"] += 1
            continue
        changed.add(int(uid))
        played[uid] = advice[uid]
        a, dx, dy = canonical_action(advice[uid], actor.belief.mirrored)
        actor._prev_actions[uid] = a
        old_hits = actor._sap_hits.pop(uid, 0)
        actor._sap_unknown.discard(uid)
        new_hits = 0
        if a == geo.SAP:
            target = ctx["ally_pos"][uid] + (dx, dy)
            visible = ctx["enemy_coords"][ctx["enemy_energies"] >= 0]
            new_hits = int(np.sum(np.all(np.abs(visible-target) <= 1, axis=1)))
            actor._sap_hits[uid] = new_hits
            world_target = positions[uid] + advice[uid, 1:]
            if not public["sensor_mask"][tuple(world_target)]:
                actor._sap_unknown.add(uid)
        actor.ep_stats["sap_attempts"] += int(after == geo.SAP) - int(before == geo.SAP)
        actor.ep_stats["sap_hits_est"] += int(new_hits > 0) - int(old_hits > 0)
        kind = ("retarget" if before == after == geo.SAP else "new_sap" if after == geo.SAP
                else "skip_sap" if before == geo.SAP else "movement")
        counts[kind] += 1
    if changed:
        counts["changed_steps"] += 1
        counts["changed_unit_orders"] += len(changed)
        if actor.cfg.dodge_verify or actor.cfg.dodge_distrust > 0:
            from agents.sherlock.opp_model import predict_sol92_saps
            # A predicted shooter contributes >= .5, the stock reporting threshold.
            shape = actor._sap_shape() if actor.cfg.dodge_shape else "man"
            predicted = {uid for _, uid in predict_sol92_saps(ctx, actor.belief, shape=shape)}
            actor._pred_pending = [p for p in actor._pred_pending if p[0] not in changed]
            for uid in sorted(changed & predicted):
                a = actor._prev_actions[uid]
                if a in (geo.STAY, geo.SAP):
                    x, y = map(int, ctx["ally_pos"][uid])
                    actor._pred_pending.append((uid, x, y, float(energies[uid]), a == geo.SAP))
        if actor.cfg.dodge_shape:
            actor._shape_pending.clear()
            actor._record_shapes(ctx)
    return played


class CounterfactualAgent(Agent_x):
    def _act(self, step, obs):
        base = super()._act(step, obs)
        # _act_est.remember now receives the true action once, including for player 1.
        return self.finish_step(step, obs, base)


class Reference:
    def __init__(self, path, seed, side, binding):
        data.check_archive(path, seed, side, binding)
        self.sha = data.file_sha(path)
        with np.load(path, allow_pickle=False) as z:
            self.meta = json.loads(z["meta"].item())
            self.rows = {}
            frame = z["global_step"][z["step"]]
            base = np.column_stack([z[k] for k in ("base_act", "base_sdx", "base_sdy")])
            advice = np.column_stack([z[k] for k in ("act", "sdx", "sdy")])
            for i, (step, uid) in enumerate(zip(frame, z["uid"])):
                self.rows.setdefault(int(step), {})[int(uid)] = (base[i], advice[i])

    def compare(self, step, public, actor, base, advice, counts):
        exp = self.rows.get(step, {})
        live = set(live_ids(public, actor.team_id)) if int(public["match_steps"]) else set()
        counts["unit_presence_differences"] += len(live.symmetric_difference(exp))
        for uid in live.intersection(exp):
            counts["compared_live_orders"] += 1
            for name, actions, old in (("v14", base, exp[uid][0]), ("teacher", advice, exp[uid][1])):
                current = canonical_action(actions[uid], actor.belief.mirrored)
                counts[name + "_order_differences"] += int(not np.array_equal(current, old))


def game(env, actor, opp, teacher, seed, side, arm, ref):
    other = data.SIDES[1 - data.SIDES.index(side)]
    for p, seat in ((actor, side), (opp, other), (teacher, side)):
        if hasattr(p, "new_game"):
            p.new_game(seat)
    random.seed(seed)
    np.random.seed(seed % 2**32)
    obs, info = env.reset(seed=seed)
    for p in (actor, opp, teacher):
        p.set_env_cfg(info["params"])
    counts, trail = Counter(), sha256()

    def finish(step, public, base):
        # Same order as data.play: V14, opponent, shadow teacher, env, teacher sync.
        nonlocal opposing
        opposing = opp.act(step, obs[other])
        advice = teacher.act(step, public)
        if arm == "control":
            ref.compare(step, public, actor, base, advice, counts)
        return substitute(actor, public, base, advice, arm, counts)

    actor.finish_step = finish
    for step in range(data.STEPS):
        opposing = None
        if int(obs[side]["steps"]) != step:
            raise ValueError("Unexpected observation step")
        played = actor.act(step, obs[side])
        require_no_agent_errors(actor, opp)
        require_no_agent_errors(actor, teacher)
        if opposing is None:
            raise RuntimeError("Missing final V14 decision")
        trail.update(np.asarray(played, dtype="<i2").tobytes())
        obs, _, term, trunc, _ = env.step({side: played, other: opposing})
        teacher.remember_played_actions(played)
        if (bool(term[side]) or bool(trunc[side])) != (step == data.STEPS - 1):
            raise ValueError("Expected 303 course steps")
    actor.finish_step = None
    team = data.SIDES.index(side)
    wins = np.asarray(obs[side]["team_wins"])
    ours, theirs = int(wins[team]), int(wins[1-team])
    expected = [ref.meta["our_wins"], ref.meta["opp_wins"]]
    out = dict(arm=arm, seed=seed, side=side, opponent=data.opponent_for(seed), steps=data.STEPS,
               our_wins=ours, opp_wins=theirs, result=float(ours>theirs)+.5*float(ours==theirs),
               archived_end_wins=expected, end_matches_archive=[ours,theirs] == expected,
               archived_sha256=ref.sha, played_world_sha256=trail.hexdigest(), counts=dict(counts))
    if arm == "control":
        out["control_reproduced"] = out["end_matches_archive"] and not any(counts[k] for k in (
            "unit_presence_differences", "v14_order_differences", "teacher_order_differences"))
    return out


def write_once(path, raw):
    data.publish(path, lambda f: f.write(raw))
    if path.read_bytes() != raw:
        raise ValueError(f"Different existing result: {path}")


def worker(job):
    from scripts.experiment import limit_threads
    limit_threads()
    from scripts.kaggle3_opponent import Kaggle3Opponent
    from luxai_s3.wrappers import LuxAIS3GymEnv
    arm, keys, datadir, out, binding, stamp, controls = job
    actor = CounterfactualAgent("player_0", agent_path=str(imitate.V14),
                                cfg=build_cfg(str(imitate.V14), []), train=False, seed=0)
    actor.set_to_eval_mode()
    actor.autosave_on_terminate = False
    if len(actor.extra_q) != 35:
        raise ValueError("Expected 36 V14 networks")
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        for seed, side in keys:
            ref = Reference(datadir / data.filename(seed, side), seed, side, binding)
            opp = imitate.make_player(data.opponent_for(seed), data.SIDES[1-data.SIDES.index(side)])
            teacher = Kaggle3Opponent(side)
            if isinstance(opp, Kaggle3Opponent) and teacher.base.Global is opp.base.Global:
                raise ValueError("Opponent and teacher share history")
            row = game(env, actor, opp, teacher, seed, side, arm, ref)
            row.update(stamp)
            if arm != "control":
                control = controls[seed, side]
                if control["archived_sha256"] != ref.sha:
                    raise ValueError("Reference changed after control")
                row["control_reproduced"] = control["control_reproduced"]
                row["control_end_wins"] = [control["our_wins"], control["opp_wins"]]
            if not row["control_reproduced"]:
                row["warning"] = "Control failed to reproduce archived V14 game or teacher decisions"
            write_once(out / arm / f"{seed}_{side}.jsonl", data.canonical_json(row) + b"\n")
            print(arm, seed, side, row["our_wins"], row["opp_wins"], row.get("warning",""), flush=True)
    finally:
        env.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--workers", type=int, choices=(1, 2), default=1)
    ap.add_argument("--arm", choices=("all", *ARMS), default="all")
    args = ap.parse_args()
    binding = data.file_sha(args.data / "protocol.json")
    stamp = dict(source_sha256=data.file_sha(Path(__file__)), original_protocol=binding,
                 current_protocol=sha256(data.canonical_json(data.protocol()) + b"\n").hexdigest())
    args.out.mkdir(parents=True, exist_ok=True)
    write_once(args.out / "study.json", data.canonical_json(dict(**stamp, arms=ARMS, keys=KEYS)) + b"\n")
    controls = {}
    phases = ARMS if args.arm == "all" else (args.arm,)
    for arm in phases:
        if arm != "control" and not controls:
            with (args.out / "control.jsonl").open() as f:
                rows = [json.loads(line) for line in f]
            controls = {(r["seed"],r["side"]):r for r in rows}
            if len(rows) != len(KEYS) or set(controls) != set(KEYS):
                raise ValueError("A complete separate control phase is required")
        directory = args.out / arm
        directory.mkdir(exist_ok=True)
        pending = [k for k in KEYS if not (directory / f"{k[0]}_{k[1]}.jsonl").exists()]
        n = min(args.workers, len(pending))
        jobs = [(arm, pending[i::n], args.data, args.out, binding, stamp, controls) for i in range(n)]
        if n == 1:
            worker(jobs[0])
        elif jobs:
            with mp.get_context("spawn").Pool(n) as pool:
                pool.map(worker, jobs)
        raw = []
        for seed, side in KEYS:
            line = (directory / f"{seed}_{side}.jsonl").read_bytes()
            row = json.loads(line)
            if (row["arm"],row["seed"],row["side"]) != (arm,seed,side) or any(row.get(k)!=v for k,v in stamp.items()):
                raise ValueError("Different result identity")
            if row["archived_sha256"] != data.file_sha(args.data / data.filename(seed, side)):
                raise ValueError("Changed reference archive")
            if arm == "control":
                controls[seed, side] = row
            raw.append(line)
        write_once(args.out / (arm + ".jsonl"), b"".join(raw))


if __name__ == "__main__":
    main()
