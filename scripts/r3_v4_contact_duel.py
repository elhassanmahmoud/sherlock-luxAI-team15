"""One paired 24-map duel between the frozen contact agent and its unmodified mixed-v4 parent."""
import argparse
import fcntl
import json
from pathlib import Path
import re

from scripts import r3_v4_contact_study as contact, r3_v4_mixed_duel as old
from scripts.residual_ensemble_compare import interval
from scripts.train_combat_advice import publish_json

MAPS=range(7170000,7170024)
SEATS=("player_0","player_1")
ROSTER=[(s,p) for s in MAPS for p in SEATS]
STUDY=Path("experiments/analysis/r3_v4_contact_20261115")
PARENT_PATH=Path("experiments/analysis/r3_v4_mixed_duel_20261115/run")
SOURCES={"games.jsonl":"a27b75757b1d66aef21ec30f513875f5bc6199715b82cf8be06f92ebb6d5a310",
         "manifest.json":"031caa35c5d92bfe3b1524deb0ae6945d5f3011aa08e7ae1eb8faf8b8203f254",
         "completed.json":"e043918977d23a99d71ee7c4fc945d0429fd1883901248e1143719885ecef8de",
         "reproduction.json":"61953e07a62833e1dadc3bbc40b8d10f0e1623c9fca20b593bcc543d19699dd0"}
SCREEN="fb24b2570afd86eeb4aa97429ff882daba445b89af3447f1e4fa39ff6063b9c2"
LOOP="b006fc1a8ac9965b4df2e176de4a83ebd622eca762657583b9dcfed57683ae73"


def check(ok,message):
    if not ok: raise ValueError(message)


def validate(row,arm,foe):
    k=(row["seed"],row["side"])
    check(k in ROSTER and row["arm"]==arm and row["opponent"]==foe,"Wrong game key")
    check(all(type(row[n]) is int for n in ("seed","steps","result","wins","losses","points","opp_points"))
          and row["steps"]==303 and row["wins"] in range(4) and row["losses"]==3-row["wins"]
          and row["result"]==int(row["wins"]>=2),"Incomplete game")
    check(row["updates"]==dict.fromkeys(SEATS,303) and set(row["commands_sha256"])==set(SEATS)
          and all(re.fullmatch(r"[0-9a-f]{64}",v) for v in row["commands_sha256"].values()),"Invalid real order/update receipt")
    matches=row["matches"]; i=SEATS.index(row["side"])
    check(len(matches)==3 and all(m["winner"] in SEATS and len(m["world_points"])==2 and
          all(type(x) is int and x>=0 for x in m["world_points"]) and
          m["world_points"][SEATS.index(m["winner"])]==max(m["world_points"]) for m in matches),"Invalid official match")
    check(sum(m["winner"]==row["side"] for m in matches)==row["wins"] and
          [sum(m["world_points"][j] for m in matches) for j in (i,1-i)]==[row["points"],row["opp_points"]],
          "World points, match winners and final game disagree")
    if arm=="contact":
        stats=row["routing"]
        check(set(stats)=={"near_unit_turns","far_unit_turns","different_near","different_far"} and
              all(type(v) is int and v>=0 for v in stats.values()) and
              0<stats["near_unit_turns"]+stats["far_unit_turns"]<=4800 and
              stats["different_near"]<=stats["near_unit_turns"] and stats["different_far"]<=stats["far_unit_turns"],
              "Invalid contact counters")
    return k


def provenance(project):
    stamp,_=contact.binding(project)
    files=project/PARENT_PATH
    check({name:old.digest(files/name) for name in SOURCES}==SOURCES and old.digest(Path(old.__file__))==LOOP,
          "Changed parent evidence or original duel loop")
    historical={}
    for line in (files/"games.jsonl").read_bytes().splitlines():
        row=json.loads(line);k=validate(row,"r3","v4")
        check(k not in historical,"Repeated original game")
        historical[k]=row
    check(set(historical)==set(ROSTER) and sum(r["result"] for r in historical.values())==12 and
          sum(r["wins"] for r in historical.values())==44,"Original 36–12 duel does not reproduce from raw results")
    parent=json.loads((files/"manifest.json").read_bytes()); oldenv=stamp["engine"]
    check(parent["tool_sha256"]==LOOP and parent["v4_source"]==stamp["v4_parent"] and
          parent["r3_research"]==stamp["r3_parent"] and parent["engine"]==oldenv["lux_modules"] and
          parent["flags"]==oldenv["runtime_flags"] and all(parent[k]==oldenv[k] for k in ("versions","python","machine","platform")) and
          parent["combat_radius"]==5 and parent["pack_mode"]=="mixed" and
          parent["student_overrides"]=={"imit_stay_bias":1.5,"imit_unstack":True},"Parent sources/settings/engine differ")
    folder=project/STUDY/"observed"
    check(old.digest(folder/"screen_assessment.json")==SCREEN,"Different contact screen")
    rec=json.loads((folder/"screen_assessment.json").read_bytes())
    check(rec["source"]==stamp and rec["passes"] is False and len(rec["raw_sha256"])==352 and
          all(old.digest(folder/k)==v for k,v in rec["raw_sha256"].items()),"Contact study does not match the frozen actor")
    return historical,dict(source=stamp,parent=SOURCES,screen=SCREEN,original_loop=LOOP,
                            runner=old.digest(Path(__file__)), helpers={name:old.digest(Path(old.__file__).with_name(name+".py"))
                            for name in ("scoring","residual_ensemble_compare","final_battle_select","experiment")},
                            study="contact vs v4 mixed",maps=list(MAPS),sides=list(SEATS))


def other_duels(project,out):
    """Detect registered role reversals and alternate existing storage for these exact keys."""
    root=project/"experiments/analysis"; foreign=set()
    for f in root.rglob("games.jsonl"):
        if f.parent.resolve()==out: continue
        for data in f.open("rb"):
            if b"contact" not in data or b"v4" not in data and b"v15" not in data: continue
            r=json.loads(data); own=r.get("arm",r.get("candidate")); foe=r.get("opponent")
            is_contact={"contact","r3_v4_contact"}; is_parent={"v4","v4_mixed","v15"}
            if r.get("seed") in MAPS and ((own in is_contact and foe in is_parent) or (foe in is_contact and own in is_parent)):
                foreign.add(str(f));break
    for f in root.rglob("*.json"):
        if f.parent.resolve()==out or not f.name.startswith(("contact_v4_","contact_v4_mixed_","v4_contact_",
               "v4_mixed_contact_","contact_v15_","v15_contact_")): continue
        if json.loads(f.read_bytes()).get("seed") in MAPS: foreign.add(str(f))
    check(not foreign,"Direct seats already recorded in a separate directory; check and reuse first: "+str(sorted(foreign)))


def ci(values):
    return interval(values,seed=2711,draws=10000)


def compare(rows,parents):
    check(set(rows)==set(parents)==set(ROSTER),"Expected exactly both seats on all 24 original maps")
    by_map=[]; gained=lost=0
    for s in MAPS:
        new=[rows[s,p] for p in SEATS]; oldrows=[parents[s,p] for p in SEATS]
        diffs=[n["result"]-o["result"] for n,o in zip(new,oldrows)]
        gained+=diffs.count(1);lost+=diffs.count(-1)
        by_map.append(dict(seed=s,contact_wins=sum(r["result"] for r in new),historical_r3_wins=sum(r["result"] for r in oldrows),
                       contact_matches=sum(r["wins"] for r in new),historical_r3_matches=sum(r["wins"] for r in oldrows)))
    shares=[m["contact_wins"]/2 for m in by_map]; diff=[(m["contact_wins"]-m["historical_r3_wins"])/2 for m in by_map]
    matches=sum(r["wins"] for r in rows.values());wins=sum(r["result"] for r in rows.values())
    interval95=ci(shares)
    return dict(games=48,maps=24,contact_wins=wins,v4_wins=48-wins,contact_match_wins=matches,v4_match_wins=144-matches,
                by_contact_seat={s:sum(r["result"] for (_,p),r in rows.items() if p==s) for s in SEATS},
                map_contact_wins_0_1_2=[sum(m["contact_wins"]==i for m in by_map) for i in range(3)],
                contact_game_share=wins/48,contact_ci95=interval95,lower_above_half=interval95[0]>0.5,
                contact_match_share_ci95=ci([m["contact_matches"]/6 for m in by_map]),
                original_r3_vs_v4=dict(r3_wins=12,v4_wins=36,r3_match_wins=44,v4_match_wins=100),
                relative_to_r3_vs_same_v4=dict(gained=gained,lost=lost,share_diff=(gained-lost)/48,
                    paired_map_ci95=ci(diff)),per_map=by_map,
                bootstrap=dict(unit="whole seed with both seats",draws=10000,generator="PCG64",seed=2711))


def paths(out):
    return {(s,p):out/f"contact_v4_mixed_{s}_{p}.json" for s,p in ROSTER}


def saved(out,protocol,complete=False):
    files=paths(out);found=set(out.glob("contact*.json"))
    check(found<=set(files.values()) and (not complete or found==set(files.values())),"Unexpected or missing direct seat")
    read={}
    for k,p in files.items():
        if p.is_file():
            r=json.loads(p.read_bytes())
            check(r["protocol_sha256"]==protocol and validate(r,"contact","v4_mixed")==k,"Changed saved direct game")
            read[k]=r
    return read


def simulate(todo,out,protocol):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    import torch
    from scripts.experiment import limit_threads
    from scripts.r3_v4_contact_agent import ContactAgent, make_v4
    limit_threads();torch.manual_seed(0)
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        actor=ContactAgent(SEATS[0]);v4=make_v4(SEATS[1])
        actors={"contact":actor,"v4_mixed":v4}
        for seed,side in todo:
            r=old.play(env,actors,"contact",seed,side,"v4_mixed")
            children=(actor.r3,actor.v4,actor.v4.v14,actor.v4.student,v4,v4.v14,v4.student)
            check(not any(getattr(x,"caught_errors",0) for x in children),"A frozen parent caught an error")
            r.update(protocol_sha256=protocol,routing=dict(actor.counts))
            validate(r,"contact","v4_mixed")
            publish_json(paths(out)[seed,side],r)
            print(seed,side,r["wins"],r["losses"],flush=True)
    finally:
        env.close()


def result(out,protocol,parents):
    rows=saved(out,protocol,True)
    data=compare(rows,parents)
    data.update(protocol_sha256=protocol,files_sha256={p.name:old.digest(p) for p in paths(out).values()})
    return data


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("operation",choices=("check","run","assess"))
    p.add_argument("--project",required=True,type=Path)
    a=p.parse_args();project=a.project.resolve();out=(project/STUDY/"direct_v4").resolve()
    parents,stamp=provenance(project)
    other_duels(project,out)
    source=out/"protocol.json"
    if a.operation=="check":
        if source.exists():
            check(json.loads(source.read_bytes())==stamp,"Different prior duel protocol")
            n=len(saved(out,old.digest(source)))
        else:
            check(not list(out.glob("contact*.json")),"Unbound prior rows");n=0
        print(f"{n} / 48 recorded; {48-n} missing; original R3-v4 12:36; fixed output {out}");return
    out.mkdir(parents=True,exist_ok=True)
    with (out/".run.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if source.exists(): check(json.loads(source.read_bytes())==stamp,"Different prior duel protocol")
        else:
            check(a.operation=="run" and not list(out.glob("contact*.json")) and not (out/"completed.json").exists(),"Unbound rows")
            publish_json(source,stamp)
        h=old.digest(source)
        if a.operation=="run" and not (out/"completed.json").exists():
            exists=saved(out,h);todo=[k for k in ROSTER if k not in exists]
            if todo: simulate(todo,out,h)
            check(provenance(project)[1]==stamp,"Source changed during games")
        completed=result(out,h,parents);dest=out/"completed.json"
        if dest.exists(): check(json.loads(dest.read_bytes())==completed,"Changed completed assessment")
        else: publish_json(dest,completed)
        print(json.dumps({k:v for k,v in completed.items() if k not in ("per_map","files_sha256")},indent=2))


if __name__=="__main__": main()
