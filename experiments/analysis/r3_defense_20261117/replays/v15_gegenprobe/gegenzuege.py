"""Replay native V15 actions, reverting just the eligible shooters for one engine step."""
from argparse import ArgumentParser
from collections import Counter, defaultdict
import gzip
from hashlib import sha256
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np

HERE = Path(__file__).resolve().parent
REPLAYS = HERE.parent
STUDY = REPLAYS.parent
sys.path[:0] = [str(REPLAYS), str(STUDY/"gegenprobe"), str(STUDY.parent/"r3_v15_blend_20261116")]
from schussumgebung import inspect
from laufzeit import verify_runtime


def compare(runtime):
    sys.path.insert(0, str(runtime))
    from einzelschritt import StepFork, scoring_fields
    from scripts.scoring import match_points_after_step
    from luxai_s3.wrappers import LuxAIS3GymEnv

    expected = json.loads((REPLAYS/"schussumgebung.json").read_bytes())
    gate = json.loads(json.dumps(inspect()))
    if expected != gate:
        raise ValueError("Archived eligibility no longer matches the rule")
    shots = defaultdict(list)
    for e in gate["events"]:
        key = e["seed"], e["seat"], 101*(e["match"]-1)+e["turn"]
        shots[key].append(e)
    hashes = json.loads((REPLAYS/"roh/sha256.json").read_bytes())
    env = LuxAIS3GymEnv(numpy_output=True)
    totals = Counter()
    games = []
    for name, digest in hashes.items():
        if not name.startswith("v15-"):
            continue
        data = (REPLAYS/"roh"/name).read_bytes()
        if sha256(data).hexdigest() != digest:
            raise ValueError(name)
        original = json.loads(gzip.decompress(data))
        seed, side = original["seed"], original["seat"]
        t = int(side[-1])
        opp = "player_"+str(1-t)
        candidate = SimpleNamespace(last_base=None)
        probe = StepFork(env, candidate, side)
        obs, _ = probe.reset(seed=seed)
        for n,f in enumerate(original["frames"]):
            active = shots.pop((seed, side, n), [])
            command = np.array(f["own_orders"], dtype=np.int16)
            control = command.copy()
            for event in active:
                uid = event["uid"]
                if f["v15_orders"][uid] != event["v15"]:
                    raise ValueError("Recorded V15 order mismatch")
                if f["r3_orders"][uid] != event["r3"] or f["own_orders"][uid] != event["v15"]:
                    raise ValueError("Intervention mismatch")
                control[uid] = event["r3"]
            if len(active) != int(np.any(command != control, axis=1).sum()):
                raise ValueError("Bad number of altered units")
            candidate.last_base = control
            commands = {side: command, opp: np.asarray(f["opp_orders"], dtype=np.int16)}
            before = obs[side]
            if list(map(int,np.asarray(before["team_points"])[[t,1-t]])) != f["before"]:
                raise ValueError("Score before original move disagrees")
            obs, _, _, _, info = probe.step(commands)
            outcome = match_points_after_step(before, obs[side], info)
            fields = [sorted(scoring_fields(info["final_state"], i)) for i in (t,1-t)]
            if (outcome[[t,1-t]].tolist() != f["after"]
                    or [sorted(map(tuple, x)) for x in f["scored_fields"]] != fields):
                raise ValueError(f"Actual trajectory diverged at {seed}/{side}/{n}")
            if active:
                event = probe.events[-1]
                if event["step"] != n or event["units"] != [e["uid"] for e in active]:
                    raise ValueError("Step fork misaligned")
        counts = Counter(turns=0, shots=0, enemy_denied=0, own_added=0,
                         turns_enemy_lower=0, turns_enemy_higher=0, enemy_energy_removed=0, own_energy_spent=0)
        for event in probe.events:
            actual_own, actual_foe = event["actual_gain"]
            alt_own, alt_foe = event["r3_gain"]
            denied, added = alt_foe-actual_foe, actual_own-alt_own
            if (denied != len(event["enemy_fields_denied"]) - len(event["enemy_fields_conceded"])
                    or added != len(event["own_fields_gained"])-len(event["own_fields_lost"])):
                raise ValueError("Field difference mismatch")
            energy = event["energy_actual_minus_r3"]
            counts.update(turns=1,shots=len(event["units"]),enemy_denied=denied,own_added=added,
                          turns_enemy_lower=int(denied>0),turns_enemy_higher=int(denied<0),
                          own_energy_spent=-energy[0],enemy_energy_removed=-energy[1])
        games.append(dict(seed=seed,seat=side,stats=counts,forks=probe.events))
        totals.update(counts)
    env.close()
    if shots or (len(games),totals["turns"],totals["shots"]) != (4,49,61):
        raise ValueError("Incomplete experiment")
    return dict(totals=totals,games=games)


if __name__ == "__main__":
    p = ArgumentParser(description=__doc__)
    p.add_argument("--runtime", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    verify_runtime(args.runtime, json.loads((STUDY.parent/"r3_v15_blend_20261116/laufzeit.json").read_bytes()))
    result = compare(args.runtime.resolve())
    with args.out.open("x") as out:
        json.dump(result,out,indent=2)
        out.write("\n")
    print(result["totals"])
