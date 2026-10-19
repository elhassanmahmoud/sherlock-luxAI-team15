"""Diagnose: Sherlock-Leitplanken ohne Netz (reine Regel) vs. old3_sym3 mit Netz.

Gleicher Belief, gleiche Zielzuweisung, gleiche Maske, gleiches Sap-Ziel.
Nur die Aktionswahl unterscheidet sich:
  net   : argmax gemittelte Q-Werte der 6 Netze (Abgabe-Agent)
  rules : Sap, wenn Gegner im Ziel und Unit am Ziel; sonst Schritt Richtung Ziel; am Ziel stehen
Aufruf aus dem Projektordner:
  .venv/bin/python <dieses_skript> --mode rules --first 660 --n 15 --out x.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path("/Users/elhassanmahmoud/Documents/AKI_LuxAgent15")
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from agents.sherlock import geometry as geo  # noqa: E402
from agents.sherlock.main import Agent_x  # noqa: E402
from scripts import protocol as P  # noqa: E402
from scripts.experiment import GAME_FIELDS, limit_threads  # noqa: E402


class RulesOnly(Agent_x):
    def _rule_move(self, ctx, uid, mask, tgt):
        a = self._step_toward(ctx, uid, mask, tgt)
        if a is not None:
            return a
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        d0 = abs(tgt[0] - x) + abs(tgt[1] - y)
        moves = [d for d in range(1, 5) if mask[d]]
        better = [d for d in moves
                  if abs(tgt[0] - x - geo.DIR_DX[d]) + abs(tgt[1] - y - geo.DIR_DY[d]) < d0]
        if better:
            return int(better[0])
        return int(self.rng.choice(moves)) if moves else geo.STAY

    def act(self, step, obs):
        self.belief.observe(obs)
        max_units = int((self.env_cfg or {}).get("max_units", 16))
        actions = np.zeros((max_units, 3), dtype=int)
        if int(np.asarray(obs["match_steps"])) == 0:
            return actions
        ctx, ids, _feats, masks, saps = self._decide(obs)
        for uid in ids:
            m = masks[uid]
            tgt = ctx["assigned"].get(int(uid))
            x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
            at_tgt = tgt is not None and (x, y) == tuple(tgt)
            sap = saps[uid]
            if self.n_actions > 5 and m[geo.SAP] and sap is not None and sap[2] > 0 \
                    and (at_tgt or tgt is None):
                dx, dy, _ = sap
                if self.belief.mirrored:
                    dx, dy = geo.mirror_delta(dx, dy)
                actions[uid] = [geo.SAP, dx, dy]
                continue
            d = self._rule_move(ctx, uid, m, tgt) if (tgt is not None and not at_tgt) else geo.STAY
            if self.belief.mirrored:
                d = geo.mirror_dir(d)
            actions[uid] = [d, 0, 0]
        return actions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["net", "rules"], required=True)
    ap.add_argument("--weights", default=str(ROOT / "experiments/ensembles/old3_sym3.pth"))
    ap.add_argument("--first", type=int, required=True)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.common import make_opponent, play_game

    env = LuxAIS3GymEnv(numpy_output=True)
    cls = RulesOnly if args.mode == "rules" else Agent_x
    agent = cls("player_0", agent_path=args.weights, train=False, seed=0)
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    seeds = [P.VAL_SEED_BASE + i for i in range(args.first, args.first + args.n)]
    with open(args.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=GAME_FIELDS)
        w.writeheader()
        for opp_name in P.EVAL_OPPONENTS:
            for seed in seeds:
                for side in P.SIDES:
                    opp = make_opponent(opp_name, "player_1" if side == "player_0" else "player_0")
                    r = play_game(env, agent, opp, seed, side, train=False)
                    r["opponent"] = opp_name
                    w.writerow({k: r.get(k) for k in GAME_FIELDS})
                fh.flush()
    env.close()


if __name__ == "__main__":
    main()
