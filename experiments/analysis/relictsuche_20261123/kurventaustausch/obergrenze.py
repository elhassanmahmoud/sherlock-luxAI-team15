"""The best physically local intermediate position an oracle could choose when two V16 movements commute."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DELTA = np.array([(0, 0), (0, -1), (1, 0), (0, 1), (-1, 0)])
FRESH = ("position", "energy", "units_mask", "commands", "move_mask", "protected", "terrain",
         "relic_nodes_mask", "team_points")


def load(source, record, name, names):
    path = source / record[name]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == record[name + "_sha"]
    with np.load(path, allow_pickle=False) as f:
        return {k: f[k][:101] for k in names}


def analyze(source, receipt):
    t = receipt["team"]
    pub = load(source, receipt, "public", FRESH)
    truth = load(source, receipt, "private", ("active", "centres"))
    centers = np.array([truth["centres"][0], 23-truth["centres"][0][::-1]])
    vision = pub["relic_nodes_mask"].any(1)
    sight = int(np.flatnonzero(vision)[0]) if np.any(vision) else 101
    gain = pub["team_points"][:, t] > 0
    credit = int(np.flatnonzero(gain)[0]) if np.any(gain) else 101
    loc = pub["position"][:, t]
    health = pub["energy"][:, t].reshape((101, 16))
    live = pub["units_mask"][:, t] & (health >= 0)
    codes = pub["commands"][:, :, 0].astype(int)
    moves = DELTA[np.minimum(codes, 4)].copy()
    moves[codes == 5] = 0
    opp = 1-t
    opportunities = []
    hits = []
    for k in range(1, min(99, sight, credit)):
        detour = loc[k]+moves[k+1]
        other = pub["position"][k, opp, pub["units_mask"][k, opp]]
        for u in np.flatnonzero(live[k] & live[k+1] & live[k+2] & ~pub["protected"][k]):
            orig, second = int(codes[k, u]), int(codes[k+1, u])
            if not (1 <= orig <= 4 and 1 <= second <= 4 and orig % 2 != second % 2):
                continue
            x = detour[u]
            if np.any(x < 0) or np.any(x >= 24) or not pub["move_mask"][k,u,second] or pub["terrain"][k, *x] == 2:
                continue
            if health[k,u] < max(30, 4*receipt["cfg"]["unit_move_cost"]) or np.any(np.all(other==x, axis=1)):
                continue
            peers = live[k].copy()
            peers[u] = False
            if np.any(np.all(loc[k,peers] == x, axis=1)) or np.any(np.all((loc[k]+moves[k])[peers] == x, axis=1)):
                continue
            if not np.array_equal(loc[k+1,u],loc[k,u]+moves[k,u]) or not np.array_equal(loc[k+2,u],x+moves[k,u]):
                continue
            opportunities.append((k, int(u), orig, second))
            if k+1<sight and truth["active"][k+1,0] and np.abs(centers-x).max(1).min()<=1:
                hits.append((k, int(u), orig, second))
    return dict(seed=receipt["seed"], team=t, opponent=receipt["opponent"], sight=sight, credit=credit,
                turns=len(opportunities), hits=hits, earliest_gain=sight-1-hits[0][0] if hits else 0)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    a=p.parse_args()
    files=sorted((a.source/"train").glob("*.json"))
    assert len(files)==160
    rows=[analyze(f.parent,json.loads(f.read_text())) for f in files]
    assert len({r["seed"] for r in rows})==len(rows)
    gains=np.array([r["earliest_gain"] for r in rows])
    moment=sum(bool(r["hits"]) for r in rows)
    q=dict(cards=len(rows),cards_with_corner=sum(r["turns"]>0 for r in rows),
        total_corners=sum(r["turns"] for r in rows),cards_with_possible_earlier_sight=moment,
        possibilities=sum(len(r["hits"]) for r in rows),potential_mean=float(gains.mean()),
        passed=bool(moment>=8 and gains.mean()>=1))
    for n,obj in (("ergebnis.json",q),):
        (HERE/n).write_text(json.dumps(obj,indent=2)+"\n")
    (HERE/"karten.jsonl.gz").write_bytes(gzip.compress(("\n".join(json.dumps(r,separators=(",",":")) for r in rows)+"\n").encode(),mtime=0))
    print(q)


if __name__=="__main__":
    main()
