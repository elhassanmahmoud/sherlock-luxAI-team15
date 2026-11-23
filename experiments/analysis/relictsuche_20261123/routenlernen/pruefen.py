"""Opening results and same-observation command checks on held-out course maps."""
import argparse
from hashlib import sha256
import json
import os
import random
import sys

import numpy as np

from collect import OUT, PACKAGE, ROOT, seeds_for
from routes import HERE, MIRROR_DIR
sys.path.insert(0, str(ROOT))
from experiments.analysis.relictsuche_20261123.routenlernen.kandidat import create
from luxai_s3.wrappers import LuxAIS3GymEnv
from scripts.common import make_opponent
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from scripts.scoring import match_points_after_step


def play(env, seed, team, arm, *, crosscheck=False):
    side, other = f"player_{team}", f"player_{1-team}"
    rival = make_opponent("solution92", other)
    package = OUT / "sherlock_routenlernen.zip" if arm == "zip" else PACKAGE
    agent = create(side) if arm == "learned" else r3_package_agent(side, package)
    agent.new_game(side)
    if hasattr(rival, "new_game"):
        rival.new_game(other)
    random.seed(seed)
    np.random.seed(seed)
    obs, info = env.reset(seed=seed)
    sensor = info["params"]["unit_sensor_range"]
    for p in (agent, rival):
        p.set_env_cfg(info["params"])
    first = first_credit = 101
    score70 = None
    changes, command_count = [], 0
    digest = sha256()
    independent = None
    proposal = None
    if arm != "original" and crosscheck:
        if arm != "zip":
            independent = r3_package_agent(side, PACKAGE)
            independent.new_game(side)
            independent.set_env_cfg(info["params"])
        raw = agent.base.act
        def spy(*args, **kwargs):
            nonlocal proposal
            action = raw(*args, **kwargs)
            proposal = action.copy()
            return action
        agent.base.act = spy
    for t in range(101):
        old = obs[side]
        action = agent.act(t, old)
        if np.asarray(old["relic_nodes_mask"]).any():
            first = min(first, t)
        if arm != "original" and crosscheck:
            if independent is not None:
                ref = independent.act(t, old)
                if not changes or sensor > 1:
                    if not np.array_equal(ref, proposal):
                        raise ValueError("Same-observation independent V16 differs before any intervention")
            changed = np.flatnonzero(np.any(action != proposal, axis=1))
            if len(changed):
                uid = int(changed[0])
                if (sensor != 1 or t > 90 or t < 10 or first <= t or first_credit < t
                        or len(changed) != 1 or not (1 <= action[uid, 0] <= 4) or proposal[uid, 0] > 4
                        or np.any(action[uid, 1:] != 0)):
                    raise ValueError("Protected instruction changed")
                p = agent.base._imitation
                ctx, ids, _, masks, _, _, pos = p.last_fz
                i = list(ids).index(uid)
                d = int(action[uid, 0])
                canonical = int(MIRROR_DIR[d]) if team else d
                if (not masks[i, canonical] or not old["units_mask"][team, uid]
                        or ctx["ally_ene"][uid] < max(14, 4 * ctx["move_cost"])
                        or ctx["point_tiles"][tuple(pos[i])] or ctx["candidate"][tuple(pos[i])]
                        or p._prev_actions[uid] != canonical):
                    raise ValueError("Unsafe or inconsistent actual course action")
                if p.param_est._prev is not None and not np.array_equal(p.param_est._prev["act"], action):
                    raise ValueError("Action memory mismatch")
                if uid != agent.history.scout or (changes and changes[0][1] != uid):
                    raise ValueError("More than one designated scout")
                changes.append([t, uid, int(proposal[uid, 0]), d])
            if agent.changes != len(changes):
                raise ValueError("Change count differs from played actions")
        digest.update(np.asarray(action, dtype="<i2").tobytes())
        command_count += len(action)
        acts = {side: action, other: rival.act(t, obs[other])}
        obs, _, _, _, info = env.step(acts)
        points = match_points_after_step(old, obs[side], info)
        scores = [int(points[team]), int(points[1 - team])]
        if scores[0]:
            first_credit = min(first_credit, t)
        if t == 70:
            score70 = scores
    require_no_agent_errors(agent, rival)
    if independent is not None:
        require_no_agent_errors(independent, rival)
    if int(obs[side]["match_steps"]) != 0 or sum(obs[side]["team_wins"]) != 1:
        raise ValueError("Not a completed original opening")
    return dict(seed=seed, side=team, arm=arm, range=int(sensor), first=first, first_credit=first_credit,
                after_70=score70, final=scores, won=int(obs[side]["team_wins"][team]), commands=command_count,
                digest=digest.hexdigest(), changes=getattr(agent, "changes", 0), events=changes)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("smoke", "replay", "zip"))
    args = p.parse_args()
    limit_threads()
    env = LuxAIS3GymEnv(numpy_output=True)
    raw = OUT / "replay_rows"
    raw.mkdir(exist_ok=True)
    try:
        if args.mode in ("smoke", "zip"):
            seeds = [int(v[0]) for v in [seeds_for("replay"), seeds_for("replay", normal=True)]]
            arm = "learned" if args.mode == "smoke" else "zip"
            rows = [play(env, seed, side, arm, crosscheck=True) for seed in seeds for side in (0, 1)]
            if (not any(r["changes"] for r in rows if r["range"] == 1)
                    or any(r["changes"] for r in rows if r["range"] > 1)):
                raise ValueError("Inactive sight group or missing scout")
            if args.mode == "zip":
                original = json.loads((HERE / "smoke.json").read_text())
                for a, b in zip(original, rows, strict=True):
                    if any(a[k] != b[k] for k in a if k != "arm"):
                        raise ValueError("Packaged and research policy disagree")
            (HERE / (args.mode + ".json")).write_text(json.dumps(rows, indent=2) + "\n")
            print([(r["side"], r["range"], r["changes"]) for r in rows])
        else:
            rows = []
            signature = sha256(b"".join((HERE / f).read_bytes() for f in (
                "kandidat.py", "routes.py", "routengewichte.json", "pruefen.py"))).hexdigest()
            for s in seeds_for("replay"):
                seed = int(s)
                for side in (0, 1):
                    for arm in ("original", "learned"):
                        filename = raw / f"{seed}_{side}_{arm}.json"
                        if filename.exists():
                            r = json.loads(filename.read_text())
                            if (r["seed"], r["side"], r["arm"], r["source"]) != (seed, side, arm, signature):
                                raise ValueError("Different replay identity")
                        else:
                            r = play(env, seed, side, arm, crosscheck=arm == "learned")
                            r["source"] = signature
                            tmp = filename.with_suffix(".tmp")
                            tmp.write_text(json.dumps(r))
                            tmp.replace(filename)
                        rows.append(r)
                print("replay", seed, flush=True)
            import gzip
            with gzip.GzipFile(filename=HERE / "eroeffnungen.jsonl.gz", mode="wb", mtime=0) as out:
                for r in rows:
                    out.write((json.dumps(r, separators=(",", ":")) + "\n").encode())
    finally:
        env.close()


if __name__ == "__main__":
    main()
