"""Identify single-unit switches on the actual, common observations of both advisers."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIAG = HERE.parents[1] / 'r3_field_20261116' / 'diagnose'
DELTAS = ((0, 0), (0, -1), (1, 0), (0, 1), (-1, 0), (0, 0))


def destinations(frame, orders, cost, blocked):
    planned = {}
    for uid, x, y, energy in frame['own']:
        dx, dy = DELTAS[orders[uid][0]]
        target = x + dx, y + dy
        if energy < cost or target in blocked or not all(0 <= z < 24 for z in target):
            target = x, y
        planned[uid] = target
    return planned


def inspect_frame(frame, cost):
    known = set(map(tuple, frame['confirmed']))
    blocked = set(map(tuple, frame['known_asteroids']))
    positions = {u: (x, y) for u, x, y, _ in frame['own']}
    own_tiles = set(positions.values())
    enemies = {(x, y) for _, x, y, _ in frame['visible']}
    r3 = destinations(frame, frame['r3_orders'], cost, blocked)
    v15 = destinations(frame, frame['v15_orders'], cost, blocked)
    r3_coverage = known & set(r3.values())
    retain = (known & own_tiles) | r3_coverage
    followup = {u: (x, y) for u, x, y in frame['next_own']}
    options = []
    combined = dict(r3)
    for uid in sorted(r3):
        target = v15[uid]
        if not (1 <= frame['v15_orders'][uid][0] <= 4 and target in known):
            continue
        if target in own_tiles or target in enemies or target in r3_coverage:
            continue
        single = dict(r3)
        single[uid] = target
        if not retain.issubset(single.values()):
            continue
        joint = dict(combined)
        joint[uid] = target
        current = set(combined.values())
        accepted = target not in current and (known & current | retain).issubset(joint.values())
        if accepted:
            combined = joint
        same_order = frame['own_orders'][uid] == frame['v15_orders'][uid]
        options.append(dict(uid=uid, origin=positions[uid], target=target,
                            r3_order=frame['r3_orders'][uid], v15_order=frame['v15_orders'][uid],
                            near=uid in frame['contact_uids'], combined=accepted, played=same_order,
                            arrived=same_order and followup.get(uid) == target,
                            observed_covered=retain.issubset(followup.values())))
    return options


def inspect():
    hashes = json.loads((DIAG / 'hashes.json').read_bytes())
    totals = Counter()
    per_game = {}
    events = []
    for p in sorted((DIAG / 'roh').glob('blend-*.json.gz')):
        data = p.read_bytes()
        if hashlib.sha256(data).hexdigest() != hashes[p.name]:
            raise ValueError(f'Unexpected original replay {p}')
        game = json.loads(gzip.decompress(data))
        frames = game['frames']
        if len(frames) != 303 or game['actual'] != game['expected']:
            raise ValueError('Missing steps or changed game result')
        counts = Counter()
        for i, f in enumerate(frames):
            if f['step'] != i:
                raise ValueError('Incorrect step sequence')
            match, turn = i // 101 + 1, i % 101
            if turn in (0, 100):
                continue
            counts['positions'] += 1
            opportunities = inspect_frame(f, game['move_cost'])
            counts['positions_with_options'] += bool(opportunities)
            for opt in opportunities:
                counts['single'] += 1
                counts['combined'] += opt['combined']
                counts['played'] += opt['played']
                counts['arrived'] += opt['arrived']
                counts['arrived_and_observed_covered'] += opt['arrived'] and opt['observed_covered']
                counts['early_later_match'] += match >= 2 and turn <= 25
                counts['early_later_match_far'] += match >= 2 and turn <= 25 and not opt['near']
                events.append(dict(seed=game['seed'], side=game['seat'], match=match, turn=turn, **opt))
        per_game[p.name] = dict(counts)
        totals.update(counts)
    if len(per_game) != 5 or totals['positions'] != 5 * 3 * 99:
        raise ValueError('Incomplete replay set')
    return dict(totals=dict(totals), per_game=per_game, events=events)


if __name__ == '__main__':
    print(json.dumps(inspect(), indent=2))
