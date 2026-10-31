"""Offline-Probe (31.10.2026): Wie viel Energie verfaellt am Matchende, und wie oft haette V12 in den letzten
Schritten auf einen sichtbaren Gegner schiessen koennen? Reines Zuschauen, keine Aktion wird veraendert.

    cd REPO && .venv/bin/python experiments/analysis/battle/v12_end_probe.py OPP SEED_FROM N WORKERS OUT.csv
    31.10.: OPP self:experiments/ensembles/league_nets6.pth bzw. solution92, SEED_FROM 800000, N 30, WORKERS 3
"""
import csv
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, ".")
LAST = 10  # letzte Schritte eines Matches (match_step 90..99)


def play(job):
    seed, side, opp_name = job
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent, play_game
    from scripts.experiment import limit_threads
    limit_threads()
    agent = Agent_x("player_0", agent_path="experiments/ensembles/battle_v12.pth", train=False)
    agent.set_to_eval_mode()
    opp_side = "player_1" if side == "player_0" else "player_0"
    if opp_name.startswith("self:"):
        opp = make_opponent("self", opp_side, self_play_path=opp_name[5:])
        opp.set_to_eval_mode()
    else:
        opp = make_opponent(opp_name, opp_side)
    rows = []
    prev_enemy = {}
    orig = agent.act

    def act(step, obs):
        actions = orig(step, obs)
        ms = int(np.asarray(obs["match_steps"]))
        team = agent.team_id
        cfg = agent.env_cfg
        cost, rng = int(cfg["unit_sap_cost"]), int(cfg["unit_sap_range"])
        pos = np.asarray(obs["units"]["position"])
        ene = np.asarray(obs["units"]["energy"])
        mask = np.asarray(obs["units_mask"])
        ours = [(u, pos[team][u], int(ene[team][u])) for u in range(pos.shape[1]) if mask[team][u]]
        enemies = [(u, pos[1 - team][u], int(ene[1 - team][u])) for u in range(pos.shape[1]) if mask[1 - team][u]]
        still = {u for u, p, e in enemies if prev_enemy.get(u) == (int(p[0]), int(p[1]))}
        prev_enemy.clear()
        prev_enemy.update({u: (int(p[0]), int(p[1])) for u, p, e in enemies})
        if ms >= 100 - LAST and ms <= 99 and ms > 0:
            for u, p, e in ours:
                inr = [(v, q, f) for v, q, f in enemies if max(abs(int(q[0]) - int(p[0])), abs(int(q[1]) - int(p[1]))) <= rng]
                rows.append(dict(seed=seed, side=side, opp=opp_name, match=int(np.asarray(obs["team_wins"]).sum()),
                                 ms=ms, uid=u, energy=e, cost=cost, can=int(e >= cost),
                                 vis_in_range=len(inr), still_in_range=sum(1 for v, q, f in inr if v in still),
                                 sapped=int(actions[u][0] == 5)))
        return actions

    agent.act = act
    env = LuxAIS3GymEnv(numpy_output=True)
    res = play_game(env, agent, opp, seed, side, train=False)
    for r in rows:
        r["game_result"] = res.get("result")
    return rows


def main():
    opp, first, n, workers, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    jobs = [(s, side, opp) for s in range(first, first + n) for side in ("player_0", "player_1")]
    with Pool(workers) as pool:
        rows = [r for rs in pool.imap_unordered(play, jobs) for r in rs]
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(jobs)} Spiele, {len(rows)} Unit-Schritte in den letzten {LAST} Schritten -> {out}")


if __name__ == "__main__":
    main()
