"""python coordination.py STUDY_CHECKOUT IMITATION_DATA NEW_RESULT.json — NumPy-only, one process."""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np


DELTA = np.array([(0,0),(0,-1),(1,0),(0,1),(-1,0),(0,0)])
DIMS = (6, 3, 4, 2, 10, 4, 3, 3)
GROUPS = int(np.prod(DIMS))
INVENTORIES = {
    "combat_advice_20261115/v14_advice_audit.json": "f5efa80451d5c1bea61b387c96960b6e4f695fff92451f050798462aaec14268",
    "movement_dagger_20261115/corpus.json": "fed298f9dd84100c119423e2a8d9c5607291a54a028b3ca560b9d454e64d405f",
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def index(repo, local):
    reports = repo / "experiments/analysis"
    for filename, expected in INVENTORIES.items():
        if digest(reports / filename) != expected:
            raise ValueError(f"Unexpected published corpus inventory: {filename}")
    file = reports / "own_command_20261115/archive/history.py"
    spec = importlib.util.spec_from_file_location("archived_history", file)
    history = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(history)
    return history.index(repo, local), digest(file)


def counts_at(stage, xy, pos, target, same, area, height, projected):
    raw = np.bincount(stage * area + xy[:, 0] * height + xy[:, 1])
    cells = stage * area + pos[:, 0] * height + pos[:, 1]
    ends = stage * area + target[:, 0] * height + target[:, 1]
    raw = np.pad(raw, (0, max(0, int(max(cells.max(), ends.max())) + 1 - len(raw))))
    return raw[cells] - (same if projected else 1), raw[ends] - (1 if projected else same)


def groups_for_board(boards, step, pos, base, features, match):
    _, _, w, h = boards.shape
    f = features
    energy = np.rint(f[:,2] * 400)
    move_cost, sap_cost = np.rint(f[:,6] * 5), np.rint(f[:,7] * 50)
    if np.any((energy < move_cost) != (f[:,3] > .5)):
        raise ValueError("Archived movement energy cannot be recovered")
    target = pos + DELTA[base]
    legal = np.all((target >= 0) & (target < [w,h]), axis=1)
    x, y = np.clip(target, [0,0], [w-1,h-1]).T
    legal &= (boards[step,5,x,y] == 0) & (energy >= move_cost)
    moving = (base > 0) & (base < 5)
    target[~(legal & moving)] = pos[~(legal & moving)]
    same = np.all(pos == target, axis=1).astype(int)
    now = counts_at(step, pos, pos, target, same, w*h, h, False)
    later = counts_at(step, target, pos, target, same, w*h, h, True)
    if min(arr.min() for arr in (*now,*later)) < 0:
        raise ValueError("Negative other-ship count")
    x, y = pos.T
    # The archival SideRecord contains every own ship with energy >= 0. The public board/features
    # can additionally include a dying, already negative ship, for which there is no projected order.
    # Count only the same decision-capable population for BOTH the physical and projected features.
    public = np.rint(boards[step,8,x,y].astype(float) * 4/127)
    if np.any(public < np.minimum(now[0]+1,4)) or np.any(public != np.rint(f[:,37] * 4)):
        raise ValueError("Live ship rows conflict with the public physical unit counts")
    has_target = f[:,33] > .5
    assigned = pos + np.rint(f[:,30:32] * [w,h]).astype(int)
    if np.any(has_target & ~np.all((assigned >= 0) & (assigned < [w,h]), axis=1)):
        raise ValueError("Invalid current assignment")
    ax, ay = np.clip(assigned, [0,0], [w-1,h-1]).T
    to_point = (boards[step,0,ax,ay] > 0) & has_target
    role = 2*(f[:,34]>.5).astype(int) + (f[:,38]>.5)
    direction = np.where(has_target,(1+np.sign(f[:,30]))*3+1+np.sign(f[:,31]),9).astype(int)
    eg = np.select([f[:,3]>.5,energy<sap_cost,energy<2*sap_cost],[0,1,2],3)
    now0, now1 = (np.minimum(a,2) for a in now)
    g = np.ravel_multi_index((base,match,role,to_point.astype(int),direction,eg,now0,now1),DIMS)
    extra = np.minimum(later[0],2)*3 + np.minimum(later[1],2)
    return g, extra, dict(public_origin_includes_dying=int(np.count_nonzero(public > np.minimum(now[0]+1,4))),
                         invalid_v14_moves=int((moving & ~legal).sum()),
                         different_projection=int(np.count_nonzero(extra != (3*now0+now1))))


def read(seed, side, opp, path):
    with np.load(path, allow_pickle=False) as z:
        if any(json.loads(z["meta"].item())[k] != v for k,v in (("seed", seed), ("side", side), ("opponent",opp))):
            raise ValueError(f"Wrong identity in {path}")
        step, uid, pos = (z[k].astype(int) for k in ("step","uid","pos"))
        obs_step = z["global_step"][step].astype(int)
        if (np.any(obs_step < 1) or np.any(obs_step > 302) or not np.array_equal(obs_step % 101,z["mstep"])
            or np.any(obs_step % 101 == 0) or np.unique(step*16 + uid).size != len(step)
            or np.any((uid<0)|(uid>=16)) or np.any((pos<0)|(pos>=24))):
            raise ValueError(f"Incomplete per-step unit identities in {path}")
        base = z["base_act"].astype(int)
        if np.any((base<0)|(base>5)):
            raise ValueError("Invalid V14 command")
        g, extra, audit = groups_for_board(z["planes"],step,pos,base,z["feats"].astype(np.float32),obs_step//101)
        # Only after extracting the full features are the teacher labels read.
        y = z["act"].astype(int)
        if np.any((y<0)|(y>5)):
            raise ValueError("Invalid teacher class")
    return g, extra, base, y, audit


def score(base, y, pb, ph, seen):
    idx = np.arange(len(y))
    b, h = pb.argmax(1) == y, ph.argmax(1) == y
    ds = (y != base) & (y > 0) & (y < 5)
    return dict(rows=len(y), control_right=int(b.sum()), projection_right=int(h.sum()),
                corrected=int((~b & h).sum()), damaged=int((b & ~h).sum()),
                control_loss=float(-np.log(pb[idx,y]).sum()), projection_loss=float(-np.log(ph[idx,y]).sum()),
                disagreement_directions=int(ds.sum()), disagreement_control=int(b[ds].sum()),
                disagreement_projection=int(h[ds].sum()), disagreement_corrected=int((~b & h & ds).sum()),
                disagreement_damaged=int((b & ~h & ds).sum()), seen_train_cell=int(seen.sum()))


def summarize(maps):
    keys = sorted(maps)
    vals = {k: np.array([maps[s][k] for s in keys]) for k in maps[keys[0]]}
    n = vals["rows"]
    ds = vals["disagreement_directions"]
    draw = np.random.default_rng(2711).integers(0,len(keys),size=(10000,len(keys)))
    def estimate(v, den, scale):
        slopes = scale*v[draw].sum(1)/den[draw].sum(1)
        return dict(delta=float(scale*v.sum()/den.sum()), ci95=np.quantile(slopes,[.025,.975]).tolist(),
                    positive_maps=int((v>0).sum()), negative_maps=int((v<0).sum()))
    return dict(maps=len(keys),totals={k:a.sum().item() for k,a in vals.items()},
                accuracy_pp=estimate(vals["projection_right"]-vals["control_right"],n,100),
                loss_nats=estimate(vals["projection_loss"]-vals["control_loss"],n,1),
                disagree_direction_pp=estimate(vals["disagreement_projection"]-vals["disagreement_control"],ds,100))


def synthetic_projection():
    # (0,0): one NORTH blocked at edge, one moves east. Two occupants of (1,0) either SAP or seek an asteroid.
    pos = np.array([[0,0],[0,0],[1,0],[1,0],[2,2]])
    board = np.zeros((1,16,24,24), dtype=np.int8)
    board[0,8,0,0] = board[0,8,1,0] = 64
    board[0,8,2,2] = 32
    board[0,5,2,0] = 127
    f = np.zeros((5,79))
    f[:,2],f[:,6],f[:,7] = .1,.6,.8
    f[:,37] = [.5,.5,.5,.5,.25]
    f[4,2], f[4,3] = 0,1
    g,ex,a = groups_for_board(board,np.zeros(5,int),pos,np.array([1,2,5,2,1]),f,np.zeros(5,int))
    physical = np.array(np.unravel_index(g,DIMS)[-2:]).T
    assert physical.tolist() == [[1,1],[1,2],[1,1],[1,1],[0,0]]
    assert ex.tolist() == [0,5,8,8,0] and a["invalid_v14_moves"] == 3


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    for name in ("repo","local","output"):
        cli.add_argument(name, type=Path)
    a = cli.parse_args()
    if a.output.exists():
        raise FileExistsError(a.output)
    synthetic_projection()
    files, root_source = index(a.repo, a.local)
    count = np.zeros((GROUPS,9,6),np.int32)
    audits = defaultdict(Counter)
    for cohort, train, seed, side, opp, path in files:
        if train:
            g, x, _, y, audit = read(seed, side, opp, path)
            np.add.at(count,(g,x,y),1)
            audits[cohort+"/train"].update(audit,rows=len(y))
    simple = count.sum(1)
    per_act = simple.reshape(6,-1,6).sum(1)
    prior = (per_act+.5)/(per_act.sum(1,keepdims=True)+3)
    pb = (simple+12*np.repeat(prior,GROUPS//6,axis=0))/(simple.sum(1,keepdims=True)+12)
    pred = defaultdict(lambda: defaultdict(Counter))
    seats = []
    for cohort, train, seed, side, opp, path in files:
        if not train:
            g,x,base,y,audit = read(seed,side,opp,path)
            counts = count[g,x]
            ph = (counts+24*pb[g])/(counts.sum(1,keepdims=True)+24)
            if not np.allclose(ph.sum(1),1) or not np.allclose(pb[g].sum(1),1):
                raise ValueError("Invalid probability normalization")
            values = score(base,y,pb[g],ph,counts.sum(1)>0)
            audits[cohort+"/validation"].update(audit,rows=len(y))
            seats.append(dict(cohort=cohort,seed=seed,side=side,opponent=opp,**values))
            for group in ("all",cohort,cohort+"/"+opp,"opponent/"+opp):
                pred[group][seed].update(values)
    result = dict(source_sha256=digest(__file__), index_source_sha256=root_source, inventories=INVENTORIES,
                  verified_archives=len(files), audits=audits, tables={k:summarize(m) for k,m in pred.items()},
                  heldout_seats=seats)
    with a.output.open("x") as stream:
        json.dump(result,stream,indent=2,sort_keys=True,allow_nan=False)
        stream.write("\n")
    for name,r in sorted(result["tables"].items()):
        print(name,r["totals"]["rows"],r["totals"]["disagreement_directions"],
              *[tuple(round(v,4) for v in [r[k]["delta"],*r[k]["ci95"]])
                for k in ("disagree_direction_pp","accuracy_pp","loss_nats")])


if __name__ == "__main__":
    main()
