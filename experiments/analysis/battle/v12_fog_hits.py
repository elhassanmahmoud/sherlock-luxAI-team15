"""Wie gut zielt der Nebel-Sap von V12? (Analyse 31.10.2026, Gewichte nur lesen)

Jeder Aufruf von `_fog_sap` mit verstecktem Gegner und Kandidaten wird festgehalten: Position, Energie, Kandidaten-Tiles
(kanonisch, wie `rules.fog_sap` mit v2 sie bildet), je Kandidat die letzte eigene Beobachtung (Gegner gesehen / leer
gesehen, Alter in Schritten), geschaetzter Streufaktor, gewaehltes Ziel. Nach dem Env-Schritt kommt die Wahrheit dazu:
gegnerische Units nach der Bewegung (der Sap wirkt nach der Bewegung), kanonisch. Ereignisse im letzten Schritt eines
Matches entfallen. Auswertung alternativer Zielwahlen offline mit v12_fog_eval.py.

    cd REPO && PYTHONPATH=$PWD:$PWD/experiments/analysis/battle .venv/bin/python -m v12_fog_hits SEEDS(a:b) OPPS OUT.csv WORKERS
"""
import csv
import os
import random
import sys
from multiprocessing import Pool

import numpy as np

W12 = os.environ.get("PROBE_W", "experiments/ensembles/battle_v12.pth")


def _tiles(mask):
    return ";".join(f"{int(x)}-{int(y)}" for x, y in zip(*np.nonzero(mask)))


def play(job):
    import torch
    torch.set_num_threads(1)
    seed, side, opp_name = job
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from agents.sherlock import geometry as geo
    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent
    env = LuxAIS3GymEnv(numpy_output=True)
    agent = Agent_x("player_0", agent_path=W12, train=False, seed=0)
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    opp_side = "player_1" if side == "player_0" else "player_0"
    opp = make_opponent(opp_name.split(":")[0], opp_side, opp_name.split(":", 1)[1] if ":" in opp_name else None)
    agent.new_game(side)
    random.seed(seed)
    np.random.seed(seed % (2 ** 32))
    obs, info = env.reset(seed=seed)
    agent.set_env_cfg(info["params"])
    opp.set_env_cfg(info["params"])
    p = info["full_params"]
    drop_true = float(p["unit_sap_dropoff_factor"])
    us, them = (0, 1) if side == "player_0" else (1, 0)
    last_occ = np.full((24, 24), -1000, dtype=np.int64)
    last_empty = np.full((24, 24), -1000, dtype=np.int64)
    pending, rows = [], []

    orig = agent._fog_sap

    def hook(ctx, uid, planned_fog):
        pf = planned_fog.copy()
        out = orig(ctx, uid, planned_fog)
        b = agent.belief
        if b._sensor_now is None:
            return out
        pt = b.point_tiles
        seen_occ = len({(int(ex), int(ey)) for ex, ey in ctx["enemy_coords"] if pt[ex, ey]})
        hidden = int(b.opp_gain) - seen_occ
        cand = pt & ~b._sensor_now & (ctx["ally_count"] == 0) & ~pf
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        R = int(ctx["sap_range"])
        reach = np.zeros_like(cand)
        reach[max(0, x - R - 1):x + R + 2, max(0, y - R - 1):y + R + 2] = True
        # nur echte Gelegenheiten: versteckter Gegner, Kandidat in (Streu-)Reichweite, Energie fuer einen Sap
        if hidden <= 0 or not (cand & reach).any() or float(ctx["ally_ene"][uid]) < float(ctx["sap_cost"]):
            return out
        cs = []
        for cx, cy in zip(*np.nonzero(cand)):
            cs.append(f"{cx}-{cy}:{gstep - last_occ[cx, cy]}:{gstep - last_empty[cx, cy]}")
        pending.append(dict(
            seed=seed, side=side, opp=opp_name, sensor=int(p["unit_sensor_range"]), drop=drop_true,
            drop_est=agent.param_est.dropoff(default=-1.0), step=gstep, mstep=int(ctx["step"]),
            uid=int(uid), x=x, y=y, ene=float(ctx["ally_ene"][uid]), cost=float(ctx["sap_cost"]),
            R=int(ctx["sap_range"]), on_pt=bool(pt[x, y]), hidden=hidden, n_seen_pt=seen_occ,
            cand=";".join(cs), fired="" if out is None else f"{x + int(out[0])}-{y + int(out[1])}"))
        return out

    agent._fog_sap = hook
    gstep, done = 0, False
    while not done:
        o, oo = obs[side], obs[opp_side]
        ms = int(np.asarray(o["match_steps"]))
        if ms == 0:
            last_occ[:] = -1000
            last_empty[:] = -1000
        # eigene Sicht dieses Schritts (kanonisch) -> letzte Beobachtung je Tile
        sens = np.asarray(o["sensor_mask"]).astype(bool)
        vis_e = np.asarray(o["units_mask"])[them]
        pos_e = np.asarray(o["units"]["position"])[them]
        if agent.belief.mirrored:
            sens = geo.mirror_map(sens)
            pos_e = geo.mirror_positions(pos_e)
        occ = np.zeros((24, 24), dtype=bool)
        for i in np.nonzero(vis_e)[0]:
            occ[pos_e[i][0], pos_e[i][1]] = True
        last_occ[occ] = gstep
        last_empty[sens & ~occ] = gstep
        pending.clear()
        a_us = np.asarray(agent.act(step=gstep, obs=o))
        a_op = opp.act(step=gstep, obs=oo)
        obs, _, term, trunc, _ = env.step({side: a_us, opp_side: a_op})
        done = bool(np.asarray(term[side])) or bool(np.asarray(trunc[side]))
        gstep += 1
        if pending and int(np.asarray(obs[side]["match_steps"])) > 0:
            no = obs[opp_side]
            m = np.asarray(no["units_mask"])[them]
            tp = np.asarray(no["units"]["position"])[them]
            if agent.belief.mirrored:
                tp = geo.mirror_positions(tp)
            truth = ";".join(f"{int(tp[i][0])}-{int(tp[i][1])}" for i in np.nonzero(m)[0])
            for r in pending:
                r["truth"] = truth
                rows.append(r)
    return rows


if __name__ == "__main__":
    a, b = (int(v) for v in sys.argv[1].split(":"))
    opps, out = sys.argv[2].split(","), sys.argv[3]
    jobs = [(s, side, o) for s in range(a, b) for side in ("player_0", "player_1") for o in opps]
    with Pool(int(sys.argv[4]) if len(sys.argv) > 4 else 4) as pool:
        res = pool.map(play, jobs, chunksize=1)
    rows = [r for rs in res for r in rs]
    with open(out, "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    print(len(jobs), "Spiele,", len(rows), "Ereignisse ->", out)
