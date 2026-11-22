"""Liest die öffentlichen Beweise für zusätzlich gelernte Punktefelder in zwei zweiten Matches."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from replays import MatchRecord, PACKAGES, limit_threads, make_opponent, play_game, r3_package_agent


class Proofs:
    def __init__(self, belief):
        self.b = belief
        self.frames = []
        self.source = None
        self.depth = 0
        self.propagations = []
        self.direct = []
        for name in ("_infer_point_tiles", "_infer_from_enemy", "_infer_points_from_enemy"):
            method = getattr(belief, name)
            def watch(*args, f=method, category=name, **kw):
                self.source = category
                try:
                    return f(*args, **kw)
                finally:
                    self.source = None
            setattr(belief, name, watch)
        method_propagate = belief._propagate
        def propagate():
            equations = [(list(t), int(k)) for t,k in belief.records]
            first = len(self.direct)
            result = method_propagate()
            marks = self.direct[first:]
            if marks:
                self.propagations.append(dict(source=self.source, groups=marks.copy(),
                                              last_equation=equations[-1] if equations else None,
                                              supporting=[(t,k) for t,k in equations if any(f in t for f,_ in marks)]))
            return result
        belief._propagate = propagate
        method_mark = belief._mark_point
        def mark(f):
            new = f not in belief._point
            if self.depth == 0 and new:
                peer = belief._mirror_idx(f)
                paired = belief.symmetry and peer != f and peer not in belief._point
                self.direct.append((int(f), int(peer) if paired else None))
            self.depth += 1
            try:
                return method_mark(f)
            finally:
                self.depth -= 1
        belief._mark_point = mark


class Trace(MatchRecord):
    def __init__(self, env, inner, tap):
        super().__init__(env)
        self.inner, self.tap = inner, tap
        self.public_frames = []
        self.previous_points = set()

    def step(self, actions):
        t = int(self.previous["match_steps"])
        n = len(self.frames)
        b = self.inner.belief
        fields = set(b._point)
        added = fields - self.previous_points
        if n // 101 == 1 or n == 202:
            obs = self.previous
            own = []
            for team in (0, 1):
                energy = np.asarray(obs["units"]["energy"])[team].reshape(-1)
                mask = np.asarray(obs["units_mask"])[team] & (energy >= 0)
                own.append([[int(i), *map(int, obs["units"]["position"][team][i]), int(energy[i])] for i in np.flatnonzero(mask)])
            visible_relic = sorted([list(map(int, p)) for p in np.asarray(obs["relic_nodes"])[np.asarray(obs["relic_nodes_mask"], dtype=bool)]])
            if b.mirrored:
                raise ValueError("Die ausgewählten Sitze müssen Player 0 sein")
            if set(f for direct, peer in self.tap.direct for f in (direct,peer) if f is not None) != added:
                raise ValueError("Nicht zugeordneter Wissenssprung")
            self.public_frames.append(dict(match=n//101+1, turn=t, known=sorted(map(int,fields)), new=sorted(map(int,added)),
                                           gains_after_inference=self.tap.propagations.copy(), candidate_n=int(np.sum(b.candidate)), dead_n=len(b._dead),
                                           own_visible_enemy=own, active_sensor=int(np.asarray(obs["sensor_mask"]).sum()),
                                           remembered_relic=sorted([list(map(int,p)) for p in b.relic_positions]),
                                           visible_relic=visible_relic, public_points=list(map(int,obs["team_points"])),
                                           active_candidates_under_own=sorted({x*24+y for _,x,y,_ in own[0] if b.candidate[x,y]}),
                                           own_moves=np.asarray(actions["player_0"]).tolist()))
        self.tap.propagations.clear()
        self.tap.direct.clear()
        self.previous_points=fields
        return super().step(actions)


def run(arm, out):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads()
    path, sha = PACKAGES[arm]
    if hashlib.sha256(path.read_bytes()).hexdigest()!=sha:
        raise ValueError("Falsches Paket")
    archive = json.loads((HERE.parent/"replays.json").read_text())["arms"][arm]
    env = LuxAIS3GymEnv(numpy_output=True)
    data = {}
    for seed in (7261020,7267071):
        ref = next(r for r in archive if r["seed"]==seed and r["side"]=="player_0")
        agent = r3_package_agent("player_0",path)
        inner = agent._actor if arm=="r3" else agent._imitation
        tap=Proofs(inner.belief)
        recorder=Trace(env,inner,tap)
        result=play_game(recorder,agent,make_opponent("solution92","player_1"),seed,"player_0",False)
        if (any(result[k]!=v for k,v in ref["expected"].items()) or len(recorder.frames)!=303
            or recorder.match_winners != [0 if m["win"] else 1 for m in ref["matches"]]):
            raise ValueError("Abweichung vom Archiv")
        flags = "canonical symmetry early_inference relic_filter subset_infer keep_dead keep_dead_fast opp_infer stale_all nebula_infer_drift_safe overlap_infer nebula_infer drift_track sym_map opp_point_infer spawn_proof".split()
        live = {name: bool(getattr(inner.belief, name)) for name in flags}
        live.update({name: bool(value) for name, value in vars(inner.belief).items() if type(value) is bool and name not in ("_cand_dirty", "_coords_dirty", "_spawn_proven")})
        data[seed] = {"flags": live, "frames": recorder.public_frames}
        print(arm,seed,"OK",flush=True)
    out.write_text(json.dumps(data,separators=(",",":")))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm",choices=PACKAGES)
    ap.add_argument("--out",type=Path,default=HERE/"wissenssprung.json.gz")
    args=ap.parse_args()
    if args.arm:return run(args.arm,args.out)
    data={}
    with tempfile.TemporaryDirectory() as td:
        for a in PACKAGES:
            path=Path(td)/(a+".json")
            subprocess.run([sys.executable,__file__,"--arm",a,"--out",str(path)],check=True)
            data[a]=json.loads(path.read_text())
    args.out.write_bytes(gzip.compress(json.dumps(data,separators=(",",":")).encode(),mtime=0))


if __name__=="__main__":
    main()
