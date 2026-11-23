"""Measure exclusive discovery on actual eight-turn course continuations from the same prefix."""
import argparse
import gzip
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from flotte import STEPS
from kandidat import FleetScout
from sammeln import OUT, ablation_function, capture, initialize, panel, real_check, without
from vorhersage import load
from luxai_s3.wrappers import LuxAIS3GymEnv
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors


def hash_tree(h, tree, prefix=""):
    if isinstance(tree, dict):
        for k in sorted(tree):
            hash_tree(h, tree[k], prefix + "/" + k)
    else:
        a = np.asarray(tree)
        h.update(json.dumps((prefix, a.dtype.str, a.shape)).encode())
        h.update(a.tobytes())


def paired(mask):
    return (mask | mask[::-1, ::-1].T)[np.add.outer(np.arange(24),np.arange(24)) <= 23]


def game(env, exact, models, seed, index, arm):
    team, side, other, opponent, base, foe, obs = initialize(env, seed, index)
    actor = FleetScout(base, *models, baseline=(arm != "cnn"), original_only=(arm == "original"))
    original = None
    existing = base.act
    def capture_action(*args, **kwargs):
        nonlocal original
        original = existing(*args, **kwargs)
        return original
    base.act = capture_action
    digest = sha256()
    margins = []
    seen_from_start = None
    all_mask = np.zeros((24,24), bool)
    rest_mask = np.zeros_like(all_mask)
    first = credit = 101
    archive = []
    before = None
    prior_scout_position = None
    discontinuity = False
    for step in range(85):
        if actor.event is not None:
            age = step - actor.event["step"]
            if 1 <= age <= STEPS:
                raw = capture(env, team, side, obs)
                alive_now = raw[2][actor.uid]
                pos_now = raw[1][actor.uid] if alive_now else None
                if (not alive_now or prior_scout_position is None or
                        int(np.abs(pos_now - prior_scout_position).sum()) > 1):
                    discontinuity = True
                prior_scout_position = pos_now
                residual = without(raw, actor.uid)
                all_mask |= raw[0] > 0
                rest_mask |= residual > 0
                if age in (1,STEPS):
                    real_check(exact, env, before, team, actor.uid, raw)
                own = obs[side]
                if np.any(own["relic_nodes_mask"]):
                    first = min(first, age)
                if own["team_points"][team] > 0:
                    credit = min(credit, age)
                margins.append(int(own["team_points"][team]) - int(own["team_points"][1-team]))
                if age == STEPS:
                    break
        own = obs[side]
        prior = actor.event is None
        actions = actor.act(step, own)
        rival = foe.act(step, obs[other])
        if prior:
            hash_tree(digest, obs)
            hash_tree(digest, original, "16-original")
            hash_tree(digest, rival, "16-opponent")
            if actor.event is not None:
                uid = actor.uid
                prior_scout_position = np.asarray(actor.event["origin"])
                peers = np.arange(16) != uid
                hash_tree(digest, actions[peers], "15-other")
                seen_from_start = actor.history.last_seen.copy() >= 0
                if original[uid, 0] != 0 or actor.history.stays[uid] < 4:
                    raise ValueError("A departure had fewer than three previous STAYs")
            else:
                if not np.array_equal(actions, original):
                    raise ValueError("A predecision action changed")
                hash_tree(digest, actions, "16-previously-played")
        delta = np.flatnonzero(np.any(actions != original, axis=1))
        if len(delta):
            uid = actor.uid
            if (len(delta) != 1 or int(delta[0]) != uid or np.any(own["relic_nodes_mask"])
                    or own["team_points"][team] or not own["units_mask"][team, uid] or original[uid,0] > 4
                    or not 1 <= actions[uid,0] <= 4 or not 16 <= step <= 83):
                raise ValueError("Illegal experimental intervention")
            archive.append([step, uid, int(original[uid,0]), int(actions[uid,0])])
        if len(archive) != actor.changes:
            raise ValueError("Change count diverges from actual output")
        if actor.event is None and (actor.history.finished or step >= 76):
            break
        before = env.state.map_features.tile_type
        obs, _, _, _, _ = env.step({side: actions, other: rival})
    require_no_agent_errors(actor.base, foe)
    if arm == "original" and archive:
        raise ValueError("Original V16 control changed")
    if actor.event is None:
        gains = dict(new_pairs=0, exclusive_pairs=0, exclusive_physical=0, extra_all=0)
    else:
        if len(margins) != STEPS or np.any(rest_mask & ~all_mask):
            raise ValueError("Invalid eight-tick measured future")
        new = ~paired(seen_from_start)
        whole, others = paired(all_mask), paired(rest_mask)
        gains = dict(new_pairs=int((whole & new).sum()), exclusive_pairs=int((whole & new & ~others).sum()),
                     exclusive_physical=int((all_mask & ~seen_from_start & ~rest_mask).sum()),
                     extra_all=int((whole & ~others).sum()))
    return dict(seed=seed, team=team, opponent=opponent, arm=arm, changes=archive,
                event=actor.event, uid_gap_or_jump=discontinuity, prefix=digest.hexdigest(), first_sight_in_window=first if first <= STEPS else None,
                first_credit_in_window=credit if credit <= STEPS else None, margins=margins, **gains)


def report(rows):
    lookup = {(r["seed"],r["team"],r["arm"]):r for r in rows}
    seeds = sorted({r["seed"] for r in rows})
    arms = ("original","simple","cnn")
    if seeds != panel("real") or len(lookup) != 6*len(seeds) or len(lookup) != len(rows):
        raise ValueError("Incomplete game groups")
    for s in seeds:
        for side in (0,1):
            variants = [lookup[s,side,a] for a in arms]
            if len({r["prefix"] for r in variants}) != 1:
                raise ValueError("Unequal observed or played prefix")
            events = [r["event"] for r in variants]
            frame = [None if e is None else (e["step"],e["uid"],tuple(e["origin"])) for e in events]
            if len(set(frame)) != 1:
                raise ValueError("Different starting opportunities")
    columns = ("exclusive_pairs", "exclusive_physical", "new_pairs", "extra_all", "first_sight_in_window",
               "first_credit_in_window", "margin_at_8", "interventions")
    def vector(r):
        return [r[k] for k in columns[:4]] + [float(r[k] is not None) for k in columns[4:6]] + [
            r["margins"][-1] if r["margins"] else 0, len(r["changes"])]
    means, effects = {}, {}
    per_map = {}
    for arm in arms:
        selected = [r for r in rows if r["arm"] == arm]
        a = np.asarray([[vector(lookup[s,t,arm]) for t in (0,1)] for s in seeds],float)
        means[arm] = dict(zip(columns,a.mean((0,1)).tolist()))
        means[arm]["eligible_seats"] = sum(r["event"] is not None for r in selected)
        means[arm]["uid_gap_or_jump_seats"] = sum(r["uid_gap_or_jump"] for r in selected)
        means[arm]["changed_seats"] = sum(bool(r["changes"]) for r in selected)
        per_map[arm] = a.mean(1)
    ids = np.random.default_rng(2311234).integers(len(seeds),size=(8000,len(seeds)))
    for comparison in ("original","simple"):
        delta = per_map["cnn"]-per_map[comparison]
        effects[comparison] = {k:dict(mean=float(delta[:,i].mean()),ci95=np.quantile(
            delta[ids,i].mean(1),[.025,.975]).tolist()) for i,k in enumerate(columns)}
    return dict(maps=len(seeds), paired_seats=2*len(seeds), actual_opening_prefixes=len(rows),
                results=means, cnn_gain=effects,
                pass_real_exclusive=effects["simple"]["exclusive_pairs"]["mean"] > 0)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--score", action="store_true")
    args = p.parse_args()
    limit_threads()
    check = json.loads((HERE/"pruefung.json").read_text())
    if not check["pass_brier_against_reference"]:
        raise ValueError("Forecast gate did not pass")
    sources = [HERE/n for n in ("AUSWERTUNGSPLAN.md","flotte.py","kandidat.py","vorhersage.py","modell.json",
                                "flottengewichte.npz","spielprobe.py")]
    signature = sha256(b"".join(p.read_bytes() for p in sources)).hexdigest()
    directory = OUT/"real"
    directory.mkdir(exist_ok=True)
    env = None if args.score else LuxAIS3GymEnv(numpy_output=True)
    exact = ablation_function(env) if env is not None else None
    models = load() if env is not None else None
    records = []
    try:
        for i, seed in enumerate(panel("real")):
            for team in (0,1):
                # initialize uses index//2 parity for opponent. Both seats of each map face the same opponent.
                for arm in ("original","simple","cnn"):
                    path = directory/f"{seed}_{team}_{arm}.json"
                    if not path.exists():
                        if env is None:
                            raise ValueError("Incomplete real prefixes")
                        row = game(env, exact, models, seed, 2*i+team, arm)
                        row["source"] = signature
                        tmp = path.with_suffix(".tmp")
                        tmp.write_text(json.dumps(row, allow_nan=False)+"\n")
                        tmp.replace(path)
                    else:
                        row = json.loads(path.read_text())
                    if (row["seed"], row["team"], row["arm"], row["source"]) != (seed,team,arm,signature):
                        raise ValueError("Different existing real prefix")
                    records.append(row)
            if not args.score:
                print(seed, flush=True)
    finally:
        if env is not None:
            env.close()
    result = report(records)
    (HERE/"spielprobe.json").write_text(json.dumps(result, indent=2)+"\n")
    with gzip.GzipFile(filename=HERE/"spielzuege.jsonl.gz", mode="wb", mtime=0) as out:
        for r in records:
            out.write((json.dumps(r,separators=(",",":"))+"\n").encode())
    print(json.dumps(result,indent=2), flush=True)


if __name__ == "__main__":
    main()
