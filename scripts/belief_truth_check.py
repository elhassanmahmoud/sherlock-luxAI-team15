"""Gedaechtnis gegen die Wahrheit pruefen (29.10.2026): falsche Punkte-/Null-Tiles je Schritt.

    python -m scripts.belief_truth_check --first 300000 --n 20 --opponents solution92,sol92_sq \
        --set opp_point_infer=true --out experiments/analysis/battle/truth_opi.json

Spielt mit den V10-Gewichten (nur lesen) und vergleicht nach jedem Schritt das kanonische Gedaechtnis
mit env.state: Punkte-Tiles, die keine sind (muss 0 bleiben), Null-Tiles, die Punkte bringen (muss 0
bleiben), Anteil bekannter wahrer Punkte-Tiles. Prueft ausserdem die Annahme von opp_point_infer:
jeder lebende Gegner auf einem Tile unserer Sensormaske erscheint in der Beobachtung.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import random
from pathlib import Path

import numpy as np

from scripts import protocol as P
from scripts.experiment import limit_threads

V10 = "experiments/releases/20261022_v10_baseline/agent_p0.pth"


def check_game(agent, env, opp, seed: int, side: str) -> dict:
    from agents.sherlock import geometry as geo
    from scripts.oracle_probe import truth_maps
    opp_side = "player_1" if side == "player_0" else "player_0"
    us, them = (0, 1) if side == "player_0" else (1, 0)
    agent.new_game(side)
    if hasattr(opp, "new_game"):
        opp.new_game(opp_side)
    random.seed(seed)
    np.random.seed(seed % (2 ** 32))
    obs, info = env.reset(seed=seed)
    for a in (agent, opp):
        if hasattr(a, "set_env_cfg"):
            a.set_env_cfg(info["params"])
    r = dict(seed=seed, side=side, steps=0, false_point_steps=0, false_dead_steps=0, hidden_visible_enemy=0,
             known_sum=0.0, known_n=0, opp_records=0)
    step, done = 0, False
    while not done:
        st = env.state
        if int(np.asarray(obs[side]["match_steps"])) > 0:
            # Annahme: Gegner auf sichtbarem Tile ist in der Beobachtung
            sens = np.asarray(obs[side]["sensor_mask"], bool)
            omask = np.asarray(obs[side]["units_mask"], bool)[them]
            tmask = np.asarray(st.units_mask, bool)[them]
            tpos = np.asarray(st.units.position)[them]
            tene = np.asarray(st.units.energy)[them][..., 0] if np.asarray(st.units.energy).ndim == 3 else np.asarray(st.units.energy)[them]
            for u in np.nonzero(tmask)[0]:
                x, y = int(tpos[u][0]), int(tpos[u][1])
                if sens[x, y] and not omask[u] and tene[u] >= 0:
                    r["hidden_visible_enemy"] += 1
        act = {side: agent.act(step=step, obs=obs[side]), opp_side: opp.act(step=step, obs=obs[opp_side])}
        b = agent.belief
        if int(np.asarray(obs[side]["match_steps"])) > 0:
            pts, _ = truth_maps(env.state)
            known = geo.mirror_map(b.point_tiles) if b.mirrored else b.point_tiles
            dead = geo.mirror_map(b.dead_tiles) if b.mirrored else b.dead_tiles
            r["steps"] += 1
            r["false_point_steps"] += int((known & ~pts).any())
            r["false_dead_steps"] += int((dead & pts).any())
            if pts.any():
                r["known_sum"] += float((known & pts).sum()) / float(pts.sum())
                r["known_n"] += 1
        obs, _, term, trunc, _ = env.step(act)
        done = bool(np.asarray(term[side])) or bool(np.asarray(trunc[side]))
        step += 1
    r["opp_records"] = int(getattr(agent.belief, "opp_point_records", 0))
    r["known_frac"] = r["known_sum"] / max(r["known_n"], 1)
    return r


def _worker(job):
    overrides, games = job
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock.main import Agent_x
    from scripts.par_eval import build_cfg
    from scripts.par_losses import opponent_for

    env = LuxAIS3GymEnv(numpy_output=True)
    agent = Agent_x("player_0", agent_path=V10, cfg=build_cfg(V10, overrides), train=False, seed=0)
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    out = []
    for seed, side, opponent in games:
        opp = opponent_for(opponent, "player_1" if side == "player_0" else "player_0")
        out.append({**check_game(agent, env, opp, seed, side), "opponent": opponent})
    env.close()
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("--first", type=int, required=True)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--opponents", default="solution92,sol92_sq")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    games = [(P.VAL_SEED_BASE + i, side, o) for o in args.opponents.split(",")
             for i in range(args.first, args.first + args.n) for side in P.SIDES]
    jobs = [(args.set, games[i::args.workers]) for i in range(args.workers)]
    with mp.get_context("spawn").Pool(len(jobs)) as pool:
        rows = [r for rs in pool.map(_worker, jobs) for r in rs]
    tot = {k: sum(r[k] for r in rows) for k in ("steps", "false_point_steps", "false_dead_steps",
                                                 "hidden_visible_enemy", "opp_records")}
    tot["known_frac_mean"] = float(np.mean([r["known_frac"] for r in rows]))
    tot["games"] = len(rows)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(dict(summary=tot, games=rows, overrides=args.set), indent=1))
    print(json.dumps(tot))


if __name__ == "__main__":
    main()
