"""Run real reference and candidate games and retain all world commands for independent comparison."""
import argparse
import base64
from datetime import datetime
import gzip
import hashlib
import json
from pathlib import Path
import random
import zlib

import numpy as np
import torch

from experiments.analysis.relictsuche_20261123.punktwissen.kandidat import create, PACKAGE
from experiments.analysis.relictsuche_20261123.punktspeicher.beweise import MIRROR
from experiments.analysis.relictsuche_20261123.vergleich.panel import sensor
from experiments.analysis.relictsuche_20261123.vergleich.spielen import CUTOFF, Monitor, common_source, sha, stamp, write_once
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from scripts.scoring import point_tile_map

HERE = Path(__file__).resolve().parent


def frozen():
    files = [HERE / n for n in ("kandidat.py", "spiele.py", "PLAN.md")]
    files += [HERE.parent / "punktspeicher" / "beweise.py"]
    return stamp(dict(common=common_source(), files={str(p.relative_to(HERE.parent)): sha(p) for p in files}))


def board_seeds():
    import jax
    pool = np.arange(162640000, 162641000, dtype=np.int32)
    return list(map(int, pool[np.asarray(jax.jit(jax.vmap(sensor))(pool)) == 1][:64]))


def archive():
    idx = {}
    for group in ("archiv", "frisch"):
        for name in ("beobachtungen", "beweise"):
            with gzip.open(HERE.parent / "punktspeicher" / group / (name + ".jsonl.gz"), "rt") as f:
                for row in map(json.loads, f):
                    idx.setdefault((row["seed"], row["team"]), {})[name] = row
    return idx


class Tape(Monitor):
    def __init__(self, env, team, candidate=None):
        super().__init__(env, team, "general")
        self.player = candidate
        self.commands = []
        self.checked = []
        self.false_positive_ticks = 0

    def step(self, acts):
        array = np.stack([acts[f"player_{n}"] for n in (0, 1)])
        assert array.shape == (2, 16, 3) and np.max(np.abs(array)) <= 24
        self.commands.append(array.astype(np.int8))
        if self.player and self.sensor == 1:
            b = self.player.base._imitation.belief
            truth = point_tile_map(self.env.state)
            self.false_positive_ticks += int(np.any(b.point_tiles & ~(truth[::-1, ::-1].T if b.mirrored else truth)))
            for event in self.player.events[len(self.checked):]:
                q = event["world"]
                assert event["t"] == self.turn and all(truth[divmod(k, 24)] for k in (q, MIRROR[q]))
                assert all(b.point_tiles[divmod(k, 24)] and not b.dead_tiles[divmod(k, 24)] for k in (q, MIRROR[q]))
                self.checked.append(event.copy())
        return super().step(acts)


def decoded(row):
    raw = zlib.decompress(base64.b64decode(row["tape"]))
    return np.frombuffer(raw, np.int8).reshape(303, 2, 16, 3)


def run(env, seed, team, version, foe, identity, keep=None):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    side, other = f"player_{team}", f"player_{1-team}"
    actor = keep if keep is not None else (create(side) if version == "neu" else r3_package_agent(side, PACKAGE))
    rival = make_opponent("solution92", other) if foe == "solution92" else r3_package_agent(other, PACKAGE)
    rec = Tape(env, team, actor if version == "neu" else None)
    raw = play_game(rec, actor, rival, seed, side, False)
    require_no_agent_errors(actor.base if version == "neu" else actor, rival)
    assert rec.turn == raw["steps"] == 303 and len(rec.matches) == 3
    assert raw["our_wins"] == sum(m["win"] for m in rec.matches)
    assert raw["game_win"] == int(raw["our_wins"] >= 2)
    if version == "neu":
        assert actor.events == rec.checked
        if rec.sensor != 1:
            assert actor.last_step == -1 and not rec.checked
    cmds = np.stack(rec.commands)
    assert hashlib.sha256(cmds.astype("<i4").tobytes()).hexdigest() == rec.digest.hexdigest()
    return dict(seed=seed, team=team, version=version, opponent=foe, source=identity,
                sensor=rec.sensor, events=rec.checked, sight=rec.first_sight, credit=rec.first_credit,
                matches=rec.matches, win=raw["game_win"], false_positive_ticks=rec.false_positive_ticks,
                digest=rec.digest.hexdigest(), tape=base64.b64encode(zlib.compress(cmds.tobytes())).decode())


def paired(ref, cand, selfplay=False):
    assert ref["seed"] == cand["seed"] and ref["source"] == cand["source"]
    base, actual = decoded(ref), decoded(cand)
    delta = np.any(base != actual, axis=(1, 2, 3))
    t = np.flatnonzero(delta)
    first = cand["events"][0]["t"] if cand["events"] else 303
    assert not delta[:first].any()
    if not cand["events"]:
        assert ref["digest"] == cand["digest"]
        if not selfplay or not cand["team"]:
            assert ref["matches"] == cand["matches"]
    return int(t[0]) if len(t) else None


def tech(env, folder, identity):
    early = archive()
    selected = [161620068, 161620111, 162300044, 162300029]
    import jax
    pool = np.arange(162645000, 162645040, dtype=np.int32)
    normal = list(map(int, pool[np.asarray(jax.jit(jax.vmap(sensor))(pool)) != 1][:2]))
    result = []
    reused = create("player_0")
    for seed, team in [(s, t) for s in selected for t in (0, 1)] + list(zip(normal, (0, 1))):
        ref = run(env, seed, team, "v16", "solution92", identity)
        new = run(env, seed, team, "neu", "solution92", identity, reused)
        first_action = paired(ref, new)
        if (seed, team) in early:
            r = early[seed, team]
            assert ref["digest"] == r["beobachtungen"]["action_hash"] and ref["matches"] == r["beobachtungen"]["matches"]
            proof = next(((row["t"], int(row["p"], 16) & ~int(old["point"], 16))
                         for row, old in zip(r["beweise"]["frames"], r["beobachtungen"]["policy"], strict=True)
                         if int(row["p"], 16) & ~int(old["point"], 16)), None)
            if proof:
                turn, mask = proof
                assert new["events"] and new["events"][0]["t"] == turn
                assert all((mask >> e["world"]) & 1 for e in new["events"] if e["t"] == turn)
            else:
                assert not new["events"]
        result.append(dict(seed=seed, team=team, sensor=ref["sensor"], ref=ref["digest"], new=new["digest"],
                           verified=new["events"], false_positive_ticks=new["false_positive_ticks"], first_action=first_action))
    assert len(result) == 10 and any(r["first_action"] is not None for r in result)
    write_once(HERE / "technik.json", dict(source=identity, cases=result))


def keys():
    return [(seed, team, a, foe) for seed in board_seeds() for team, a, foe in
            [(0, "v16", "v16"), (0, "v16", "solution92"), (1, "v16", "solution92"),
             (0, "neu", "solution92"), (1, "neu", "solution92"),
             (0, "neu", "v16"), (1, "neu", "v16")]]


def path(folder, key):
    return folder / "partien" / ("_".join(map(str, key)) + ".json")


def main():
    from luxai_s3.wrappers import LuxAIS3GymEnv
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder", type=Path)
    p.add_argument("stage", choices=("technik", "spiel"))
    p.add_argument("lane", default=0, type=int, nargs="?")
    p.add_argument("stride", default=1, type=int, nargs="?")
    a = p.parse_args()
    limit_threads()
    ident = frozen()
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        if a.stage == "technik":
            tech(env, a.folder, ident)
        else:
            assert json.loads((HERE / "technik.json").read_text())["source"] == ident
            jobs = keys()
            assert len(set(jobs)) == 448
            write_once(a.folder / "quelle.json", dict(source=ident, cards=board_seeds()))
            for key in jobs[a.lane::a.stride]:
                if datetime.now(CUTOFF.tzinfo) >= CUTOFF:
                    break
                out = path(a.folder, key)
                if out.exists():
                    assert json.loads(out.read_text())["source"] == ident
                else:
                    row = run(env, *key, ident)
                    assert row["sensor"] == 1
                    write_once(out, row)
    finally:
        env.close()
    assert frozen() == ident


if __name__ == "__main__":
    main()
