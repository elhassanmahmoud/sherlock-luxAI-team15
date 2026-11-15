"""Diagnose je Match (15.11.2026): Punkte, Sieger, Einheiten und Energie am Matchende, Verluste.

Spielt Sherlock (Abgabe-Gewichte, optional mit --set-Schaltern) gegen einen Gegner aus
scripts.common.make_opponent und schreibt eine Zeile pro Match. Nur Messung, kein Lernen.

    python -m scripts.match_trace --opponent kaggle3 --seeds 7150000:7150010 --out x.csv
"""
from __future__ import annotations

import argparse
import csv
import multiprocessing as mp
from pathlib import Path

import numpy as np

from scripts.scoring import match_points_after_step

WEIGHTS = "agents/sherlock/weights/agent_p0.pth"  # mit --weights ersetzbar (auch Imitation-Checkpoints)


def _energy(obs, team):
    m = np.asarray(obs["units_mask"])[team].astype(bool)
    e = np.asarray(obs["units"]["energy"])[team]
    return int(np.maximum(e[m], 0).sum())


def play(job):
    weights, overrides, opponent, seed, side = job
    from scripts.experiment import limit_threads
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent
    from scripts.par_eval import build_cfg

    env = LuxAIS3GymEnv(numpy_output=True)
    agent = Agent_x("player_0", agent_path=weights, cfg=build_cfg(weights, overrides), train=False, seed=0)
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    opp_side = "player_1" if side == "player_0" else "player_0"
    if hasattr(agent, "new_game"):
        agent.new_game(side)
    opp = make_opponent(opponent, opp_side)
    obs, info = env.reset(seed=seed)
    for a in (agent, opp):
        if hasattr(a, "set_env_cfg"):
            a.set_env_cfg(info["params"])
    team = 0 if side == "player_0" else 1
    rows, step, done = [], 0, False
    sides = {team: side, 1 - team: opp_side}

    def fresh():
        return dict(deaths=[0, 0], saps=[0, 0], first_point=[-1, -1], tiles_sum=[0, 0], spawned=[0, 0])

    acc = fresh()
    while not done:
        actions = {side: agent.act(step=step, obs=obs[side]), opp_side: opp.act(step=step, obs=obs[opp_side])}
        nxt, _, term, trunc, info = env.step(actions)
        done = bool(np.asarray(term[side])) or bool(np.asarray(trunc[side]))
        o_now, o_next = obs[side], nxt[side]
        ms_next = int(np.asarray(o_next["match_steps"]))
        ms_now = int(np.asarray(o_now["match_steps"]))
        reset = ms_next == 0 or done
        tp = match_points_after_step(o_now, o_next, info)
        start = ms_now == 0  # Reste des alten Matches verschwinden jetzt: keine Tode
        for t in (0, 1):
            own_now, own_next = obs[sides[t]], nxt[sides[t]]  # jedes Team sieht die eigenen Units immer
            a = np.asarray(actions[sides[t]])
            m_now = np.asarray(own_now["units_mask"])[t].astype(bool)
            acc["saps"][t] += int(((a[:, 0] == 5) & m_now).sum())
            if not reset and not start:
                m_next = np.asarray(own_next["units_mask"])[t].astype(bool)
                acc["deaths"][t] += int((m_now & ~m_next).sum())
                acc["spawned"][t] += int((~m_now & m_next).sum())
            gain = int(tp[t]) - int(np.asarray(own_now["team_points"])[t])
            acc["tiles_sum"][t] += max(gain, 0)
            if gain > 0 and acc["first_point"][t] < 0:
                acc["first_point"][t] = ms_now + 1
        if reset:  # Match zu Ende (Reset) oder Spielende
            wins_before = np.asarray(o_now["team_wins"]).astype(int)
            wins_after = np.asarray(o_next["team_wins"]).astype(int)
            winner = int(np.argmax(wins_after - wins_before)) if (wins_after - wins_before).sum() else -1
            alive = [int(np.asarray(obs[sides[t]]["units_mask"])[t].sum()) for t in (0, 1)]
            rows.append(dict(
                seed=seed, side=side, match=int(wins_before.sum()) + 1,
                our_points=int(tp[team]), opp_points=int(tp[1 - team]), we_won=int(winner == team),
                our_first_point=acc["first_point"][team], opp_first_point=acc["first_point"][1 - team],
                our_deaths=acc["deaths"][team], opp_deaths=acc["deaths"][1 - team],
                our_saps=acc["saps"][team], opp_saps=acc["saps"][1 - team],
                our_alive_end=alive[team], opp_alive_end=alive[1 - team],
                our_energy_end=_energy(obs[sides[team]], team), opp_energy_end=_energy(obs[sides[1 - team]], 1 - team),
            ))
            acc = fresh()
        obs = nxt
        step += 1
    env.close()
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--opponent", default="kaggle3")
    ap.add_argument("--seeds", required=True, help="first:end")
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--weights", default=WEIGHTS)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    lo, hi = (int(x) for x in a.seeds.split(":"))
    jobs = [(a.weights, a.set, a.opponent, s, side) for s in range(lo, hi) for side in ("player_0", "player_1")]
    with mp.get_context("spawn").Pool(min(a.workers, len(jobs))) as pool:
        rows = [r for part in pool.map(play, jobs) for r in part]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    def fp(rs, k):
        v = [r[k] for r in rs if r[k] >= 0]
        return f"{np.median(v):.0f}" if v else "-"

    for m in (1, 2, 3):
        rs = [r for r in rows if r["match"] == m]
        if not rs:
            continue
        mean = lambda k: np.mean([r[k] for r in rs])
        print(f"Match {m}: gewonnen {sum(r['we_won'] for r in rs)}/{len(rs)} | Punkte {mean('our_points'):.0f}:"
              f"{mean('opp_points'):.0f} | erster Punkt (Median-Schritt) {fp(rs, 'our_first_point')}:"
              f"{fp(rs, 'opp_first_point')} | verlorene Units {mean('our_deaths'):.1f}:{mean('opp_deaths'):.1f} | "
              f"Schuesse {mean('our_saps'):.1f}:{mean('opp_saps'):.1f} | lebend am Ende {mean('our_alive_end'):.1f}:"
              f"{mean('opp_alive_end'):.1f} | Energie am Ende {mean('our_energy_end'):.0f}:{mean('opp_energy_end'):.0f}")


if __name__ == "__main__":
    main()
