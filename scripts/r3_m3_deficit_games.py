"""Replay-triggered, paired late-switch counterfactuals. Only the 16 registered Solution seats run."""
import argparse
from collections import Counter
import fcntl
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from scripts import r3_m3_deficit_replay as replay
from scripts import r3_v4_wl_solution as scope
from scripts.r3_v4_wl_solution_registry import registered
from scripts.residual_ensemble_compare import interval
from scripts.train_combat_advice import publish_json

REPLAY_SHA = "ec3ce775afdb7536897385514649876d5c3a42be3868457921b1fe3d6a299b42"
REPLAY_CODE = "8e1f0e514589306fdc69da0030182602c644eeaea8754bfa284c2cedaa6836b2"
SEATS = replay.SEATS
require = replay.require
digest = scope.wl.direct.digest


def setup(a):
    require(a.replay_sha256 == REPLAY_SHA == digest(a.replay), "Different or incomplete trigger replay")
    report = json.loads(a.replay.read_bytes())
    require(digest(Path(replay.__file__)) == REPLAY_CODE == report["script_sha256"] and
            report["archive_sha256"] == replay.SOURCES and report["original_frames_replayed"] == 5151,
            "Different replay source or missing frames")
    old = a.project / replay.PARENT
    _, original_protocol = scope.setup(a.project)
    require(json.loads((old/"protocol.json").read_bytes()) == original_protocol, "Different live study parents or environment")
    all_cases, sources = registered(a.project)
    originals = {(r["seed"],r["side"]):r for r,_ in replay.archive(old)}
    observed = {(r["seed"],r["side"]):r for r in report["games"]}
    require(len(report["games"]) == len(originals) == 17 and observed.keys() == originals.keys(),
            "Missing or repeated tied seat")
    selected = {}
    for k, r in observed.items():
        ref = originals[k]
        require(r["original_game"] == ref["game"] == all_cases[(*k,"solution92")]["expected"] and
                r["original_matches"] == ref["matches"] and r["original_sequence"] == ref["sequence"] and
                r["original_commands_sha256"] == ref["commands_sha256"] and
                r["original_game_win"] == bool(ref["game"]["result"]), "Different archived control")
        if r["trigger"] is not None:
            selected[k] = r
    require(report["summary"] == replay.summarize(report["games"]) and len(selected) == 16 and
            sum(not r["original_game_win"] for r in selected.values()) == 4, "No qualified loss or incomplete roster")
    scripts = Path(__file__).parent
    source = {name:digest(scripts/name) for name in ("r3_m3_deficit_agent.py","r3_m3_deficit_games.py",
                                                      "r3_m3_deficit_replay.py","residual_ensemble_compare.py")}
    stamp = dict(replay_sha256=REPLAY_SHA, parent_protocol_sha256=replay.SOURCES["protocol.json"],
                 roster_sha256=sources["roster_sha256"], sources=source,
                 cases=[dict(seed=k[0],side=k[1],trigger=r["trigger"]) for k,r in sorted(selected.items())])
    return all_cases, originals, selected, stamp


def check_prefix(actual, original, expected):
    t = expected["global_step"]
    require(252 <= t <= 302 and expected["match_step"] == t - 202 and expected["points"] < expected["opponent_points"],
            "Invalid registered trigger")
    require(actual.shape == original.shape == (303,2,16,3) and np.array_equal(actual[:t],original[:t]),
            "World commands differ before the registered intervention")
    return {seat:sha256(actual[:t,i].astype("<i8").tobytes()).hexdigest() for i,seat in enumerate(SEATS)}


def validate(row, ref, trigger, token):
    seat = ref["side"]
    require(row["seed"] == ref["seed"] and row["side"] == seat and row["opponent"] == "solution92" and
            row["arm"] == "late_deficit" and row["protocol_sha256"] == token and row["trigger"] == trigger,
            "Wrong seat, source or actual intervention")
    actual = replay.original_commands(row)
    original = replay.original_commands(ref)
    prefix = check_prefix(actual, original, trigger)
    require(row["identical_prefix_sha256"] == prefix, "Incomplete prefix proof")
    # Solution has seen the identical state and cannot observe our simultaneous new action.
    rival = 1 - SEATS.index(seat)
    step = trigger["global_step"]
    require(np.array_equal(actual[step,rival], original[step,rival]), "Solution already differed at trigger")
    require(row["matches"][:2] == ref["matches"][:2] and len(row["matches"]) == 3, "Different first two matches")
    matches = row["matches"]
    require(all(len(m["world_points"]) == 2 and all(type(x) is int and x >= 0 for x in m["world_points"])
                and m["winner"] in SEATS and m["world_points"][SEATS.index(m["winner"])] == max(m["world_points"])
                for m in matches), "Wrong terminal award or points")
    seq = "".join("W" if m["winner"] == seat else "L" for m in matches)
    sums = [sum(m["world_points"][i] for m in matches) for i in (1-rival,rival)]
    require(row["sequence"] == seq and row["game"] == dict(result=int(seq.count("W")>=2), wins=seq.count("W"),
            losses=seq.count("L"),points=sums[0],opp_points=sums[1],steps=303), "Incorrect official totals")
    st = row["actor_stats"]; first = row["first_different_active_step"]
    require(st["v4_steps"] == 303-step and 0 <= st["different_active"] <= st["different_orders"] <= 16*(303-step)
            and ((first is None and st["different_active"] == 0) or
                 (isinstance(first,int) and step <= first <= 302 and st["different_active"] > 0)),
            "Incomplete switch/allied activity count")
    return row


def path_for(folder, k):
    return folder/f"{k[0]}_{k[1]}.json"


def assessment(cases, selected, games):
    require(games.keys() == selected.keys(), "Incomplete or unregistered causal game")
    flipped = []; data = {}; by_group = {"intervened":Counter(),"unchanged":Counter()}
    for (seed,side,_), c in sorted(cases.items()):
        key = (seed,side); before = c["expected"]; after = games[key]["game"] if key in games else before
        group = by_group["intervened" if key in games else "unchanged"]
        group["seats"] += 1
        for kind, outcome in (("original",before),("candidate",after)):
            for name in ("result","wins","points","opp_points"):
                group[kind+"_"+name] += outcome[name]
        data.setdefault(seed,[]).append(after["result"] - before["result"])
        if after["result"] != before["result"]:
            flipped.append(dict(seed=seed,side=side,original=before,candidate=after))
    require(len(data)==184 and all(len(v)==2 for v in data.values()) and by_group["unchanged"]["seats"]==352,
            "Unexpected map denominator")
    totals = by_group["intervened"].copy()
    totals.update(by_group["unchanged"])
    require(totals["seats"] == 368 and totals["original_result"] == 364, "Changed original baseline")
    delta = [sum(v)/2 for v in data.values()]
    return dict(groups=by_group,total=totals,gained=sum(f["candidate"]["result"] for f in flipped),
                lost=sum(f["original"]["result"] for f in flipped),flips=flipped,
                paired_win_difference=sum(delta)/len(delta),paired_card_ci95=interval(delta,seed=2711,draws=10000),
                may_plan_fresh=totals["candidate_result"] > totals["original_result"])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("operation",choices=("check","run","verify"))
    for key in ("project","replay","out"):
        p.add_argument("--"+key,type=lambda v:Path(v).resolve(),required=True)
    p.add_argument("--replay-sha256",required=True)
    a=p.parse_args()
    cases, originals, selected, stamp=setup(a)
    if a.operation=="check":
        print(f"{len(selected)} registered causal games"); return
    folder=a.out
    if a.operation=="run": folder.mkdir(parents=True,exist_ok=True)
    with (folder/".run.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        protocol=folder/"protocol.json"
        if protocol.exists():
            require(json.loads(protocol.read_bytes())==stamp,"Different frozen sources or selection")
        else:
            require(a.operation=="run" and not any(f.name!=".run.lock" for f in folder.iterdir()),"Missing source freeze")
            publish_json(protocol,stamp)
        token=digest(protocol)
        files={k:path_for(folder,k) for k in selected}
        require(set(folder.glob("*_player_*.json")) <= set(files.values()),"Unexpected extra game")
        todo=[k for k,f in sorted(files.items()) if not f.exists()]
        require(not todo or (a.operation=="run" and not (folder/"assessment.json").exists()),"Incomplete seal")
        games={}
        for k,f in files.items():
            if f.exists(): games[k]=validate(json.loads(f.read_bytes()),originals[k],selected[k]["trigger"],token)
        if todo:
            from scripts.r3_m3_deficit_agent import DeficitAgent
            from scripts.experiment import limit_threads
            from luxai_s3.wrappers import LuxAIS3GymEnv
            import torch
            limit_threads(); torch.manual_seed(0)
            env=LuxAIS3GymEnv(numpy_output=True)
            try:
                actor=DeficitAgent(todo[0][1])
                for k in todo:
                    stream=scope.WorldStream(env)
                    ref=originals[k]; t=selected[k]["trigger"]
                    row=scope.wl.play(stream,actor,(*k,"solution92"),{"group":cases[(*k,"solution92")]["panel"]},
                                      "late_deficit",token)
                    row.update(orders=stream.pack(),trigger=actor.decision,first_different_active_step=actor.first_different_active_step)
                    row["identical_prefix_sha256"]=check_prefix(replay.original_commands(row),replay.original_commands(ref),t)
                    games[k]=validate(row,ref,t,token)
                    publish_json(files[k],row)
                    print(k,"trigger",t["global_step"],ref["sequence"],"->",row["sequence"],flush=True)
            finally:
                env.close()
        require(setup(a)[3]==stamp,"Sources changed during the study")
        out=assessment(cases,selected,games)
        out.update(protocol_sha256=token,files_sha256={f.name:digest(f) for f in files.values()})
        result=folder/"assessment.json"
        if result.exists(): require(json.loads(result.read_bytes())==out,"Published result differs")
        else:
            require(a.operation=="run","Missing final assessment")
            publish_json(result,out)
        print(json.dumps(out["total"],sort_keys=True))


if __name__=="__main__":
    main()
