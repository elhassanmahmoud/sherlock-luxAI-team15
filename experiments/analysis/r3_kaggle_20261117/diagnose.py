"""Wo verliert R3 gegen Kaggle Energie und Einheiten? (17.11.2026, nur Messung)

Spielt das unveränderte R3-Paket gegen den Kaggle-Dritten und rechnet jeden Schritt mit den Regeln der Engine
(luxai_s3/env.py: Bewegung, Saps nach der Bewegung, Zusammenstöße mit der Energie vor den Saps, Energie-Sog der
4 Nachbarfelder, danach Energiefeld und Nebel) für beide Seiten nach. Zusammenstöße prüft das Skript gegen den
echten Folgezustand (Spalte `check_mismatch` muss 0 sein).

Ausgabe in --out: `matches.csv` (eine Zeile je Spiel, Match und Team mit Energieflüssen, Saps, Todesursachen,
Punkten) und `deaths.csv` (eine Zeile je Tod).

    python experiments/analysis/r3_kaggle_20261117/diagnose.py --seeds 7256000:7256030 --workers 10 --out DIR
    python experiments/analysis/r3_kaggle_20261117/diagnose.py --agent r3t:granate,sog --seeds ... --out DIR

Mit --agent r3t:SCHALTER spielt R3 mit der Taktikschicht (agents/sherlock_r3t); `games.csv` enthält dann je Spiel,
wie oft jede Taktik eingegriffen hat. Mit --agent student:ens9 spielt der reine Imitations-Schüler alle Units
(Schalter wie bei r3t:schueler=, also stay_bias 1.5 und unstack).
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

DIRS = np.array([[0, 0], [0, -1], [1, 0], [0, 1], [-1, 0]])
ADJ4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
R3_ZIP = ROOT / "experiments/releases/20261116_r3_finale/agent.zip"
FLOWS = ("move", "sap_paid", "sap_direct_in", "sap_splash_in", "void_in", "field_net", "nebula")


def snap(state) -> dict:
    return dict(pos=np.asarray(state.units.position).astype(int), en=np.asarray(state.units.energy)[..., 0].astype(int),
                mask=np.asarray(state.units_mask).astype(bool), tile=np.asarray(state.map_features.tile_type).astype(int),
                weights=np.asarray(state.relic_nodes_map_weights), match_steps=int(state.match_steps),
                points=np.asarray(state.team_points).astype(int), wins=np.asarray(state.team_wins).astype(int))


def tile_at(tile, x, y):
    """Wie die Engine vor dem Begrenzen: -1 ist das letzte Feld, zu große Indizes das letzte Feld."""
    w, h = tile.shape
    return tile[min(x, w - 1), min(y, h - 1)]


def account(s: dict, act: np.ndarray, p: dict) -> dict:
    """Ein Schritt nach den Engine-Regeln. act: (2, 16, 3) Weltaktionen. Gibt Flüsse, Tode und Schussdaten zurück."""
    W, H = s["tile"].shape
    cost, rng, drop, vf, mc = p["unit_sap_cost"], p["unit_sap_range"], p["unit_sap_dropoff_factor"], \
        p["unit_energy_void_factor"], p["unit_move_cost"]
    alive = s["mask"] & (s["en"] >= 0)
    if s["match_steps"] == 0:
        alive[:] = False
    pos, en = s["pos"].copy(), s["en"].copy()
    fl = {k: np.zeros((2, 16), int) for k in FLOWS}
    for t in range(2):
        for u in np.flatnonzero(alive[t]):
            a = int(act[t][u][0])
            if 1 <= a <= 4 and en[t, u] >= mc:
                nx, ny = pos[t, u] + DIRS[a]
                if tile_at(s["tile"], nx, ny) != 2:
                    pos[t, u] = (min(max(nx, 0), W - 1), min(max(ny, 0), H - 1))
                    en[t, u] -= mc
                    fl["move"][t, u] += mc
    orig = en.copy()
    sap_ok = np.zeros((2, 16), bool)
    tgt = np.zeros((2, 16, 2), int)
    for t in range(2):
        for u in np.flatnonzero(alive[t]):
            if int(act[t][u][0]) == 5:
                dx, dy = int(act[t][u][1]), int(act[t][u][2])
                tx, ty = pos[t, u, 0] + dx, pos[t, u, 1] + dy
                if orig[t, u] >= cost and max(abs(dx), abs(dy)) <= rng and 0 <= tx < W and 0 <= ty < H:
                    sap_ok[t, u], tgt[t, u] = True, (tx, ty)
    shots = {t: [] for t in range(2)}  # je Schuss: Treffer direkt, Treffer Streu, Schaden
    for t in range(2):
        o = 1 - t
        for v in np.flatnonzero(sap_ok[t]):
            d = int(sum(1 for u in np.flatnonzero(alive[o]) if (pos[o, u] == tgt[t, v]).all()))
            sp = int(sum(1 for u in np.flatnonzero(alive[o]) if np.abs(pos[o, u] - tgt[t, v]).max() == 1))
            shots[t].append((d, sp))
        for u in np.flatnonzero(alive[o]):
            nd = int(sum(1 for v in np.flatnonzero(sap_ok[t]) if (tgt[t, v] == pos[o, u]).all()))
            ns = int(sum(1 for v in np.flatnonzero(sap_ok[t]) if np.abs(tgt[t, v] - pos[o, u]).max() == 1))
            dd = cost * nd
            ds = int(np.float32(cost) * np.float32(drop) * np.float32(ns))
            en[o, u] -= dd + ds
            fl["sap_direct_in"][o, u] += dd
            fl["sap_splash_in"][o, u] += ds
        for v in np.flatnonzero(sap_ok[t]):
            en[t, v] -= cost
            fl["sap_paid"][t, v] += cost
    agg = np.zeros((2, W, H), int)
    cnt = np.zeros((2, W, H), int)
    void = np.zeros((2, W, H), int)
    for t in range(2):
        for u in np.flatnonzero(alive[t]):
            x, y = pos[t, u]
            agg[t, x, y] += orig[t, u]
            cnt[t, x, y] += 1
            for dx, dy in ADJ4:
                if 0 <= x + dx < W and 0 <= y + dy < H:
                    void[t, x + dx, y + dy] += orig[t, u]
    collided = np.zeros((2, 16), bool)
    for t in range(2):
        o = 1 - t
        for u in np.flatnonzero(alive[t]):
            x, y = pos[t, u]
            if cnt[o, x, y] > 0 and not agg[o, x, y] < agg[t, x, y]:
                collided[t, u] = True
    survive = alive & ~collided
    for t in range(2):
        o = 1 - t
        for u in np.flatnonzero(survive[t]):
            x, y = pos[t, u]
            loss = int(np.floor(np.float32(vf) * np.float32(void[o, x, y]) / np.float32(cnt[t, x, y])))
            en[t, u] -= loss
            fl["void_in"][t, u] += loss
    return dict(alive=alive, pos=pos, en_after_void=en, orig=orig, fl=fl, collided=collided, survive=survive,
                sap_ok=sap_ok, shots=shots)


def play(job):
    seed, side, spec = job
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    from scripts.experiment import limit_threads
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from scripts import r3_package
    from scripts.common import make_opponent

    env = LuxAIS3GymEnv(numpy_output=True)
    opp_side = "player_1" if side == "player_0" else "player_0"
    if spec.startswith("r3t:"):
        from agents.sherlock_r3t.agent import make_r3t
        me = make_r3t(side, R3_ZIP, spec[4:])
    elif spec.startswith("student:"):  # 17.11.: reiner Schüler (alle Units), gleiche Schalter wie in r3t:schueler=
        from agents.sherlock_r3t.agent import load_student
        me = load_student(spec[len("student:"):], side)
    else:
        me = r3_package.r3_package_agent(side, str(R3_ZIP))
    opp = make_opponent("kaggle3", opp_side)
    for a, sd in ((me, side), (opp, opp_side)):
        if hasattr(a, "new_game"):
            a.new_game(sd)
    import random
    random.seed(seed)
    np.random.seed(seed % (2 ** 32))
    obs, info = env.reset(seed=seed)
    p = {k: info["full_params"][k] for k in ("unit_sap_cost", "unit_sap_range", "unit_sap_dropoff_factor",
                                              "unit_energy_void_factor", "unit_move_cost", "nebula_tile_energy_reduction")}
    for a in (me, opp):
        if hasattr(a, "set_env_cfg"):
            a.set_env_cfg(info["params"])
    team = 0 if side == "player_0" else 1
    rows, deaths = {}, []
    match, mismatch, step, done = -1, 0, 0, False
    from agents.sherlock_r3t.tactics import Tactics, TacticsCfg
    predictor = Tactics(TacticsCfg())
    pred = {}  # Kategorie -> [n, Summe p(tatsaechlich), Treffer top-1, blieb stehen, lief weiter]
    prev_true = {}
    while not done:
        s = snap(env.state)
        if s["match_steps"] == 0:
            match += 1
        acts = {side: me.act(step=step, obs=obs[side]), opp_side: opp.act(step=step, obs=obs[opp_side])}
        act = np.zeros((2, 16, 3), int)
        act[team] = np.asarray(acts[side])
        act[1 - team] = np.asarray(acts[opp_side])
        r = account(s, act, p)
        obs, _, term, trunc, _ = env.step(acts)
        done = bool(np.asarray(term[side])) or bool(np.asarray(trunc[side]))
        s2 = snap(env.state)
        k = 1 - team
        if s["match_steps"] != 0 and s2["match_steps"] != 0:
            W_, H_ = s["tile"].shape
            for u in np.flatnonzero(r["alive"][k] & r["survive"][k]):
                q = (int(s["pos"][k, u, 0]), int(s["pos"][k, u, 1]))
                nxt = (int(r["pos"][k, u, 0]), int(r["pos"][k, u, 1]))
                prv = prev_true.get(int(u))
                holder = bool(s["weights"][q] > 0)
                cat = "halter" if holder else "unbekannt" if prv is None else "stehend" if prv == q else "laufend"
                d = predictor._predict(q, prv, int(s["en"][k, u]), int(p["unit_move_cost"]), s["tile"], holder, W_, H_)
                c = pred.setdefault(cat, [0, 0.0, 0, 0, 0])
                c[0] += 1
                c[1] += d.get(nxt, 0.0)
                c[2] += int(max(d, key=d.get) == nxt)
                c[3] += int(nxt == q)
                if prv is not None and prv != q:
                    c[4] += int((nxt[0] - q[0], nxt[1] - q[1]) == (q[0] - prv[0], q[1] - prv[1]))
        # Position zu Beginn dieses Schritts merken: im nächsten Schritt ist das die Vorposition (wie in der Taktikschicht,
        # die die Gegnerposition der letzten Beobachtung mit der aktuellen vergleicht)
        prev_true = {int(u): (int(s["pos"][k, u, 0]), int(s["pos"][k, u, 1]))
                     for u in np.flatnonzero(r["alive"][k] & r["survive"][k])} if s2["match_steps"] != 0 else {}
        for t in range(2):
            key = (match, t)
            row = rows.setdefault(key, dict(seed=seed, side=side, match=match, team="R3" if t == team else "Kaggle",
                                            **{f: 0 for f in FLOWS}, saps=0, sap_direct_hits=0, sap_splash_hits=0,
                                            sap_misses=0, deaths_collision=0, deaths_energy=0, unit_steps=0,
                                            field_net_points=0, field_raw_points=0, field_raw_other=0,
                                            unit_steps_on_points=0, energy_sum_end=0, units_end=0, points=0,
                                            won=0, check_mismatch=0))
            al = r["alive"][t]
            row["unit_steps"] += int(al.sum())
            for u in np.flatnonzero(al):
                x, y = r["pos"][t, u]
                row["unit_steps_on_points"] += int(s["weights"][x, y] > 0)
            for f in FLOWS[:5]:
                row[f] += int(r["fl"][f][t].sum())
            for d, sp in r["shots"][t]:
                row["saps"] += 1
                row["sap_direct_hits"] += d
                row["sap_splash_hits"] += sp
                row["sap_misses"] += int(d == 0 and sp == 0)
            o = 1 - t
            for u in np.flatnonzero(al):
                x, y = r["pos"][t, u]
                near = [int(r["orig"][o, v]) for v in np.flatnonzero(r["alive"][o])
                        if abs(r["pos"][o, v] - r["pos"][t, u]).sum() <= 2]
                info_row = dict(seed=seed, side=side, match=match, match_step=s["match_steps"],
                                team="R3" if t == team else "Kaggle", energy_before=int(s["en"][t, u]),
                                on_point=int(s["weights"][x, y] > 0), enemies_within2=len(near),
                                max_enemy_energy_within2=max(near) if near else 0,
                                sap_in=int(r["fl"]["sap_direct_in"][t, u] + r["fl"]["sap_splash_in"][t, u]),
                                void_in=int(r["fl"]["void_in"][t, u]))
                if r["collided"][t, u]:
                    row["deaths_collision"] += 1
                    deaths.append(dict(info_row, cause="collision"))
                elif s2["match_steps"] != 0:
                    if not s2["mask"][t, u]:
                        mismatch += 1  # Engine entfernte die Unit, obwohl die Nachrechnung sie überleben lässt
                    e2 = int(s2["en"][t, u])
                    gain = e2 - int(r["en_after_void"][t, u])
                    if s2["tile"][x, y] == 1:
                        row["nebula"] += int(p["nebula_tile_energy_reduction"])
                    row["field_net"] += gain
                    raw = int(np.asarray(env.state.map_features.energy)[x, y])  # Feldwert ohne Kappung
                    if s["weights"][x, y] > 0:
                        row["field_net_points"] += gain
                        row["field_raw_points"] += raw
                    else:
                        row["field_raw_other"] += raw
                    if e2 < 0:
                        row["deaths_energy"] += 1
                        cause = "sap" if info_row["sap_in"] >= info_row["void_in"] and info_row["sap_in"] > 0 else \
                            "void" if info_row["void_in"] > 0 else "other"
                        deaths.append(dict(info_row, cause=cause))
            if s2["match_steps"] != 0:
                for u in np.flatnonzero(r["collided"][t]):
                    if s2["mask"][t, u] and (s2["pos"][t, u] == r["pos"][t, u]).all() and s2["en"][t, u] == r["orig"][t, u]:
                        mismatch += 1  # angeblich zusammengestoßen, aber unverändert im Folgezustand
        if s2["match_steps"] == 0 or done:  # Matchende: Stand vor dem Reset festhalten
            for t in range(2):
                row = rows[(match, t)]
                m = s2["mask"][t] & (s2["en"][t] >= 0)  # die Engine entfernt die Units erst im nächsten Schritt
                row["units_end"] = int(m.sum())
                row["energy_sum_end"] = int(s2["en"][t][m].sum())
                row["won"] = int(s2["wins"][t] > s["wins"][t])
        for t in range(2):
            if s2["match_steps"] != 0:
                rows[(match, t)]["points"] = int(s2["points"][t])
            else:
                rows[(match, t)]["points"] = max(rows[(match, t)]["points"], int(s["points"][t]))
        step += 1
    env.close()
    out = list(rows.values())
    for row in out:
        row["check_mismatch"] = mismatch
    counts = dict(getattr(getattr(me, "tactics", None), "counts", {}) or {})
    game = dict(seed=seed, side=side, agent=spec or "r3", **{f"t_{k}": v for k, v in sorted(counts.items())})
    for cat, (n, ps, top, stay, cont) in pred.items():
        game.update({f"v_{cat}_n": n, f"v_{cat}_p": ps, f"v_{cat}_top1": top, f"v_{cat}_stay": stay,
                     f"v_{cat}_cont": cont})
    return out, deaths, game


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", required=True, help="START:ENDE (Ende exklusiv)")
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--out", required=True)
    ap.add_argument("--agent", default="r3", help="r3 (unverändertes Paket), r3t:SCHALTER oder student:NAME|PFAD")
    a = ap.parse_args()
    lo, hi = map(int, a.seeds.split(":"))
    spec = "" if a.agent == "r3" else a.agent
    jobs = [(s, side, spec) for s in range(lo, hi) for side in ("player_0", "player_1")]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    with mp.get_context("spawn").Pool(a.workers) as pool:
        res = pool.map(play, jobs, chunksize=1)
    matches = [r for rows, _, _ in res for r in rows]
    deaths = [d for _, ds, _ in res for d in ds]
    games = [g for _, _, g in res]
    keys = sorted({k for g in games for k in g if k.startswith(("t_", "v_"))})
    games = [{**{k: g.get(k) for k in ("seed", "side", "agent")}, **{k: g.get(k, 0) for k in keys}} for g in games]
    for name, data in (("matches.csv", matches), ("deaths.csv", deaths), ("games.csv", games)):
        with open(out / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0]))
            w.writeheader()
            w.writerows(data)
    print(f"{len(jobs)} Spiele, {len(matches)} Matchzeilen, {len(deaths)} Tode, "
          f"Nachrechnung abweichend: {sum(r['check_mismatch'] for r in matches if r['match'] == 0 and r['team'] == 'R3')}")


if __name__ == "__main__":
    main()
