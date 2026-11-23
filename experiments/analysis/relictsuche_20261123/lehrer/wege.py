"""Look for exact public starting positions for short successful demonstrated routes on the opposite history."""
from hashlib import sha256
import gzip
import json
from pathlib import Path

import numpy as np

from archiv import ARCHIVE, DELTA, HERE, is_moved, read


def candidates(seed, team, src, dst, events, teacher, student, cost, sap_range):
    """Retrospective filter on actual independent trajectories, not interventional labels."""
    start, end = events[student], events[teacher]
    sight = end["first_sight"]
    finder = end["finder"]
    nondelayed = (sight < start["first_sight"] and end["first_credit"] <= start["first_credit"] and
                  end["win_match"] >= start["win_match"] and end["points70"]-end["enemy70"] >= start["points70"]-start["enemy70"])
    if not nondelayed or not finder or len(finder["possible"]) != 1 or not finder["moved"]:
        return nondelayed, []
    unit = finder["moved"][0]
    results = []
    for length in range(2, 7):
        begin = sight-length
        if begin < 0 or any(not is_moved(src, team, t, unit) for t in range(begin+1,sight+1)):
            continue
        trajectory = src["units/position"][begin:sight+1,team,unit]
        if len(set(map(tuple, trajectory))) != len(trajectory):
            continue
        first = int(src["commands"][begin,unit,0])
        for t in range(max(1,begin-8), begin+1):
            if t >= min(start["first_sight"],start["first_credit"]+1) or t+length < events["first_active_observation"]:
                continue
            ids = np.flatnonzero(dst["units_mask"][t,team] & (dst["units/energy"][t,team] >= 3*cost))
            foes = dst["units/position"][t,1-team][dst["units_mask"][t,1-team]]
            for uid in map(int,ids):
                pos = dst["units/position"][t,team,uid]
                if (not np.array_equal(pos,trajectory[0]) or int(dst["commands"][t,uid,0]) not in range(5) or
                        int(dst["commands"][t,uid,0]) == first or (len(foes) and
                            np.any(np.abs(foes-pos).max(1) <= sap_range))):
                    continue
                # Only the current public board is used to decide eligibility. Unknown later terrain is explicitly counted.
                tiles = dst["map_features/tile_type"][t,trajectory[1:,0],trajectory[1:,1]]
                if tiles[0] < 0 or np.any(tiles == 2):
                    continue
                live_all = dst["units_mask"][t,team] & (dst["units/energy"][t,team] >= 0)
                peer_ids = np.flatnonzero(live_all & (np.arange(16) != uid))
                cmds = dst["commands"][t,peer_ids,0]
                peer_dest = np.clip(dst["units/position"][t,team,peer_ids]+DELTA[np.where(cmds <= 4,cmds,0)],0,23)
                if np.any((peer_dest == trajectory[1]).all(1)):
                    continue
                results.append(dict(observer=teacher, receiver=student, seed=seed, team=team, teacher_unit=unit,
                    unit=uid, turn=t, teacher_turn=begin, direction=first, original=int(dst["commands"][t,uid,0]),
                    path=trajectory.tolist(), seen_path=int((tiles >= 0).sum()), length=length,
                    energy=int(dst["units/energy"][t,team,uid]), outcome_seen=sight))
    return nondelayed, results


def main():
    from luxai_s3.wrappers import LuxAIS3GymEnv
    rows = json.loads(gzip.decompress((HERE/"sitzpaare.json.gz").read_bytes()))
    env = LuxAIS3GymEnv(numpy_output=True)
    params = {}
    records = []
    try:
        for r in rows:
            seed, team = r["seed"], r["team"]
            if seed not in params:
                _, info = env.reset(seed=seed)
                params[seed] = info["params"]
            paths = {k: ARCHIVE/f"{k}_{seed}_player_{team}.json" for k in ("r3", "v16")}
            data = {k: read(json.loads(v.read_bytes())) for k,v in paths.items()}
            for teacher, receiver in (("r3","v16"),("v16","r3")):
                good, items = candidates(seed,team,data[teacher],data[receiver],r,teacher,receiver,
                                      params[seed]["unit_move_cost"],params[seed]["unit_sap_range"])
                records.append(dict(seed=seed, team=team, teacher=teacher, nondelayed=bool(good), opportunities=items))
    finally:
        env.close()
    out={k: {"nondegraded_seats":sum(v["nondelayed"] for v in records if v["teacher"]==k),
        "matched_seats":sum(bool(v["opportunities"]) for v in records if v["teacher"]==k),
        "matched_paths":sum(len(v["opportunities"]) for v in records if v["teacher"]==k)} for k in ("r3","v16")}
    out.update(records=records, sources={p.name:sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), HERE/"sitzpaare.json.gz")})
    (HERE/"suchwege.json").write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps({k:out[k] for k in ("r3","v16")},indent=2))


if __name__=="__main__":
    main()
