"""Verbesserungsrunde: einen fertigen Lauf weitertrainieren, besten Checkpoint
NUR nach Validierung waehlen, dann einmal auf den Test-Seeds auswerten.

    python -m scripts.finetune --init experiments/runs/20261010_full_s0 --games 3000 \
        --name 20261011_full_ft2_s0

Unterschiede zu scripts/experiment.py:
  * Start aus vorhandenen Gewichten (env_steps bleiben erhalten -> eps bleibt 0.05)
  * Replay Buffer: wird aus dem Init-Lauf geladen (<gewichte>.buffer.npz). Fehlt
    er, wird er zuerst mit --prefill-games Spielen der eingefrorenen Policy
    aufgefuellt, OHNE zu lernen. Grund: Die erste Runde (10.10.) startete mit
    leerem Buffer, lernte nur auf wenigen frischen Transitions und verlernte
    sofort (Validierung nach 250 Spielen deutlich schlechter als vorher).
  * Gegner-Pool / Self-Play (--pool, --mix, --snapshot-every): neben default und
    Solution_92 spielt der Lerner gegen eingefrorene Versionen von uns selbst
    (z. B. Abgabe-Ensemble) und gegen eigene Schnappschuesse waehrend des
    Trainings. Ziel: robuster gegen unbekannte Spielstile (andere Gruppen).
  * kleinere Lernrate (Default 1e-4 statt 3e-4) und 16 statt 8 Validierungs-Seeds,
    damit die Checkpoint-Auswahl weniger vom Zufall abhaengt
  * Gegner-Mix mit hoeherem Solution_92-Anteil (--sol92-frac), Rest default
    (gegen Vergessen)
  * nach jeder Validierung: Checkpoint behalten, wenn der Validierungs-Score
    besser ist. Score = mittlere Winrate ueber beide Gegner + 0.5 * Match-Winrate
    gegen Solution_92 (dort sind Spielsiege selten, Matches sind feiner).
  * Test nur mit dem nach Validierung besten Checkpoint.
  * 29.10.2026 (Battle-Vorbereitung): --variant setzt die Config des Lerners (z. B. full_rules_v10:
    alle V10-Regeln schon im Training), --mix erlaubt alle Gegner aus scripts.common (z. B.
    sol92_sq, sol92_weak, rush), --keep-final behaelt den Endstand statt des Validierungs-Besten
    (16 Validierungskarten waehlen sonst leicht einen Zufallstreffer oder den unveraenderten Start).
Ausgabeformat (train/val/eval.csv, manifest.json) wie experiment.py, damit
scripts/report.py die Laeufe mit auswertet.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import time
from datetime import datetime
from pathlib import Path

import numpy as np

from scripts import protocol as P
from scripts.common import make_opponent, play_game
from scripts.experiment import (GAME_FIELDS, RUNS, TRAIN_FIELDS, VAL_FIELDS, Learners,
                                git_info, limit_threads, play_set, summarize)
from scripts.variants import seed_everything

FT_SEED_BASE = 200_000  # eigene Trainings-Seeds, disjunkt zu Training/Validierung/Test


def val_score(by_opp: dict) -> float:
    return (by_opp["default"]["winrate"] + by_opp["solution92"]["winrate"]) / 2 \
        + 0.5 * by_opp["solution92"]["match_winrate"]


def parse_mix(text: str | None, sol92_frac: float) -> dict[str, float]:
    """Gegner-Anteile pruefen; erlaubt sind alle Gegner aus scripts.common ausser self, dazu pool."""
    from scripts.common import OPPONENTS
    if text:
        mix = {k: float(v) for k, v in (kv.split("=") for kv in text.split(","))}
    else:
        mix = {"solution92": sol92_frac, "default": 1.0 - sol92_frac}
    allowed = (set(OPPONENTS) - {"self"}) | {"pool"}
    if not set(mix) <= allowed:
        raise SystemExit(f"Unbekannte Gegner im Mix: {sorted(set(mix) - allowed)}")
    if abs(sum(mix.values()) - 1.0) > 1e-6:
        raise SystemExit(f"Anteile ergeben nicht 1: {mix}")
    return mix


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", required=True, help="Run-Ordner mit Startgewichten")
    ap.add_argument("--games", type=int, default=3000)
    ap.add_argument("--sol92-frac", type=float, default=0.5)
    ap.add_argument("--val-every", type=int, default=250)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--name", required=True)
    ap.add_argument("--no-test", action="store_true")
    ap.add_argument("--lr", type=float, default=1e-4, help="Lernrate (0 = die des Checkpoints)")
    ap.add_argument("--prefill-games", type=int, default=120,
                    help="Spiele zum Auffuellen des Buffers, falls keiner gespeichert ist")
    ap.add_argument("--n-val", type=int, default=16, help="Validierungs-Seeds pro Gegner")
    ap.add_argument("--pool", nargs="*", default=[],
                    help="eingefrorene Sherlock-Gewichte als Gegner (auch Ensembles)")
    ap.add_argument("--mix", default=None,
                    help="Gegner-Anteile, z. B. solution92=0.35,default=0.15,pool=0.5 "
                         "(Default: --sol92-frac, Rest default)")
    ap.add_argument("--snapshot-every", type=int, default=0,
                    help="alle n Spiele Schnappschuss des Lerners in den Pool (0 = aus)")
    ap.add_argument("--max-snapshots", type=int, default=4)
    ap.add_argument("--variant", default=None, help="Config des Lerners (Default: Variante des Init-Laufs)")
    ap.add_argument("--keep-final", action="store_true",
                    help="Endstand behalten statt des besten Checkpoints nach Validierung")
    args = ap.parse_args()

    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv

    init = Path(args.init)
    src_man = json.loads((init / "manifest.json").read_text())
    variant = args.variant or src_man.get("base_variant", src_man["variant"])  # Kette: ft eines ft-Laufs
    run_dir = RUNS / args.name
    if run_dir.exists():
        raise SystemExit(f"{run_dir} existiert schon - neuen Namen waehlen")
    assert FT_SEED_BASE + args.seed * 10_000 + 5_000 + args.games // 2 < P.VAL_SEED_BASE, \
        "Trainings-Seeds wuerden in die Validierung laufen"
    (run_dir / "weights").mkdir(parents=True, exist_ok=True)
    for pat in ("*.pth", "*.buffer.npz"):
        for f in (init / "weights").glob(pat):
            shutil.copyfile(f, run_dir / "weights" / f.name)
    logf = open(run_dir / "log.txt", "a", encoding="utf-8")

    def log(msg):
        line = f"[{datetime.now():%H:%M:%S}] {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    seed_everything(args.seed)
    learners = Learners(variant, run_dir, args.seed, load=True)
    if args.lr:
        for _, a in learners.unique():
            for g in a.opt.param_groups:
                g["lr"] = args.lr
            a.cfg.lr = args.lr

    rng = np.random.default_rng(args.seed)
    mix = parse_mix(args.mix, args.sol92_frac)
    assert abs(sum(mix.values()) - 1.0) < 1e-6, mix
    assert mix.get("pool", 0) == 0 or args.pool or args.snapshot_every, "pool ohne Gegner"
    for p in args.pool:
        assert Path(p).is_file(), p
    pool = list(args.pool)          # feste Pool-Gegner
    snapshots: list[str] = []       # rollierende Schnappschuesse des Lerners
    pool_agents: dict[str, object] = {}
    mix_names, mix_p = list(mix), np.array(list(mix.values()))

    def pick_opponent(opp_side: str):
        name = mix_names[rng.choice(len(mix_names), p=mix_p)]
        if name != "pool":
            return name, make_opponent(name, opp_side)
        path = (pool + snapshots)[rng.integers(len(pool) + len(snapshots))]
        if path not in pool_agents:   # einmal laden, danach wiederverwenden
            pool_agents[path] = make_opponent("self", opp_side, self_play_path=path)
        label = "pool:" + Path(path).parent.parent.name + "/" + Path(path).name
        return label, pool_agents[path]
    manifest = dict(
        name=args.name, variant=f"{variant}_ft", base_variant=variant, kind="finetune",
        init_from=str(init), init_train_games=src_man.get("train_games"),
        run_seed=args.seed, train_games=args.games, sol92_frac=args.sol92_frac,
        lr=args.lr or None, mix=mix, pool=pool, snapshot_every=args.snapshot_every,
        prefill_games=args.prefill_games, buffer_loaded=0,
        train_seeds=[FT_SEED_BASE + args.seed * 10_000,
                                 FT_SEED_BASE + args.seed * 10_000 + args.games // 2],
        selection=("Endstand (--keep-final)" if args.keep_final else
                   "bester Checkpoint nach val_score (Validierung), siehe Docstring"),
        val_seeds=P.val_seeds(args.n_val), val_every=args.val_every,
        test_seeds=[] if args.no_test else P.test_seeds(),
        eval_opponents=list(P.EVAL_OPPONENTS), eval_epsilon=0.0,
        git=git_info(), started=datetime.now().isoformat(timespec="seconds"),
        config=learners.agents["player_0"].cfg.to_dict(),
    )
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    env = LuxAIS3GymEnv(numpy_output=True)
    t0 = time.time()
    best = dict(score=-1.0, after=None)
    best_dir = run_dir / "weights_best"

    def validate(after, vw):
        learners.eval_mode()
        rows = play_set(env, learners, P.val_seeds(args.n_val), P.EVAL_OPPONENTS)
        learners.train_mode()
        by = {o: summarize([r for r in rows if r["opponent"] == o]) for o in P.EVAL_OPPONENTS}
        for o, s in by.items():
            vw.writerow({**{k: s.get(k) for k in VAL_FIELDS}, "after_games": after, "opponent": o})
        sc = val_score(by)
        log(f"  VAL nach {after}: default {by['default']['winrate']:.3f} | sol92 "
            f"{by['solution92']['winrate']:.3f} (Matches {by['solution92']['match_winrate']:.3f}, "
            f"Punkte {by['solution92']['avg_points']:.0f}:{by['solution92']['avg_opp_points']:.0f}) "
            f"-> score {sc:.3f}")
        if sc > best["score"]:
            best.update(score=sc, after=after)
            learners.save()
            shutil.rmtree(best_dir, ignore_errors=True)
            shutil.copytree(run_dir / "weights", best_dir, ignore=shutil.ignore_patterns("*.npz"))
            log(f"    neuer bester Checkpoint (nach {after} Spielen)")

    learners.train_mode()
    n_buf = learners.load_buffers()
    manifest["buffer_loaded"] = n_buf
    log(f"Buffer aus Init-Lauf geladen: {n_buf} Transitions")
    if n_buf == 0 and args.prefill_games > 0:
        # Buffer mit der eingefrorenen Policy (eps wie im Training) fuellen.
        # Eigene Seeds hinter den Trainings-Seeds dieses Starts (games < 10_000).
        assert args.games // 2 < 5_000
        for _, a in learners.unique():
            a.learn_enabled = False
        for g in range(args.prefill_games):
            side = P.SIDES[g % 2]
            seed = FT_SEED_BASE + args.seed * 10_000 + 5_000 + g // 2
            _, opp = pick_opponent("player_1" if side == "player_0" else "player_0")
            play_game(env, learners.agents[side], opp, seed, side, train=True)
        for _, a in learners.unique():
            a.learn_enabled = True
        log(f"Buffer aufgefuellt: {args.prefill_games} Spiele, "
            f"{len(learners.agents['player_0'].buffer)} Transitions")
    results = []
    with open(run_dir / "train.csv", "w", newline="") as fh, open(run_dir / "val.csv", "w", newline="") as vh:
        tw = csv.DictWriter(fh, fieldnames=TRAIN_FIELDS); tw.writeheader()
        vw = csv.DictWriter(vh, fieldnames=VAL_FIELDS); vw.writeheader()
        validate(0, vw)
        for g in range(args.games):
            side = P.SIDES[g % 2]
            seed = FT_SEED_BASE + args.seed * 10_000 + g // 2
            agent = learners.agents[side]
            opp_name, opp = pick_opponent("player_1" if side == "player_0" else "player_0")
            row = play_game(env, agent, opp, seed, side, train=True)
            results.append(row["result"])
            row.update(game=g, opponent=opp_name, epsilon=round(agent.epsilon, 4),
                       mean_loss=round(agent.pop_mean_loss(), 5),
                       env_steps=agent.env_steps, learn_steps=agent.learn_steps,
                       winrate_50=round(float(np.mean(results[-50:])), 4))
            tw.writerow({k: row.get(k) for k in TRAIN_FIELDS})
            if (g + 1) % 25 == 0:
                fh.flush()
                log(f"[{g+1}/{args.games}] {opp_name} {row['our_wins']}-{row['opp_wins']} "
                    f"P {row['our_points']}:{row['opp_points']} loss={row['mean_loss']}")
            if args.snapshot_every and (g + 1) % args.snapshot_every == 0:
                snap = run_dir / "snapshots" / f"snap_{g + 1:05d}.pth"
                snap.parent.mkdir(exist_ok=True)
                agent.save_agent(str(snap))
                snapshots.append(str(snap))
                if len(snapshots) > args.max_snapshots:
                    old = snapshots.pop(0)
                    pool_agents.pop(old, None)
                log(f"  Schnappschuss {snap.name} im Pool ({len(pool) + len(snapshots)} Pool-Gegner)")
            if (g + 1) % args.val_every == 0:
                learners.save()
                validate(g + 1, vw)
                vh.flush()
    manifest["train_secs"] = round(time.time() - t0, 1)
    manifest["best_after_games"] = best["after"]
    manifest["best_val_score"] = best["score"]

    # bester Checkpoint -> weights/ (fuer Test, Replays, Abgabe). Der Buffer
    # (Stand Trainingsende) kommt daneben, damit der Lauf weitertrainierbar ist.
    if args.keep_final:
        learners.save()
    else:
        shutil.rmtree(run_dir / "weights")
        shutil.copytree(best_dir, run_dir / "weights")
    learners.save_buffers()
    if not args.no_test:
        learners = Learners(variant, run_dir, args.seed, load=True)
        learners.eval_mode()
        t1 = time.time()
        with open(run_dir / "eval.csv", "w", newline="") as eh:
            ew = csv.DictWriter(eh, fieldnames=GAME_FIELDS); ew.writeheader()
            rows = play_set(env, learners, P.test_seeds(), P.EVAL_OPPONENTS, writer=ew)
        for o in P.EVAL_OPPONENTS:
            s = summarize([r for r in rows if r["opponent"] == o])
            manifest.setdefault("test_summary", {})[o] = s
            log(f"TEST {o}: WR={s['winrate']:.3f} Matches={s['match_winrate']:.3f} "
                f"Punkte {s['avg_points']:.0f}:{s['avg_opp_points']:.0f}")
        manifest["test_secs"] = round(time.time() - t1, 1)
    env.close()
    manifest.update(status="done", finished=datetime.now().isoformat(timespec="seconds"),
                    runtime_secs=round(time.time() - t0, 1))
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    log(f"Fertig, bester Checkpoint nach {best['after']} Spielen (score {best['score']:.3f})")


if __name__ == "__main__":
    main()
