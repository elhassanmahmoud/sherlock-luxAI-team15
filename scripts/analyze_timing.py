"""Wo geht in einem Match die Zeit bis zum ersten Punkt verloren?

    python -m scripts.analyze_timing --weights agents/sherlock/weights/agent_p0.pth \
        --opponent solution92 --first 0 --n-seeds 10 --out experiments/analysis/timing_0.csv

Eine Zeile pro (Spiel, Match). Gemessen mit env.state (Ground Truth):
  spawn_step       match_step, an dem in diesem Match ein Relic-Paar erscheint (-1: keins)
  active_relics    Anzahl aktiver Relics bei Matchende
  seen_step        erster match_step, an dem unser Belief ein AKTIVES Relic kennt
  opp_seen_step    erster match_step, an dem ein aktives Relic im Sensorbereich des Gegners liegt
  first_score      erster match_step mit eigenem Punkt (101: nie), opp_first_score ebenso
  proven_50/75/100 bewiesene Punkte-Tiles (Belief) zu diesen match_steps, true_tiles = echte
  near_relic_50    eigene Units im 5x5-Umfeld aktiver Relics bei match_step 50 (Gegner: opp_near_50)
Nur Validierungs-Seeds (500 000+).
"""
from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

import numpy as np

from scripts import protocol as P
from scripts.analyze_losses import point_tile_map
from scripts.experiment import limit_threads

FIELDS = ["seed", "side", "match", "won_match", "spawn_step", "active_relics", "seen_step",
          "opp_seen_step", "first_score", "opp_first_score", "points", "opp_points",
          "proven_50", "proven_75", "proven_100", "true_tiles", "near_relic_50", "opp_near_50"]


def zone_map(st, W: int = 24, H: int = 24) -> np.ndarray:
    """5x5-Umfeld aller aktiven Relics."""
    z = np.zeros((W, H), bool)
    pos = np.asarray(st.relic_nodes)
    for i in np.nonzero(np.asarray(st.relic_nodes_mask))[0]:
        x, y = int(pos[i][0]), int(pos[i][1])
        z[max(0, x - 2):x + 3, max(0, y - 2):y + 3] = True
    return z


def play_and_time(env, agent, opp, seed: int, our_side: str) -> list[dict]:
    from agents.sherlock import geometry as geo

    opp_side = "player_1" if our_side == "player_0" else "player_0"
    us, them = (0, 1) if our_side == "player_0" else (1, 0)
    agent.new_game(our_side)
    if hasattr(opp, "new_game"):
        opp.new_game(opp_side)
    random.seed(seed)
    np.random.seed(seed % (2**32))
    obs, info = env.reset(seed=seed)
    for a in (agent, opp):
        if hasattr(a, "set_env_cfg"):
            a.set_env_cfg(info["params"])

    rows: list[dict] = []
    wins_before = np.zeros(2, dtype=int)
    match_idx, step, done = 0, 0, False

    def new_row() -> dict:
        sched = np.asarray(env.state.relic_spawn_schedule)
        lo = match_idx * 101
        spawn = [int(s) - lo for s in sched if lo <= s < lo + 101]
        return dict(seed=seed, side=our_side, match=match_idx, spawn_step=min(spawn) if spawn else -1,
                    seen_step=101, opp_seen_step=101, first_score=101, opp_first_score=101,
                    proven_50=0, proven_75=0, proven_100=0, near_relic_50=0, opp_near_50=0)

    row = new_row()
    while not done:
        actions = {our_side: agent.act(step=step, obs=obs[our_side]),
                   opp_side: opp.act(step=step, obs=obs[opp_side])}
        obs, reward, term, trunc, info = env.step(actions)
        done = bool(np.asarray(term[our_side])) or bool(np.asarray(trunc[our_side]))
        step += 1
        st = env.state
        ms = int(np.asarray(obs[our_side]["match_steps"]))
        if ms == 0 or done:
            wins = np.asarray(obs[our_side]["team_wins"])
            row["won_match"] = int(wins[us] > wins_before[us])
            row["proven_100"] = int(agent.belief.point_tiles.sum())
            wins_before = wins.copy()
            rows.append(row)
            match_idx += 1
            if not done:
                row = new_row()
            continue

        ptm = point_tile_map(st)
        zone = zone_map(st)
        tp = np.asarray(st.team_points)
        relic_pos = np.asarray(st.relic_nodes)
        active = np.nonzero(np.asarray(st.relic_nodes_mask))[0]
        row["active_relics"] = len(active)
        row["true_tiles"] = int(ptm.sum())
        row["points"], row["opp_points"] = int(tp[us]), int(tp[them])
        if row["first_score"] == 101 and tp[us] > 0:
            row["first_score"] = ms
        if row["opp_first_score"] == 101 and tp[them] > 0:
            row["opp_first_score"] = ms

        if row["seen_step"] == 101 and len(active):
            known = agent.belief.relic_positions
            for i in active:
                x, y = int(relic_pos[i][0]), int(relic_pos[i][1])
                if agent.belief.mirrored:
                    x, y = geo.mirror_positions(np.array([[x, y]]), 24, 24)[0]
                if (int(x), int(y)) in known:
                    row["seen_step"] = ms
                    break
        if row["opp_seen_step"] == 101 and len(active):
            sens = np.asarray(st.sensor_mask)[them] if np.asarray(st.sensor_mask).ndim == 3 else None
            if sens is not None and any(sens[int(relic_pos[i][0]), int(relic_pos[i][1])] for i in active):
                row["opp_seen_step"] = ms

        if ms in (50, 75):
            row[f"proven_{ms}"] = int(agent.belief.point_tiles.sum())
        if ms == 50:
            mask = np.asarray(st.units_mask, bool)
            pos = np.asarray(st.units.position)
            for t, key in ((us, "near_relic_50"), (them, "opp_near_50")):
                p = pos[t][mask[t]]
                row[key] = int(zone[p[:, 0], p[:, 1]].sum()) if len(p) else 0
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
                for r in play_and_time(env, agent, opp, seed, side):
                    w.writerow({k: r.get(k) for k in FIELDS})
            fh.flush()
    env.close()


if __name__ == "__main__":
    main()
