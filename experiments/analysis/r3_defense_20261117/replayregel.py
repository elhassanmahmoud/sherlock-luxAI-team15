"""Replay the live public-only selector and independently check team field coverage."""
from collections import Counter
import gzip
import json
from pathlib import Path
import sys

from feldbeschuss import switches
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "unit_handoff_20261116"))
from feldplan import endpoint


def audit():
    summary = {}
    files = sorted((HERE / "replays/roh").glob("*.json.gz"))
    if len(files) != 12:
        raise ValueError("Expected four cases for each of three policies")
    for path in files:
        data = json.loads(gzip.decompress(path.read_bytes()))
        arena = Counter()
        for f in data["frames"]:
            if f["step"] % 101 == 0:
                continue
            own = [(u, (x, y), e) for u, x, y, e in f["own"]]
            enemy = {(x,y) for _,x,y,_ in f["visible"]}
            points = set(map(tuple, f["confirmed"]))
            blocked = set(map(tuple, f["known_asteroids"]))
            base, advice = f["r3_orders"], f["v15_orders"]
            planned = {u: endpoint(pos, base[u][0], e, data["move_cost"], blocked, (24,24)) for u,pos,e in own}
            chosen = switches(own, enemy, points, planned, base, advice, data["sap_cost"], data["sap_range"])
            own_positions = {u: pos for u,pos,_ in own}
            effective = dict(planned)
            for uid, target in chosen:
                effective[uid] = own_positions[uid]
                if target not in points or target in enemy or target in own_positions.values() or advice[uid][0] != 5:
                    raise ValueError("Gate violation")
                arena["empty_in_splash"] += int(not any(max(abs(x-target[0]), abs(y-target[1])) <= 1 for x,y in enemy))
                arena["r3_would_have_fired"] += int(base[uid][0] == 5)
                arena["shooter_on_known"] += int(own_positions[uid] in points)
            if (points & set(planned.values())) - set(effective.values()):
                raise ValueError("Would drop previously planned scoring coverage")
            arena["turns"] += 1
            arena["changed_turns"] += int(bool(chosen))
            arena["choices"] += len(chosen)
        summary[path.stem] = dict(arena)
    return summary


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
