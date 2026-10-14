"""Warum verlieren wir? Spiele mit Ground Truth aus dem Env-Zustand analysieren.

    python -m scripts.analyze_losses --weights agents/sherlock/weights/agent_p0.pth \
        --opponent solution92 --first 0 --n-seeds 10 --out experiments/analysis/a_0.csv

Eine Zeile pro (Spiel, Match, Team). Gemessen wird mit env.state, also mit
Wissen, das kein Agent hat: welche Tiles WIRKLICH Punkte bringen (Formel aus
luxai_s3/env.py, team_relic_score), wo alle Units stehen, wer stirbt.
Nur Validierungs-Seeds (500 000+).
Ab Punktemessung v2: first_score_step=-1 bedeutet nie gepunktet;
101 ist ein erster Punkt im letzten Schritt (bei max_steps_in_match=100).
"""
from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

import numpy as np

from scripts import protocol as P
from scripts.experiment import limit_threads
from scripts.scoring import POINT_COUNTING_VERSION, match_points_after_step, point_tile_map

FIELDS = ["seed", "side", "match", "team", "is_us", "won_match", "points", "point_counting_version",
          "first_score_step", "occ_mean", "occ_mean_late", "point_tiles_total",
          "occ_own_half", "occ_enemy_half", "contested_mean", "units_mean",
          "units_on_points_mean", "energy_mean", "neg_energy_units_mean", "deaths",
          "belief_known", "belief_correct"]


def play_and_measure(env, agent, opp, seed: int, our_side: str) -> list[dict]:
    from agents.sherlock import geometry as geo

    opp_side = "player_1" if our_side == "player_0" else "player_0"
    us = 0 if our_side == "player_0" else 1
    agent.new_game(our_side)
    if hasattr(opp, "new_game"):
        opp.new_game(opp_side)
    random.seed(seed)
    np.random.seed(seed % (2**32))
    obs, info = env.reset(seed=seed)
    for a in (agent, opp):
        if hasattr(a, "set_env_cfg"):
            a.set_env_cfg(info["params"])
    W = H = 24
    xs, ys = np.meshgrid(np.arange(W), np.arange(H), indexing="ij")
    # eigene Haelfte: naeher am eigenen Spawn (Team 0: (0,0), Team 1: (23,23))
    own_half = [xs + ys < W - 1, xs + ys > W - 1]

    acc = None
    rows: list[dict] = []
    prev_alive = None
    step, done = 0, False

    def new_acc():
        return {t: dict(first=None, occ=[], occ_late=[], own=[], enemy=[], cont=[], units=[],
                        on_pts=[], energy=[], neg=[], deaths=0, pts=0) for t in (0, 1)}

    def flush(match_idx, final_obs):
        wins = np.asarray(final_obs[our_side]["team_wins"])
        b = agent.belief
        known = b.point_tiles if not b.mirrored else geo.mirror_map(b.point_tiles)
        for t in (0, 1):
            a = acc[t]
            row = dict(seed=seed, side=our_side, match=match_idx, team=t, is_us=int(t == us),
                       point_counting_version=POINT_COUNTING_VERSION,
                       points=a["pts"], first_score_step=a["first"] if a["first"] is not None else -1,
                       occ_mean=np.mean(a["occ"]), occ_mean_late=np.mean(a["occ_late"] or [0]),
                       point_tiles_total=int(ptm.sum()), occ_own_half=np.mean(a["own"]),
                       occ_enemy_half=np.mean(a["enemy"]), contested_mean=np.mean(a["cont"]),
                       units_mean=np.mean(a["units"]), units_on_points_mean=np.mean(a["on_pts"]),
                       energy_mean=np.mean(a["energy"]), neg_energy_units_mean=np.mean(a["neg"]),
                       deaths=a["deaths"])
            if t == us:
                row["belief_known"] = int(known.sum())
                row["belief_correct"] = int((known & ptm).sum())
            rows.append(row)
        # Matchsieger ueber Delta der team_wins
        return wins

    wins_before = np.zeros(2, dtype=int)
    match_idx = 0
    acc = new_acc()
    ptm = np.zeros((W, H), bool)
    while not done:
        actions = {our_side: agent.act(step=step, obs=obs[our_side]),
                   opp_side: opp.act(step=step, obs=obs[opp_side])}
        previous = obs[our_side]
        obs, reward, term, trunc, info = env.step(actions)
        done = bool(np.asarray(term[our_side])) or bool(np.asarray(trunc[our_side]))
        step += 1
        st = env.state
        ms = int(np.asarray(obs[our_side]["match_steps"]))
        tp = match_points_after_step(previous, obs[our_side], info)
        for t in (0, 1):
            acc[t]["pts"] = int(tp[t])
            if acc[t]["first"] is None and tp[t] > 0:
                acc[t]["first"] = int(np.asarray(previous["match_steps"])) + 1
        if ms == 0 or done:   # Match zu Ende; Endpunkte vor dem Reset rekonstruiert
            wins = flush(match_idx, obs)
            for r in rows[-2:]:
                r["won_match"] = int(wins[r["team"]] > wins_before[r["team"]])
            wins_before = wins.copy()
            match_idx += 1
            acc = new_acc()
            prev_alive = None
            continue
        ptm = point_tile_map(st)
        mask = np.asarray(st.units_mask, bool)
        pos = np.asarray(st.units.position)
        ene = np.asarray(st.units.energy)[..., 0]
        occ_maps = []
        for t in (0, 1):
            ok = mask[t] & (ene[t] >= 0)
            m = np.zeros((W, H), bool)
            m[pos[t][ok, 0], pos[t][ok, 1]] = True
            occ_maps.append(m & ptm)
        for t in (0, 1):
            a = acc[t]
            o = occ_maps[t]
            a["occ"].append(int(o.sum()))
            if ms >= 50:
                a["occ_late"].append(int(o.sum()))
            a["own"].append(int((o & own_half[t]).sum()))
            a["enemy"].append(int((o & own_half[1 - t]).sum()))
            a["cont"].append(int((o & occ_maps[1 - t]).sum()))
            alive = mask[t]
            a["units"].append(int(alive.sum()))
            on = ptm[pos[t][alive, 0], pos[t][alive, 1]] if alive.any() else np.array([])
            a["on_pts"].append(int(on.sum()))
            a["energy"].append(float(ene[t][alive].mean()) if alive.any() else 0.0)
            a["neg"].append(int((ene[t][alive] < 0).sum()))
            if prev_alive is not None:
                a["deaths"] += int((prev_alive[t] & ~alive).sum())
        prev_alive = mask.copy()
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--opponent", default="solution92")
    ap.add_argument("--first", type=int, default=0)
    ap.add_argument("--n-seeds", type=int, default=10)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent

    env = LuxAIS3GymEnv(numpy_output=True)
    agent = Agent_x("player_0", agent_path=args.weights, train=False)
    agent.set_to_eval_mode()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for seed in P.val_seeds(args.first + args.n_seeds)[args.first:]:
            for side in P.SIDES:
                opp = make_opponent(args.opponent, "player_1" if side == "player_0" else "player_0")
                for r in play_and_measure(env, agent, opp, seed, side):
                    w.writerow(r)
            fh.flush()
    env.close()


if __name__ == "__main__":
    main()
