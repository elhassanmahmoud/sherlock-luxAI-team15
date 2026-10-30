"""Wie viel mehr Punkte-Tiles wuerde eine exakte Loesung der Gleichungen liefern? (Analyse 30.10.2026)

Spielt V11 gegen einen Gegner (Gewichte nur lesen) und loest an festen Matchschritten die offenen Gleichungen des
Gedaechtnisses (belief.records nach der Propagation) exakt: Spiegel-Tiles als eine Variable, Zusammenhangs-
komponenten mit hoechstens MAXV Variablen vollstaendig aufgezaehlt. Gezaehlt: zusaetzlich erzwungene Punkte-/
Null-Tiles und ob sie mit der Wahrheit (env.state) uebereinstimmen.

    cd REPO && PYTHONPATH=REPO:DIESER_ORDNER .venv/bin/python -m exact_probe SEEDS.csv OPP OUT.csv WORKERS
"""
import csv
import random
import sys
from multiprocessing import Pool

import numpy as np

V11 = "experiments/releases/20261030_v11_baseline/agent_p0.pth"
MAXV = 18
CHECK = (30, 50, 70, 90)


def exact_forced(belief):
    """Liefert (punkte, nullen): flache Indizes, die alle konsistenten Belegungen gleich setzen."""
    H, W = belief.H, belief.W

    def canon(f):
        if not belief.symmetry:
            return f
        x, y = divmod(f, H)
        m = (W - 1 - y) * H + (H - 1 - x)
        return min(f, m)

    eqs = []
    for tiles, rest in belief.records:
        open_t = [t for t in tiles if t not in belief._point and t not in belief._dead]
        if not open_t:
            continue
        rest_now = rest - sum(1 for t in tiles if t in belief._point)
        coef = {}
        for t in open_t:
            c = canon(t)
            coef[c] = coef.get(c, 0) + 1
        eqs.append((coef, rest_now))
    if not eqs:
        return set(), set(), 0
    parent = {}

    def find(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for coef, _ in eqs:
        vs = list(coef)
        for v in vs[1:]:
            parent[find(v)] = find(vs[0])
        find(vs[0])
    comps = {}
    for coef, rest in eqs:
        comps.setdefault(find(next(iter(coef))), []).append((coef, rest))
    pts, dead, skipped = set(), set(), 0
    for eq_list in comps.values():
        vars_ = sorted({v for coef, _ in eq_list for v in coef})
        n = len(vars_)
        if n > MAXV:
            skipped += 1
            continue
        idx = {v: i for i, v in enumerate(vars_)}
        A = np.zeros((len(eq_list), n), dtype=np.int16)
        b = np.zeros(len(eq_list), dtype=np.int16)
        for r, (coef, rest) in enumerate(eq_list):
            for v, c in coef.items():
                A[r, idx[v]] = c
            b[r] = rest
        X = ((np.arange(2 ** n)[:, None] >> np.arange(n)[None, :]) & 1).astype(np.int16)
        ok = (X @ A.T == b[None, :]).all(axis=1)
        if not ok.any():
            continue  # widerspruechlich (z. B. ungesehenes neues Relic)
        S = X[ok]
        for i, v in enumerate(vars_):
            if S[:, i].min() == 1:
                pts.add(v)
            elif S[:, i].max() == 0:
                dead.add(v)
    return pts, dead, skipped


def play(job):
    import torch
    torch.set_num_threads(1)  # wie scripts.experiment.limit_threads
    seed, side, opp_name = job
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent
    from scripts.scoring import point_tile_map
    from agents.sherlock import geometry as geo
    env = LuxAIS3GymEnv(numpy_output=True)
    agent = Agent_x("player_0", agent_path=V11, train=False, seed=0)
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    opp_side = "player_1" if side == "player_0" else "player_0"
    opp = make_opponent(opp_name, opp_side)
    agent.new_game(side)
    random.seed(seed)
    np.random.seed(seed % (2 ** 32))
    obs, info = env.reset(seed=seed)
    agent.set_env_cfg(info["params"])
    opp.set_env_cfg(info["params"])
    rows = []
    step, done = 0, False
    while not done:
        actions = {side: agent.act(step=step, obs=obs[side]), opp_side: opp.act(step=step, obs=obs[opp_side])}
        obs, _, term, trunc, _ = env.step(actions)
        done = bool(np.asarray(term[side])) or bool(np.asarray(trunc[side]))
        step += 1
        ms = int(np.asarray(obs[side]["match_steps"]))
        if ms in CHECK:
            agent.belief.observe(obs[side])  # Stand nach diesem Schritt (act ruft observe sonst erst spaeter)
            b = agent.belief
            truth = point_tile_map(env.state)
            if b.mirrored:
                truth = geo.mirror_map(truth)
            H = b.H
            pts, dead, skipped = exact_forced(b)
            known_before = int(b.point_tiles.sum())

            def is_pt(f):
                x, y = divmod(f, H)
                return bool(truth[x, y])

            def expand(fs):
                out = set()
                for f in fs:
                    out.add(f)
                    if b.symmetry:
                        x, y = divmod(f, H)
                        out.add((b.W - 1 - y) * H + (H - 1 - x))
                return out

            P, D = expand(pts) - b._point, expand(dead) - b._dead
            rows.append(dict(seed=seed, side=side, opp=opp_name, match=step // 101, ms=ms,
                             truth_pts=int(truth.sum()), known_pts=known_before, open_eqs=len(b.records),
                             new_pts=len(P), new_pts_true=sum(is_pt(f) for f in P),
                             new_dead=len(D), new_dead_true=sum(not is_pt(f) for f in D), skipped=skipped))
    return rows


if __name__ == "__main__":
    import pandas as pd
    games = pd.read_csv(sys.argv[1])
    opp, out = sys.argv[2], sys.argv[3]
    jobs = [(int(r.seed), r.side, opp) for r in games.itertuples()]
    with Pool(int(sys.argv[4]) if len(sys.argv) > 4 else 4) as pool:
        res = pool.map(play, jobs, chunksize=1)
    rows = [r for rr in res for r in rr]
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "Messpunkte ->", out)
