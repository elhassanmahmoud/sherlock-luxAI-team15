"""Verify actual guarded policy on outside-trigger maps and held-out decisions."""
import json
from pathlib import Path

from match import play
from sammeln import HERE, OPP, WORK, game_path, panel
from spielen import require, sha, write_once
from scripts.experiment import limit_threads


def run():
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads()
    cards = json.loads((HERE/"karten.json").read_text())
    model = HERE/"modell.json"
    require(model.exists(), "Fit the frozen policy first")
    order = sorted(k for keys in panel("train").values() for k in keys)
    outside = []
    for k in order:
        loc = game_path("train","reference",k)
        if loc.exists() and not json.loads(loc.read_text())["eligible"]:
            outside.append(k)
            if len(outside) == 3:
                break
    require(len(outside) == 3, "Missing outside-trigger controls")
    outside.append((cards["normal_technical"][0],1,"v16"))
    env = LuxAIS3GymEnv(numpy_output=True)
    checks=[]
    try:
        for i,(s,t,o) in enumerate(outside):
            a=play(env,s,t,o,"original",only_qualifying=False,normal=(i==3))
            b=play(env,s,t,o,"learned",only_qualifying=False,normal=(i==3))
            require(b["features"] is None and b["choice"] is None and not b["events"], "Unexpected activation")
            require(a["action_hash"]==b["action_hash"] and a["match"]==b["match"], "Outside-trigger V16 mismatch")
            checks.append(dict(kind="outside",seed=s,team=t,opponent=o,sensor=b["sensor"],actions_per_side=101,
                               both_seats_101_turn_action_digest=b["action_hash"]))
        sets=json.loads((WORK/"test/auswahl.json").read_text())["selected"]
        for o in OPP:
            for s,t,_ in sets[o][:2]:
                r=play(env,s,t,o,"learned")
                frozen=json.loads(game_path("test",r["choice"],(s,t,o)).read_text())
                require(all(r[f]==frozen[f] for f in ("features","events","sight","credit","match","after70","action_hash","prefix_commands","prefix_observations")), "Learned selection did not replay selected held-out branch")
                checks.append(dict(kind="heldout",seed=s,team=t,opponent=o,choice=r["choice"],changes=len(r["events"]),
                                   action_hash=r["action_hash"],full_match_reproduced=True))
    finally:
        env.close()
    write_once(HERE/"technik.json",dict(passed=True,model_sha256=sha(model),outside_paired_openings=8,
                                       heldout_replays=4,checks=checks))
    print("All four unchanged openings and four actual held-out selected arms verified.")


if __name__=="__main__":
    run()
