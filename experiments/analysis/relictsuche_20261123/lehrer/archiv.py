"""Read paired authenticated public R3/V16 observations. Recreate only static maps, never step a game."""
from collections import Counter, defaultdict
import gzip
from hashlib import sha256
import inspect
import json
from pathlib import Path

import numpy as np
from luxai_s3 import state, wrappers

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ARCHIVE = Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/finalwoche_20261122/kurze_sicht/spiele")
GROUPS = ("r3_only", "both")
DIGEST = {"r3": "8aabdc732143a1e3f5babdd6edb6272e166b54671ee397e50e02083261c4a64d",
          "v16": "0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"}
DELTA = np.array([[0, 0], [0, -1], [1, 0], [0, 1], [-1, 0]])


def first(mask):
    found = np.flatnonzero(mask)
    return int(found[0]) if len(found) else 101


def read(record):
    path = ARCHIVE/record["filename"]
    if sha256(path.read_bytes()).hexdigest() != record["sha256"] or DIGEST[record["agent"]] != record["package"]:
        raise ValueError(f"Changed observation archive {path}")
    with np.load(path, allow_pickle=False) as f:
        data = {k: f[k][:102] for k in f}
    if not np.array_equal(data["steps"], np.arange(102)) or not np.array_equal(data["match_steps"], np.arange(102)%101):
        raise ValueError("Incomplete first match")
    return data


def events(a, team, tiles, spawn):
    mask = a["units_mask"][:, team]
    pos = a["units/position"][:, team]
    energy = a["units/energy"][:, team]
    pts = a["team_points"][:, team]
    gains = []
    for t in range(1, 102):
        p = pos[t][mask[t] & (energy[t] >= 0)]
        xy = {tuple(k) for k in p}
        g = sum(bool(tiles[x, y]) for x, y in xy) if t >= spawn else 0
        if t <= 100 and g != pts[t]-pts[t-1]:
            raise ValueError("The reconstructed visible score differs before the reset")
        gains.append(g)
    known = np.asarray(a["relic_nodes_mask"][:101])
    sight = first(known.any(1))
    credit = first(np.asarray(gains) > 0)
    return dict(first_sight=sight, first_credit=credit, win_match=int(a["team_wins"][101, team]),
                points70=int(pts[71]), enemy70=int(a["team_points"][71, 1-team]),
                final_points=int(sum(gains)), last_gain=int(gains[-1]))


def is_moved(a, team, t, uid):
    if t < 1 or not a["units_mask"][t-1, team, uid] or not a["units_mask"][t, team, uid] or a["units/energy"][t-1, team, uid] < 0:
        return False
    direction = int(a["commands"][t-1, uid, 0])
    return 1 <= direction <= 4 and np.array_equal(a["units/position"][t-1, team, uid]+DELTA[direction],
                                                  a["units/position"][t, team, uid])


def active(a, team, end):
    seen = a["sensor_mask"][0].copy()
    per_ship = Counter()
    productive = moves = fresh_count = 0
    for t in range(1, end+1):
        sensor = a["sensor_mask"][t]
        new = np.argwhere(sensor & ~seen)
        fresh_count += len(new)
        seen |= sensor
        ids = np.flatnonzero(a["units_mask"][t, team])
        moved = {int(uid) for uid in ids if is_moved(a, team, t, uid)}
        moves += len(moved)
        if not len(new) or not len(ids):
            continue
        pos = a["units/position"][t, team, ids]
        coverage = np.abs(pos[:, None, :]-new).max(2) <= 1
        n = coverage.sum(0)
        if np.any(n == 0):
            raise ValueError("New publicly sensed cell lacks a possible contributing unit")
        unique = coverage[:, n == 1].sum(1)
        for uid, count in zip(ids, unique):
            if count and uid in moved:
                per_ship[int(uid)] += int(count)
                productive += 1
    return dict(active_ships=len(per_ship), unique_new=int(sum(per_ship.values())), ship_moves=moves,
                productive_moves=productive, new_seen=fresh_count, per_ship=sorted(per_ship.items()))


def finder(a, team, t, spawn):
    if t == 101:
        return None
    cells = a["relic_nodes"][t][a["relic_nodes_mask"][t]]
    ids = np.flatnonzero(a["units_mask"][t, team])
    positions = a["units/position"][t, team, ids]
    covers = (np.abs(positions[:, None, :]-cells).max(2) <= 1).any(1)
    possible = [int(uid) for uid in ids[covers]]
    moved = [uid for uid in possible if is_moved(a, team, t, uid)]
    if not possible:
        raise ValueError("Observed relic had no possible sensing source")
    return dict(on_spawn=t == spawn, visible=cells.tolist(), possible=possible, moved=moved,
                path={str(uid): [p.tolist() if m else None for p, m in zip(
                    a["units/position"][max(0,t-6):t+1,team,uid], a["units_mask"][max(0,t-6):t+1,team,uid])] for uid in possible})


def shared(a, b, team, coords, cost):
    """What actually differs at the first common-history choice? Compare the two actual one-step positions."""
    t = first(np.any(a["commands"][:101] != b["commands"][:101], axis=(1, 2)))
    if t == 101:
        return None
    if any(not np.array_equal(a[key][:t+1], b[key][:t+1]) for key in a if key != "commands"):
        raise ValueError("Same command prefix but different public state; no matched decision")
    ids = np.flatnonzero(np.any(a["commands"][t] != b["commands"][t], axis=1))
    pos = a["units/position"][t, team]
    choices = []
    for uid in ids:
        uid = int(uid)
        d = lambda p: int(np.abs(p[None, :]-coords).sum(1).min())
        vals = []
        for arm in (a, b):
            position = arm["units/position"][t+1, team, uid]
            vals.append(dict(cmd=int(arm["commands"][t, uid, 0]), position=position.tolist(),
                             distance=d(position) if arm["units_mask"][t+1, team, uid] else None))
        choices.append(dict(uid=uid, position=pos[uid].tolist(), live=bool(a["units_mask"][t, team, uid]),
                            energy=int(a["units/energy"][t, team, uid]), r3=vals[0], v16=vals[1]))
    same_search = (not a["relic_nodes_mask"][:t+1].any() and not a["team_points"][:t+1,team].any() and
                   len(choices) == 1 and choices[0]["live"] and choices[0]["energy"] >= 3*cost and
                   all(choices[0][arm]["cmd"] <= 4 and choices[0][arm]["distance"] is not None for arm in ("r3","v16")))
    return dict(step=t, changed=choices, single_free_pre_search=bool(same_search))


def summarize(rows):
    def cmp(a, b):
        x, y = np.asarray(a), np.asarray(b)
        return {"r3_mean": float(x.mean()), "v16_mean": float(y.mean()), "r3_median": float(np.median(x)),
                "v16_median": float(np.median(y)), "r3_less": int((x < y).sum()),
                "ties": int((x == y).sum()), "r3_more": int((x > y).sum())}
    def describe(rs):
        metrics = {}
        for k in ("first_sight", "first_credit", "win_match", "points70", "enemy70", "final_points"):
            metrics[k] = cmp([r["r3"][k] for r in rs], [r["v16"][k] for r in rs])
        for k in ("active_ships", "unique_new", "productive_moves", "ship_moves", "new_seen"):
            metrics[k] = cmp([r["r3"]["early"][k] for r in rs], [r["v16"]["early"][k] for r in rs])
        common = [r for r in rs if r["common"] and r["common"]["single_free_pre_search"]]
        passed = [r for r in common if r["common"]["changed"][0]["r3"]["distance"] < r["common"]["changed"][0]["v16"]["distance"]]
        out = dict(maps=len({r["seed"] for r in rs}), seats=len(rs), metrics=metrics, single_common=len(common),
                   common_r3_closer=len(passed), common_r3_closer_earlier_sight=sum(r["r3"]["first_sight"]<r["v16"]["first_sight"] for r in passed),
                   r3_earlier_both=sum(r["r3"]["first_sight"]<r["v16"]["first_sight"] and r["r3"]["first_credit"]<r["v16"]["first_credit"] for r in rs),
                   mean_common_steps=float(np.mean([r["common_end"] for r in rs])))
        for arm in ("r3", "v16"):
            finds = [r[arm]["finder"] for r in rs if r[arm]["finder"]]
            out[arm+"_finders"] = dict(finds=len(finds), at_spawn=sum(f["on_spawn"] for f in finds),
                exactly_one_moved=sum(len(f["possible"])==1 and len(f["moved"])==1 for f in finds),
                exactly_one_moved_after_spawn=sum(len(f["possible"])==1 and len(f["moved"])==1 and not f["on_spawn"] for f in finds))
        return out
    return {label: describe(rs) for label, rs in [("all", rows), *((g,[r for r in rows if r["group"]==g]) for g in GROUPS),
             *((f"p{t}", [r for r in rows if r["team"]==t]) for t in (0,1))]}


def main():
    records = [json.loads(p.read_bytes()) for p in sorted(ARCHIVE.glob("*.json"))]
    pairs = defaultdict(dict)
    for rec in records:
        seat = rec["seat"]
        if seat["sensor"] == 1:
            pairs[(seat["seed"], seat["side"])][rec["agent"]] = rec
    if len(records) != 92 or len(pairs) != 28 or any(set(v) != {"r3", "v16"} for v in pairs.values()):
        raise ValueError("Wrong underlying archive")
    rows = []
    env = wrappers.LuxAIS3GymEnv(numpy_output=True)
    current = None
    try:
        for (seed, side), pair in sorted(pairs.items()):
            if seed != current:
                _, info = env.reset(seed=seed)
                if info["params"]["unit_sensor_range"] != 1:
                    raise ValueError("Different map parameters")
                s = env.state
                tiles = np.asarray(s.relic_nodes_map_weights) == 1
                coords = np.asarray(s.relic_nodes)[[0, 3]]
                spawn = int(s.relic_spawn_schedule[0])+1
                cost = info["params"]["unit_move_cost"]
                current = seed
            data = {k: read(v) for k,v in pair.items()}
            team = int(side[-1])
            r = dict(seed=seed, team=team, group=pair["r3"]["seat"]["group"], first_active_observation=spawn,
                     sha256={k:v["sha256"] for k,v in pair.items()})
            for name, a in data.items():
                r[name] = events(a, team, tiles, spawn)
                r[name]["finder"] = finder(a, team, r[name]["first_sight"], spawn)
            r["common_end"] = min(35,*[r[k]["first_sight"]-1 for k in data],*[r[k]["first_credit"] for k in data])
            for name, a in data.items():
                r[name]["early"] = active(a, team, r["common_end"])
            r["common"] = shared(data["r3"], data["v16"], team, coords, cost)
            rows.append(r)
    finally:
        env.close()
    (HERE/"sitzpaare.json.gz").write_bytes(gzip.compress((json.dumps(rows, sort_keys=True)+"\n").encode(), mtime=0))
    out = summarize(rows)
    out["sources"] = {p.name: sha256(p.read_bytes()).hexdigest() for p in (Path(inspect.getfile(state)), Path(inspect.getfile(wrappers)),
                   Path(__file__), HERE/"PLAN.md", HERE/"sitzpaare.json.gz")}
    out["packages"] = DIGEST
    (HERE/"ergebnis.json").write_text(json.dumps(out, indent=2)+"\n")
    print(json.dumps(out["all"], indent=2))


if __name__ == "__main__":
    main()
