"""Check frozen posterior scores and candidate command parity on disjoint, unmodified V16 prefixes."""
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import sys

import jax
import jax.numpy as jnp
import numpy as np
import torch
from luxai_s3.params import env_params_ranges
from luxai_s3.wrappers import LuxAIS3GymEnv

from kandidat import COORD, DELTA, HERE, MIRROR, PACKAGE, ROOT, Scout, create, feature_columns
sys.path.insert(0, str(ROOT))
from scripts.common import make_opponent
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent

NAMES = ("flat", "flat_visibility", "learned_visibility", "learned_full")
OUTPUT = Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/zielschaetzer")


def sensor(seed):
    key, _ = jax.random.split(jax.random.key(seed))
    for name, values in env_params_ranges.items():
        key, sub = jax.random.split(key)
        if name == "unit_sensor_range":
            return jax.random.choice(sub, jnp.array(values))
    raise ValueError("Missing public sensor range")


def scores(policy, actual, step):
    e = policy.evidence
    loc = e.density(step, 50, use_points=False)
    flat = np.where(COORD.sum(1) == 23, 1, 2)/576
    actual_id = np.flatnonzero((COORD == actual).all(1)).item()
    res = {}
    for label, w in zip(NAMES, (flat, flat*loc, e.prior*loc, e.location_weights(step, 50))):
        p = w/w.sum()
        if p[actual_id] <= 0:
            raise ValueError("Public negative evidence contradicts actual first-pair label")
        # Fixed 75 of 300 representatives, fractional tie credit.
        fraction = np.clip((75 - (p > p[actual_id]).sum()) / (p == p[actual_id]).sum(), 0, 1)
        res[label] = {"logloss": float(-np.log(p[actual_id])), "top_quarter": float(fraction)}
    return res


def run_seat(env, seed, team, duplicate):
    side, other = f"player_{team}", f"player_{1-team}"
    policy = create(side)
    control = r3_package_agent(side, PACKAGE) if duplicate else None
    rival = make_opponent("solution92", other)
    policy.new_game(side)
    if control:
        control.new_game(side)
    if hasattr(rival, "new_game"):
        rival.new_game(other)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    obs, info = env.reset(seed=seed)
    if info["params"]["unit_sensor_range"] != 1:
        raise ValueError("Invalid validation stratum")
    for agent in (policy, control, rival):
        if agent is not None:
            agent.set_env_cfg(info["params"])
    true = np.array(env.state.relic_nodes[0])
    if true.sum() >= 24:
        true = 23-true[::-1]
    actual = []
    raw_act = policy.base.act
    def capture(step, obs):
        cmd = raw_act(step, obs)
        student = policy.base._imitation
        actual.append((cmd.copy(), student._prev_actions.copy(), student._sap_hits.copy()))
        return cmd
    policy.base.act = capture
    row = {"seed": seed, "side": side, "snapshots": [], "changes": 0, "with_plan": 0, "duplicate_commands": 0,
           "ineligible": 0, "changed_ids": [], "memory_verified": 0, "prefix_commands": 81, "first_seen": None, "first_point": None}
    for step in range(81):
        o = obs[side]
        out = policy.act(step, o)
        original, old_actions, old_sap = actual.pop()
        if control:
            np.testing.assert_array_equal(control.act(step, o), original)
            row["duplicate_commands"] += len(original)
        observed = np.any(o["relic_nodes_mask"])
        if observed and row["first_seen"] is None:
            row["first_seen"] = step
        if o["team_points"][team] and row["first_point"] is None:
            row["first_point"] = step
        eligible = 12 <= step and row["first_seen"] is None and row["first_point"] is None
        diff = np.flatnonzero(np.any(out != original, axis=1))
        if not eligible:
            row["ineligible"] += 1
            if len(diff):
                raise ValueError("Out-of-scope change")
        if policy.last is not None:
            row["with_plan"] += 1
        if len(diff):
            if len(diff) != 1 or tuple(policy.last) != (int(diff[0]), int(out[diff[0], 0])):
                raise ValueError("Invalid changed-ship attribution")
            uid = diff.item()
            ctx, ids, feat, masks, _, _, pos = policy.base._imitation.last_fz
            k = list(ids).index(uid)
            cmd = int(out[uid, 0])
            canonical = int(MIRROR[cmd]) if team else cmd
            after = pos[k]+DELTA[canonical]
            names, threat = feature_columns()
            if not (1 <= cmd <= 4 and out[uid, 1:].tolist() == [0, 0] and masks[k, canonical] and
                    original[uid, 0] <= 4 and (feat[k, names] == 0).all() and feat[k, threat] == 0 and
                    ctx["ally_ene"][uid] >= max(10, 3*ctx["move_cost"]) and
                    (after >= 0).all() and (after < 24).all()):
                raise ValueError("Invalid or protected unit decision")
            if uid not in row["changed_ids"]:
                row["changed_ids"].append(uid)
            student = policy.base._imitation
            if (len(row["changed_ids"]) != 1 or uid != policy.ship or
                    int(student._prev_actions[uid]) != canonical or uid in student._sap_hits or
                    (student.param_est._prev is not None and not np.array_equal(student.param_est._prev["act"], out))):
                raise ValueError("Scout changed identity or kept a stale command")
            row["memory_verified"] += 1
            row["changes"] += 1
        # Only V16 actions are executed in this shadow study. Retain them for V16's next observation.
        policy.base._imitation._prev_actions = old_actions
        policy.base._imitation._sap_hits = old_sap
        policy.base._imitation.param_est.record_played_actions(original)
        if eligible and step in (20, 35, 50, 65):
            row["snapshots"].append({"step": step, "scores": scores(policy, true, step)})
        if step < 80:
            enemy = rival.act(step, obs[other])
            obs, _, term, trunc, _ = env.step({side: original, other: enemy})
            if term[side] or trunc[side]:
                raise ValueError("Unexpected terminal transition")
    if row["changes"] != policy.changes:
        raise ValueError("Changes counter drift")
    require_no_agent_errors(policy.base, rival)
    if control:
        require_no_agent_errors(control, rival)
    return row


def main():
    if os.getenv("PYTHONHASHSEED") != "0":
        raise ValueError("Use PYTHONHASHSEED=0")
    limit_threads()
    seeds = np.arange(161180000, 161181000, dtype=np.int32)
    chosen = seeds[np.asarray(jax.jit(jax.vmap(sensor))(seeds)) == 1][:32].tolist()
    source = {p.name: sha256(p.read_bytes()).hexdigest() for p in (
        HERE/"kandidat.py", HERE/"lernen.py", HERE/"ort.json", HERE/"PLAN.md", Path(__file__), PACKAGE)}
    sig = sha256(json.dumps(source, sort_keys=True).encode()).hexdigest()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rows = []
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        for seed in chosen:
            for team in (0, 1):
                target = OUTPUT/f"{seed}-{team}-{sig[:12]}.json"
                if not target.exists():
                    row = run_seat(env, seed, team, seed == chosen[0])
                    row["source"] = sig
                    tmp = target.with_suffix(".tmp")
                    tmp.write_text(json.dumps(row, allow_nan=False)+"\n")
                    tmp.replace(target)
                row = json.loads(target.read_bytes())
                if row["source"] != sig or row["seed"] != seed or row["side"] != f"player_{team}":
                    raise ValueError("Prefix cache mismatch")
                rows.append(row)
            print(f"{len(rows)} / 64 V16 prefixes", flush=True)
    finally:
        env.close()
    snaps = [s for r in rows for s in r["snapshots"]]
    result = {name: {key: float(np.mean([s["scores"][name][key] for s in snaps])) for key in ("logloss", "top_quarter")} for name in NAMES}
    totals = {k: sum(r[k] for r in rows) for k in ("changes", "with_plan", "ineligible", "duplicate_commands", "prefix_commands", "memory_verified")}
    group_changes = {str(t): sum(r["changes"] for r in rows if r["side"] == f"player_{t}") for t in (0, 1)}
    eligible = (result["learned_full"]["logloss"] < result["flat_visibility"]["logloss"] and all(group_changes.values()))
    summary = dict(eligible=bool(eligible), sources=source, first_seed=chosen[0], last_seed=chosen[-1], maps=len(chosen),
                   seats=len(rows), snapshots=len(snaps), by_step=dict(Counter(s["step"] for s in snaps)), totals=totals,
                   changes_by_side=group_changes, quality=result)
    (HERE/"sichtpruefung.json").write_text(json.dumps(summary, indent=2)+"\n")
    import gzip
    with (HERE/"beobachtungen.jsonl.gz").open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as f:
            f.write("".join(json.dumps(row, sort_keys=True)+"\n" for row in rows).encode())
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
