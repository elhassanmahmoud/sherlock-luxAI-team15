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
import copy
import csv
import hashlib
import json
import os
import platform
import random
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


def state_sha256(value) -> str:
    """Canonical typed hash of small state trees; never a torch.save container hash.

    Tensor names, dtype, shape and bytes are included. Used for networks,
    optimizer and RNG state, never for the preallocated replay arrays.
    """
    import torch

    digest = hashlib.sha256()

    def emit(data: bytes) -> None:
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)

    def visit(item):
        if isinstance(item, torch.Tensor):
            tensor = item.detach().cpu().contiguous()
            emit(b"tensor")
            emit(str(tensor.dtype).encode())
            visit(list(tensor.shape))
            emit(tensor.reshape(-1).view(torch.uint8).numpy().tobytes())
        elif isinstance(item, np.ndarray):
            emit(b"ndarray")
            emit(item.dtype.str.encode())
            visit(list(item.shape))
            emit(item.tobytes(order="C"))
        elif isinstance(item, dict):
            emit(b"dict")
            emit(str(len(item)).encode())
            for key in sorted(item, key=lambda k: (type(k).__name__, repr(k))):
                visit(key)
                visit(item[key])
        elif isinstance(item, (list, tuple)):
            emit(type(item).__name__.encode())
            emit(str(len(item)).encode())
            for child in item:
                visit(child)
        elif isinstance(item, (str, int, float, bool, type(None))):
            emit(type(item).__name__.encode())
            emit(repr(item).encode())
        elif isinstance(item, np.generic):
            visit(item.item())
        else:
            raise TypeError(f"Unsupported identity state: {type(item).__name__}")

    visit(value)
    return digest.hexdigest()


def _global_rng_state() -> dict:
    import torch
    states = {"python": random.getstate(), "numpy": np.random.get_state(),
              "torch_cpu": torch.get_rng_state().clone()}
    # Do not initialize a GPU merely to capture state on this CPU study.
    if torch.cuda.is_initialized():
        states["torch_cuda"] = torch.cuda.get_rng_state_all()
    return states


def _restore_global_rng(states: dict) -> None:
    import torch
    random.setstate(states["python"])
    np.random.set_state(states["numpy"])
    torch.set_rng_state(states["torch_cpu"])
    if "torch_cuda" in states:
        torch.cuda.set_rng_state_all(states["torch_cuda"])


def _replay_metadata(buffer, *, identities: bool = False) -> dict:
    result = {key: getattr(buffer, key)
              for key in ("capacity", "obs_dim", "pos", "size", "_mask_dim")}
    result["arrays"] = {
        key: {"shape": list(value.shape), "dtype": value.dtype.str,
              **({"id": id(value)} if identities else {})}
        for key, value in vars(buffer).items() if isinstance(value, np.ndarray)
    }
    if identities:
        result["id"] = id(buffer)
    return result


def _learning_identity(agent, *, identities: bool = False) -> dict:
    return dict(
        q_sha256=state_sha256(agent.q.state_dict()),
        target_q_sha256=state_sha256(agent.target_q.state_dict()),
        optimizer_sha256=state_sha256(agent.opt.state_dict()),
        replay=_replay_metadata(agent.buffer, identities=identities),
        config=copy.deepcopy(agent.cfg.to_dict()), device=str(agent.device),
        env_steps=agent.env_steps, learn_steps=agent.learn_steps,
        learn_enabled=agent.learn_enabled, autosave_on_terminate=agent.autosave_on_terminate,
        recent_losses=list(agent.recent_losses),
    )


def initial_identity(learners: Learners) -> dict:
    """Evidence from the actual freshly constructed learners, before validation 0.

    Empty replay content is represented logically: unused allocated slots cannot
    be sampled. No addresses, timestamps or output paths enter paired identity.
    """
    entries = []
    for _, agent in learners.unique():
        entry = _learning_identity(agent)
        if (agent.buffer.size, agent.buffer.pos, agent.buffer._mask_dim) != (0, 0, 1):
            raise ValueError("Initial identity requires a fresh empty replay buffer")
        entry["replay"]["logical_content"] = "empty-replay-v1"
        entry["agent_rng_sha256"] = state_sha256(agent.rng.bit_generator.state)
        entry["sides"] = [s for s, a in learners.agents.items() if a is agent]
        entries.append(entry)
    return {"schema_version": 1, "learners": entries,
            "rng_sha256": {k: state_sha256(v) for k, v in _global_rng_state().items()}}


def run_validation(env, learners: Learners, seeds, opponents, *, isolate: bool) -> list[dict]:
    """Run diagnostics with optional RNG/context isolation and learning guards.

    The opt-in path supports Sherlock learners and the two fresh fixed opponents.
    Learning mutations abort the run; they are never silently repaired. Large
    replay arrays are guarded read-only, with identity/metadata checks, not copied.
    """
    if not isolate:
        # Preserve the historical CLI behavior unless isolation was requested.
        learners.eval_mode()
        try:
            return play_set(env, learners, seeds, opponents)
        finally:
            learners.train_mode()

    opponents = tuple(opponents)
    if any(name not in P.EVAL_OPPONENTS for name in opponents):
        raise ValueError("Isolated validation supports only default and solution92")
    global_rng = _global_rng_state()
    snapshots = []
    guarded_methods = []
    guarded_arrays = []
    missing = object()

    def forbidden(*args, **kwargs):
        raise RuntimeError("Learning/replay operation forbidden during validation")

    try:
        for _, agent in learners.unique():
            snapshot = dict(agent=agent, learning=_learning_identity(agent, identities=True),
                            rng=copy.deepcopy(agent.rng.bit_generator.state),
                            training=agent.training, q_training=agent.q.training,
                            target_training=agent.target_q.training,
                            player=agent.player, env_cfg=copy.deepcopy(agent.env_cfg))
            snapshots.append(snapshot)
            for owner, names in ((agent, ("update", "_learn", "save_agent", "pop_mean_loss")),
                                 (agent.buffer, ("push", "sample")), (agent.opt, ("step",))):
                for name in names:
                    guarded_methods.append((owner, name, vars(owner).get(name, missing)))
                    setattr(owner, name, forbidden)
            for array in vars(agent.buffer).values():
                if isinstance(array, np.ndarray):
                    guarded_arrays.append((array, array.flags.writeable))
                    array.flags.writeable = False
        learners.eval_mode()
        return play_set(env, learners, seeds, opponents)
    finally:
        # Even a failed game must leave guards, episode state, modes and RNG clean.
        # If the game itself failed, retain that exception instead of masking it
        # with a secondary invariant diagnostic. In either case training aborts.
        game_failed = sys.exc_info()[0] is not None
        changed = []
        try:
            for snapshot in snapshots:
                if _learning_identity(snapshot["agent"], identities=True) != snapshot["learning"]:
                    changed.append(snapshot["player"])
        finally:
            try:
                for owner, name, original in reversed(guarded_methods):
                    if original is missing:
                        delattr(owner, name)
                    else:
                        setattr(owner, name, original)
                for array, writable in guarded_arrays:
                    array.flags.writeable = writable
                for snapshot in snapshots:
                    agent = snapshot["agent"]
                    agent.set_env_cfg(snapshot["env_cfg"] or {})
                    agent.env_cfg = snapshot["env_cfg"]
                    agent.new_game(snapshot["player"])
                    agent._paths.step = None
                    agent._paths.maps.clear()
                    agent.training = snapshot["training"]
                    agent.q.train(snapshot["q_training"])
                    agent.target_q.train(snapshot["target_training"])
            finally:
                for snapshot in snapshots:
                    snapshot["agent"].rng.bit_generator.state = snapshot["rng"]
                _restore_global_rng(global_rng)
        if changed and not game_failed:
            raise RuntimeError(f"Learning state changed during validation: {changed}")


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
    ap.add_argument("--val-seed-start", type=int, default=P.VAL_SEED_BASE,
                    help="Absoluter erster Validierungsseed")
    ap.add_argument("--isolate-validation", action="store_true",
                    help="Validierung von Trainings-RNG und Episodenzustand isolieren")
    ap.add_argument("--test-seeds", type=int, default=P.N_TEST)
    ap.add_argument("--no-test", action="store_true", help="Test-Seeds nicht anfassen")
    ap.add_argument("--pool", nargs="*", default=[], help="eigene Checkpoints als Gegner")
    ap.add_argument("--pool-frac", type=float, default=0.0, help="Anteil Pool-Gegner nach der Aufwaermphase")
    ap.add_argument("--sol92-frac", type=float, default=None,
                    help="Anteil Solution_92 nach der Aufwaermphase (Default: Protokoll, 50 %%)")
    ap.add_argument("--opponent-plan", choices=("standard", "early_sol100"), default="standard")
    ap.add_argument("--seed-file", default=None,
                    help="JSON-Liste von Env-Seeds fuer die Solution_92-Spiele (21.10.2026: "
                         "schwere Karten, auf denen V3 verliert); default-Spiele bleiben unveraendert")
    ap.add_argument("--tag", default="")
    ap.add_argument("--out", default=None, help="Run-Ordner (Default: experiments/runs/<datum>_...)")
    ap.add_argument("--date", default=datetime.now().strftime("%Y%m%d"))
    args = ap.parse_args(argv)

    trainable = is_trainable(args.variant)
    games = args.games if trainable else 0
    try:
        schedule = P.opponent_schedule(games, args.sol92_frac, args.pool_frac, args.opponent_plan)
    except ValueError as exc:
        ap.error(str(exc))
    if args.isolate_validation and VARIANTS[args.variant][0] != "sherlock":
        ap.error("--isolate-validation requires a Sherlock learner")
    validation_seeds = list(range(args.val_seed_start, args.val_seed_start + args.val_seeds))
    hard_seeds: list[int] = []
    if args.seed_file:
        hard_seeds = [int(s) for s in json.loads(Path(args.seed_file).read_text())]
        if not hard_seeds:
            ap.error("--seed-file ist leer")
        if set(hard_seeds) & set(validation_seeds):
            ap.error("--seed-file ueberschneidet sich mit den Validierungsseeds")

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

    seed_everything(args.run_seed)
    learners = Learners(args.variant, run_dir, args.run_seed)
    if args.isolate_validation:
        (run_dir / "initial_identity.json").write_text(json.dumps(initial_identity(learners), indent=2))

    manifest = dict(
        name=name, variant=args.variant, kind=VARIANTS[args.variant][0],
        overrides=VARIANTS[args.variant][1],
        config=variant_cfg(args.variant).to_dict() if VARIANTS[args.variant][0] == "sherlock" else None,
        separate_side_networks=learners.split,
        run_seed=args.run_seed, train_games=games,
        train_seeds=[P.train_seed(args.run_seed, 0), P.train_seed(args.run_seed, max(0, games - 1))] if games else [],
        curriculum=("early_sol100" if args.opponent_plan == "early_sol100" else
                    f"erste {P.CURRICULUM_WARMUP_FRAC:.0%} default, dann abwechselnd default/solution92"
                    if args.sol92_frac is None else
                    f"erste {P.CURRICULUM_WARMUP_FRAC:.0%} default, dann {args.sol92_frac:.0%} solution92"),
        opponent_plan=args.opponent_plan, opponent_schedule=schedule,
        seed_file=args.seed_file, seed_file_count=len(hard_seeds),
        seed_file_sha256=(hashlib.sha256(Path(args.seed_file).read_bytes()).hexdigest()
                          if args.seed_file else None),
        opponent_schedule_sha256=hashlib.sha256(
            json.dumps(schedule, separators=(",", ":")).encode()).hexdigest(),
        isolate_validation=args.isolate_validation,
        val_seeds=validation_seeds if args.val_every else [],
        val_every=args.val_every,
        test_seeds=[] if args.no_test else P.test_seeds(args.test_seeds),
        eval_opponents=list(P.EVAL_OPPONENTS), sides=list(P.SIDES), eval_epsilon=0.0,
        git=git_info(), started=datetime.now().isoformat(timespec="seconds"),
        python=sys.version.split()[0], platform=platform.platform(),
        argv=sys.argv,
    )
    if args.isolate_validation:
        manifest["learner_devices"] = [str(agent.device) for _, agent in learners.unique()]
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
                open(run_dir / "val.csv", "w", newline="", encoding="utf-8") as vh, \
                open(run_dir / "val_games.csv", "w", newline="", encoding="utf-8") as vgh:
            tw = csv.DictWriter(fh, fieldnames=TRAIN_FIELDS)
            tw.writeheader()
            vw = csv.DictWriter(vh, fieldnames=VAL_FIELDS)
            vw.writeheader()
            vgw = csv.DictWriter(vgh, fieldnames=["after_games"] + GAME_FIELDS)
            vgw.writeheader()

            def validate(after: int) -> None:
                if not args.val_every:
                    return
                tv = time.time()
                rows = run_validation(env, learners, validation_seeds, P.EVAL_OPPONENTS,
                                      isolate=args.isolate_validation)
                for row in rows:
                    vgw.writerow({"after_games": after, **{k: row.get(k) for k in GAME_FIELDS}})
                vgh.flush()
                for opp_name in P.EVAL_OPPONENTS:
                    s = summarize([r for r in rows if r["opponent"] == opp_name])
                    s.update(after_games=after, opponent=opp_name, secs=round(time.time() - tv, 1))
                    vw.writerow({k: s.get(k) for k in VAL_FIELDS})
                    log(f"  VAL nach {after}: {opp_name} WR={s['winrate']:.3f} "
                        f"Punkte {s['avg_points']:.0f}:{s['avg_opp_points']:.0f}")
                vh.flush()

            validate(0)
            pool_cache: dict = {}
            if args.pool_frac and not args.pool:
                raise SystemExit("--pool-frac braucht --pool")
            for g in range(games):
                side = P.train_side(g)
                opp_name = schedule[g]
                seed = P.train_seed(args.run_seed, g)
                if hard_seeds and opp_name == "solution92":
                    # beide Seiten eines Paares auf derselben schweren Karte, je Start versetzt
                    seed = hard_seeds[(g // 2 + 997 * args.run_seed) % len(hard_seeds)]
                agent = learners.agents[side]
                opp_side = "player_1" if side == "player_0" else "player_0"
                if opp_name == "pool":
                    # eingefrorene eigene Checkpoints, reihum; einmal geladen, dann wiederverwendet
                    path = args.pool[(g // 2) % len(args.pool)]
                    if path not in pool_cache:
                        pool_cache[path] = make_opponent("self", opp_side, self_play_path=path)
                    opp = pool_cache[path]
                    opp_name = f"pool:{Path(path).stem}"
                else:
                    opp = make_opponent(opp_name, opp_side)
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
