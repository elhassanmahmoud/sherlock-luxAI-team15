"""Ein Experiment-Lauf: Variante x Trainingsstart -> Training, Lernkurve, Test.

    python -m scripts.experiment --variant full --run-seed 0 --games 1200
    python -m scripts.experiment --variant baseline_prof            # nur Test
    python -m scripts.experiment --variant full --games 20 --test-seeds 2 --tag probe

Ergebnis in experiments/runs/<datum>_<variante>_s<seed>[_<tag>]/:
  train.csv      ein Eintrag pro Trainingsspiel (Ergebnis, Loss, Epsilon, Kennzahlen)
  val.csv        Lernkurve: eps=0-Winrate auf den Validierungs-Seeds
  eval.csv       finale Auswertung auf den Test-Seeds (beide Seiten, beide Gegner)
  manifest.json  Config, Seeds, Git-Commit, Laufzeit, Versionen
  weights/       Checkpoints (.pth, gitignored)

Protokoll (Seeds, Curriculum, Gegner): scripts/protocol.py und
docs/EXPERIMENT_PROTOKOLL.md.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

from scripts import protocol as P
from scripts.common import ROOT, make_opponent, play_game
from scripts.variants import (VARIANTS, is_trainable, make_learner, seed_everything,
                              separate_sides, variant_cfg)

RUNS = ROOT / "experiments" / "runs"

GAME_FIELDS = [
    "seed", "side", "opponent", "result", "game_win", "point_win", "our_wins", "opp_wins",
    "our_points", "opp_points", "point_counting_version", "wait_frac", "invalid_frac", "greedy_masked_frac",
    "sap_attempts", "sap_hits", "stack_frac", "relics_found", "relics_seen",
    "known_point_tiles", "belief_contradictions", "unit_steps", "steps", "secs",
]
TRAIN_FIELDS = ["game"] + GAME_FIELDS + ["epsilon", "mean_loss", "env_steps", "learn_steps",
                                         "winrate_50"]
VAL_FIELDS = ["after_games", "opponent", "games", "winrate", "match_winrate",
              "point_winrate", "avg_points", "avg_opp_points", "point_counting_version", "secs"]


def git_info() -> dict:
    def run(*cmd):
        try:
            return subprocess.check_output(cmd, cwd=ROOT, text=True,
                                           stderr=subprocess.DEVNULL).strip()
        except Exception:
            return ""
    return {"commit": run("git", "rev-parse", "HEAD"),
            "dirty": bool(run("git", "status", "--porcelain", "--untracked-files=no"))}


def limit_threads() -> None:
    """Ein Lauf = ein Kern. Viele Laeufe parallel sind schneller als einer mit
    vielen Threads (kleine Netze, Python-lastige Feature-Berechnung)."""
    import torch
    torch.set_num_threads(1)


class Learners:
    """Ein Netz fuer beide Seiten (kanonisch) oder je Seite eins (no_canonical)."""

    def __init__(self, variant: str, run_dir: Path, run_seed: int, load: bool = False):
        self.variant = variant
        self.split = separate_sides(variant)
        wdir = run_dir / "weights"
        wdir.mkdir(parents=True, exist_ok=True)
        if self.split:
            self.paths = {s: str(wdir / f"agent_{s[-2:].replace('_', 'p')}.pth") for s in P.SIDES}
        else:
            shared = str(wdir / "agent.pth")
            self.paths = {s: shared for s in P.SIDES}
        self.agents = {}
        for i, side in enumerate(P.SIDES):
            if not self.split and self.agents:
                self.agents[side] = self.agents[P.SIDES[0]]
                continue
            self.agents[side] = make_learner(
                variant, side, self.paths[side] if load else None,
                seed=run_seed * 100 + i)

    def unique(self):
        seen = {}
        for side, a in self.agents.items():
            seen.setdefault(id(a), (side, a))
        return list(seen.values())

    def train_mode(self) -> None:
        for _, a in self.unique():
            if hasattr(a, "set_to_train_mode"):
                a.set_to_train_mode()

    def eval_mode(self) -> None:
        for _, a in self.unique():
            a.set_to_eval_mode()

    def save(self) -> None:
        for side, a in self.unique():
            a.save_agent(self.paths[side])

    def buffer_path(self, side: str) -> str:
        return self.paths[side].replace(".pth", ".buffer.npz")

    def save_buffers(self) -> None:
        """Replay Buffer neben die Gewichte legen (fuer Weitertraining)."""
        for side, a in self.unique():
            if hasattr(a, "save_buffer"):
                a.save_buffer(self.buffer_path(side))

    def load_buffers(self) -> int:
        """Gespeicherte Buffer laden, falls vorhanden. Gibt Anzahl Transitions zurueck."""
        n = 0
        for side, a in self.unique():
            if hasattr(a, "load_buffer") and Path(self.buffer_path(side)).is_file():
                n += a.load_buffer(self.buffer_path(side))
        return n


def play_set(env, learners: Learners, seeds, opponents, log=None, writer=None) -> list[dict]:
    """eps=0, ohne Lernen: jeder Seed von beiden Seiten gegen jeden Gegner."""
    rows = []
    for opp_name in opponents:
        for seed in seeds:
            for side in P.SIDES:
                opp_side = "player_1" if side == "player_0" else "player_0"
                opp = make_opponent(opp_name, opp_side)
                r = play_game(env, learners.agents[side], opp, seed, side, train=False)
                r["opponent"] = opp_name
                rows.append(r)
                if writer is not None:
                    writer.writerow({k: r.get(k) for k in GAME_FIELDS})
                if log:
                    log(f"  {opp_name:10s} seed {seed} {side}: {r['our_wins']}-{r['opp_wins']} "
                        f"P {r['our_points']}:{r['opp_points']}")
    return rows


def summarize(rows: list[dict]) -> dict:
    versions = {r.get("point_counting_version", 1) for r in rows}
    if len(versions) > 1:
        raise ValueError("Alte und korrigierte Punktemessungen nicht gemeinsam mitteln.")
    w = sum(r["our_wins"] for r in rows)
    m = sum(r["our_wins"] + r["opp_wins"] for r in rows)
    return dict(
        games=len(rows),
        point_counting_version=next(iter(versions), None),
        winrate=float(np.mean([r["result"] for r in rows])) if rows else float("nan"),
        match_winrate=w / max(1, m),
        point_winrate=float(np.mean([r["point_win"] for r in rows])) if rows else float("nan"),
        avg_points=float(np.mean([r["our_points"] for r in rows])) if rows else float("nan"),
        avg_opp_points=float(np.mean([r["opp_points"] for r in rows])) if rows else float("nan"),
    )


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=list(VARIANTS), required=True)
    ap.add_argument("--run-seed", type=int, default=0, help="Trainingsstart (torch/numpy/Env-Seeds)")
    ap.add_argument("--games", type=int, default=1200, help="Trainingsspiele")
    ap.add_argument("--val-every", type=int, default=150, help="0 = keine Lernkurve")
    ap.add_argument("--val-seeds", type=int, default=P.N_VAL)
    ap.add_argument("--test-seeds", type=int, default=P.N_TEST)
    ap.add_argument("--no-test", action="store_true", help="Test-Seeds nicht anfassen")
    ap.add_argument("--sol92-frac", type=float, default=None,
                    help="Anteil Solution_92 nach der Aufwaermphase (Default: Protokoll, 50 %%)")
    ap.add_argument("--tag", default="")
    ap.add_argument("--out", default=None, help="Run-Ordner (Default: experiments/runs/<datum>_...)")
    ap.add_argument("--date", default=datetime.now().strftime("%Y%m%d"))
    args = ap.parse_args(argv)

    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv

    name = f"{args.date}_{args.variant}_s{args.run_seed}" + (f"_{args.tag}" if args.tag else "")
    run_dir = Path(args.out) if args.out else RUNS / name
    run_dir.mkdir(parents=True, exist_ok=True)
    logf = open(run_dir / "log.txt", "a", encoding="utf-8")

    def log(msg: str) -> None:
        line = f"[{datetime.now():%H:%M:%S}] {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    trainable = is_trainable(args.variant)
    games = args.games if trainable else 0
    seed_everything(args.run_seed)
    learners = Learners(args.variant, run_dir, args.run_seed)

    manifest = dict(
        name=name, variant=args.variant, kind=VARIANTS[args.variant][0],
        overrides=VARIANTS[args.variant][1],
        config=variant_cfg(args.variant).to_dict() if VARIANTS[args.variant][0] == "sherlock" else None,
        separate_side_networks=learners.split,
        run_seed=args.run_seed, train_games=games,
        train_seeds=[P.train_seed(args.run_seed, 0), P.train_seed(args.run_seed, max(0, games - 1))] if games else [],
        curriculum=(f"erste {P.CURRICULUM_WARMUP_FRAC:.0%} default, dann abwechselnd default/solution92"
                    if args.sol92_frac is None else
                    f"erste {P.CURRICULUM_WARMUP_FRAC:.0%} default, dann {args.sol92_frac:.0%} solution92"),
        val_seeds=P.val_seeds(args.val_seeds) if args.val_every else [],
        val_every=args.val_every,
        test_seeds=[] if args.no_test else P.test_seeds(args.test_seeds),
        eval_opponents=list(P.EVAL_OPPONENTS), sides=list(P.SIDES), eval_epsilon=0.0,
        git=git_info(), started=datetime.now().isoformat(timespec="seconds"),
        python=sys.version.split()[0], platform=platform.platform(),
        argv=sys.argv,
    )
    try:
        import importlib.metadata as md
        manifest["versions"] = {p: md.version(p) for p in ("torch", "numpy", "luxai-s3", "jax")}
    except Exception:
        pass
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    env = LuxAIS3GymEnv(numpy_output=True)
    t0 = time.time()
    timings = {}

    # ------------------------------------------------------------ Training
    if games:
        log(f"Training {args.variant} s{args.run_seed}: {games} Spiele")
        learners.train_mode()
        results: list[float] = []
        with open(run_dir / "train.csv", "w", newline="", encoding="utf-8") as fh, \
                open(run_dir / "val.csv", "w", newline="", encoding="utf-8") as vh:
            tw = csv.DictWriter(fh, fieldnames=TRAIN_FIELDS)
            tw.writeheader()
            vw = csv.DictWriter(vh, fieldnames=VAL_FIELDS)
            vw.writeheader()

            def validate(after: int) -> None:
                if not args.val_every:
                    return
                tv = time.time()
                learners.eval_mode()
                rows = play_set(env, learners, P.val_seeds(args.val_seeds), P.EVAL_OPPONENTS)
                learners.train_mode()
                for opp_name in P.EVAL_OPPONENTS:
                    s = summarize([r for r in rows if r["opponent"] == opp_name])
                    s.update(after_games=after, opponent=opp_name, secs=round(time.time() - tv, 1))
                    vw.writerow({k: s.get(k) for k in VAL_FIELDS})
                    log(f"  VAL nach {after}: {opp_name} WR={s['winrate']:.3f} "
                        f"Punkte {s['avg_points']:.0f}:{s['avg_opp_points']:.0f}")
                vh.flush()

            validate(0)
            for g in range(games):
                side = P.train_side(g)
                opp_name = P.train_opponent(g, games, args.sol92_frac)
                seed = P.train_seed(args.run_seed, g)
                agent = learners.agents[side]
                opp = make_opponent(opp_name, "player_1" if side == "player_0" else "player_0")
                row = play_game(env, agent, opp, seed, side, train=True)
                results.append(row["result"])
                row.update(
                    game=g, opponent=opp_name,
                    epsilon=round(agent.epsilon, 4),
                    mean_loss=round(agent.pop_mean_loss(), 5),
                    env_steps=getattr(agent, "env_steps", ""),
                    learn_steps=getattr(agent, "learn_steps", ""),
                    winrate_50=round(float(np.mean(results[-50:])), 4),
                )
                tw.writerow({k: row.get(k) for k in TRAIN_FIELDS})
                if (g + 1) % 25 == 0 or g == games - 1:
                    fh.flush()
                    log(f"[{g+1}/{games}] {opp_name} {side} {row['our_wins']}-{row['opp_wins']} "
                        f"eps={row['epsilon']} loss={row['mean_loss']} WR50={row['winrate_50']:.2f}")
                if (g + 1) % 100 == 0:
                    learners.save()
                if args.val_every and (g + 1) % args.val_every == 0 and g + 1 < games:
                    validate(g + 1)
            learners.save()
            learners.save_buffers()
            validate(games)
        timings["train_secs"] = round(time.time() - t0, 1)

    # ------------------------------------------------------------ Test
    if not args.no_test:
        t1 = time.time()
        learners.eval_mode()
        log(f"Test: {args.test_seeds} Seeds x {len(P.SIDES)} Seiten x {list(P.EVAL_OPPONENTS)}")
        with open(run_dir / "eval.csv", "w", newline="", encoding="utf-8") as eh:
            ew = csv.DictWriter(eh, fieldnames=GAME_FIELDS)
            ew.writeheader()
            rows = play_set(env, learners, P.test_seeds(args.test_seeds), P.EVAL_OPPONENTS,
                            writer=ew)
        for opp_name in P.EVAL_OPPONENTS:
            s = summarize([r for r in rows if r["opponent"] == opp_name])
            log(f"TEST {opp_name}: WR={s['winrate']:.3f} Matches={s['match_winrate']:.3f} "
                f"Punkte {s['avg_points']:.0f}:{s['avg_opp_points']:.0f}")
            manifest.setdefault("test_summary", {})[opp_name] = s
        timings["test_secs"] = round(time.time() - t1, 1)

    env.close()
    manifest.update(timings, finished=datetime.now().isoformat(timespec="seconds"),
                    runtime_secs=round(time.time() - t0, 1), status="done")
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    log(f"Fertig in {manifest['runtime_secs'] / 60:.1f} min -> {run_dir}")
    logf.close()


if __name__ == "__main__":
    os.chdir(ROOT)
    main()
