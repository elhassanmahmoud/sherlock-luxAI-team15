"""Infer from public rows only, then compare with independent referee and V16 readouts."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import sys

from beweise import CANONICAL, Evidence, MIRROR, PAIR, folded, indices, worlds
from spuren import HERE, WORK, jobs, manifest, sha, stamp, write_once
from spielen import require
from auswerten import save_archive

CATEGORIES=("extra","dead","local_extra","only_persistent","carried","all_false_dead",
            "legal_adj","strict_adj","strict_four","dead_adj","dead_four","persistent_adj","persistent_four","carried_four")
DELTAS=((0,0),(0,-1),(1,0),(0,1),(-1,0))
NEIGHBORS={}
for cell in range(576):
    x,y=divmod(cell,24)
    NEIGHBORS[cell]=[(d,24*(x+dx)+y+dy) for d,(dx,dy) in enumerate(DELTAS)
                     if d and 0<=x+dx<24 and 0<=y+dy<24]


def access(public, policy, target, always_positive):
    """World-cell masks. Immediate availability is separated from a stationary-board path."""
    witnesses={}
    if not target:
        return 0,0,0,witnesses
    safe=int(policy["known_passable"],16)
    visible=int(policy["visible"],16)
    exclusion=set(public["occupied"])|set(policy["enemy"])|set(policy["planned"])
    strict=target&visible&safe
    for xy in exclusion:strict &= ~(1<<xy)
    enemy=set(policy["enemy"])
    broad=immediate=multi=0
    for uid,origin,original,assigned,legality in policy["free"]:
        if (always_positive>>origin)&1 or (assigned is not None and (always_positive>>assigned)&1):
            continue
        for d,neighbor in NEIGHBORS[origin]:
            if not (legality>>d)&1:continue
            bit=1<<neighbor
            if target&bit:broad |= bit
            if d==original or neighbor in enemy or not safe&bit:continue
            if strict&bit:
                immediate |=bit
                witnesses.setdefault(neighbor,[uid,[origin,neighbor],original,d])
            if not strict:continue
            visited={origin,neighbor}
            frontier=[(neighbor,[origin,neighbor])]
            for depth in range(1,5):
                following=[]
                for here,path in frontier:
                    here_bit=1<<here
                    if strict&here_bit:
                        multi |=here_bit
                        old=witnesses.get(here)
                        if old is None or len(old[1])>len(path):
                            witnesses[here]=[uid,path,original,d]
                    if depth==4:continue
                    for _,nxt in NEIGHBORS[here]:
                        if nxt in visited or nxt in enemy or not(safe>>nxt)&1:continue
                        visited.add(nxt)
                        following.append((nxt,[*path,nxt]))
                frontier=following
                if not frontier:break
    return broad,immediate,multi,witnesses


def calculate(game):
    full=Evidence()
    local=Evidence(forget_at_match=True)
    frames=[];first={};vf={};seenproofs={};hits={}
    checks=Counter();old_truth=None;stable_truth=None;stable_key=None
    expected=game["public"]
    require(len(expected)==len(game["policy"])==len(game["referee"])==303,"Incomplete raw game")
    for raw,policy,judge in zip(expected,game["policy"],game["referee"],strict=True):
        # This is the only input to either reasoner. It excludes observations of the opposing fleet, V16 labels and referee data.
        added=full.observe(raw)
        local.observe(raw)
        t,ms=raw["step"],raw["ms"]
        truth=int(judge,16)
        require(not full.positive&~truth and not full.negative&truth,"False main certificate")
        require(not local.positive&~truth and not local.negative&truth,"False control certificate")
        require(not local.positive&~full.positive,"Match-local control found unsupported extra fact")
        require(old_truth is None or not old_truth&~truth,"Nonmonotone referee")
        old_truth=truth
        if ms and full.stable:
            if stable_key==full.epoch:
                require(stable_truth==truth,"Truth changed in a claimed stable epoch")
            stable_key,stable_truth=full.epoch,truth
        else:
            stable_key=stable_truth=None
        checks["observations"]+=1
        checks["usable_equations"]+=int(ms>0)
        checks["main_positive_pair_ticks"]+=full.positive.bit_count()
        checks["main_negative_pair_ticks"]+=full.negative.bit_count()
        checks["local_positive_pair_ticks"]+=local.positive.bit_count()
        checks["local_negative_pair_ticks"]+=local.negative.bit_count()
        for k in added:
            first[k]=t
            seenproofs[k]=full.proofs[k]
        point=int(policy["point"],16)
        dead=int(policy["dead"],16)
        checks["v16_false_positive_world_ticks"]+=(point&~truth).bit_count()
        checks["v16_false_dead_world_ticks"]+=(dead&truth).bit_count()
        for k in indices(folded(point)):
            vf.setdefault(k,t)
        p=full.positive
        known=folded(point)
        extra=p&~known
        dead_proved=folded(dead & worlds(p))
        carried=sum(1<<k for k in indices(extra) if first[k]//101 < t//101)
        only=extra&~local.positive
        target_world=worlds(extra)| (dead & worlds(p))
        broad,adj,four,witness=access(raw,policy,target_world,worlds(p)|point) if ms else (0,0,0,{})
        broad,adj,four=map(folded,(broad,adj,four))
        vals=dict(extra=extra,dead=dead_proved,local_extra=local.positive&~known,only_persistent=only,carried=carried,
                  all_false_dead=folded(dead&truth),legal_adj=broad,strict_adj=adj,strict_four=four,dead_adj=adj&dead_proved,
                  dead_four=four&dead_proved,persistent_adj=adj&only,persistent_four=four&only,carried_four=four&carried)
        for cell,route in witness.items():
            k=PAIR[cell]; label=(k,t//101)
            old=hits.get(label)
            if old is None or len(route[1])<len(old["path"]):
                hits[label]=dict(step=t,cell=cell,pair=k,uid=route[0],path=route[1],v16=route[2],other_direction=route[3],
                                 at_v16_dead=bool((dead>>cell)&1),prior_match=bool(carried>>k&1),
                                 only_persistent=bool(only>>k&1))
        frames.append(dict(t=t,p=format(p,"x"),n=format(full.negative,"x"),local=format(local.positive,"x"),
                           **{k:format(v,"x") for k,v in vals.items() if v}))
    facts=[dict(pair=k,proof=t,v16=vf.get(k),lead=vf.get(k,303)-t,witness=seenproofs[k]) for k,t in sorted(first.items())]
    return dict(seed=game["seed"],team=game["team"],group=game["group"],win=game["win"],action_hash=game["action_hash"],checks=dict(checks),
                original_source=game["source"],points=facts,reach_examples=list(hits.values()),frames=frames)


def archive(group):
    keys=jobs(group)
    expected={WORK/group/f"{s}_{t}.json" for s,t in keys}
    require(len(expected)==len(keys) and expected==set((WORK/group).glob("*.json")),"Incomplete game set, no analysis")
    src=manifest()
    require(json.loads((WORK/"herkunft.json").read_text())==src,"Source drift")
    result=[];games=[]
    for source in sorted(expected):
        r=json.loads(source.read_text())
        require(r["source"]==stamp(src) and r["sensor"]==1 and r["agent_errors"]==[0,0],"Bad original sources")
        result.append(calculate(r));games.append(r)
    out=HERE/group;out.mkdir(exist_ok=True)
    rawpath=out/"beobachtungen.jsonl.gz"
    require(save_archive(games,rawpath)==games, "Original archive differs")
    proofpath=out/"beweise.jsonl.gz"
    require(save_archive(result,proofpath)==result,"Proof archive differs")
    checks=Counter()
    tallies={};strict=[]
    for r in result:
        checks.update(r["checks"])
        for q in r["points"]:
            if q["lead"]>0:strict.append((r["seed"],r["team"],q["pair"],q["lead"],q["v16"]))
    for cat in CATEGORIES:
        by_seat=set();by_map=set();maps=set();seats=set();ticks=0;activity=[0,0,0]
        for r in result:
            for f in r["frames"]:
                mask=int(f.get(cat,"0"),16)
                if not mask:continue
                s,t=r["seed"],r["team"]
                seats.add((s,t));maps.add(s)
                ticks+=mask.bit_count()
                activity[f["t"]//101]+=mask.bit_count()
                for k in indices(mask):
                    by_map.add((s,k));by_seat.add((s,t,k))
        tallies[cat]=dict(maps=len(maps),seats=len(seats),pairs_per_map=len(by_map),pairs_per_seat=len(by_seat),
                          pair_ticks=ticks,by_match_ticks=activity)
    summary=dict(group=group,games=len(games),maps=len(games)//2,checks=dict(checks),categories=tallies,
                 strict_leads=dict(seat_pairs=len(strict),map_pairs=len({(r[0],r[2]) for r in strict}),maps=len({r[0] for r in strict}),
                                   seats=len({r[:2] for r in strict}),never_confirmed=sum(r[-1] is None for r in strict),
                                   at_least_three_steps=sum(r[3]>=3 for r in strict)),
                 range_gate_passed=True,action_hashes={f"{r['seed']}_{r['team']}":r["action_hash"] for r in result},
                 raw_sha256=sha(rawpath),proof_sha256=sha(proofpath),source=src,algorithm=sha(HERE/"beweise.py"),
                 evaluator=sha(Path(__file__)))
    write_once(out/"ergebnis.json",summary)
    print(group,len(result),"complete original games",json.dumps(tallies,sort_keys=True),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("group",choices=("archiv","frisch"))
    archive(parser.parse_args().group)
