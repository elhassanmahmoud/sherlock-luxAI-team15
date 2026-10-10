"""Evaluation: N Seeds gegen einen festen Gegner, jeder Seed von BEIDEN Seiten.

    python -m scripts.evaluate --games 20 --opponent solution92
    python -m scripts.evaluate --games 20 --opponent default --weights agents/sherlock/weights/agent_best.pth
"""
from __future__ import annotations

import argparse

import numpy as np

from scripts.common import OPPONENTS, make_opponent, play_game
from scripts.protocol import VAL_SEED_BASE


def evaluate(weights: str, opponent: str, games: int = 20, base_seed: int = VAL_SEED_BASE,
             verbose: bool = True, env=None, agent=None) -> dict:
    """Spielt `games` Seeds x 2 Seiten ohne Exploration und ohne Lernen."""
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock.main import Agent_x

    own_env = env is None
    env = env or LuxAIS3GymEnv(numpy_output=True)
    own_agent = agent is None
    if agent is None:
        agent = Agent_x("player_0", agent_path=weights, train=False)
    prev_training = agent.training
    agent.set_to_eval_mode()

    rows = []
    try:
        for g in range(games):
            seed = base_seed + g
            for side in ("player_0", "player_1"):
                opp = make_opponent(opponent, "player_1" if side == "player_0" else "player_0",
                                    self_play_path=weights)
                if hasattr(opp, "set_to_eval_mode"):
                    opp.set_to_eval_mode()
                r = play_game(env, agent, opp, seed, side, train=False)
                rows.append(r)
                if verbose:
                    print(f"  seed {seed} as {side}: {r['our_wins']}-{r['opp_wins']} "
                          f"(Punkte {r['our_points']}:{r['opp_points']}, "
                          f"Punkte-Tiles {r['known_point_tiles']}, Relics {r['relics_found']})")
    finally:
        if own_env:
            env.close()
        if not own_agent and prev_training:
            agent.set_to_train_mode()

    res = dict(
        games=len(rows),
        winrate=float(np.mean([r["result"] for r in rows])),
        match_winrate=float(
            np.sum([r["our_wins"] for r in rows])
            / max(1, np.sum([r["our_wins"] + r["opp_wins"] for r in rows]))
        ),
        avg_points=float(np.mean([r["our_points"] for r in rows])),
        avg_opp_points=float(np.mean([r["opp_points"] for r in rows])),
        avg_point_tiles=float(np.mean([r["known_point_tiles"] for r in rows])),
        avg_relics=float(np.mean([r["relics_found"] for r in rows])),
    )
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=20, help="Anzahl Seeds (x2 Seiten)")
    ap.add_argument("--opponent", choices=OPPONENTS, default="default")
    ap.add_argument("--weights", default="agents/sherlock/weights/agent_p0.pth")
    ap.add_argument("--seed", type=int, default=VAL_SEED_BASE,
                    help="Default: Validierungs-Seeds (Test-Seeds nur fuer die finale Auswertung)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    res = evaluate(args.weights, args.opponent, args.games, args.seed, not args.quiet)
    print("\n=== Evaluation gegen", args.opponent, "===")
    print(f"Spiele:            {res['games']}")
    print(f"Winrate (Spiele):  {res['winrate']:.3f}")
    print(f"Winrate (Matches): {res['match_winrate']:.3f}")
    print(f"Punkte (wir/Gegner): {res['avg_points']:.1f} / {res['avg_opp_points']:.1f}")
    print(f"Gefundene Punkte-Tiles (Schnitt): {res['avg_point_tiles']:.1f}")
    print(f"Gefundene Relics (Schnitt):       {res['avg_relics']:.1f}")


if __name__ == "__main__":
    main()
