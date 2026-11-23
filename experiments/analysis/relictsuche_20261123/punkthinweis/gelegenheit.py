"""Enumerate public, short, legal-looking paths for a different V16 ship, before a first relic sighting."""
from collections import deque

import numpy as np

from belegung import occupied

DELTA = np.array(((0,0),(0,-1),(1,0),(0,1),(-1,0)),dtype=np.int16)
XY = np.indices((24,24),dtype=np.int16).reshape(2,-1).T
STEP = np.full((576,5),-1,np.int16)
for xy,here in zip(XY,range(576)):
    n = xy[None,:]+DELTA
    ok = ((n>=0)&(n<24)).all(1)
    STEP[here,ok]=n[ok,0]*24+n[ok,1]


def mobile(d,team,t,first,score_prob,cost):
    # Negative-energy slots do not score. A ship with any remaining possibility of having supplied
    # a positive observation is protected, including when that ship has since moved away.
    ever_producer = set()
    visited = np.zeros(576,bool)
    for k in range(first,t+1):
        gain = d["team_points"][k,team]-d["team_points"][k-1,team]
        if gain <= 0:
            continue
        mask = d["units_mask"][k,team] & (d["energy"][k,team] >= 0)
        uid = np.flatnonzero(mask)
        p = d["position"][k,team,uid]
        cells = p[:,0]*24+p[:,1]
        possible = score_prob[cells] > 0.
        ever_producer.update(uid[possible].tolist())
        visited[cells[possible]] = True
    masks = d["units_mask"][t,team] & (d["energy"][t,team] >= 0)
    ids = np.flatnonzero(masks)
    pos = d["position"][t,team,ids]
    cells = pos[:,0]*24+pos[:,1]
    cmds = d["commands"][t,ids,0]
    nxt = np.clip(pos+DELTA[np.where(cmds<=4,cmds,0)],0,23)
    dest = nxt[:,0]*24+nxt[:,1]
    suitable = (cmds <= 4) & (d["energy"][t,team,ids] >= max(10,3*cost)) & ~d["protected"][t,ids]
    suitable &= np.asarray([uid not in ever_producer for uid in ids]) & (score_prob[cells] == 0)
    available = ids[suitable]
    return available, np.asarray(sorted(ever_producer),int), visited, ids, dest


def candidate_paths(d,team,t,first,score_prob,cost):
    units, producers, possible_scored, ids, dest = mobile(d,team,t,first,score_prob,cost)
    blocked = d["terrain"][t].ravel()==2
    target_forbidden = possible_scored.reshape(24,24)
    target_forbidden = (target_forbidden | target_forbidden[::-1,::-1].T | d["known_points"][t]).ravel()
    for side in (0,1):
        target_forbidden[occupied(d,side,t)] = True
    target_forbidden[dest] = True
    proposals=[]
    current_pos=d["position"][t,team]
    for uid in units:
        start=int(current_pos[uid,0]*24+current_pos[uid,1])
        reserved=set(dest[ids!=uid].tolist())
        original=int(d["commands"][t,uid,0])
        # Exclude targets that the original first move could reach just as quickly.
        keep_first = {}
        original_next = int(STEP[start,original])
        if original > 0 and original_next >= 0 and not blocked[original_next]:
            keep_first[original_next] = 1
            frontier = deque([original_next])
            while frontier:
                at = frontier.popleft()
                depth = keep_first[at]
                if depth < 6:
                    for nxt in STEP[at,1:]:
                        nxt = int(nxt)
                        if nxt >= 0 and nxt not in keep_first and not blocked[nxt]:
                            keep_first[nxt] = depth+1
                            frontier.append(nxt)
        queue=deque()
        seen={start}
        for move in range(1,5):
            loc=int(STEP[start,move])
            if (move!=original and d["move_mask"][t,uid,move] and loc>=0 and not blocked[loc] and loc not in reserved):
                queue.append((loc,move,(loc,)))
                seen.add(loc)
        while queue:
            cell,move,path=queue.popleft()
            if not target_forbidden[cell] and len(path) < keep_first.get(cell, 100):
                proposals.append((int(uid),cell,move,path))
            if len(path)>=6:
                continue
            for mov in range(1,5):
                nxt=int(STEP[cell,mov])
                if nxt>=0 and nxt not in seen and not blocked[nxt]:
                    seen.add(nxt)
                    queue.append((nxt,move,(*path,nxt)))
    return units,producers,proposals


def choose(proposals,prob):
    if not proposals:
        return None
    def rank(p):
        uid,cell,move,path=p
        return (float(prob[cell])/(1+len(path)/4),float(prob[cell]),-len(path),-uid,-cell,-move)
    item=max(proposals,key=rank)
    if prob[item[1]] <= 0:
        return None
    return item


def grade(item,d,truth,team,t,prob):
    if item is None:
        return None
    uid,cell,move,path=item
    spots=truth["points"].ravel()
    arrival=t+len(path)
    occupied_future=own_future=other_future=old_unique=available_slots=0
    first_other=first_own=None
    late_turns=late_available=late_original=0
    for tick in range(arrival,min(102,arrival+20)):
        if tick == 101:
            p = truth["end_position"]
            live = truth["end_live"] & (truth["end_energy"] >= 0)
        else:
            p=d["position"][tick,team]
            live=d["units_mask"][tick,team] & (d["energy"][tick,team]>=0)
        ids=np.flatnonzero(live)
        tile=p[ids,0]*24+p[ids,1]
        here=ids[tile==cell]
        if len(here) and first_own is None:
            first_own=tick
        if np.any(here!=uid) and first_other is None:
            first_other=tick
        if tick>=arrival+5:
            if tick<arrival+15:
                late_turns+=1
                late_available+=int(spots[cell] and not np.any(here!=uid))
                if uid in ids:
                    original=int(p[uid,0]*24+p[uid,1])
                    late_original+=int(spots[original] and np.count_nonzero(tile==original)==1)
            continue
        occupied_future += int(len(here)>0)
        other_future += int(np.any(here!=uid))
        own_future += int(uid in here)
        if spots[cell] and not np.any(here!=uid):
            available_slots+=1
        if uid in ids:
            original=int(p[uid,0]*24+p[uid,1])
            if spots[original] and np.count_nonzero(tile==original)==1:
                old_unique+=1
    return dict(uid=uid,turn=t,target=list(map(int,divmod(cell,24))),first_command=move,
                original=int(d["commands"][t,uid,0]),steps=len(path),route=[list(map(int,divmod(k,24))) for k in path],
                known_steps=int((d["terrain"][t].ravel()[list(path)]>=0).sum()),prob=float(prob[cell]),
                real_score=bool(spots[cell]),baseline_used_target5=occupied_future,
                baseline_other_used_target5=other_future,baseline_ship_used_target5=own_future,
                available_scoring_slots5=available_slots,baseline_ship_unique_points5=old_unique,
                later_observed_turns=late_turns,later_available_slots=late_available,later_original_unique=late_original,
                first_baseline_occupation_until20=first_own,first_other_occupation_until20=first_other)
