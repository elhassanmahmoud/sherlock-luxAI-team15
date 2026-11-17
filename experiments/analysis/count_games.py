"""Wie viele Spiele hat das Projekt gespielt? Zaehlt nur gespeicherte Dateien, spielt nichts (31.10.2026).

    .venv/bin/python experiments/analysis/count_games.py

- Training DQN: Zeilen aller experiments/runs/*/train.csv (eine Zeile je Trainingsspiel), nach manifest.json "kind".
- Validierung im Training: Spalte "games" aller experiments/runs/*/val.csv.
- Training CNN/PPO: Spalte "games" aller experiments/ppo/*/ppo.csv.
- Bewertung: Zeilen aller CSVs unter experiments/compare/ mit den Spalten seed, side, result (eine Zeile je Spiel),
  Zeilen, die in allen Spalten (auch secs) gleich sind, nur einmal; das trifft auch verschiedene Laeufe mit
  genau gleichem Spielverlauf, die Zahl ist also eine untere Grenze. Dazu experiments/runs/*/eval.csv.
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
    compare_only = len(seen)
    # 17.11.2026: Seit dem 01.11. liegen die Bewertungen unter experiments/analysis/ (par_eval-Format mit Spalte
    # "opponent"). Dateien mit Spalte "match" oder "step" haben eine Zeile je Match/Schritt und zaehlen nicht.
    analysis_files = 0
    for f in glob.glob("experiments/analysis/**/*.csv", recursive=True):
        with open(f, encoding="utf-8", errors="ignore") as fh:
            header = fh.readline().strip()
            cols = set(header.split(","))
            if not {"seed", "side", "result", "opponent"} <= cols or cols & {"match", "step"}:
                continue
            analysis_files += 1
            for line in fh:
                rows += 1
                seen.add(hashlib.md5((header + "|" + line.strip()).encode()).digest())
    run_eval = sum(sum(1 for _ in open(e)) - 1 for e in glob.glob("experiments/runs/*/eval.csv"))
    evals = len(seen) + run_eval
    runs = len(glob.glob("experiments/runs/*/train.csv"))
    # 17.11.2026: Datensammlung fuer die Nachahmung (Lehrerspiele und DAgger-Runden), aus collect.json je Sammlung
    imit = {}
    for c in sorted(glob.glob("experiments/imitation/*/collect.json")):
        d = json.load(open(c))
        name = os.path.basename(os.path.dirname(c))
        kind = "smoke" if "smoke" in name else "holdout" if "holdout" in name else (
            "dagger" if d.get("dagger") else "teacher")
        g, s = imit.get(kind, (0, 0))
        imit[kind] = (g + int(d.get("games", 0)), s + int(d.get("samples", 0)))
    imit_games = sum(g for g, _ in imit.values())
    print(f"Training DQN: {train:,} Spiele in {runs} Laeufen, nach Art {kinds}")
    print(f"Training CNN/PPO: {ppo:,} Spiele")
    print(f"Validierung im Training: {val:,} Spiele")
    print(f"Bewertung: {evals:,} Spiele ({rows - len(seen):,} in allen Spalten gleiche Zeilen nur einmal gezaehlt; "
          f"davon experiments/compare {compare_only:,}, dazu {analysis_files} Dateien unter experiments/analysis)")
    for kind, (g, s) in imit.items():
        print(f"Nachahmung {kind}: {g:,} Spiele, {s:,} Einheitsentscheidungen")
    print(f"Zusammen: {train + ppo + val + evals + imit_games:,} Spiele")


if __name__ == "__main__":
    main()
