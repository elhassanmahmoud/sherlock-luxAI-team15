"""Training des team_lux-Agenten.

    python -m scripts.train --games 400 --opponent default
    python -m scripts.train --games 300 --opponent solution92 --resume
    python -m scripts.train --games 300 --opponent self --self-update 25

Der Agent wird EINMAL erzeugt (Netz, Replay Buffer, Epsilon, Optimizer bleiben
ueber alle Spiele erhalten) und nach jedem Spiel gespeichert. Gegen beide Seiten
wird abwechselnd gespielt; dank kanonischer Features (geometry.py) fliesst die
Erfahrung beider Seiten in EIN Netz.
"""
from __future__ import annotations

import argparse
import csv
import shutil
import time
from datetime import datetime
from pathlib import Path

import numpy as np

from scripts.common import ROOT, OPPONENTS, make_opponent, play_game
from scripts.protocol import VAL_SEED_BASE

WEIGHTS = ROOT / "agents" / "team_lux" / "weights"
LOGS = ROOT / "logs"

LOG_FIELDS = [
    "game", "seed", "side", "opponent", "result", "our_wins", "opp_wins",
    "our_points", "opp_points", "relics_found", "known_point_tiles",
    "epsilon", "mean_loss", "buffer", "env_steps", "learn_steps", "secs",
    "winrate_50",
]


def save_all(agent, tag: str = "") -> None:
    """Gewichte an alle von Paths.csv erwarteten Orte schreiben.

    Die Features sind seitenunabhaengig, deshalb ist P0 == P1.
    """
    WEIGHTS.mkdir(parents=True, exist_ok=True)
    main_path = WEIGHTS / "agent_p0.pth"
    agent.save_agent(str(main_path))
    shutil.copyfile(main_path, WEIGHTS / "agent_p1.pth")
    if tag:
        shutil.copyfile(main_path, WEIGHTS / f"agent_{tag}.pth")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=200)
    ap.add_argument("--opponent", choices=OPPONENTS, default="default")
    ap.add_argument("--seed", type=int, default=0, help="Basis-Seed")
    ap.add_argument("--resume", action="store_true", help="vorhandene Gewichte weitertrainieren")
    ap.add_argument("--save-every", type=int, default=10)
    ap.add_argument("--eval-every", type=int, default=0, help="0 = keine Zwischen-Evaluation")
    ap.add_argument("--eval-games", type=int, default=8)
    ap.add_argument("--eval-opponent", choices=OPPONENTS, default=None)
    ap.add_argument("--self-update", type=int, default=25,
                    help="bei --opponent self: Snapshot alle n Spiele erneuern")
    ap.add_argument("--tag", default="", help="Suffix fuer Logdatei")
    args = ap.parse_args()

    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.team_lux.config import AgentConfig
    from agents.team_lux.main import Agent_x

    cfg = AgentConfig()
    resume_path = str(WEIGHTS / "agent_p0.pth") if args.resume else None
    agent = Agent_x("player_0", agent_path=resume_path, cfg=cfg, train=True)
    agent.autosave_on_terminate = False  # wir speichern selbst, kontrolliert
    agent.set_to_train_mode()

    WEIGHTS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_{args.tag}" if args.tag else ""
    log_path = LOGS / f"train_{args.opponent}{suffix}_{stamp}.csv"
    snapshot = WEIGHTS / "agent_selfplay_snapshot.pth"
    if args.opponent == "self" or args.eval_opponent == "self":
        agent.save_agent(str(snapshot))

    print("=" * 72)
    print(f"Training: {args.games} Spiele gegen {args.opponent}")
    print(f"Konfiguration: {cfg.to_dict()}")
    print(f"Log: {log_path}")
    print("=" * 72)

    env = LuxAIS3GymEnv(numpy_output=True)
    results: list[float] = []
    best_eval = -1.0
    t_start = time.time()

    with open(log_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=LOG_FIELDS)
        writer.writeheader()
        try:
            for g in range(args.games):
                side = "player_0" if g % 2 == 0 else "player_1"
                seed = args.seed + g // 2  # jeder Seed einmal von jeder Seite
                opp = make_opponent(
                    args.opponent,
                    "player_1" if side == "player_0" else "player_0",
                    self_play_path=str(snapshot),
                )
                row = play_game(env, agent, opp, seed, side, train=True)
                results.append(row["result"])
                win50 = float(np.mean(results[-50:]))

                row.update(
                    game=g, opponent=args.opponent,
                    epsilon=round(agent.epsilon, 4),
                    mean_loss=round(agent.pop_mean_loss(), 5),
                    buffer=len(agent.buffer),
                    env_steps=agent.env_steps, learn_steps=agent.learn_steps,
                    winrate_50=round(win50, 4),
                )
                writer.writerow({k: row.get(k) for k in LOG_FIELDS})
                fh.flush()

                print(f"[{g+1}/{args.games}] seed={seed} {side} "
                      f"{row['our_wins']}-{row['opp_wins']} "
                      f"P {row['our_points']}:{row['opp_points']} | "
                      f"eps={agent.epsilon:.3f} loss={row['mean_loss']} "
                      f"buf={len(agent.buffer)} | WR50={win50:.2f} "
                      f"| relics={row['relics_found']} tiles={row['known_point_tiles']} "
                      f"| {row['secs']}s")

                if (g + 1) % args.save_every == 0 or g == args.games - 1:
                    save_all(agent)
                if args.opponent == "self" and (g + 1) % args.self_update == 0:
                    agent.save_agent(str(snapshot))
                    print(f"    -> Self-Play-Snapshot aktualisiert (Spiel {g+1})")

                if args.eval_every and (g + 1) % args.eval_every == 0:
                    from scripts.evaluate import evaluate
                    opp_eval = args.eval_opponent or args.opponent
                    res = evaluate(str(snapshot), opp_eval, args.eval_games,
                                   base_seed=VAL_SEED_BASE, verbose=False,
                                   env=env, agent=agent)
                    agent.set_to_train_mode()
                    print(f"    -> Eval gegen {opp_eval}: WR={res['winrate']:.3f} "
                          f"(Matches {res['match_winrate']:.3f}, "
                          f"Punkte {res['avg_points']:.0f}:{res['avg_opp_points']:.0f})")
                    if res["winrate"] > best_eval:
                        best_eval = res["winrate"]
                        save_all(agent, tag="best")
                        print(f"    -> neuer Bestwert, agent_best.pth gespeichert")
        except KeyboardInterrupt:
            print("\nAbbruch durch Nutzer - speichere aktuellen Stand ...")
        finally:
            save_all(agent)
            env.close()

    mins = (time.time() - t_start) / 60
    print("=" * 72)
    print(f"Fertig. {len(results)} Spiele in {mins:.1f} min")
    if results:
        print(f"Winrate gesamt: {np.mean(results):.3f} | letzte 50: {np.mean(results[-50:]):.3f}")
    print(f"Gewichte: {WEIGHTS/'agent_p0.pth'} (+ agent_p1.pth)")
    print(f"Log:      {log_path}")


if __name__ == "__main__":
    main()
