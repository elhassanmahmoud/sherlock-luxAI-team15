"""Echte Züge von Sherlock V16 für die Abschlusspräsentation (19.11.2026, nur Messung).

Spielt das unveränderte Abgabepaket (experiments/releases/20261117_sherlock_v16/agent.zip, geladen wie in den
Bestätigungen über scripts/r3_package.py) als player_0 gegen einen Gegner und protokolliert für jede eigene Einheit
und jeden Zug:

- die Bewertungen beider Netze (v9 und v8L) vor und nach der Aktionsmaske,
- Stay-Bias und Halter-Regel, die Aktion vor und nach dem Entstapeln und den tatsächlich gesendeten Befehl,
- bei Schüssen das Zielfeld, ob es für Sherlock sichtbar war, ob ein Gegner sichtbar in Trefferweite stand und
  die tatsächlichen Treffer nach den Engine-Regeln (Bewegung vor dem Schuss; `account()` aus
  experiments/analysis/r3_kaggle_20261117/diagnose.py).

Jeder Zug wird gegen den echten Befehl des Pakets geprüft (gleiche Aktion, gleiches Schussziel). Das Paket wird
nicht verändert; die Messung hängt sich nur an Funktionen des geladenen Pakets an.

    python experiments/analysis/finale_20261119/zugbeispiel.py --seed 4242 --opponent kaggle3 --out DIR
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

V16_ZIP = ROOT / "experiments/releases/20261117_sherlock_v16/agent.zip"
V16_SHA = "0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"
ACTIONS = ("stehen", "hoch", "rechts", "runter", "links", "schuss")
DIRS = np.array([[0, 0], [0, -1], [1, 0], [0, 1], [-1, 0]])


def load_diagnose():
    path = ROOT / "experiments/analysis/r3_kaggle_20261117/diagnose.py"
    spec = importlib.util.spec_from_file_location("diagnose_r3_kaggle", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def softmax(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    finite = np.isfinite(x)
    out = np.zeros_like(x)
    if finite.any():
        e = np.exp(x[finite] - x[finite].max())
        out[finite] = e / e.sum()
    return out


def log_softmax(x: np.ndarray) -> np.ndarray:
    """Wie torch.log_softmax: gesperrte Einträge (-inf) bleiben -inf."""
    x = np.asarray(x, dtype=np.float64)
    out = np.full_like(x, -np.inf)
    finite = np.isfinite(x)
    if finite.any():
        m = x[finite].max()
        out[finite] = x[finite] - (m + np.log(np.exp(x[finite] - m).sum()))
    return out


def install_probes(ia, inet, cap: dict) -> None:
    """Hängt sich an die Funktionen des geladenen Pakets (Rückgabewerte unverändert)."""
    orig_feat = ia.featurize

    def featurize(agent, obs):
        fz = orig_feat(agent, obs)
        cap["fz"] = fz
        return fz

    ia.featurize = featurize

    orig_fwd = inet.ImitationNet.forward_all

    def forward_all(self, planes, step_idx, pos, feats):
        out = orig_fwd(self, planes, step_idx, pos, feats)
        cap.setdefault("nets", []).append(dict(ch=int(self.arch["ch"]), blocks=int(self.arch["blocks"]),
                                               logits=out[0].detach().numpy().copy(),
                                               smap=out[2].detach().numpy().copy()))
        return out

    inet.ImitationNet.forward_all = forward_all

    orig_hold = ia.ImitationAgent._point_holder_rows

    def holder_rows(self, ctx, ids, pos):
        rows = orig_hold(self, ctx, ids, pos)
        cap["holders"] = [int(r) for r in rows]
        return rows

    ia.ImitationAgent._point_holder_rows = holder_rows

    orig_unstack = ia.ImitationAgent._unstack_actions

    def unstack(self, ctx, ids, pos, logp, acts):
        out = orig_unstack(self, ctx, ids, pos, logp, acts)
        cap["logp"] = np.asarray(logp, dtype=np.float64).copy()
        cap["pre_unstack"] = np.asarray(acts).copy()
        cap["post_unstack"] = np.asarray(out).copy()
        return out

    ia.ImitationAgent._unstack_actions = unstack


def mask_reason(a: int, x: int, y: int, belief, energy: float, move_cost: float, W: int, H: int) -> str:
    """Grober Grund einer gesperrten Bewegung (nur für die Beschreibung, nicht für die Prüfung)."""
    if a == 0:
        return "stehen gesperrt"
    if a == 5:
        return "zu wenig Energie für einen Schuss"
    nx, ny = x + int(DIRS[a][0]), y + int(DIRS[a][1])
    if not (0 <= nx < W and 0 <= ny < H):
        return "Kartenrand"
    if int(np.asarray(belief.tile_type)[nx, ny]) == 2:
        return "Asteroid"
    if energy < move_cost:
        return "zu wenig Energie"
    return "Gefahr durch stärkeren Gegner (safe_moves/collision_guard) oder Nebel"


def run(seed: int, opponent: str, out: Path) -> dict:
    from scripts.experiment import limit_threads
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from scripts import r3_package
    from scripts.common import make_opponent

    data = V16_ZIP.read_bytes()
    if hashlib.sha256(data).hexdigest() != V16_SHA:
        raise SystemExit("Abgabepaket hat eine andere SHA-256")
    diag = load_diagnose()
    side, opp_side, team = "player_0", "player_1", 0
    me = r3_package.r3_package_agent(side, str(V16_ZIP))
    ia = sys.modules["sherlock.imitation_agent"]
    inet = sys.modules["sherlock.imitation_net"]
    im = me._imitation
    if im is None or len(im.extra_nets) != 1:
        raise SystemExit("Erwartet: nachgeahmtes Ensemble aus zwei Netzen")
    cap: dict = {}
    install_probes(ia, inet, cap)

    env = LuxAIS3GymEnv(numpy_output=True)
    opp = make_opponent(opponent, opp_side)
    for a, sd in ((me, side), (opp, opp_side)):
        if hasattr(a, "new_game"):
            a.new_game(sd)
    random.seed(seed)
    np.random.seed(seed % (2 ** 32))
    obs, info = env.reset(seed=seed)
    p = {k: info["full_params"][k] for k in ("unit_sap_cost", "unit_sap_range", "unit_sap_dropoff_factor",
                                              "unit_energy_void_factor", "unit_move_cost")}
    for a in (me, opp):
        if hasattr(a, "set_env_cfg"):
            a.set_env_cfg(info["params"])
    stay_bias = float(im.cfg.imit_stay_bias)
    rows, examples = [], []
    checks = dict(decisions=0, action_equal=0, target_equal=0, saps=0, logp_equal=0)
    step, done = 0, False
    while not done:
        s = diag.snap(env.state)
        cap.clear()
        o = obs[side]
        my_act = np.asarray(me.act(step=step, obs=o))
        opp_act = np.asarray(opp.act(step=step, obs=obs[opp_side]))
        act = np.zeros((2, 16, 3), int)
        act[team], act[1 - team] = my_act, opp_act
        r = diag.account(s, act, p)
        fz = cap.get("fz")
        if fz is not None:
            if len(cap.get("nets", [])) != 2 or "logp" not in cap:
                raise SystemExit(f"Schritt {step}: Messpunkte unvollständig")
            ctx, ids, feats, masks, sap_targets, planes, pos = fz
            if im.belief.mirrored:
                raise SystemExit("player_0 darf nicht gespiegelt sein")
            W, H = int(ctx["W"]), int(ctx["H"])
            energy = np.array([float(ctx["ally_ene"][u]) for u in ids])
            legal = ia.sap_legal(masks, energy, float(ctx["sap_cost"]))
            net_logp = []
            raw_p = []
            for n in cap["nets"]:
                lg = n["logits"].astype(np.float64)
                raw_p.append(np.stack([softmax(row) for row in lg]))
                ml = np.where(legal, lg, -np.inf)
                net_logp.append(np.stack([log_softmax(row) for row in ml]))
            comb = net_logp[0] + net_logp[1]
            holders = set(cap.get("holders", []))
            bias = np.array([0.0 if k in holders else stay_bias for k in range(len(ids))])
            expect = comb.copy()
            expect[:, 0] -= bias
            final = cap["logp"]
            finite = np.isfinite(final)
            same_logp = bool(np.array_equal(finite, np.isfinite(expect)) and
                             np.allclose(final[finite], expect[finite], atol=1e-4))
            sap_rng = int(ctx["sap_range"])
            sm = [n["smap"][0].astype(np.float64) for n in cap["nets"]]
            smap = sum(log_softmax(m.flatten()).reshape(W, H) for m in sm)
            vis = np.asarray(o["sensor_mask"], dtype=bool)
            emask = np.asarray(o["units_mask"][1 - team], dtype=bool)
            epos = np.asarray(o["units"]["position"][1 - team])
            visible_enemies = [(int(x), int(y)) for (x, y), mm in zip(epos, emask) if mm and x >= 0]
            shots = dict(zip(np.flatnonzero(r["sap_ok"][team]).tolist(), r["shots"][team]))
            for k, uid in enumerate(ids):
                uid = int(uid)
                checks["decisions"] += 1
                checks["logp_equal"] += int(same_logp)
                x, y = int(pos[k][0]), int(pos[k][1])
                world = [int(v) for v in my_act[uid]]
                a_post = int(cap["post_unstack"][k])
                a_sent = world[0]
                same_action = (a_post == a_sent) or (a_post == 5 and a_sent == 5)
                checks["action_equal"] += int(same_action)
                comb_p = softmax(comb[k])
                final_p = softmax(final[k])
                raw_comb = np.log(np.maximum(raw_p[0][k], 1e-300)) + np.log(np.maximum(raw_p[1][k], 1e-300))
                top_raw = int(np.argmax(raw_comb))
                row = dict(step=step, match=step // 101 + 1, match_step=int(ctx["match_step"]), unit=uid, x=x, y=y,
                           energy=round(float(energy[k]), 1), holder=int(k in holders),
                           action=ACTIONS[a_sent] if 0 <= a_sent <= 5 else str(a_sent),
                           argmax_before_unstack=ACTIONS[int(cap["pre_unstack"][k])],
                           top_unmasked=ACTIONS[top_raw], top_unmasked_legal=int(bool(legal[k, top_raw])),
                           top_without_bias=ACTIONS[int(np.argmax(comb[k]))])
                for j, name in enumerate(ACTIONS):
                    row[f"p_{name}"] = round(float(final_p[j]), 4)
                if a_sent == 5:
                    checks["saps"] += 1
                    dx, dy = world[1], world[2]
                    tx, ty = x + dx, y + dy
                    window = np.full((W, H), -np.inf)
                    xs, ys = np.meshgrid(np.arange(W), np.arange(H), indexing="ij")
                    inside = np.maximum(np.abs(xs - x), np.abs(ys - y)) <= sap_rng
                    window[inside] = smap[inside]
                    best = np.unravel_index(int(np.argmax(window)), window.shape)
                    checks["target_equal"] += int((int(best[0]), int(best[1])) == (tx, ty))
                    tp = softmax(window.flatten()).reshape(W, H)
                    near_visible = [e for e in visible_enemies if max(abs(e[0] - tx), abs(e[1] - ty)) <= 1]
                    in_range_visible = [e for e in visible_enemies if max(abs(e[0] - x), abs(e[1] - y)) <= sap_rng]
                    dist_vis = min((max(abs(e[0] - tx), abs(e[1] - ty)) for e in visible_enemies), default=99)
                    # sichtbar: ein sichtbarer Gegner im 3x3 um das Ziel; vorhalten: nächster sichtbarer Gegner genau
                    # zwei Felder vom Ziel (kann mit einem Zug hineinlaufen); unsichtbar: kein sichtbarer Gegner näher
                    category = "sichtbar" if dist_vis <= 1 else "vorhalten" if dist_vis == 2 else "unsichtbar"
                    direct, splash = shots.get(uid, (None, None))
                    row.update(target_x=tx, target_y=ty, target_dist=max(abs(dx), abs(dy)),
                               target_visible=int(vis[tx, ty]), enemy_visible_near_target=int(bool(near_visible)),
                               nearest_visible_enemy_to_target=dist_vis, shot_category=category,
                               enemies_visible_in_range=len(in_range_visible), target_p=round(float(tp[tx, ty]), 4),
                               direct_hits=direct, splash_hits=splash)
                    if category == "unsichtbar" and direct:
                        order = np.argsort(-tp.flatten())[:5]
                        top = [dict(x=int(i // H), y=int(i % H), p=round(float(tp.flatten()[i]), 4)) for i in order]
                        true_enemy = [(int(r["pos"][1 - team, u, 0]), int(r["pos"][1 - team, u, 1]))
                                      for u in np.flatnonzero(r["alive"][1 - team])]
                        hit_enemies = [dict(x=ex, y=ey, direct=int((ex, ey) == (tx, ty)))
                                       for ex, ey in true_enemy if max(abs(ex - tx), abs(ey - ty)) <= 1]
                        own_units = [(int(ctx["ally_pos"][u][0]), int(ctx["ally_pos"][u][1])) for u in ids]
                        examples.append(dict(kind="schuss_ohne_sichtbaren_gegner", **row, top_targets=top,
                                             sap_range=sap_rng, sap_cost=float(ctx["sap_cost"]),
                                             visible_enemies=visible_enemies, true_enemies_after_move=true_enemy,
                                             hit_enemies=hit_enemies, own_units=own_units,
                                             relics=[[int(a), int(b)] for a, b in im.belief.relic_positions],
                                             point_tiles=np.asarray(im.belief.point_tiles).astype(int).tolist(),
                                             target_known_point_tile=int(bool(np.asarray(im.belief.point_tiles)[tx, ty])),
                                             nebula=np.asarray(im.belief.tile_type == 1).astype(int).tolist(),
                                             asteroid=np.asarray(im.belief.tile_type == 2).astype(int).tolist(),
                                             sensor_mask=vis.astype(int).tolist()))
                if not legal[k, top_raw]:
                    examples.append(dict(kind="bester_zug_gesperrt", **row,
                                         reason=mask_reason(top_raw, x, y, im.belief, float(energy[k]),
                                                            float(p["unit_move_cost"]), W, H),
                                         raw_v9=[round(float(v), 4) for v in raw_p[0][k]],
                                         raw_v8L=[round(float(v), 4) for v in raw_p[1][k]],
                                         legal=[int(v) for v in legal[k]],
                                         combined_after_mask=[round(float(v), 4) for v in comb_p],
                                         final=[round(float(v), 4) for v in final_p]))
                if k in holders:
                    without = comb[k].copy()
                    without[0] -= stay_bias
                    if int(np.argmax(without)) != int(np.argmax(final[k])):
                        examples.append(dict(kind="halter_regel_entscheidet", **row,
                                             combined_after_mask=[round(float(v), 4) for v in comb_p],
                                             final=[round(float(v), 4) for v in final_p],
                                             without_holder_rule=[round(float(v), 4) for v in softmax(without)]))
                rows.append(row)
        obs, _, term, trunc, _ = env.step({side: my_act, opp_side: opp_act})
        done = bool(np.asarray(term[side])) or bool(np.asarray(trunc[side]))
        step += 1
    wins = [int(v) for v in np.asarray(obs[side]["team_wins"])]
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{opponent}_{seed}"
    with (out / f"zuege_{stem}.csv").open("w", newline="") as f:
        keys = sorted({k for rw in rows for k in rw}, key=lambda k: (k not in rows[0], k))
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    saps = [rw for rw in rows if rw["action"] == "schuss"]

    def shot_stats(cat):
        rws = [rw for rw in saps if rw["shot_category"] == cat]
        return dict(n=len(rws), direct=sum(1 for rw in rws if (rw["direct_hits"] or 0) > 0),
                    any_hit=sum(1 for rw in rws if (rw["direct_hits"] or 0) + (rw["splash_hits"] or 0) > 0),
                    target_not_visible=sum(1 for rw in rws if not rw["target_visible"]))

    reasons: dict[str, int] = {}
    for e in examples:
        if e["kind"] == "bester_zug_gesperrt":
            reasons[e["reason"]] = reasons.get(e["reason"], 0) + 1
    summary = dict(seed=seed, opponent=opponent, v16_side=side, package_sha256=V16_SHA, steps=step,
                   match_wins_v16_opponent=wins, stay_bias=stay_bias, checks=checks,
                   decisions=len(rows), saps=len(saps),
                   shots={c: shot_stats(c) for c in ("sichtbar", "vorhalten", "unsichtbar")},
                   blocked_best_moves=sum(1 for e in examples if e["kind"] == "bester_zug_gesperrt"),
                   blocked_reasons=reasons,
                   holder_rule_decisive=sum(1 for e in examples if e["kind"] == "halter_regel_entscheidet"),
                   stay_bias_decisive=sum(1 for rw in rows if rw["top_without_bias"] == "stehen"
                                          and rw["argmax_before_unstack"] != "stehen"))
    (out / f"beispiele_{stem}.json").write_text(json.dumps(dict(summary=summary, examples=examples),
                                                           ensure_ascii=False, indent=1))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=4242)
    ap.add_argument("--opponent", default="kaggle3")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    print(json.dumps(run(a.seed, a.opponent, a.out), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
