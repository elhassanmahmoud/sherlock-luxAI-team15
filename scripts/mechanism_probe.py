"""Mechanismus-Probe: Energiebilanz pro Team und Match (Sap, Void, Kollision, Tod).

Spielt Sherlock (Gewichte nur lesen) gegen Solution_92 und rekonstruiert jeden
Engine-Schritt aus dem wahren Zustand vor/nach dem Schritt (Engine-Logik aus
luxai_s3/env.py nachgebaut). Reine Messung, keine Aktion wird veraendert.

    .venv/bin/python scripts/mechanism_probe.py --weights W --seeds 500720-500779 [--set k=v] --out X.json
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DIRS = np.array([[0, 0], [0, -1], [1, 0], [0, 1], [-1, 0]])
ADJ8 = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]
ADJ4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def snap(state):
    return dict(
        pos=np.asarray(state.units.position).astype(int),
        ene=np.asarray(state.units.energy)[..., 0].astype(int),
        mask=np.asarray(state.units_mask).astype(bool),
        tile=np.asarray(state.map_features.tile_type).astype(int),
        msteps=int(np.asarray(state.match_steps)),
        steps=int(np.asarray(state.steps)),
        rw=np.asarray(state.relic_nodes_map_weights).astype(int),
        rmask=np.asarray(state.relic_nodes_mask).astype(bool),
        points=np.asarray(state.team_points).astype(int),
    )


def simulate(s0, acts, p):
    """Ein Engine-Schritt bis vor das Energiefeld. Liefert Ereignisse je Unit."""
    W, H = s0["tile"].shape
    pos0, ene0 = s0["pos"].copy(), s0["ene"].copy()
    mask = s0["mask"] & (ene0 >= 0)
    if s0["msteps"] == 0:
        mask[:] = False
    pos, ene = pos0.copy(), ene0.copy()
    moved = np.zeros_like(mask)
    for t in range(2):
        for u in range(pos.shape[1]):
            a = int(acts[t][u][0])
            if not mask[t, u] or not (1 <= a <= 4) or ene[t, u] < p["move_cost"]:
                continue
            npos = np.clip(pos[t, u] + DIRS[a], 0, [W - 1, H - 1])
            if s0["tile"][npos[0], npos[1]] == 2:  # Asteroid
                continue
            pos[t, u] = npos
            ene[t, u] -= p["move_cost"]
            moved[t, u] = True
    orig = ene.copy()
    ev = {k: np.zeros((2, pos.shape[1]), dtype=float) for k in
          ("sap_direct", "sap_adj", "sap_paid", "void", "sap_fired", "sap_hit")}
    for t in range(2):
        o = 1 - t
        for u in range(pos.shape[1]):
            a = acts[t][u]
            if not mask[t, u] or int(a[0]) != 5 or orig[t, u] < p["sap_cost"]:
                continue
            dx, dy = int(a[1]), int(a[2])
            if max(abs(dx), abs(dy)) > p["sap_range"]:
                continue
            tx, ty = pos[t, u, 0] + dx, pos[t, u, 1] + dy
            if not (0 <= tx < W and 0 <= ty < H):
                continue
            ev["sap_fired"][t, u] = 1
            ev["sap_paid"][t, u] += p["sap_cost"]
            hit = False
            for v in range(pos.shape[1]):
                if not mask[o, v]:
                    continue
                ddx, ddy = pos[o, v, 0] - tx, pos[o, v, 1] - ty
                if ddx == 0 and ddy == 0:
                    ev["sap_direct"][o, v] += p["sap_cost"]
                    hit = True
                elif max(abs(ddx), abs(ddy)) == 1:
                    ev["sap_adj"][o, v] += int(p["sap_cost"] * p["dropoff"])
                    hit = True
            ev["sap_hit"][t, u] = float(hit)
    ene = ene - ev["sap_direct"] - ev["sap_adj"] - ev["sap_paid"]
    # Kollisionen (Energie nach Bewegung, vor Sap)
    agg = np.zeros((2, W, H))
    cnt = np.zeros((2, W, H))
    for t in range(2):
        for u in range(pos.shape[1]):
            if mask[t, u]:
                agg[t, pos[t, u, 0], pos[t, u, 1]] += orig[t, u]
                cnt[t, pos[t, u, 0], pos[t, u, 1]] += 1
    collided = np.zeros_like(mask)
    for t in range(2):
        for u in range(pos.shape[1]):
            if not mask[t, u]:
                continue
            x, y = pos[t, u]
            if cnt[1 - t, x, y] > 0 and not (agg[1 - t, x, y] < agg[t, x, y]):
                collided[t, u] = True
    # Void (aus orig, alle maskierten Units)
    void = np.zeros((2, W, H))
    for t in range(2):
        for u in range(pos.shape[1]):
            if not mask[t, u]:
                continue
            for dx, dy in ADJ4:
                x, y = pos[t, u, 0] + dx, pos[t, u, 1] + dy
                if 0 <= x < W and 0 <= y < H:
                    void[t, x, y] += orig[t, u]
    for t in range(2):
        for u in range(pos.shape[1]):
            if mask[t, u] and not collided[t, u]:
                x, y = pos[t, u]
                ev["void"][t, u] = np.floor(p["void"] * void[1 - t, x, y] / cnt[t, x, y])
    ene = ene - ev["void"]
    return dict(mask=mask, pos=pos, moved=moved, orig=orig, collided=collided,
                ene_pre_field=ene, ev=ev)


def point_tiles(s):
    n = s["rmask"].sum() // 2
    return (s["rw"] > 0) & (s["rw"] <= n)


def new_match_stats():
    keys = ["unit_steps", "pt_unit_steps", "productive", "stacked_unit_steps",
            "pt_stacked_unit_steps", "pt_energy_sum", "sap_fired", "sap_hit", "sap_dmg_dealt",
            "sap_dmg_direct_dealt", "sap_dmg_adj_dealt", "void_dealt", "sap_paid",
            "deaths_collision", "deaths_energy", "deaths_on_pt", "move_paid",
            "field_gain", "kills_by_sap_dealt", "kills_by_void_dealt", "pt_unit_steps_lowE"]
    return [{k: 0.0 for k in keys} for _ in range(2)]


def classify(agent, s0, pt_world, us, st):
    """Was tun unsere Units? (kanonischer Raum, Sicht des Agenten)"""
    from agents.sherlock import geometry as geo
    if agent._cache is None or agent._cache[0] != s0["steps"]:
        return
    ctx = agent._cache[1]
    b = agent.belief
    W, H = ctx["W"], ctx["H"]
    pt_true = geo.mirror_map(pt_world) if b.mirrored else pt_world
    ec = {tuple(c) for c in ctx["enemy_coords"].tolist()}
    own_half = lambda x, y: x + y <= W - 1
    targeted = set()
    for uid in ctx["ally_ids"].tolist():
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        e = float(ctx["ally_ene"][uid])
        tg = ctx["assigned"].get(int(uid))
        if tg is not None:
            targeted.add(tuple(tg))
        if e < 0:
            c = "dying"
        elif b.point_tiles[x, y]:
            c = "on_pt_first" if ctx["first_on_tile"].get((x, y)) == uid else "on_pt_stacked"
            if not pt_true[x, y]:
                c = "on_false_pt"
        elif tg is None:
            c = "no_target"
        elif b.point_tiles[tg]:
            own = own_half(*tg)
            c = "to_pt_own" if own else "to_pt_enemy"
            d = abs(tg[0] - x) + abs(tg[1] - y)
            st["dist_" + c] = st.get("dist_" + c, 0.0) + d
            if tuple(tg) in ec:
                st["to_pt_enemy_occupied"] = st.get("to_pt_enemy_occupied", 0.0) + 1
        elif b.candidate[tg]:
            c = "to_cand_own" if own_half(*tg) else "to_cand_enemy"
        else:
            c = "explore"
        st["cls_" + c] = st.get("cls_" + c, 0.0) + 1
    ally = {(int(ctx["ally_pos"][u][0]), int(ctx["ally_pos"][u][1])) for u in ctx["ally_ids"].tolist()}
    for x, y in np.argwhere(b.point_tiles).tolist():
        if (x, y) in ally:
            continue
        half = "own" if own_half(x, y) else "enemy"
        k = f"free_pt_{half}" if (x, y) not in ec else f"enemy_pt_{half}"
        st[k] = st.get(k, 0.0) + 1
        if (x, y) not in ec and (x, y) not in targeted:
            st[f"untargeted_free_pt_{half}"] = st.get(f"untargeted_free_pt_{half}", 0.0) + 1
    # wahre Punktfelder, die wir nicht kennen (eigene Haelfte)
    unknown = pt_true & ~b.point_tiles
    xs, ys = np.indices((W, H))
    st["true_pt_unknown_own"] = st.get("true_pt_unknown_own", 0.0) + float((unknown & (xs + ys <= W - 1)).sum())
    # davon: Relic bekannt (Kandidat ungetestet) oder Relic unbekannt (nie gesehen)
    near_known = np.zeros((W, H), dtype=bool)
    for rx, ry in b.relic_positions:
        near_known[max(0, rx - 2):rx + 3, max(0, ry - 2):ry + 3] = True
    own = xs + ys <= W - 1
    st["unknown_own_relic_known"] = st.get("unknown_own_relic_known", 0.0) + float((unknown & own & near_known).sum())
    st["unknown_own_relic_unseen"] = st.get("unknown_own_relic_unseen", 0.0) + float((unknown & own & ~near_known).sum())
    st["true_pt_own"] = st.get("true_pt_own", 0.0) + float((pt_true & (xs + ys <= W - 1)).sum())
    # Gegner auf wahren Punktfeldern in unserer Haelfte (Wahrheit, kanonisch)
    opp = 1 - us
    for u in np.nonzero(s0["mask"][opp] & (s0["ene"][opp] >= 0))[0]:
        x, y = s0["pos"][opp, u]
        if b.mirrored:
            x, y = geo.mirror_xy(x, y, W, H)
        if pt_true[x, y]:
            k = "opp_on_pt_our_half" if own_half(x, y) else "opp_on_pt_their_half"
            st[k] = st.get(k, 0.0) + 1


def play(seed, side, weights, overrides=()):
    import random

    import torch
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent

    torch.set_num_threads(1)
    env = LuxAIS3GymEnv(numpy_output=True)
    from scripts.par_eval import build_cfg
    agent = Agent_x("player_0", agent_path=weights, cfg=build_cfg(weights, list(overrides)), train=False, seed=0)
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    opp_side = "player_1" if side == "player_0" else "player_0"
    opp = make_opponent("solution92", opp_side)
    agent.new_game(side)
    random.seed(seed)
    np.random.seed(seed % (2 ** 32))
    obs, info = env.reset(seed=seed)
    env_cfg = info["params"]
    fp = info["full_params"]
    p = dict(move_cost=int(fp["unit_move_cost"]), sap_cost=int(fp["unit_sap_cost"]),
             sap_range=int(fp["unit_sap_range"]), dropoff=float(fp["unit_sap_dropoff_factor"]),
             void=float(fp["unit_energy_void_factor"]))
    agent.set_env_cfg(env_cfg)
    opp.set_env_cfg(env_cfg)
    us = 0 if side == "player_0" else 1
    matches = []
    cur = new_match_stats()
    step, done = 0, False
    mismatch = 0
    checked = 0
    while not done:
        a_us = agent.act(step=step, obs=obs[side])
        a_op = opp.act(step=step, obs=obs[opp_side])
        actions = {side: a_us, opp_side: a_op}
        s0 = snap(env.state)
        acts = [None, None]
        acts[us], acts[1 - us] = np.asarray(a_us), np.asarray(a_op)
        sim = simulate(s0, acts, p)
        obs, reward, term, trunc, info = env.step(actions)
        s1 = snap(env.state)
        done = bool(np.asarray(term[side])) or bool(np.asarray(trunc[side]))
        step += 1
        if s0["msteps"] == 0:
            continue
        pt = point_tiles(s0)
        classify(agent, s0, pt, us, cur[0])
        for t in range(2):
            T = 0 if t == us else 1  # 0 = wir, 1 = Gegner
            st = cur[T]
            m = sim["mask"][t]
            st["unit_steps"] += m.sum()
            occ = set()
            tiles = {}
            for u in np.nonzero(m)[0]:
                key = tuple(sim["pos"][t, u])
                tiles.setdefault(key, []).append(u)
            for key, us_ in tiles.items():
                on_pt = bool(pt[key])
                if len(us_) > 1:
                    st["stacked_unit_steps"] += len(us_)
                    if on_pt:
                        st["pt_stacked_unit_steps"] += len(us_)
                if on_pt:
                    occ.add(key)
                    st["pt_unit_steps"] += len(us_)
                    for u in us_:
                        st["pt_energy_sum"] += sim["orig"][t, u]
                        if sim["orig"][t, u] < p["sap_cost"]:
                            st["pt_unit_steps_lowE"] += 1
            st["productive"] += len(occ)
            if occ and st.get("first_point_step") is None:
                st["first_point_step"] = float(s0["msteps"])  # erster Schritt mit eigenem Punkt-Tile
            if len(occ) >= 3 and st.get("first_3pt_step") is None:
                st["first_3pt_step"] = float(s0["msteps"])
            ev = sim["ev"]
            st["sap_fired"] += ev["sap_fired"][t].sum()
            st["sap_hit"] += ev["sap_hit"][t].sum()
            st["sap_paid"] += ev["sap_paid"][t].sum()
            o = 1 - t
            st["sap_dmg_direct_dealt"] += ev["sap_direct"][o].sum()
            st["sap_dmg_adj_dealt"] += ev["sap_adj"][o].sum()
            st["sap_dmg_dealt"] += ev["sap_direct"][o].sum() + ev["sap_adj"][o].sum()
            st["void_dealt"] += ev["void"][o].sum()
            st["move_paid"] += sim["moved"][t].sum() * p["move_cost"]
            # Tode: Kollision oder Energie < 0 am Ende des Schritts
            for u in np.nonzero(m)[0]:
                if sim["collided"][t, u]:
                    st["deaths_collision"] += 1
                    if pt[tuple(sim["pos"][t, u])]:
                        st["deaths_on_pt"] += 1
                elif s1["ene"][t, u] < 0 and s1["msteps"] != 0:
                    st["deaths_energy"] += 1
                    if pt[tuple(sim["pos"][t, u])]:
                        st["deaths_on_pt"] += 1
                    # Ursache fuer den Gegner zaehlen
                    if ev["sap_direct"][t, u] + ev["sap_adj"][t, u] > 0:
                        cur[1 - T]["kills_by_sap_dealt"] += 1
                    elif ev["void"][t, u] > 0:
                        cur[1 - T]["kills_by_void_dealt"] += 1
                elif s1["msteps"] != 0 and s1["mask"][t, u]:
                    g = s1["ene"][t, u] - sim["ene_pre_field"][t, u]
                    st["field_gain"] += g
                    checked += 1
        if s1["msteps"] == 0 or done:  # Match vorbei
            pts = s0["points"] + 0
            res = {"us": cur[0], "opp": cur[1], "match": len(matches)}
            matches.append(res)
            cur = new_match_stats()
    wins = np.asarray(obs[side]["team_wins"]).tolist()
    env.close()
    return dict(seed=seed, side=side, params=p, wins=[int(wins[us]), int(wins[1 - us])],
                matches=matches)


def worker(job):
    weights, items, overrides = job
    out = []
    for seed, side in items:
        t0 = time.time()
        r = play(seed, side, weights, overrides)
        r["secs"] = round(time.time() - t0, 1)
        out.append(r)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--seeds", default=None, help="a-b")
    ap.add_argument("--seed-list", default=None, help="JSON-Liste von Seeds (statt --seeds)")
    ap.add_argument("--workers", type=int, default=7)
    ap.add_argument("--out", required=True)
    ap.add_argument("--set", action="append", default=[])
    args = ap.parse_args()
    if args.seed_list:
        seeds = [int(s) for s in json.loads(Path(args.seed_list).read_text())]
    else:
        a, b = (int(x) for x in args.seeds.split("-"))
        seeds = list(range(a, b + 1))
    items = [(s, side) for s in seeds for side in ("player_0", "player_1")]
    chunks = [items[i::args.workers] for i in range(args.workers)]
    ctx = mp.get_context("spawn")
    t0 = time.time()
    with ctx.Pool(len(chunks)) as pool:
        res = pool.map(worker, [(args.weights, c, args.set) for c in chunks if c])
    games = sorted((g for r in res for g in r), key=lambda g: (g["seed"], g["side"]))
    Path(args.out).write_text(json.dumps(games, default=float))
    print(f"{len(games)} Spiele in {time.time() - t0:.0f}s -> {args.out}")


if __name__ == "__main__":
    main()
