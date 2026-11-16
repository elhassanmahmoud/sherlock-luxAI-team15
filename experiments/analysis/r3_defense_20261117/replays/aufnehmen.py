"""Record original and advisory moves plus the tiles actually scored after each move."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from hashlib import sha256
import gzip
import json
import multiprocessing
from pathlib import Path
import random
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
STUDIES = HERE.parents[1]
UNIT = STUDIES / "unit_handoff_20261116"
BLEND = STUDIES / "r3_v15_blend_20261116"
sys.path[:0] = [str(UNIT), str(BLEND / "diagnose")]
from duelle import play, spiele, verify_runtime
from replay import Observer, originals, require


@contextmanager
def preserve_rng():
    import torch
    python, numpy, pytorch = random.getstate(), np.random.get_state(), torch.get_rng_state()
    try:
        yield
    finally:
        random.setstate(python)
        np.random.set_state(numpy)
        torch.set_rng_state(pytorch)


def active(public, team):
    pos = np.asarray(public["units"]["position"])[team]
    energy = np.asarray(public["units"]["energy"])[team].reshape(-1)
    mask = np.asarray(public["units_mask"])[team] & (energy >= 0)
    return [[int(uid), *map(int, pos[uid]), int(energy[uid])] for uid in np.flatnonzero(mask)]


def evaluated_fields(state, team):
    from scripts.scoring import point_tile_map
    scoring = point_tile_map(state)
    positions = np.asarray(state.units.position)
    alive = np.asarray(state.units_mask) & (np.asarray(state.units.energy)[..., 0] >= 0)
    return [sorted({tuple(map(int, p)) for p in positions[t, alive[t]] if scoring[tuple(p)]})
            for t in (team, 1 - team)]


class Recorder(Observer):
    def __init__(self, actor, arm, side):
        parent = actor.r3 if arm == "unit" else (actor.v14 if arm == "v15" else actor)
        super().__init__(spiele.env, parent, "r3", side)
        self.policy = arm
        self.taps = {}
        self.originals = []
        if arm == "unit":
            for name, adviser in (("r3", actor.r3), ("v15", actor.v4)):
                original = adviser.act
                def record(step, obs, name=name, original=original):
                    order = original(step, obs)
                    self.taps[name] = (int(step), np.asarray(order).tolist())
                    return order
                self.originals.append((adviser, original))
                adviser.act = record

    def reset(self, **kwargs):
        from scripts.r3_v4_contact_agent import make_r3, make_v4
        obs, info = super().reset(**kwargs)
        params = info["params"]
        self.move_cost = int(params["unit_move_cost"])
        self.sap_cost = int(params["unit_sap_cost"])
        if self.policy != "unit":
            with preserve_rng():
                self.shadow = (make_v4 if self.policy == "r3" else make_r3)(self.side)
                self.shadow.new_game(self.side)
                self.shadow.set_env_cfg(params)
        return obs, info

    def step(self, commands):
        from agents.sherlock.belief import TILE_ASTEROID
        from scripts.r3_v4_contact_agent import sync
        public = self.obs[self.side]
        n = len(self.frames)
        played = np.asarray(commands[self.side])
        if self.policy == "unit":
            require(all(self.taps[k][0] == n for k in ("r3", "v15")), "Adviser frame mismatch")
            suggestions = {k: self.taps[k][1] for k in ("r3", "v15")}
        else:
            with preserve_rng():
                alternate = np.asarray(self.shadow.act(n, public)).tolist()
                observers = ((self.shadow.v14, True), (self.shadow.student, False)) if self.policy == "r3" else ((self.shadow, True),)
                for adviser, estimator in observers:
                    sync(adviser, public, played, estimator=estimator)
                require(not any(getattr(a, "caught_errors", 0) for a in (self.shadow, *(p for p, _ in observers))), "Shadow error")
            other = "v15" if self.policy == "r3" else "r3"
            suggestions = {self.policy: played.tolist(), other: alternate}
        known_asteroids = np.argwhere(self.agent.belief.tile_type == TILE_ASTEROID)
        if self.agent.belief.mirrored:
            known_asteroids = 23 - known_asteroids[:, ::-1]
        result = super().step(commands)
        f = self.frames[-1]
        scored = evaluated_fields(result[4]["final_state"], self.team)
        require([len(x) for x in scored] == [a-b for a, b in zip(f["after"], f["before"])], "Score tile mismatch")
        after = result[0][self.side]
        f.update(scored_fields=scored, next_own=active(after, self.team), next_visible=active(after, 1-self.team),
                 known_asteroids=known_asteroids.tolist(), r3_orders=suggestions["r3"], v15_orders=suggestions["v15"])
        return result


def record(job):
    arm, seed, side, ref, out = job
    if arm == "unit" and arm not in spiele.actors:
        from agent_unit import UnitHandoff
        spiele.actors[arm] = UnitHandoff(side)
    rec = Recorder(spiele.actor(arm, side), arm, side)
    spiele.env = rec
    try:
        result = play((arm, "solution", seed, side))
    finally:
        for actor, original in rec.originals:
            actor.act = original
        spiele.env = rec.env
    require(len(rec.frames) == 303 and all(result[k] == ref[k] for k in ref), "Different archived result")
    digests = {k: h.hexdigest() for k, h in rec.commands.items()}
    name = f"{arm}-{seed}-{side}.json.gz"
    archived = BLEND / "diagnose/roh" / name
    if archived.is_file():
        old = json.loads(gzip.decompress(archived.read_bytes()))
        require(digests == old["command_sha256"], "Different archived command stream")
        for f, g in zip(old["frames"], rec.frames, strict=True):
            require(all(f[k] == g[k] for k in f), "Different archived public observation")
    payload = dict(arm=arm, seed=seed, seat=side, actual=result, expected=ref, sap_range=rec.radius,
                   sap_cost=rec.sap_cost, move_cost=rec.move_cost, command_sha256=digests, frames=rec.frames)
    data = gzip.compress(json.dumps(payload, separators=(",", ":")).encode(), mtime=0)
    tmp = out / (name + ".tmp")
    tmp.write_bytes(data)
    tmp.rename(out / name)
    return name, sha256(data).hexdigest()


def main(runtime, out):
    cases = [tuple(p) for p in json.loads((UNIT / "archiv.json").read_bytes())["vs_v15"]["lost"]]
    _, parents = originals(spiele.ROOT)
    raw = (UNIT / "archiv/games.jsonl").read_bytes()
    seal = json.loads((UNIT / "archiv/complete.json").read_bytes())
    require(seal == {"n": 80, "sha256": sha256(raw).hexdigest()}, "Unsealed unit benchmark")
    units = {(r["seed"], r["seat"]): r for r in map(json.loads, raw.splitlines())}
    require(set(cases) == {k for k,r in units.items() if parents["v15"][k][0] > r["game_win"]}, "Unexpected seats")
    verify_runtime(runtime, json.loads((BLEND / "laufzeit.json").read_bytes()))
    out.mkdir(parents=True, exist_ok=False)
    jobs = [(arm, s, p, units[s,p] if arm=="unit" else dict(zip(spiele.GAME, parents[arm][s,p], strict=True)), out)
            for s,p in cases for arm in ("unit", "v15", "r3")]
    with ProcessPoolExecutor(max_workers=2, mp_context=multiprocessing.get_context("spawn"),
                             initializer=spiele.initialize, initargs=(runtime,)) as pool:
        hashes = {}
        for name, digest in pool.map(record, jobs):
            hashes[name] = digest
            print(name, flush=True)
    (out / "sha256.json").write_text(json.dumps(hashes, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    main(args.runtime.resolve(), args.out.resolve())
