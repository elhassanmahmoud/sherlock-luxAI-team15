"""Look at actual opponent scoring before and after the observed V15 defensive shots."""
from collections import Counter
import gzip
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parents[1] / "unit_handoff_20261116")]
from feldbeschuss import switches
from feldplan import endpoint


def record(before, after, counts):
    counts["events"] += 1
    counts["with_scoring_before"] += bool(before)
    counts["with_scoring_after"] += bool(after)
    counts["vacated_all"] += bool(before) and not after
    counts["any_vacated"] += bool(before - after)
    counts["any_new"] += bool(after - before)
    counts["empty_both"] += not bool(before | after)
    counts["field_points_before"] += len(before)
    counts["field_points_after"] += len(after)
    counts["retained_field_points"] += len(before & after)


def inspect():
    hashes = json.loads((HERE / "roh/sha256.json").read_bytes())
    union = Counter()
    individual = Counter()
    by_match = {}
    cases = []
    for name, digest in sorted(hashes.items()):
        if not name.startswith("v15-"):
            continue
        by_match[name] = [Counter(), Counter(), Counter()]
        raw = (HERE / "roh" / name).read_bytes()
        if sha256(raw).hexdigest() != digest:
            raise ValueError("Unverified trace")
        game = json.loads(gzip.decompress(raw))
        for i, f in enumerate(game["frames"]):
            if i % 101 == 0:
                continue
            if f["own_orders"] != f["v15_orders"]:
                raise ValueError("Not the original V15 action")
            ours = [(u, (x,y), e) for u,x,y,e in f["own"]]
            foes = {(x,y) for _,x,y,_ in f["visible"]}
            blocks = set(map(tuple, f["known_asteroids"]))
            points = set(map(tuple, f["confirmed"]))
            planned = {u: endpoint(p, f["r3_orders"][u][0], e, game["move_cost"], blocks, (24,24)) for u,p,e in ours}
            eligible = switches(ours, foes, points, planned, f["r3_orders"], f["v15_orders"],
                                game["sap_cost"], game["sap_range"])
            if not eligible:
                continue
            pre = set(map(tuple, game["frames"][i-1]["scored_fields"][1]))
            post = set(map(tuple, f["scored_fields"][1]))
            area = set()
            for uid, (x,y) in eligible:
                reach = {(x+dx,y+dy) for dx in (-1,0,1) for dy in (-1,0,1)}
                area.update(reach)
                record(pre & reach, post & reach, individual)
                individual["visible_enemy_near"] += bool(reach & foes)
                individual["r3_already_sap"] += f["r3_orders"][uid][0] == 5
                cases.append(dict(seed=game["seed"], seat=game["seat"], match=i//101+1, turn=i%101, uid=uid,
                                  target=[x,y], r3=f["r3_orders"][uid], v15=f["v15_orders"][uid],
                                  before=sorted(pre & reach), after=sorted(post & reach)))
            record(pre & area, post & area, union)
            record(pre & area, post & area, by_match[name][i//101])
    return dict(shots=individual, turns=union, per_match=by_match, events=cases)


if __name__ == "__main__":
    print(json.dumps(inspect(), indent=2))
