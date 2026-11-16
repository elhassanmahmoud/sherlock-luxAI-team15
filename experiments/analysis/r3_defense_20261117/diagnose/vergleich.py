"""Measure scored field occupation and compare world commands on the same observed state."""
from collections import Counter, defaultdict
from hashlib import sha256
import gzip
import json
from pathlib import Path
from statistics import median
from typing import Iterable

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "replays" / "roh"
KEYS = [(7158016, "player_0"), (7158020, "player_0"), (7158020, "player_1"), (7158030, "player_1")]
ARMS = ("r3", "v15", "unit")
DELTAS = ((0, 0), (0, -1), (1, 0), (0, 1), (-1, 0), (0, 0))


def coords(units):
    return {(x, y) for _, x, y, _ in units}


def xyset(seq):
    return set(map(tuple, seq))


def within(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1])) <= 1


def durations(steps: Iterable[set]):
    """One run per uninterrupted scoring coordinate; ends at every match boundary."""
    ended = []
    active = {}
    for occupied in steps:
        ended.extend(n for p, n in active.items() if p not in occupied)
        active = {p: active.get(p, 0) + 1 for p in occupied}
    return ended + list(active.values())


def lengths(runs):
    return {"field_turns": sum(runs), "episodes": len(runs),
            "mean": sum(runs) / len(runs) if runs else 0,
            "median": median(runs) if runs else 0, "max": max(runs, default=0)}


def first_occupation(steps):
    first = {}
    for t, fields in enumerate(steps):
        for cell in fields:
            first.setdefault(cell, t)
    potential = sum(len(steps) - turn for turn in first.values())
    points = sum(len(fields) for fields in steps)
    return dict(distinct=len(first), turns_after_first=potential, off_after_first=potential-points,
                first=[[*point, t] for point, t in sorted(first.items())])


def queue_metric(count, key, targets, previous, after):
    count[key + "_threatened"] += len(previous & targets)
    count[key + "_no_longer_scored"] += len((previous & targets) - after)


def endpoint(pos, order, energy, cost, blocks):
    dx, dy = DELTAS[order[0]]
    cell = pos[0] + dx, pos[1] + dy
    if energy < cost or cell in blocks or not all(0 <= z < 24 for z in cell):
        return pos
    return cell


def classify(f, turn, history, cost):
    """Actual shots, same-state disagreement and coverage using only known pre-action inputs."""
    known = xyset(f["confirmed"])
    allies = coords(f["own"])
    foes = coords(f["visible"])
    actions = f["own_orders"]
    scored = [xyset(p) for p in f["scored_fields"]]
    before = history[-1][1] if history else set()
    counts = Counter()
    seen_targets = set()
    all_footprint = set()
    shot_examples = []
    parent_events = []
    is_unit = "r3_orders" in f and "v15_orders" in f
    if is_unit:
        base, other = f["r3_orders"], f["v15_orders"]
        blocks = xyset(f["known_asteroids"])
        plan = {uid: endpoint((x, y), base[uid], energy, cost, blocks) for uid, x, y, energy in f["own"]}
        cover = Counter(plan.values())
    for uid, x, y, energy in f["own"]:
        origin = x, y
        a, dx, dy = actions[uid]
        if a == 5:
            target = x + dx, y + dy
            counts["shots"] += 1
            counts["shot_from_own_known"] += origin in known
            counts["shot_on_known"] += target in known
            counts["shot_on_free_known"] += target in known - allies
            counts["shot_on_free_known_no_visible_center"] += target in known - allies - foes
            counts["shot_on_free_known_no_visible_area"] += target in known - allies and not any(within(target, p) for p in foes)
            seen_targets.add(target)
            all_footprint.update(p for p in before if within(target, p))
            if target in known - allies and target in before and target not in scored[1]:
                shot_examples.append(dict(turn=turn, uid=uid, origin=origin, target=target,
                                          enemy_visible_at_center=target in foes,
                                          own_points=f["after"][0], opponent_points=f["after"][1]))
        if not is_unit or other[uid][0] != 5 or other[uid] == base[uid]:
            continue
        target = x + other[uid][1], y + other[uid][2]
        if target not in known - allies:
            continue
        protected = plan[uid] == origin or plan[uid] not in known or cover[plan[uid]] > 1
        near = any(within(target, p) for p in foes)
        parent_events.append(dict(turn=turn, uid=uid, origin=origin, target=target, r3_order=base[uid],
                                  v15_order=other[uid], actual=actions[uid],
                                  enemy_at_center=target in foes, enemy_in_area=near,
                                  covered=protected, enemy_scored_recently=any(target in pair[1] for pair in history[-3:]),
                                  enemy_prev_scored_center=target in before, enemy_next_scored_center=target in scored[1]))
    # Fields are counted once per turn in spite of multiple shots or overlapping splash.
    queue_metric(counts, "all_centers", seen_targets, before, scored[1])
    queue_metric(counts, "free_known_centers", seen_targets & (known - allies), before, scored[1])
    queue_metric(counts, "publicly_empty_centers", seen_targets & (known - allies - foes), before, scored[1])
    queue_metric(counts, "shot_area", all_footprint, before, scored[1])
    counts["enemy_existing"] += len(before)
    counts["enemy_exits"] += len(before - scored[1])
    return counts, shot_examples, parent_events


def process(d):
    fs = d["frames"]
    if len(fs) != 303:
        raise ValueError("Incomplete trace")
    rounds = []
    total = Counter()
    runs = [[], []]
    all_events = []
    all_shots = []
    for match in range(1, 4):
        window = fs[(match - 1) * 101:match * 101]
        history = []
        c = Counter()
        for t, f in enumerate(window):
            if f["step"] != (match - 1) * 101 + t:
                raise ValueError("Game clock")
            scored = [xyset(p) for p in f["scored_fields"]]
            if [len(p) for p in scored] != [v - u for u, v in zip(f["before"], f["after"], strict=True)]:
                raise ValueError("Scoring field counts do not reproduce official increment")
            marks, examples, events = classify(f, t, history, d.get("move_cost"))
            c.update(marks)
            for group, out in ((examples, all_shots), (events, all_events)):
                for row in group:
                    out.append({"match": match, **row})
            history.append(scored)
        closed = [durations(entry[k] for entry in history) for k in (0, 1)]
        for side in (0, 1):
            runs[side].extend(closed[side])
        points = window[-1]["after"]
        if list(map(sum, closed)) != points:
            raise ValueError("Streaks disagree with official result")
        wins = window[-1]["next_wins"][0] - window[0]["next_wins"][0]
        arrivals = [first_occupation([entry[k] for entry in history]) for k in (0, 1)]
        milestones = [window[t]["after"] for t in (25, 50, 75, 100)]
        rounds.append(dict(match=match, points=points, win=wins, own=lengths(closed[0]),
                           foe=lengths(closed[1]), milestones=milestones, first_occupation=arrivals, counts=c))
        total.update(c)
    if (sum(runs[0]), sum(runs[1]), sum(r["win"] for r in rounds)) != (
            d["actual"]["our_points"], d["actual"]["opp_points"], d["actual"]["our_wins"]):
        raise ValueError("Trace sums or official match wins disagree")
    return dict(matches=rounds, total_counts=total, own=lengths(runs[0]), foe=lengths(runs[1]),
                shot_examples=all_shots, alternatives=all_events)


def opponent_difference(reference, v15):
    """Decompose reference minus V15 opponent score using first scoring turns per field."""
    result = Counter()
    for a, b in zip(reference["matches"], v15["matches"], strict=True):
        r, v = (m["first_occupation"][1] for m in (a, b))
        rr, vv = ({(x, y): t for x, y, t in record["first"]} for record in (r, v))
        result["different_fields"] += sum(101 - rr[p] for p in rr.keys() - vv.keys())
        result["different_fields"] -= sum(101 - vv[p] for p in vv.keys() - rr.keys())
        result["delay_on_shared_fields"] += sum(vv[p] - rr[p] for p in vv.keys() & rr.keys())
        result["more_off_after_first"] += v["off_after_first"] - r["off_after_first"]
    if sum(result.values()) != reference["foe"]["field_turns"] - v15["foe"]["field_turns"]:
        raise ValueError("Opponent score decomposition disagrees")
    return result


def collect():
    out = {}
    hashes = json.loads((RAW / "sha256.json").read_bytes())
    for seed, seat in KEYS:
        key = f"{seed}/P{seat[-1]}"
        out[key] = {}
        for arm in ARMS:
            path = RAW / f"{arm}-{seed}-{seat}.json.gz"
            blob = path.read_bytes()
            if sha256(blob).hexdigest() != hashes[path.name]:
                raise ValueError(f"Replay hash mismatch: {path}")
            d = json.loads(gzip.decompress(blob))
            if d["arm"] != arm or d["seed"] != seed or d.get("seat", d.get("side")) != seat:
                raise ValueError(f"Unexpected replay identity {path}")
            out[key][arm] = process(d)
        out[key]["foe_points_denied_relative_to"] = {
            ref: opponent_difference(out[key][ref], out[key]["v15"]) for ref in ("unit", "r3")}
    return out


if __name__ == "__main__":
    print(json.dumps(collect(), sort_keys=True, ensure_ascii=False, indent=1))
