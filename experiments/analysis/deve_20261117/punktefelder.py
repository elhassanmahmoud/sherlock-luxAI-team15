"""Wie gut kennen und besetzen wir die Punktefelder gegen Kaggle? (17.11.2026, nur Messung)

Spielt einen Agenten gegen den Kaggle-Dritten und vergleicht in jedem Schritt die echten Punktefelder (Engine:
relic_nodes_map_weights > 0) mit dem Gedächtnis des Agenten (belief.point_tiles, in Weltkoordinaten) und mit der
Besetzung durch beide Teams. Ausgabe: eine Zeile je Spiel, Match und Zehnerblock von Matchschritten.

    python experiments/analysis/deve_20261117/punktefelder.py --agent student:ens9 --seeds 7256000:7256010 --out X.csv
    --agent r3 | r3t:SCHALTER | student:NAME
"""
from __future__ import annotations

import argparse
import csv
import multiprocessing as mp
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
R3_ZIP = ROOT / "experiments/releases/20261116_r3_finale/agent.zip"


def mirror(m: np.ndarray) -> np.ndarray:
    """Anti-Diagonal-Spiegelung M(x, y) = (W-1-y, H-1-x) wie in geometry.mirror_map."""
    return np.ascontiguousarray(m[::-1, ::-1].T)


def make_agent(spec: str, side: str):
    if spec.startswith("r3t:"):
        from agents.sherlock_r3t.agent import make_r3t
        return make_r3t(side, R3_ZIP, spec[4:])
    if spec.startswith("student:"):
        from agents.sherlock_r3t.agent import load_student
        return load_student(spec[len("student:"):], side)
    from scripts import r3_package
    return r3_package.r3_package_agent(side, str(R3_ZIP))


def play(job):
    seed, side, spec = job
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    from scripts.experiment import limit_threads
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from scripts.common import make_opponent

    env = LuxAIS3GymEnv(numpy_output=True)
    opp_side = "player_1" if side == "player_0" else "player_0"
    me, opp = make_agent(spec, side), make_opponent("kaggle3", opp_side)
    for a, sd in ((me, side), (opp, opp_side)):
        if hasattr(a, "new_game"):
            a.new_game(sd)
    obs, info = env.reset(seed=seed)
    for a in (me, opp):
        if hasattr(a, "set_env_cfg"):
            a.set_env_cfg(info["params"])
    team = 0 if side == "player_0" else 1
    rows, match, step, done = {}, -1, 0, False
    while not done:
        ms = int(env.state.match_steps)
        if ms == 0:
            match += 1
        acts = {side: me.act(step=step, obs=obs[side]), opp_side: opp.act(step=step, obs=obs[opp_side])}
        obs, _, term, trunc, _ = env.step(acts)
        done = bool(np.asarray(term[side])) or bool(np.asarray(trunc[side]))
        st = env.state
        ms2 = int(st.match_steps)
        if ms2 != 0:
            true = np.asarray(st.relic_nodes_map_weights) > 0
            b = me.belief
            known = np.asarray(b.point_tiles, dtype=bool)
            if b.mirrored:
                known = mirror(known)
            pos = np.asarray(st.units.position).astype(int)
            alive = np.asarray(st.units_mask).astype(bool)
            occ = np.zeros((2,) + true.shape, dtype=bool)
            for t in range(2):
                for u in np.flatnonzero(alive[t]):
                    occ[t, pos[t, u, 0], pos[t, u, 1]] = True
            ours, theirs = occ[team] & true, occ[1 - team] & true
            W, H = true.shape
            xx, yy = np.meshgrid(np.arange(W), np.arange(H), indexing="ij")
            corner = (0, 0) if team == 0 else (W - 1, H - 1)
            other = (W - 1, H - 1) if team == 0 else (0, 0)
            own_half = (np.abs(xx - corner[0]) + np.abs(yy - corner[1])) < (np.abs(xx - other[0]) + np.abs(yy - other[1]))
            key = (match, (ms2 - 1) // 10)
            r = rows.setdefault(key, dict(seed=seed, side=side, agent=spec or "r3", match=match,
                                          block=(ms2 - 1) // 10, steps=0, true=0, known_true=0, known_false=0,
                                          ours=0, ours_known=0, theirs=0, theirs_known=0, free_known=0,
                                          free_unknown=0, true_own=0, ours_own=0, theirs_own=0, free_known_own=0,
                                          units_ours=0, units_theirs=0, idle_ours=0))
            r["steps"] += 1
            r["true"] += int(true.sum())
            r["known_true"] += int((known & true).sum())
            r["known_false"] += int((known & ~true).sum())
            r["ours"] += int(ours.sum())
            r["ours_known"] += int((ours & known).sum())
            r["theirs"] += int(theirs.sum())
            r["theirs_known"] += int((theirs & known).sum())
            free = true & ~occ[0] & ~occ[1]
            r["free_known"] += int((free & known).sum())
            r["free_unknown"] += int((free & ~known).sum())
            r["true_own"] += int((true & own_half).sum())
            r["ours_own"] += int((ours & own_half).sum())
            r["theirs_own"] += int((theirs & own_half).sum())
            r["free_known_own"] += int((free & known & own_half).sum())
            r["units_ours"] += int(alive[team].sum())
            r["units_theirs"] += int(alive[1 - team].sum())
            # eigene Units nicht auf einem Punktefeld und ohne Gegner im Abstand <= 3 (Chebyshev)
            ep = pos[1 - team][alive[1 - team]]
            for u in np.flatnonzero(alive[team]):
                x, y = pos[team, u]
                if true[x, y]:
                    continue
                if len(ep) and (np.maximum(np.abs(ep[:, 0] - x), np.abs(ep[:, 1] - y)) <= 3).any():
                    continue
                r["idle_ours"] += 1
        step += 1
    env.close()
    return list(rows.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="r3")
    ap.add_argument("--seeds", required=True, help="START:ENDE (Ende exklusiv)")
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    lo, hi = map(int, a.seeds.split(":"))
    spec = "" if a.agent == "r3" else a.agent
    jobs = [(s, side, spec) for s in range(lo, hi) for side in ("player_0", "player_1")]
    with mp.get_context("spawn").Pool(a.workers) as pool:
        res = pool.map(play, jobs, chunksize=1)
    rows = [r for rs in res for r in rs]
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(jobs)} Spiele, {len(rows)} Zeilen -> {a.out}")


if __name__ == "__main__":
    main()
