"""Reproduce the registered original R3 games, then run the W-L switch on each same seat."""
import argparse
import fcntl
from hashlib import sha256
import json
from pathlib import Path
import re

import numpy as np

from scripts import r3_v4_contact_study as contact
from scripts import r3_v4_mixed_duel as direct
from scripts.common import make_opponent, play_game
from scripts.scoring import match_points_after_step
from scripts.train_combat_advice import publish_json

STUDY = Path("experiments/analysis/r3_v4_wl_20261115/diagnosis")
DIRECT = Path("experiments/analysis/r3_v4_mixed_duel_20261115/run/games.jsonl")
DIRECT_SHA = "a27b75757b1d66aef21ec30f513875f5bc6199715b82cf8be06f92ebb6d5a310"
SEATS = ("player_0", "player_1")
ARMS = ("control", "switch")
GAME = ("result", "wins", "losses", "points", "opp_points", "steps")
HASH = re.compile("[a-f0-9]{64}")


def require(ok, explanation):
    if not ok:
        raise ValueError(explanation)


class Record:
    """Both unchanged historical runners call this adapter at the actual env boundary."""

    def __init__(self, env, seat):
        self.env = env
        self.seat = seat
        self.matches = []
        self.steps = 0
        self.full = {s: sha256() for s in SEATS}
        self.prefix = {}

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        self.before = obs[self.seat]
        return obs, info

    def step(self, orders):
        require(set(orders) == set(SEATS), "Missing actual world orders")
        for s, h in self.full.items():
            a = np.asarray(orders[s])
            require(a.shape == (16, 3) and np.issubdtype(a.dtype, np.integer)
                    and np.all((a[:, 0] >= 0) & (a[:, 0] <= 5)), "Invalid world action")
            h.update(a.astype("<i8").tobytes())
        if self.steps == 201:
            self.prefix = self.commands()
        result = self.env.step(orders)
        obs, _, term, trunc, info = result
        after = obs[self.seat]
        self.steps += 1
        require(all((bool(term[s]) or bool(trunc[s])) == (self.steps == 303) for s in SEATS),
                "Unexpected episode clock")
        change = np.asarray(after["team_wins"]) - np.asarray(self.before["team_wins"])
        boundary = self.steps in (101, 202, 303)
        if boundary:
            require(int(self.before["match_steps"]) == 100 and list(change) in ([1,0],[0,1]), "Missing match award")
            points = match_points_after_step(self.before, after, info).tolist()
            self.matches.append(dict(winner=SEATS[int(np.argmax(change))], world_points=points))
        else:
            require(not np.any(change), "Match awarded off boundary")
        self.before = after
        return result

    def commands(self):
        return {s: h.hexdigest() for s, h in self.full.items()}


def info(project):
    from scripts import r3_v4_wl_plan as plan
    cases = plan.cases(project)
    saved, _ = contact.binding(project)
    file = project / DIRECT
    require(direct.digest(file) == DIRECT_SHA, "Different archived direct games")
    duels = {(r["seed"],r["side"]):r for r in map(json.loads, file.read_bytes().splitlines())}
    for (seed,side,foe), c in cases.items():
        require(side in SEATS and foe in ("v4_mixed","solution92") and c["group"], "Invalid case")
        expected = c["expected"]
        supported = set(GAME)
        if (seed,foe) == (7287108,"solution92"):
            supported = {"result","wins","losses","steps"}
        require(set(expected) == supported and expected["steps"] == 303, "Incomplete archival reference")
        if foe == "v4_mixed":
            original = duels[seed,side]
            require(expected == {k:original[k] for k in GAME}, "Different original direct score")
    scripts = Path(__file__).resolve().parent
    src = {p:direct.digest(scripts / p) for p in ("r3_v4_wl_games.py","r3_v4_wl_agent.py",
           "r3_v4_wl_plan.py","r3_v4_mixed_duel.py","common.py","scoring.py","metrics.py")}
    require(src["r3_v4_mixed_duel.py"] == "b006fc1a8ac9965b4df2e176de4a83ebd622eca762657583b9dcfed57683ae73",
            "Different historical direct runner")
    stamp = dict(source=saved, files_sha256=src, plan=plan.provenance(project), direct_games=DIRECT_SHA,
                 cases=[dict(seed=k[0],side=k[1],opponent=k[2],**v) for k,v in sorted(cases.items())])
    return cases, duels, stamp


def validate(row, key, case, arm, token, original=None):
    seed, seat, foe = key
    require([row[k] for k in ("seed","side","opponent","arm","group","protocol_sha256")] ==
            [seed,seat,foe,arm,case["group"],token], "Different saved run")
    g = row["game"]
    matches = row["matches"]
    require(len(matches) == 3 and all(m["winner"] in SEATS and len(m["world_points"]) == 2
            and all(type(x) is int and x >= 0 for x in m["world_points"])
            and m["world_points"][SEATS.index(m["winner"])] == max(m["world_points"]) for m in matches),
            "Invalid course match")
    seq = "".join("W" if m["winner"] == seat else "L" for m in matches)
    team = SEATS.index(seat)
    wins = seq.count("W")
    points = [sum(m["world_points"][i] for m in matches) for i in (team,1-team)]
    require(row["sequence"] == seq and g == dict(zip(GAME,(int(wins >= 2),wins,3-wins,*points,303))), "Invalid final totals")
    for hashes in (row["prefix_sha256"],row["commands_sha256"]):
        require(set(hashes) == set(SEATS) and all(HASH.fullmatch(h) for h in hashes.values()), "Invalid action receipt")
    stats = row["actor_stats"]
    nsteps = 101 if arm=="switch" and seq[:2]=="WL" else 0
    require(stats["v4_steps"] == nsteps and type(stats["different_orders"]) is int
            and 0 <= stats["different_orders"] <= 16*nsteps, "Wrong switching phase or action count")
    if arm == "control":
        require(all(g[k] == v for k,v in case["expected"].items()) and (not case.get("sequence") or seq == case["sequence"]),
                f"Original game not reproduced: {key}")
        if foe == "v4_mixed":
            require(row["commands_sha256"] == original["commands_sha256"] and matches == original["matches"],
                    "Direct original action stream or match sequence changed")


def verify_pair(control, switch):
    require(control["prefix_sha256"] == switch["prefix_sha256"] and control["matches"][:2] == switch["matches"][:2],
            "First two matches differ in actions or awards")
    if control["sequence"][:2] != "WL":
        require(control["commands_sha256"] == switch["commands_sha256"] and control["matches"] == switch["matches"],
                "Untreated full trajectory changed")


def location(folder, key, arm):
    return folder / ("_".join(map(str,(*key,arm))) + ".json")


def play(env, actor, key, case, arm, token):
    from scripts.r3_v4_contact_agent import make_v4
    from scripts.par_eval import require_no_agent_errors
    seed, seat, foe = key
    rival_seat = SEATS[1-SEATS.index(seat)]
    recorder = Record(env,seat)
    if foe == "v4_mixed":
        rival = make_v4(rival_seat)
        raw = direct.play(recorder,{arm:actor,foe:rival},arm,seed,seat,foe)
        require(raw["matches"] == recorder.matches and raw["commands_sha256"] == recorder.commands(), "Direct recorder mismatch")
        require_no_agent_errors(rival.v14,rival.student)
        game = {k:raw[k] for k in GAME}
    else:
        rival = make_opponent(foe,rival_seat,str(contact.WEIGHTS))
        raw = play_game(recorder,actor,rival,seed,seat,False)
        game = dict(zip(GAME,[int(raw[k]) for k in contact.GAME]))
    require_no_agent_errors(actor,rival)
    require(recorder.steps == 303 and len(recorder.matches) == 3, "Incomplete recorder")
    seq = "".join("W" if m["winner"] == seat else "L" for m in recorder.matches)
    return dict(seed=seed,side=seat,opponent=foe,group=case["group"],arm=arm,game=game,matches=recorder.matches,
                sequence=seq,prefix_sha256=recorder.prefix,commands_sha256=recorder.commands(),
                actor_stats=actor.episode_stats(),protocol_sha256=token)


def receipt(folder, paths, token):
    return dict(protocol_sha256=token,games=len(paths),files_sha256={p.name:direct.digest(p) for p in sorted(paths)})


def verified_pairs(project, *, sealing=False):
    project = Path(project).resolve()
    folder = project/STUDY
    cases,duels,stamp = info(project)
    protocol = folder/"protocol.json"
    require(json.loads(protocol.read_bytes()) == stamp, "Different saved protocol")
    token = direct.digest(protocol)
    pairs = {}
    expected = {location(folder,k,a) for k in cases for a in ARMS}
    require(set(folder.glob("*_player_*.json")) == expected, "Unexpected or missing seat files")
    seal = folder/"completed.json"
    if seal.exists() or not sealing:
        require(json.loads(seal.read_bytes()) == receipt(folder,expected,token), "Changed or incomplete sealed evidence")
    for k,c in cases.items():
        rows = {arm:json.loads(location(folder,k,arm).read_bytes()) for arm in ARMS}
        for arm,r in rows.items():
            validate(r,k,c,arm,token,duels.get(k[:2]))
        verify_pair(rows["control"],rows["switch"])
        pairs[k] = rows
    return pairs


def run(project, folder, cases, duels, stamp):
    import torch
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.experiment import limit_threads
    from scripts.r3_v4_wl_agent import SwitchAgent
    folder.mkdir(exist_ok=True,parents=True)
    with (folder/".run.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_NB|fcntl.LOCK_EX)
        protocol = folder/"protocol.json"
        if protocol.exists():
            require(json.loads(protocol.read_bytes()) == stamp, "Different protocol on resume")
        else:
            require(not any(p.name != ".run.lock" for p in folder.iterdir()), "Unbound prior rows")
            publish_json(protocol,stamp)
        token = direct.digest(protocol)
        roster = {location(folder,k,a) for k in cases for a in ARMS}
        require(set(folder.glob("*_player_*.json")) <= roster, "Unexpected previous seat")
        if (folder/"completed.json").exists():
            verified_pairs(project)
            print("Sealed study verified")
            return
        limit_threads()
        torch.manual_seed(0)
        env = None
        try:
            for arm in ARMS:
                actor = None
                for k,c in cases.items():
                    path = location(folder,k,arm)
                    if not path.exists():
                        if env is None:
                            env = LuxAIS3GymEnv(numpy_output=True)
                        if actor is None:
                            actor = SwitchAgent(k[1],enabled=arm=="switch")
                        data = play(env,actor,k,c,arm,token)
                        publish_json(path,data)  # Keep mismatches inspectable and stop before the next game.
                    r = json.loads(path.read_bytes())
                    validate(r,k,c,arm,token,duels.get(k[:2]))
                    if arm=="switch":
                        verify_pair(json.loads(location(folder,k,"control").read_bytes()),r)
                    print(arm,k,r["sequence"],r["game"]["result"],flush=True)
        finally:
            if env is not None:
                env.close()
        verified_pairs(project,sealing=True)
        result = receipt(folder,list(folder.glob("*_player_*.json")),token)
        dest = folder/"completed.json"
        if dest.exists():
            require(json.loads(dest.read_bytes()) == result, "Changed finished rows")
        else:
            publish_json(dest,result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("check","run","verify"))
    parser.add_argument("--project",required=True,type=Path)
    args = parser.parse_args()
    project = args.project.resolve()
    folder = project/STUDY
    if args.operation == "verify":
        print(len(verified_pairs(project)), "verified paired keys")
        return
    cases,duels,stamp = info(project)
    if args.operation == "check":
        print(len(cases),"keys;",2*len(cases),"registered games;",folder)
    else:
        run(project,folder,cases,duels,stamp)


if __name__ == "__main__":
    main()
