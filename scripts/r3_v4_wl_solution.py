"""Whole original R3 controls on every 1:2/2:1 seat, then only the public W-L interventions."""
import argparse
import base64
from collections import Counter
import fcntl
from hashlib import sha256
import json
from pathlib import Path
import zlib

import numpy as np

from scripts import r3_v4_wl_games as wl
from scripts.train_combat_advice import publish_json

STUDY = Path("experiments/analysis/r3_v4_wl_20261115/solution_scope")
SHAPE = (303, 2, 16, 3)  # engine step, player_0/player_1, unit, world action components


def selected(cases):
    counts = Counter(c["expected"]["wins"] for c in cases.values())
    wl.require(counts == {1:4, 2:42, 3:322} and len({k[0] for k in cases}) == 184,
               "Different 368-seat archive")
    for key,c in cases.items():
        s,side,foe = key
        g = c["expected"]
        wl.require(foe == "solution92" and side in wl.SEATS and (s,wl.SEATS[1-wl.SEATS.index(side)],foe) in cases
                   and set(g) == set(wl.GAME) and g["steps"] == 303 and g["losses"] == 3-g["wins"]
                   and g["result"] == int(g["wins"] >= 2), "Invalid registered course game")
    return {k:dict(expected=c["expected"],group=c["panel"]) for k,c in sorted(cases.items()) if c["expected"]["wins"] < 3}


def setup(project):
    from scripts.r3_v4_wl_solution_registry import registered
    cases, archives = registered(project)
    scope = selected(cases)
    source, _ = wl.contact.binding(project)
    files = {name:wl.direct.digest(Path(__file__).with_name(name+".py")) for name in
             ("r3_v4_wl_solution","r3_v4_wl_solution_registry","r3_v4_wl_games","r3_v4_wl_agent","common","metrics","scoring")}
    wl.require(files["r3_v4_wl_games"] == "c2fbdc36f5387ad8d7045752dbd821895ef093acaf9ea514fe2d4c84c64b0a22" and
               files["r3_v4_wl_agent"] == "eac15aea06f4baa3bcba772f53110aca6b6e9a0fc82e86ecead7f271d3175544",
               "Changed published W-L policy or measurement")
    return scope, dict(source=source, files_sha256=files, archives=archives,
                       controls=[dict(seed=k[0],side=k[1],opponent=k[2],**c) for k,c in scope.items()],
                       stream_layout="steps, world player_0/player_1, UID, action/dx/dy; little-endian signed int16")


class WorldStream:
    """Passive recorder inside the historical runner's action-hashing Record wrapper."""

    def __init__(self, env):
        self.env = env
        self.frames = []

    def reset(self, **kwargs):
        self.frames.clear()
        return self.env.reset(**kwargs)

    def step(self, orders):
        a = np.stack([orders[s] for s in wl.SEATS])
        wl.require(a.shape == SHAPE[1:] and np.issubdtype(a.dtype,np.integer) and
                   np.all((a >= -32768) & (a <= 32767)), "World actions cannot be stored losslessly")
        self.frames.append(a.astype("<i2").tobytes())
        return self.env.step(orders)

    def pack(self):
        wl.require(len(self.frames) == SHAPE[0], "Incomplete world action stream")
        raw = b"".join(self.frames)
        return dict(format="zlib-base64-int16le",shape=list(SHAPE),raw_sha256=sha256(raw).hexdigest(),
                    data=base64.b64encode(zlib.compress(raw)).decode("ascii"))


def verify_orders(row):
    o = row["orders"]
    wl.require(o["format"] == "zlib-base64-int16le" and o["shape"] == list(SHAPE), "Different command format")
    raw = zlib.decompress(base64.b64decode(o["data"],validate=True))
    wl.require(sha256(raw).hexdigest() == o["raw_sha256"] and len(raw) == 2*np.prod(SHAPE), "Bad raw command stream")
    orders = np.frombuffer(raw,dtype="<i2").reshape(SHAPE)
    wl.require(np.all((orders[...,0]>=0) & (orders[...,0]<=5)), "Invalid stored action")
    for n,key in ((202,"prefix_sha256"),(303,"commands_sha256")):
        for i,s in enumerate(wl.SEATS):
            digest = sha256(orders[:n,i].astype("<i8").tobytes()).hexdigest()
            wl.require(digest == row[key][s], "World stream differs from historical runner's action hash")


def load(folder, key, case, arm, token):
    row = json.loads(wl.location(folder,key,arm).read_bytes())
    wl.validate(row,key,case,arm,token)
    verify_orders(row)
    return row


def read_pairs(folder, scope, token):
    pairs = {}
    expected = set()
    for key,case in scope.items():
        control = load(folder,key,case,"control",token)
        expected.add(wl.location(folder,key,"control"))
        switch = None
        if control["sequence"].startswith("WL"):
            switch = load(folder,key,case,"switch",token)
            expected.add(wl.location(folder,key,"switch"))
            wl.verify_pair(control,switch)
        pairs[key] = dict(control=control,switch=switch)
    wl.require(set(folder.glob("*_player_*.json")) == expected, "Unexpected extra control or unscheduled intervention")
    return pairs, wl.receipt(folder,expected,token)


def complete(project):
    project = Path(project).resolve()
    folder = project/STUDY
    scope,stamp = setup(project)
    protocol = folder/"protocol.json"
    wl.require(json.loads(protocol.read_bytes()) == stamp, "Changed protocol")
    pairs,seal = read_pairs(folder,scope,wl.direct.digest(protocol))
    wl.require(json.loads((folder/"completed.json").read_bytes()) == seal, "Incomplete or altered source evidence")
    return pairs


def run(project, scope, stamp):
    import torch
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.experiment import limit_threads
    from scripts.r3_v4_wl_agent import SwitchAgent

    folder = project/STUDY
    folder.mkdir(parents=True,exist_ok=True)
    with (folder/".run.lock").open("a") as guard:
        fcntl.flock(guard,fcntl.LOCK_EX | fcntl.LOCK_NB)
        protocol = folder/"protocol.json"
        if protocol.exists():
            wl.require(json.loads(protocol.read_bytes()) == stamp, "Different run on resume")
        else:
            wl.require(not any(p.name != ".run.lock" for p in folder.iterdir()), "Unbound previous run")
            publish_json(protocol,stamp)
        if (folder/"completed.json").exists():
            complete(project)
            return
        token = wl.direct.digest(protocol)
        existing = set(folder.glob("*_player_*.json"))
        allowed = {wl.location(folder,k,a) for k in scope for a in wl.ARMS}
        wl.require(existing <= allowed, "Unexpected saved game")
        if any(p.name.endswith("_switch.json") for p in existing):
            wl.require(all(wl.location(folder,k,"control") in existing for k in scope), "Intervention before all controls")
        limit_threads()
        torch.manual_seed(0)
        env = None
        try:
            controls = {}
            for arm in wl.ARMS:
                actor = None
                for key,case in scope.items():
                    if arm == "switch" and not controls[key]["sequence"].startswith("WL"):
                        wl.require(not wl.location(folder,key,arm).exists(), "Unscheduled switch exists")
                        continue
                    path = wl.location(folder,key,arm)
                    if not path.exists():
                        if env is None:
                            env = LuxAIS3GymEnv(numpy_output=True)
                        if actor is None:
                            actor = SwitchAgent(key[1],enabled=arm=="switch")
                        stream = WorldStream(env)
                        row = wl.play(stream,actor,key,case,arm,token)
                        row["orders"] = stream.pack()
                        publish_json(path,row)
                    row = load(folder,key,case,arm,token)
                    if arm == "control":
                        controls[key] = row
                    else:
                        wl.verify_pair(controls[key],row)
                    print(arm,key,row["sequence"],flush=True)
        finally:
            if env is not None:
                env.close()
        wl.require(setup(project) == (scope,stamp), "Sources changed during games")
        _,seal = read_pairs(folder,scope,token)
        publish_json(folder/"completed.json",seal)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("operation",choices=("check","run","verify"))
    p.add_argument("--project",required=True,type=Path)
    a = p.parse_args()
    project = a.project.resolve()
    if a.operation == "verify":
        pairs = complete(project)
        print(len(pairs),"controls;",sum(r["switch"] is not None for r in pairs.values()),"paired W-L interventions")
    else:
        scope,stamp = setup(project)
        if a.operation == "check":
            print(len(scope),"registered controls; enabled W-L interventions only;",project/STUDY)
        else:
            run(project,scope,stamp)


if __name__ == "__main__":
    main()
