"""Verify full public decision-prefix parity independently of the frozen branch collector."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import sys

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from luxai_s3.wrappers import LuxAIS3GymEnv
from scripts.common import make_opponent
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.scoring import match_points_after_step
from steuern import AntiStall, MIRROR

RAW = Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/standsuche/train")
CASES = ((0, 161500001, 0), (2, 161500008, 0), (3, 161500012, 1),
         (4, 161500013, 0), (5, 161500015, 1), (6, 161500016, 0))
FULL_THREADS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS")


def require(test, message):
    if not test:
        raise ValueError(message)


def same(got, expected, context):
    a, b = np.asarray(got), np.asarray(expected)
    require(a.dtype == b.dtype and a.shape == b.shape and a.tobytes() == b.tobytes(),
            f"Byte mismatch at {context}")


def public_leaves(tree, path=()):
    if isinstance(tree, dict):
        return {key: value for k in sorted(tree)
                for key, value in public_leaves(tree[k], path + (k,)).items()}
    return {path: np.asarray(tree).copy()}


def add_digest(h, leaves):
    for path, data in sorted(leaves.items()):
        header = json.dumps([list(path), data.dtype.str, list(data.shape)], separators=(",", ":")).encode()
        h.update(len(header).to_bytes(4, "big"))
        h.update(header)
        content = data.tobytes()
        h.update(len(content).to_bytes(8, "big"))
        h.update(content)


def chosen(folder):
    rows = sorted((json.loads(p.read_text()) for p in folder.glob("*.json")), key=lambda r: r["index"])
    prefix = [r for r in rows if r["index"] <= CASES[-1][0]]
    require([r["index"] for r in prefix] == list(range(7)), "Incomplete deterministic seven-map prefix")
    present = [(r["index"], r["seed"], r["team"]) for r in prefix if r["event"] is not None]
    require(tuple(present) == CASES, "Preselected six first event maps differ")
    cases = [r for r in prefix if r["event"] is not None]
    for r in cases:
        for name, expected in r["files"].items():
            require(sha256((ROOT / name).read_bytes()).hexdigest() == expected,
                    f"Frozen branch source differs: {name}")
        require(r["original"]["changes"] == 0 and r["event"]["x"].keys() == r["trials"].keys(),
                "Incomplete original record")
    return cases


def run_prefix(env, archived, direction, reference=None):
    team, seed = archived["team"], archived["seed"]
    side, other = f"player_{team}", f"player_{1-team}"
    stop = archived["event"]["step"]
    uid = archived["event"]["uid"]
    player = AntiStall(side, force=direction)
    rival = make_opponent("solution92", other)
    for actor, seat in ((player, side), (rival, other)):
        if hasattr(actor, "new_game"):
            actor.new_game(seat)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    obs, info = env.reset(seed=seed)
    require(info["params"]["unit_sensor_range"] == 1, "Wrong real map stratum")
    for actor in (player, rival):
        if hasattr(actor, "set_env_cfg"):
            actor.set_env_cfg(info["params"])
    native_act = player.base.act
    proposals = []
    def capture(*args, **kwargs):
        original = native_act(*args, **kwargs)
        proposals.append(original.copy())
        return original
    player.base.act = capture
    old_anchor = sha256()
    full = sha256()
    trajectory = []
    actual_idle = 0
    previous_position = None
    leaves_count = 0
    for t in range(stop + 1):
        own = obs[side]
        require(int(own["match_steps"]) == t and int(own["steps"]) == t, "Wrong match chronology")
        full_obs = public_leaves(obs)
        require({k[0] for k in full_obs} == {side, other}, "Incomplete player observations")
        require(player.event is None, "Early or duplicated decision")
        played = player.act(t, own)
        enemy = rival.act(t, obs[other])
        require(len(proposals) == t + 1, "Did not obtain exactly one original V16 proposal")
        original = proposals[-1]
        require(original.shape == (16, 3) and enemy.shape == (16, 3), "Malformed game commands")
        leaves_count += len(full_obs)
        add_digest(full, full_obs)
        add_digest(full, {("original-V16",): original, ("opponent",): enemy})
        for a in (own["units"]["position"], own["units"]["energy"], own["sensor_mask"], enemy):
            old_anchor.update(np.asarray(a).tobytes())
        if t < stop:
            require(player.event is None, "Original archived branch point moved earlier")
            same(played, original, f"{seed}/{t}/actual equals original")
            old_anchor.update(played.tobytes())
            add_digest(full, {("own-played",): played})
        else:
            require(player.event == archived["event"], "Features/eligible directions differ from archived event")
            require(old_anchor.hexdigest() == archived["anchor"], "Original collector's prefix hash differs")
            require(not np.any(own["relic_nodes_mask"]) and int(own["team_points"][team]) == 0,
                    "First own credit or relic preceded intervention")
            require(int(original[uid, 0]) == 0 and actual_idle >= 3, "Fewer than three executed stationary commands")
            require(bool(own["units_mask"][team, uid]), "Selected ship is no longer alive")
            observed_position = np.asarray(own["units"]["position"])[team, uid]
            canonical = 23 - observed_position[::-1] if team else observed_position
            energy = float(np.asarray(own["units"]["energy"])[team].reshape(-1)[uid])
            require(energy == archived["event"]["energy"] and energy >= max(45, 8 * info["params"]["unit_move_cost"]),
                    "Selected energy does not match archived public data")
            require(np.array_equal(canonical, archived["event"]["pos"])
                    and np.array_equal(previous_position, observed_position),
                    "Changed public position of the stationary ship")
            require(player.history.stays[uid] == actual_idle + 1 == archived["event"]["idle"],
                    "Publicly reconstructed executed STAY streak differs")
            teammates = np.arange(16) != uid
            same(played[teammates], original[teammates], f"{seed}/{t}/15 simultaneous teammate commands")
            add_digest(full, {("own-15",): played[teammates]})
            if direction:
                world = int(MIRROR[direction]) if team else direction
                require(np.array_equal(played[uid], [world, 0, 0]) and player.changes == 1,
                        "Chosen legal world direction differs")
                ctx, ids, _, mask, _, _, _ = player.base._imitation.last_fz
                require(bool(mask[list(ids).index(uid), direction]), "Original public move mask rejected direction")
            else:
                same(played, original, f"{seed}/{t}/control")
                require(player.changes == 0, "Original control intervened")
        if reference is None:
            trajectory.append((full_obs, original.copy(), enemy.copy(), played.copy()))
        else:
            expected_obs, expected_com, expected_foe, expected_play = reference[t]
            require(full_obs.keys() == expected_obs.keys(), "Public field set differs")
            for k in full_obs:
                same(full_obs[k], expected_obs[k], (seed, t, k))
            same(original, expected_com, (seed, t, "16 original commands"))
            same(enemy, expected_foe, (seed, t, "16 enemy commands"))
            if t < stop:
                same(played, expected_play, (seed, t, "16 previously played own commands"))
            else:
                same(played[teammates], expected_play[teammates], (seed, t, "15 simultaneously played own commands"))
        alive = np.asarray(own["units_mask"])[team, uid] and np.asarray(own["units"]["energy"])[team].reshape(-1)[uid] >= 0
        xy = np.asarray(own["units"]["position"])[team, uid]
        if alive and played[uid, 0] == 0:
            actual_idle = actual_idle + 1 if np.array_equal(previous_position, xy) else 1
        else:
            actual_idle = 0
        previous_position = xy.copy() if alive else None
        # Send even the first distinct decision to the real engine. Subsequent worlds can differ.
        obs, _, done, truncated, _ = env.step({side: played, other: enemy})
        require(not bool(done[side]) and not bool(truncated[side]), "Early termination")
    require_no_agent_errors(player.base, rival)
    return trajectory, dict(prefix=full.hexdigest(), frames=stop + 1, observed_leaves=leaves_count,
                            chosen_world_action=played[uid].tolist(), played_before_intervention=stop)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw", type=Path, default=RAW)
    p.add_argument("--out", type=Path, default=HERE/"paritaet.json")
    args = p.parse_args()
    require(os.getenv("PYTHONHASHSEED") == "0" and all(os.getenv(k) == "1" for k in FULL_THREADS),
            "Incorrect replay randomness/thread settings")
    limit_threads()
    cases = chosen(args.raw)
    results = []
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        for r in cases:
            reference, baseline = run_prefix(env, r, 0)
            branches = {}
            for d in sorted(map(int, r["event"]["x"])):
                _, branch = run_prefix(env, r, d, reference)
                require(branch["prefix"] == baseline["prefix"] and branch["frames"] == baseline["frames"],
                        "New independent joint prefix does not match control")
                branches[str(d)] = branch
            results.append(dict(index=r["index"], seed=r["seed"], team=r["team"], uid=r["event"]["uid"],
                                energy=r["event"]["energy"], already_executed_stays=r["event"]["idle"] - 1,
                                step=r["event"]["step"], archived_anchor=r["anchor"],
                                archive_sha256=sha256((args.raw/f"{r['seed']}.json").read_bytes()).hexdigest(),
                                original=baseline, alternatives=branches))
            print(r["seed"], r["team"], sorted(branches), flush=True)
    finally:
        env.close()
    require(chosen(args.raw) == cases, "Frozen sources or six input rows changed during audit")
    result = dict(maps=len(results), independent_prefix_runs=sum(1 + len(r["alternatives"]) for r in results),
                  alternatives=sum(len(r["alternatives"]) for r in results),
                  real_steps=sum(r["original"]["frames"] * (1 + len(r["alternatives"])) for r in results),
                  new_complete_matches=0, evidence=results)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
