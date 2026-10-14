"""Training des Sherlock-Agenten.

    python -m scripts.train --games 400 --opponent default
    python -m scripts.train --games 300 --opponent solution92 \
        --resume experiments/runs/<lauf>/weights/agent_p0.pth
    python -m scripts.train --games 300 --opponent self --self-update 25

Der Agent wird EINMAL erzeugt (Netz, Replay Buffer, Epsilon, Optimizer bleiben
ueber alle Spiele erhalten) und nach jedem Spiel gespeichert. Gegen beide Seiten
wird abwechselnd gespielt; dank kanonischer Features (geometry.py) fliesst die
Erfahrung beider Seiten in EIN Netz. Jeder Aufruf schreibt in einen NEUEN
Run-Ordner. --resume liest einen Einzelnetz-Checkpoint; die Quelle und die
Abgabe-Gewichte bleiben unveraendert. Ensembles sind hier nur zum Spielen.
"""
from __future__ import annotations

import argparse
import csv
import re
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path

import numpy as np

from scripts.common import ROOT, OPPONENTS, make_opponent, play_game
from scripts.protocol import VAL_SEED_BASE
from scripts.output_paths import checked_output

WEIGHTS = ROOT / "agents" / "sherlock" / "weights"

LOG_FIELDS = [
    "game", "seed", "side", "opponent", "result", "our_wins", "opp_wins",
    "our_points", "opp_points", "point_counting_version", "relics_found", "known_point_tiles",
    "epsilon", "mean_loss", "buffer", "env_steps", "learn_steps", "secs",
    "winrate_50",
]


def create_run_dir(output_dir: str | None) -> Path:
    """Reserve a fresh output directory, never reuse an existing run."""
    if output_dir is not None:
        run_dir = checked_output(Path(output_dir), WEIGHTS)
        run_dir.mkdir(parents=True, exist_ok=False)
    else:
        base = checked_output(ROOT / "experiments" / "runs", WEIGHTS)
        base.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path(tempfile.mkdtemp(prefix=f"train_{stamp}_", dir=base))
    return run_dir


def save_all(agent, weights_dir: Path, tag: str = "") -> None:
    """Gewichte ausschliesslich in den neuen Trainingslauf schreiben.

    Die Features sind seitenunabhaengig, deshalb ist P0 == P1.
    """
    weights_dir = checked_output(weights_dir, WEIGHTS)
    names = ["agent_p0.pth", "agent_p1.pth"]
    if tag:
        names.append(f"agent_{tag}.pth")
    # Validate all targets before the first write (also on final/interrupt saves).
    paths = [checked_output(weights_dir / name, WEIGHTS) for name in names]
    weights_dir.mkdir(parents=True, exist_ok=True)
    main_path = paths[0]
    agent.save_agent(str(main_path))
    for path in paths[1:]:
        shutil.copyfile(main_path, path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=200)
    ap.add_argument("--opponent", choices=OPPONENTS, default="default")
    ap.add_argument("--seed", type=int, default=0, help="Basis-Seed")
    ap.add_argument("--resume", metavar="CHECKPOINT", help="Einzelnetz-Checkpoint nur lesen; neuer Lauf als Ausgabe")
    ap.add_argument("--output-dir", help="Neuer, noch nicht existierender Run-Ordner (Default: experiments/runs/train_...)")
    ap.add_argument("--save-every", type=int, default=10)
    ap.add_argument("--eval-every", type=int, default=0, help="0 = keine Zwischen-Evaluation")
    ap.add_argument("--eval-games", type=int, default=8)
    ap.add_argument("--eval-opponent", choices=OPPONENTS, default=None)
    ap.add_argument("--self-update", type=int, default=25,
                    help="bei --opponent self: Snapshot alle n Spiele erneuern")
    ap.add_argument("--tag", default="", help="Suffix fuer Logdatei")
    args = ap.parse_args()
    if args.games < 0 or args.save_every < 1 or args.self_update < 1 or args.eval_every < 0 or args.eval_games < 1:
        ap.error("Spiele/Eval-Intervall muessen >= 0 sein; Speicherintervall, Self-Update und Eval-Spiele >= 1.")
    if args.tag and not re.fullmatch(r"[A-Za-z0-9_-]+", args.tag):
        ap.error("--tag darf nur Buchstaben, Ziffern, _ und - enthalten.")
    if args.output_dir:
        try:
            output = checked_output(Path(args.output_dir), WEIGHTS)
            if output.exists():
                ap.error(f"Ausgabeordner existiert bereits; neuen Namen waehlen: {output}")
        except (ValueError, OSError) as exc:
            ap.error(str(exc))
    resume_path = Path(args.resume).expanduser().resolve() if args.resume else None
    if resume_path is not None and not resume_path.is_file():
        ap.error(f"Checkpoint fehlt: {resume_path}")

    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock.config import AgentConfig
    from agents.sherlock.main import Agent_x, FEATURE_DIM, N_ACTIONS

    cfg = AgentConfig()
    if resume_path:
        import torch

        checkpoint = torch.load(resume_path, map_location="cpu", weights_only=False)
        if not isinstance(checkpoint, dict) or "q" not in checkpoint or not isinstance(checkpoint.get("cfg"), dict):
            ap.error("--resume braucht einen Sherlock-Checkpoint mit gespeicherter Config und Q-Netz.")
        if checkpoint.get("ensemble"):
            ap.error("--resume erwartet ein Einzelnetz, kein Ensemble. Mitglieder separat trainieren und danach neu zusammenbauen.")
        cfg = AgentConfig.from_dict(checkpoint["cfg"])
        if (checkpoint.get("feature_dim") != FEATURE_DIM
                or checkpoint.get("n_actions") != (N_ACTIONS if cfg.use_sap else 5)):
            ap.error("Checkpoint passt nicht zur aktuellen Architektur (feature_dim/n_actions).")

    agent = Agent_x("player_0", agent_path=str(resume_path) if resume_path else None,
                    cfg=cfg, train=True)
    agent.autosave_on_terminate = False  # wir speichern selbst, kontrolliert
    agent.set_to_train_mode()

    try:
        run_dir = create_run_dir(args.output_dir)
    except (ValueError, OSError) as exc:
        ap.error(str(exc))
    weights_dir = run_dir / "weights"
    weights_dir.mkdir()
    agent.agent_path = str(weights_dir / "agent_p0.pth")
    suffix = f"_{args.tag}" if args.tag else ""
    log_path = run_dir / f"train{suffix}.csv"
    snapshot = weights_dir / "agent_selfplay_snapshot.pth"
    if args.opponent == "self" or args.eval_opponent == "self":
        agent.save_agent(str(checked_output(snapshot, WEIGHTS)))

    print("=" * 72)
    print(f"Training: {args.games} Spiele gegen {args.opponent}")
    print(f"Konfiguration: {cfg.to_dict()}")
    print(f"Ausgabe: {run_dir} (Abgabe-Gewichte bleiben unveraendert)")
    if resume_path:
        print(f"Start-Checkpoint (nur lesen): {resume_path}")
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
                    save_all(agent, weights_dir)
                if args.opponent == "self" and (g + 1) % args.self_update == 0:
                    agent.save_agent(str(checked_output(snapshot, WEIGHTS)))
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
                        save_all(agent, weights_dir, tag="best")
                        print(f"    -> neuer Bestwert, agent_best.pth gespeichert")
        except KeyboardInterrupt:
            print("\nAbbruch durch Nutzer - speichere aktuellen Stand ...")
        finally:
            try:
                save_all(agent, weights_dir)
            finally:
                env.close()

    mins = (time.time() - t_start) / 60
    print("=" * 72)
    print(f"Fertig. {len(results)} Spiele in {mins:.1f} min")
    if results:
        print(f"Winrate gesamt: {np.mean(results):.3f} | letzte 50: {np.mean(results[-50:]):.3f}")
    print(f"Gewichte: {weights_dir/'agent_p0.pth'} (+ agent_p1.pth)")
    print(f"Log:      {log_path}")


if __name__ == "__main__":
    main()
