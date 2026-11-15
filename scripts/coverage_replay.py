"""Offline coverage-repair replay on exactly the first twelve DAgger development maps."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np

from agents.sherlock import geometry as geo
from scripts.collect_combat_advice import filename, opponent_for
from scripts.coverage_restore import choose_restorations

SEEDS = range(7272200, 7272212)
SIDES = ("player_0","player_1")
INPUT_SHA = "2664d3bcd013195ed1d0acd5f74c1f19d8bb99475839190a5609e40dfad7731a"
PROTOCOL_SHA = "50bf0bb810f7b913acce8940937d335ebf180bc796457dcf880ffa6743ec2724"
DELTAS = np.array([(0,0),(0,-1),(1,0),(0,1),(-1,0),(0,0)])
FIELDS = ("planes","global_step","step","uid","pos","feats","mask","base_act","base_sdx","base_sdy",
          "played_act","played_sdx","played_sdy","act","sdx","sdy")
R1_CONTROL = dict(boards=7200, unit_rows=76195, changed_orders=8035, lost_vs_base=459,
                  gained_vs_base=98, restored_all_seen=321)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def keys_and_hash(data_dir):
    keys = {(s,side): data_dir/filename(s,side) for s in SEEDS for side in SIDES}
    raw = "".join(f"{p.name} {digest(p)}\n" for p in sorted(keys.values()))
    if hashlib.sha256(raw.encode()).hexdigest() != INPUT_SHA or digest(data_dir/"protocol.json") != PROTOCOL_SHA:
        raise ValueError("Unexpected original archive set or data protocol")
    return keys


def gated_classes(base, raw, confidence):
    accept = (confidence>=0.70) & (raw!=geo.SAP) & (base!=geo.SAP)
    return np.where(accept,raw,base)


def commands_world(canonical, ids, team):
    full = np.zeros((16,3),int)
    converted = canonical.copy()
    if team:
        movement = converted[:,0]!=geo.SAP
        converted[movement,0] = geo.MIRROR_DIR[canonical[movement,0]]
        converted[~movement,1:] = -canonical[~movement,1:][:,::-1]
    full[ids] = converted
    return full


def known_coverage(pos, classes, known):
    # All final movement commands reaching this helper were checked as payable and passable.
    return {tuple(cell) for cell in pos+DELTAS[classes] if known[tuple(cell)]}


def legal_projected_classes(pos, classes, energy, cost, blocked):
    move = (classes>0) & (classes<geo.SAP)
    target = pos+DELTAS[classes]
    inside = np.all((target>=0)&(target<24),axis=1)
    x,y = np.clip(target,0,23).T
    legal = ~move | ((energy>=cost) & inside & ~blocked[x,y])
    return np.where(legal,classes,geo.STAY),legal


def board_view(plane, pos, energy, ids, team, sap_range):
    known, blocked = plane[0]>0, plane[5]>0
    own = np.full((2,16,2),-1,int)
    energies = np.full((2,16),-1,int)
    active = np.zeros((2,16),bool)
    own[team,ids] = geo.mirror_positions(pos) if team else pos
    energies[team,ids], active[team,ids] = energy, True
    asteroid_world = geo.mirror_map(blocked) if team else blocked
    public = dict(units=dict(position=own,energy=energies),units_mask=active,
                  map_features=dict(tile_type=np.where(asteroid_world,2,-1)))
    ally_pos = np.full((16,2),-1,int)
    ally_pos[ids] = pos
    enemy = np.argwhere(plane[10]>0)
    ctx = dict(ally_pos=ally_pos,point_tiles=known,passable=~blocked,enemy_coords=enemy,sap_range=sap_range,
               enemy_energies=np.zeros(len(enemy),int))
    return public,ctx,blocked


def measure_board(rows, ref, name, counts, output):
    ids,pos,energy,cost,public,ctx,blocked,team,plane,stamp = rows
    base,base_world,B,original = ref
    projected,valid = legal_projected_classes(pos,original,energy,cost,blocked)
    # In movement mode illegal new orders fall back to the native command, including its offsets.
    rejected = ~valid & (original!=base[:,0])
    classes = np.where(rejected,base[:,0],original)
    if name=="r1" and rejected.any():
        raise ValueError("Archived played R1 command failed the receipt checks")
    projected = np.where(rejected,base[:,0],projected)
    canon = base.copy()
    different = classes!=base[:,0]
    canon[different,0],canon[different,1:] = classes[different],0
    world = commands_world(canon,ids,team)
    R = known_coverage(pos,projected,ctx["point_tiles"])
    counts.update(boards=1,unit_rows=len(ids),changed_orders=int(different.sum()),rejected_moves=int(rejected.sum()),
                  lost_vs_base=len(B-R),gained_vs_base=len(R-B),known_before_restore=len(R))
    enemy = ctx["enemy_coords"]
    enemy_positive = plane[11][tuple(enemy.T)]>0
    event = dict(model=name,**stamp,lost_vs_base=sorted(B-R),gained_vs_base=sorted(R-B))
    all_seen_fixed = None
    for mode in ("all_seen","positive_energy"):
        # Nonpositive quantized energy can mean a live 0/1-energy enemy or a negative-energy remnant.
        ctx["enemy_energies"] = np.zeros(len(enemy),int) if mode=="all_seen" else np.where(enemy_positive,0,-1)
        uids = choose_restorations(public,ctx,team,bool(team),{"unit_move_cost":cost},base_world,world,Counter())
        selected = np.isin(ids,uids)
        final = np.where(selected,base[:,0],projected)
        covered = known_coverage(pos,final,ctx["point_tiles"])
        added,removed = covered-R,R-covered
        counts.update({f"restored_{mode}":len(added),f"last_fields_lost_{mode}":len(removed),
                       f"restored_boards_{mode}":int(bool(added))})
        if removed or len(added)!=len(uids) or not added<=B:
            raise ValueError("Coverage bookkeeping mismatch")
        event[mode] = dict(uids=uids,added=sorted(added),removed=sorted(removed))
        if mode=="all_seen":
            all_seen_fixed = covered
            counts["known_after_restore"] += len(covered)
        else:
            counts["energy_assumption_different_fields"] += len(all_seen_fixed ^ covered)
            counts["energy_assumption_different_boards"] += int(all_seen_fixed != covered)
    if B!=R or event["all_seen"]["uids"] or event["positive_energy"]["uids"]:
        output.write(json.dumps(event,default=int,separators=(",",":"))+"\n")
    return classes,world,R,all_seen_fixed


def measure(path,members,out):
    with np.load(path,allow_pickle=False) as z:
        meta=json.loads(z["meta"].item())
        a={k:z[k] for k in FIELDS}
    if members is not None:
        from scripts.coverage_replay_inference import predict
        raw,score=predict(members,a)
    gs,frame_nr=a["global_step"],a["step"]
    bounds=np.searchsorted(frame_nr,np.arange(len(gs)+1))
    cols=lambda prefix:np.column_stack([a[prefix+k] for k in ("act","sdx","sdy")]).astype(int)
    base_all,played_all,teacher_all=cols("base_"),cols("played_"),cols("")
    counts=defaultdict(Counter)
    team=int(meta["side"][-1])
    for j,g in enumerate(gs):
        sl=slice(bounds[j],bounds[j+1])
        ids,pos,feat=a["uid"][sl],a["pos"][sl].astype(int),a["feats"][sl].astype(float)
        energy=np.rint(400*feat[:,2]).astype(int)
        costs=np.rint(5*feat[:,6]).astype(int)
        if len(set(costs))!=1 or not np.array_equal(energy<costs,feat[:,3]>0):
            raise ValueError("Unrecoverable own movement cost")
        cost=int(costs[0])
        public,ctx,blocked=board_view(a["planes"][j],pos,energy,ids,team,meta["sap_range"])
        stamp=dict(seed=meta["seed"],side=meta["side"],opponent=meta["opponent"],global_step=int(g))
        rows=ids,pos,energy,cost,public,ctx,blocked,team,a["planes"][j],stamp
        base,played=base_all[sl],played_all[sl]
        if not legal_projected_classes(pos,base[:,0],energy,cost,blocked)[1].all():
            raise ValueError("Unexpected archived V14 movement endpoint")
        B=known_coverage(pos,base[:,0],ctx["point_tiles"])
        world=commands_world(base,ids,team)
        r1,world1,C1,_=measure_board(rows,(base,world,B,played[:,0]),"r1",counts["r1"],out)
        if not np.array_equal(world1,commands_world(played,ids,team)):
            raise ValueError("Lost the recorded full R1 world command")
        teacher=teacher_all[sl]
        teacher_world=commands_world(teacher,ids,team)
        counts["r1"]["matches_teacher_world_order"] += int(np.all(world1[ids]==teacher_world[ids],axis=1).sum())
        counts["v14"]["matches_teacher_world_order"] += int(np.all(world[ids]==teacher_world[ids],axis=1).sum())
        if members is None:
            continue
        c=counts["r2"]
        pred=gated_classes(base[:,0],raw[sl],score[sl])
        c["masked_top_matches_teacher_class"]+=int((raw[sl]==teacher[:,0]).sum())
        c["masked_top_matches_v14_class"]+=int((raw[sl]==base[:,0]).sum())
        c["confidence_at_least_070"]+=int((score[sl]>=.70).sum())
        c["confident_different_nonsap_classes"]+=int((pred!=base[:,0]).sum())
        c["masked_top_matches_r1_class"]+=int((raw[sl]==r1).sum())
        c["threshold_within_0.005"]+=int((abs(score[sl]-.70)<=.005).sum())
        r2,world2,C2,_=measure_board(rows,(base,world,B,pred),"r2",c,out)
        c["r2_matches_recorded_r1_class"]+=int((r1==r2).sum())
        c["r2_matches_recorded_r1_world_order"]+=int(np.all(world1[ids]==world2[ids],axis=1).sum())
        c["r2_matches_teacher_world_order"]+=int(np.all(world2[ids]==teacher_world[ids],axis=1).sum())
        c["lost_vs_recorded_r1"]+=len(C1-C2)
        c["gained_vs_recorded_r1"]+=len(C2-C1)
    return stamp["seed"],stamp["side"],stamp["opponent"],counts


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data",type=Path,required=True)
    select=p.add_mutually_exclusive_group(required=True)
    select.add_argument("--model",type=Path)
    select.add_argument("--recorded-r1-only",action="store_true")
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    keys=keys_and_hash(args.data)
    members=model_sha=None
    if args.model:
        from scripts.experiment import limit_threads
        from scripts.coverage_replay_inference import load_r2
        limit_threads()
        members,validated,model_sha=load_r2(args.model,args.data)
        if keys!=validated:
            raise ValueError("Checkpoint validation paths differ from the pinned archives")
    args.out.mkdir(parents=True,exist_ok=False)
    games=[]; groups=defaultdict(lambda:defaultdict(Counter))
    with (args.out/"fields.jsonl").open("x") as events:
        for key,path in keys.items():
            seed,side,opponent,c=measure(path,members,events)
            if (seed,side)!=key or opponent_for(seed)!=opponent:
                raise ValueError("Archive key mismatch")
            games.append(dict(seed=seed,side=side,opponent=opponent,counts=c))
            for name,cnt in c.items():
                for group in ("all",opponent,str(seed)):
                    groups[group][name].update(cnt)
    verified={k:groups["all"]["r1"][k] for k in R1_CONTROL}
    if verified!=R1_CONTROL:
        raise ValueError(f"Recorded R1 control differs: {verified}")
    report=dict(model_sha256=model_sha,archive_set_sha256=INPUT_SHA,protocol_sha256=PROTOCOL_SHA,
                r1_control=verified,summary=groups,games=games,fields_sha256=digest(args.out/"fields.jsonl"),
                sources_sha256={f.name:digest(f) for f in [Path(__file__),Path(__file__).with_name("coverage_restore.py"),
                                                                      Path(__file__).with_name("coverage_replay_inference.py")]},
                limitations=["R2 forward on quantized original R1 observations; no counterfactual game trajectory.",
                             "Raw means masked canonical class, before the confidence and movement gates. SAP world deltas come from V14.",
                             "Recorded R1 orders and alive unit rows are exact. Direct sensor mask and individual enemy energies are absent.",
                             "all_seen counts every observed enemy as active; positive_energy excludes ambiguous zero energy cells.",
                             "The archive stores belief terrain. Negative own units, match resets, collisions and later deaths do not supply projected coverage."])
    (args.out/"summary.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")


if __name__=="__main__":
    main()
