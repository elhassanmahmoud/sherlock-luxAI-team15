"""Wie viele Spiele hat das Projekt gespielt? Zaehlt nur gespeicherte Dateien, spielt nichts (31.10.2026).

    .venv/bin/python experiments/analysis/count_games.py

- Training DQN: Zeilen aller experiments/runs/*/train.csv (eine Zeile je Trainingsspiel), nach manifest.json "kind".
- Validierung im Training: Spalte "games" aller experiments/runs/*/val.csv.
- Training CNN/PPO: Spalte "games" aller experiments/ppo/*/ppo.csv.
- Bewertung: Zeilen aller CSVs unter experiments/compare/ mit den Spalten seed, side, result (eine Zeile je Spiel),
  exakt doppelt gespeicherte Zeilen nur einmal; dazu experiments/runs/*/eval.csv.
"""
import glob
import hashlib
import json
import os

import pandas as pd


def main():
    train, kinds = 0, {}
    for t in glob.glob("experiments/runs/*/train.csv"):
        n = sum(1 for _ in open(t)) - 1
        m = os.path.join(os.path.dirname(t), "manifest.json")
        kind = json.load(open(m)).get("kind", "?") if os.path.exists(m) else "?"
        train += n
        kinds[kind] = kinds.get(kind, 0) + n
    val = sum(int(pd.read_csv(v)["games"].sum()) for v in glob.glob("experiments/runs/*/val.csv")
              if "games" in pd.read_csv(v, nrows=0).columns)
    ppo = sum(int(pd.read_csv(p)["games"].sum()) for p in glob.glob("experiments/ppo/*/ppo.csv"))
    seen, rows = set(), 0
    for f in glob.glob("experiments/compare/**/*.csv", recursive=True):
        with open(f) as fh:
            header = fh.readline().strip()
            if not {"seed", "side", "result"} <= set(header.split(",")):
                continue
            for line in fh:
                rows += 1
                seen.add(hashlib.md5((header + "|" + line.strip()).encode()).digest())
    run_eval = sum(sum(1 for _ in open(e)) - 1 for e in glob.glob("experiments/runs/*/eval.csv"))
    evals = len(seen) + run_eval
    runs = len(glob.glob("experiments/runs/*/train.csv"))
    print(f"Training DQN: {train:,} Spiele in {runs} Laeufen, nach Art {kinds}")
    print(f"Training CNN/PPO: {ppo:,} Spiele")
    print(f"Validierung im Training: {val:,} Spiele")
    print(f"Bewertung: {evals:,} Spiele ({rows - len(seen):,} doppelt gespeicherte Zeilen nicht gezaehlt)")
    print(f"Zusammen: {train + ppo + val + evals:,} Spiele")


if __name__ == "__main__":
    main()
