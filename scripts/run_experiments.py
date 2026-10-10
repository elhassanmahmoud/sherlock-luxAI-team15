"""Alle Varianten x Trainingsstarts parallel ausfuehren (ein Prozess pro Lauf).

    python -m scripts.run_experiments --games 3000 --workers 11
    python -m scripts.run_experiments --variants full no_sap --starts 1 --games 50 --tag probe

Fertige Laeufe (manifest.json mit status=done) werden uebersprungen, ein
abgebrochener Batch kann also einfach neu gestartet werden.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from scripts.common import ROOT
from scripts.experiment import RUNS
from scripts.variants import VARIANTS, is_trainable

SINGLE_THREAD_ENV = {
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "XLA_FLAGS": "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", nargs="+", default=list(VARIANTS))
    ap.add_argument("--starts", type=int, default=3, help="Trainingsstarts pro Variante")
    ap.add_argument("--games", type=int, default=3000)
    ap.add_argument("--val-every", type=int, default=250)
    ap.add_argument("--workers", type=int, default=11)
    ap.add_argument("--date", default=datetime.now().strftime("%Y%m%d"))
    ap.add_argument("--tag", default="")
    ap.add_argument("--extra", nargs=argparse.REMAINDER, default=[],
                    help="weitere Argumente fuer scripts.experiment")
    args = ap.parse_args()

    jobs = []
    for s in range(args.starts):
        for v in args.variants:
            # eingefrorene Prof-Gewichte: deterministisch, ein Lauf genuegt
            if not is_trainable(v) and s > 0:
                continue
            name = f"{args.date}_{v}_s{s}" + (f"_{args.tag}" if args.tag else "")
            man = RUNS / name / "manifest.json"
            if man.is_file() and json.loads(man.read_text()).get("status") == "done":
                print(f"uebersprungen (fertig): {name}")
                continue
            cmd = [sys.executable, "-m", "scripts.experiment", "--variant", v,
                   "--run-seed", str(s), "--games", str(args.games),
                   "--val-every", str(args.val_every), "--date", args.date]
            if args.tag:
                cmd += ["--tag", args.tag]
            jobs.append((name, cmd + args.extra))

    print(f"{len(jobs)} Laeufe, {args.workers} parallel")
    env = {**os.environ, **SINGLE_THREAD_ENV}
    RUNS.mkdir(parents=True, exist_ok=True)

    def run(job):
        name, cmd = job
        (RUNS / name).mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        with open(RUNS / name / "stdout.txt", "w") as out:
            rc = subprocess.call(cmd, cwd=ROOT, env=env, stdout=out, stderr=subprocess.STDOUT)
        print(f"{'OK ' if rc == 0 else 'ERR'} {name} ({(time.time() - t0) / 60:.1f} min)", flush=True)
        return rc

    with ThreadPoolExecutor(args.workers) as ex:
        codes = list(ex.map(run, jobs))
    failed = sum(1 for c in codes if c != 0)
    print(f"Fertig: {len(codes) - failed} ok, {failed} Fehler")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
